"""
Version améliorée de `scrape_trusted_sites.py` (drop-in) — **docstrings en français**

Objectifs (tout en conservant l'API publique existante) :
1) Gérer `h1/h4/ol/table/blockquote` dans l'extraction structurée **sans modifier le format de retour**.
2) Enregistrer les **hyperliens par section** (persistés dans le JSON via `save_page_as_json`, sans changer
   le retour Python d'`extract_structured_content`).
3) Effectuer un **crawl BFS** jusqu'à **profondeur = 2** sur le **même domaine**, avec **limite de pages par site**.
4) Extraire des **métadonnées** (date/auteur/canonique + **source originelle**), persistées avec la page JSON.

Compatibilité :
- Signatures conservées (mêmes noms d'arguments) pour :
  * `is_irrelevant_text(text: str) -> bool`
  * `extract_useful_links(start_url: str, base_url: str) -> List[str]`
  * `extract_structured_content(page_url: str) -> Tuple[str, List[Dict[str, str]]]`
  * `save_page_as_json(base_url: str, page_url: str, title: str, sections: list, outlinks: list, output_dir: Optional[str] = None) -> None`
  * `scrape_all_trusted_sites(trusted_sites: list, output_dir: str, max_pages_per_site: int = 200, max_depth: int = 2) -> dict`

Sécurisation & observabilité :
- Ajout d'un **logger** module (`logging.getLogger(__name__)`) + une fonction utilitaire `_log_print()`
  qui **log** et **print** les événements clés (début/fin de fonction, comptages, erreurs).
- Try/except prudents avec journalisation des erreurs sans interrompre la collecte.
"""
from __future__ import annotations

import sys
import json
import os
import re
import time
import logging
import importlib.util
from urllib.parse import urljoin, urlparse, urldefrag
from collections import deque
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path

import requests
from bs4 import BeautifulSoup


from config.config import WEB_SITES_MODULE_PATH, WEB_SITES_JSON_HEALTH_DOC_BASE

# -----------------------------------------------------------------------------
# Journalisation (logger + print)
# -----------------------------------------------------------------------------

logger = logging.getLogger(__name__)
if not logger.handlers:
    _handler = logging.StreamHandler()
    _formatter = logging.Formatter('[%(levelname)s] %(asctime)s - %(name)s - %(message)s')
    _handler.setFormatter(_formatter)
    logger.addHandler(_handler)
logger.setLevel(logging.INFO)


def load_trusted_sites(module_path: str) -> List[Dict[str, Any]]:
    """Charge la variable `trusted_sites` depuis un fichier .py (liste de dicts)."""
    try:
        module_path = str(module_path)
        spec = importlib.util.spec_from_file_location("trusted_web_sites", module_path)
        if spec is None or spec.loader is None:
            print(f"[ERREUR] Spec introuvable pour {module_path}", file=sys.stderr)
            return []
        mod = importlib.util.module_from_spec(spec)
        sys.modules["trusted_web_sites"] = mod  # optionnel, utile si imports internes
        spec.loader.exec_module(mod)
        sites = getattr(mod, "trusted_sites", [])
        if not isinstance(sites, list):
            print("[ERREUR] `trusted_sites` n'est pas une liste.", file=sys.stderr)
            return []
        return sites
    except Exception as e:
        print(f"[ERREUR] Impossible de charger la liste des sites : {e}", file=sys.stderr)
        return []


def _ensure_output_dir(path: str | Path) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p



def _log_print(level: str, msg: str, *args) -> None:
    """Log + print un message formaté (sécurisation/trace)."""
    try:
        text = msg % args if args else msg
    except Exception:
        text = msg
    # print pour traces rapides en console
    try:
        print(text)
    except Exception:
        pass
    # logger pour traces structurées
    lvl = (level or "info").lower()
    if lvl == "debug":
        logger.debug(text)
    elif lvl == "warning":
        logger.warning(text)
    elif lvl == "error":
        logger.error(text)
    else:
        logger.info(text)


# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0 Safari/537.36"
)
HEADERS = {"User-Agent": USER_AGENT, "Accept-Language": "fr,fr-FR;q=0.9,en;q=0.8"}
TIMEOUT = 20
REQUESTS_SLEEP_S = 0.5  # courtoisie réseau

# Profondeur/limites par défaut
MAX_LINKS_PER_START_PAGE = 200  # conservé pour compatibilité
DEFAULT_MAX_DEPTH = 2
DEFAULT_MAX_PAGES_PER_SITE = 200

# Exclusions d'URL (authent, médias, documents binaires, etc.)
STOP_URL_PATTERNS = [
    re.compile(p, re.I)
    for p in [
        r"/login", r"/connexion", r"/auth", r"/account", r"/mon-compte",
        r"/inscription", r"/register", r"/subscribe", r"/abonn", r"/newsletter",
        r"/cart", r"/panier", r"/shop", r"/boutique", r"/store",
        r"/press", r"/presse", r"/media", r"/ads", r"/advert",
        r"/jobs", r"/emploi", r"/recrut", r"/stage",
        r"/contact", r"/aide", r"/faq",
        r"/mentions-?legales", r"/cgu", r"/cgv", r"/cookies?", r"/privacy", r"/donnees?-personnelles",
        r"/plan-du-site", r"/sitemap", r"/rss",
        r"\.pdf($|\?)", r"\.docx?($|\?)", r"\.xlsx?($|\?)",
        r"\.jpg($|\?)", r"\.jpeg($|\?)", r"\.png($|\?)", r"\.gif($|\?)", r"\.svg($|\?)",
        r"\.mp4($|\?)", r"\.mp3($|\?)", r"\.zip($|\?)", r"\.rar($|\?)",
        r"/tag/", r"/etiquette/", r"/label/",
        r"/imprimer", r"/print/",
        r"/share", r"/twitter", r"/facebook", r"/linkedin", r"/youtube", r"/instagram",
        r"/404", r"/erreur",
    ]
]

# Mots-clés textuels à ignorer (renforcé)
IRRELEVANT_TEXT_KEYWORDS = [
    # bannières/politiques/navigation
    "cookie", "cookies", "consentement", "accepter les cookies", "paramètres des cookies",
    "mentions légales", "conditions générales", "conditions d'utilisation", "cgu", "cgv",
    "politique de confidentialité", "protection des données", "rgpd", "plan du site",
    "fil d'ariane", "breadcrumb", "télécharger", "imprimer", "partager", "newsletter",
    "abonnement", "s'abonner", "rss", "javascript", "captcha",
    "connexion", "se connecter", "mon compte", "panier", "don", "faire un don",
    # bruit éditorial générique
    "publicité", "sponsorisé", "publié par le service communication",
]

# Mots-clés de pertinence (renforcés) — maintien à domicile / gériatrie / accompagnement
KEYWORDS = [
    # maintien à domicile / autonomie
    "maintien à domicile", "autonomie", "perte d'autonomie", "aidant", "aidants",
    "aidant familial", "accompagnement", "plan d'aide", "plan d’accompagnement", "ppa",
    "agir", "agirir", "aggir", "gir", "apa", "mdph", "ccas", "clic",
    # prévention / risques
    "prévention des chutes", "chute", "escarres", "ulcères", "plaies", "pansements",
    "dénutrition", "nutrition", "hydratation", "déshydratation", "douleur",
    # troubles / maladies chroniques
    "alzheimer", "parkinson", "démence", "troubles cognitifs", "dépression",
    "bpco", "insuffisance cardiaque", "diabète", "hta", "arthrose", "ostéoporose",
    # soins / professionnels
    "infirmier", "infirmière", "kinésithérapeute", "ergothérapeute", "orthophoniste",
    "médecin", "pharmacien", "téléassistance", "télémédecine", "télésoins",
    "had", "hospitalisation à domicile", "ssiad", "service de soins infirmiers à domicile",
    # actes de la vie quotidienne
    "toilette", "habillage", "alimentation", "mobilité", "déambulateur", "fauteuil",
    "barres d'appui", "aménagement du logement", "adaptation du logement",
    # sécurité / environnement
    "domotique", "détecteur de chute", "canicule", "plan canicule", "hiver froid",
    # médicaments / iatrogénie
    "traitement", "ordonnance", "posologie", "iatrogénie", "anticoagulant", "analgésique",
    # social / isolement / répit
    "isolement social", "solitude", "stimulation cognitive", "atelier mémoire", "répit aidants",
    # droits / aides
    "allocation", "aide financière", "dossier", "évaluation", "grille aggir",
]

# -----------------------------------------------------------------------------
# Aides internes
# -----------------------------------------------------------------------------

def _same_domain(url: str, base_url: str) -> bool:
    """Vrai si `url` et `base_url` partagent le même host (sécurité domaine)."""
    try:
        return urlparse(url).netloc == urlparse(base_url).netloc
    except Exception as e:
        _log_print("error", "[_same_domain] Erreur: %s", e)
        return False


def _clean_url(href: str, base_url: str) -> Optional[str]:
    """Nettoie et résout une URL relative (supprime fragments)."""
    try:
        if not href:
            return None
        if href.startswith("mailto:") or href.startswith("tel:"):
            return None
        href = urljoin(base_url, href)
        href, _ = urldefrag(href)
        return href
    except Exception as e:
        _log_print("error", "[_clean_url] Erreur: %s", e)
        return None


def _blocked_by_stop_patterns(url: str) -> bool:
    """Vrai si l'URL correspond à un motif explicitement exclu (STOP)."""
    try:
        return any(p.search(url) for p in STOP_URL_PATTERNS)
    except Exception as e:
        _log_print("error", "[_blocked_by_stop_patterns] Erreur: %s", e)
        return False


def is_irrelevant_text(text: str) -> bool:
    """Filtre conservateur de bruit/boilerplate (renforcé).

    Retourne True si le texte est vide ou contient des mots-clés de bruit (cookies, CGU, etc.).
    """
    try:
        if not text:
            return True
        t = text.strip().lower()
        if not t:
            return True
        res = any(k in t for k in IRRELEVANT_TEXT_KEYWORDS)
        if res:
            _log_print("debug", "[is_irrelevant_text] Texte ignoré: %.80s…", t)
        return res
    except Exception as e:
        _log_print("error", "[is_irrelevant_text] Erreur: %s", e)
        return True


# Signature publique conservée

def is_relevant_link(url: str) -> bool:
    """Heuristique de pertinence basée sur l'URL (signature conservée).

    NB: On ne dispose pas ici de l'ancre; on combine les mots-clés dans l'URL
    et le filtre STOP pour une décision rapide.
    """
    try:
        if not url:
            return False
        if _blocked_by_stop_patterns(url):
            return False
        path = urlparse(url).path.lower()
        score = sum(1 for kw in KEYWORDS if kw in path)
        return score >= 1 or True  # par défaut permissif, filtrages ailleurs
    except Exception as e:
        _log_print("error", "[is_relevant_link] Erreur: %s", e)
        return False


def _request_soup(url: str) -> Tuple[Optional[BeautifulSoup], Optional[str]]:
    """Récupère et parse une page HTML, retourne (soup, url_finale)."""
    try:
        _log_print("info", "[_request_soup] GET %s", url)
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        if r.status_code >= 400:
            _log_print("warning", "[_request_soup] Statut HTTP %s pour %s", r.status_code, url)
            return None, None
        return BeautifulSoup(r.text, "html.parser"), r.url
    except Exception as e:
        _log_print("error", "[_request_soup] Erreur: %s", e)
        return None, None


def _extract_metadata(soup: BeautifulSoup, url: str) -> Dict[str, Optional[str]]:
    """Extrait des métadonnées communes (titre, dates, auteur, canonique, langue, source)."""
    try:
        def _get(*selectors):
            for sel in selectors:
                el = soup.select_one(sel)
                if el:
                    if el.has_attr("content"):
                        return el.get("content")
                    if el.has_attr("datetime"):
                        return el.get("datetime")
                    if el.name == "link" and el.has_attr("href"):
                        return el.get("href")
                    txt = el.get_text(separator=" ", strip=True)
                    if txt:
                        return txt
            return None

        md = {
            "title": _get("meta[property='og:title']", "meta[name='title']", "title"),
            "published_time": _get(
                "meta[property='article:published_time']",
                "time[pubdate]",
                "meta[name='date']",
                "meta[name='dcterms.date']",
                "meta[name='DC.date']",
                "time[datetime]",
            ),
            "modified_time": _get(
                "meta[property='article:modified_time']",
                "meta[name='last-modified']",
                "meta[name='revised']",
            ),
            "author": _get(
                "meta[name='author']",
                "meta[property='article:author']",
                "a[rel='author']",
                "span.author", "div.author", "address .author",
            ),
            "canonical": _get("link[rel='canonical']"),
            "lang": _get("html[lang]"),
        }

        # Normalisation simple de dates (si ISO)
        for k in ("published_time", "modified_time"):
            v = md.get(k)
            if v:
                try:
                    dt = datetime.fromisoformat(v.replace("Z", "+00:00")) if "-" in v else None
                    if dt:
                        md[k] = dt.isoformat()
                except Exception:
                    pass

        md["source_url"] = url  # URL d'origine (après redirections)
        _log_print("debug", "[_extract_metadata] Métadonnées: %s", md)
        return md
    except Exception as e:
        _log_print("error", "[_extract_metadata] Erreur: %s", e)
        return {"source_url": url}


def _table_to_text(table) -> str:
    """Convertit un <table> en texte compact type Markdown (entêtes + lignes)."""
    try:
        headers = []
        rows = []
        thead = table.find("thead")
        if thead:
            ths = [th.get_text(" ", True) for th in thead.find_all(["th", "td"]) ]
            if ths:
                headers = ths
        else:
            first_tr = table.find("tr")
            if first_tr:
                ths = [th.get_text(" ", True) for th in first_tr.find_all(["th", "td"]) ]
                headers = ths

        for tr in table.find_all("tr"):
            cells = [td.get_text(" ", True) for td in tr.find_all(["td", "th"]) ]
            if cells:
                rows.append(cells)

        lines = []
        if headers:
            lines.append(" | ".join(headers))
            lines.append(" | ".join(["---"] * len(headers)))
        for r in rows:
            lines.append(" | ".join(r))
        txt = "".join(lines)
        _log_print("debug", "[_table_to_text] %d lignes", len(rows))
        return txt
    except Exception as e:
        _log_print("error", "[_table_to_text] Erreur: %s", e)
        return ""


def _iter_content_blocks(soup: BeautifulSoup):
    """Itère les blocs de contenu dans l'ordre visuel utile."""
    try:
        for el in soup.find_all(["h1", "h2", "h3", "h4", "p", "ul", "ol", "table", "blockquote"]):
            yield el.name, el
    except Exception as e:
        _log_print("error", "[_iter_content_blocks] Erreur: %s", e)
        return


def _extract_sections_and_links(soup: BeautifulSoup, page_url: str) -> Tuple[List[Dict[str, str]], List[str], List[List[Dict[str, str]]]]:
    """
    Extrait :
      - sections_plain : List[{"tag": str, "text": str}] (compatible avec l'existant)
      - outlinks       : List[str] (URLs uniques trouvées dans le contenu)
      - sections_links : List[List[{"href": str, "anchor": str}]] (parallèle à sections_plain)
    """
    sections_plain: List[Dict[str, str]] = []
    sections_links: List[List[Dict[str, str]]] = []
    outlinks_set = set()
    try:
        for tag, el in _iter_content_blocks(soup):
            if tag == "table":
                text = _table_to_text(el)
            elif tag in ("ul", "ol"):
                items = [li.get_text(separator=" ", strip=True) for li in el.find_all("li")]
                text = "".join(f"- {it}" for it in items if it)
            else:
                text = el.get_text(separator=" ", strip=True)

            if not text or is_irrelevant_text(text):
                continue

            links = []
            for a in el.find_all("a", href=True):
                href = _clean_url(a.get("href"), page_url)
                if not href or _blocked_by_stop_patterns(href):
                    continue
                links.append({
                    "href": href,
                    "anchor": a.get_text(separator=" ", strip=True) or None,
                })
                outlinks_set.add(href)

            sections_plain.append({"tag": tag, "text": text})
            sections_links.append(links)

        _log_print("info", "[_extract_sections_and_links] %d sections, %d outlinks", len(sections_plain), len(outlinks_set))
        return sections_plain, sorted(outlinks_set), sections_links
    except Exception as e:
        _log_print("error", "[_extract_sections_and_links] Erreur: %s", e)
        return sections_plain, sorted(outlinks_set), sections_links


# -----------------------------------------------------------------------------
# API publique : extraction de contenu structuré
# -----------------------------------------------------------------------------

def extract_structured_content(page_url: str) -> Tuple[str, List[Dict[str, str]]]:
    """Télécharge et extrait (titre, sections) de la page.

    Le format de retour est **inchangé** : `(title: str, sections: List[Dict[tag,text]])`.
    Les liens par section sont uniquement ajoutés lors de la persistance JSON.
    """
    try:
        soup, final_url = _request_soup(page_url)
        if not soup:
            return "", []
        title = soup.title.get_text(" ", True) if soup.title else ""
        sections_plain, _, _ = _extract_sections_and_links(soup, final_url or page_url)
        if not sections_plain:
            main = soup.select_one("main, article, [role='main']")
            if main:
                sections_plain, _, _ = _extract_sections_and_links(main, final_url or page_url)
        _log_print("info", "[extract_structured_content] %s → %d sections", (final_url or page_url), len(sections_plain))
        return title, sections_plain
    except Exception as e:
        _log_print("error", "[extract_structured_content] Erreur: %s", e)
        return "", []


# -----------------------------------------------------------------------------
# API publique : découverte de liens utiles (BFS profondeur<=2)
# -----------------------------------------------------------------------------

def extract_useful_links(start_url: str, base_url: str) -> List[str]:
    """Explore en BFS depuis `start_url` (même domaine) et retourne les liens utiles.

    - Profondeur maximale par défaut : 2 (contrôlée par constantes)
    - Limite : `MAX_LINKS_PER_START_PAGE` (compatibilité avec l'existant)
    """
    visited = set()
    results: List[str] = []
    try:
        q = deque([(start_url, 0)])
        while q and len(results) < MAX_LINKS_PER_START_PAGE:
            url, depth = q.popleft()
            if url in visited:
                continue
            visited.add(url)

            if not _same_domain(url, base_url) or _blocked_by_stop_patterns(url):
                continue

            soup, final_url = _request_soup(url)
            if not soup:
                continue

            for a in soup.find_all("a", href=True):
                href = _clean_url(a.get("href"), final_url or url)
                if not href or not _same_domain(href, base_url) or _blocked_by_stop_patterns(href):
                    continue
                anchor = a.get_text(separator=" ", strip=True).lower()
                url_l = href.lower()
                kw_hit = any(kw in url_l or kw in anchor for kw in KEYWORDS)
                if kw_hit or depth < DEFAULT_MAX_DEPTH:
                    if href not in visited and href not in results:
                        results.append(href)
                        if depth + 1 <= DEFAULT_MAX_DEPTH:
                            q.append((href, depth + 1))

            _log_print("debug", "[extract_useful_links] depth=%d, résultats=%d, queue=%d", depth, len(results), len(q))
            time.sleep(REQUESTS_SLEEP_S)
        _log_print("info", "[extract_useful_links] %d liens retournés", len(results))
        return results[:MAX_LINKS_PER_START_PAGE]
    except Exception as e:
        _log_print("error", "[extract_useful_links] Erreur: %s", e)
        return results[:MAX_LINKS_PER_START_PAGE]


# -----------------------------------------------------------------------------
# API publique : persistance JSON avec métadonnées & liens par section
# -----------------------------------------------------------------------------

def save_page_as_json(base_url: str, page_url: str, title: str, sections: list, outlinks: list, output_dir: Optional[str] = None) -> None:
    """Sauvegarde la page en JSON (métadonnées + liens par section).

    - Format de `sections` conservé ; on ajoute la clé `links` lors de l'écriture JSON uniquement.
    - `output_dir` est optionnel.
    """
    try:
        parsed = urlparse(page_url)
        safe_path = (parsed.path or "/").rstrip("/").replace("/", "_")
        if not safe_path:
            safe_path = "index"
        fname = f"{parsed.netloc}{safe_path}.json"

        if not output_dir:
            output_dir = os.path.join("outputs", "web_pages_json")
        os.makedirs(output_dir, exist_ok=True)

        soup, final_url = _request_soup(page_url)
        metadata = _extract_metadata(soup, (final_url or page_url)) if soup else {"source_url": page_url}

        sections_links: List[List[Dict[str, str]]] = []
        if soup:
            _, _, sections_links = _extract_sections_and_links(soup, final_url or page_url)

        if len(sections_links) != len(sections):
            if len(sections_links) < len(sections):
                sections_links.extend([] for _ in range(len(sections) - len(sections_links)))
            else:
                sections_links = sections_links[:len(sections)]

        payload = {
            "base_url": base_url,
            "page_url": page_url,
            "resolved_url": final_url or page_url,
            "title": title,
            "metadata": metadata,
            "sections": [
                {**sec, "links": sections_links[i] if i < len(sections_links) else []}
                for i, sec in enumerate(sections)
            ],
            "outlinks": outlinks,
            "saved_at": datetime.utcnow().isoformat() + "Z",
        }

        path = os.path.join(output_dir, fname)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        _log_print("info", "[save_page_as_json] Écrit: %s", path)
    except Exception as e:
        _log_print("error", "[save_page_as_json] Erreur: %s", e)


# -----------------------------------------------------------------------------
# Orchestrateur principal
# -----------------------------------------------------------------------------
def scrape_all_trusted_sites(
    trusted_sites: Optional[List[Dict[str, Any]]] = None,
    output_dir: Optional[str | Path] = None,
) -> List[Path]:
    """
    Scrape les sites de confiance et sauvegarde les JSON.
    - Paramètres optionnels : si absents, on charge depuis la config (rétro-compat).
    - Retourne la liste des fichiers JSON écrits (pratique pour les tests).
    """
    # Valeurs par défaut si non fournies (→ compat avec tes anciens appels sans arguments)
    if trusted_sites is None:
        trusted_sites = load_trusted_sites(WEB_SITES_MODULE_PATH)
    if output_dir is None:
        output_dir = WEB_SITES_JSON_HEALTH_DOC_BASE

    outdir = _ensure_output_dir(output_dir)
    written: List[Path] = []

    for site in trusted_sites:
        name = site.get("name")
        base_url = site.get("base_url")
        start_pages = site.get("start_pages", [])
        print(f"\n[INFO] Traitement du site : {name} ({base_url})")
        for start_page in start_pages:
            print(f"  > Page de départ : {start_page}")

            # 🔽 1. Extraire le contenu de la page de départ elle-même
            try:
                title, sections = extract_structured_content(start_page)
                if sections:
                    outlinks = extract_useful_links(start_page, base_url) or []
                    save_page_as_json(base_url, start_page, title, sections, outlinks, str(outdir))
                    # save_page_as_json(base_url, start_page, title, sections)  # <- si ta signature ne prend pas output_dir
                    written.append(Path(outdir) / "???")  # (facultatif : si save_page_as_json renvoie un chemin, utilise-le)
                else:
                    print(f"[WARN] Aucun contenu utile trouvé pour page de départ : {start_page}")
            except Exception as e:
                print(f"[ERREUR] Extraction échouée pour {start_page} : {e}", file=sys.stderr)

            # 🔽 2. Ensuite, explorer les liens internes filtrés
            try:
                level1_links = extract_useful_links(start_page, base_url)
                print(f"    - {len(level1_links)} liens retenus (filtrés)")
                for page_url in level1_links:
                    try:
                        title, sections = extract_structured_content(page_url)
                        if sections:
                            # 🔹 OUTLINKS de la page courante (obligatoire pour save_page_as_json)
                            page_outlinks = extract_useful_links(page_url, base_url) or []
                            save_page_as_json(
                                base_url, page_url, title, sections, page_outlinks,
                                output_dir=str(outdir)  # <-- keyword pour éviter l'ambiguïté
                            )
                        else:
                            print(f"[WARN] Aucun contenu utile trouvé pour {page_url}")
                    except Exception as e:
                        print(f"[ERREUR] Extraction échouée pour {page_url} : {e}", file=sys.stderr)
            except Exception as e:
                print(f"[ERREUR] Exploration liens depuis {start_page} : {e}", file=sys.stderr)

    return written


# -----------------------------------------------------------------------------
# Exécution manuelle:
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    SITES = [
        {
            "base_url": "https://www.has-sante.fr",
            "start_urls": [
                "https://www.has-sante.fr/jcms/c_2603694/fr/qualite-de-la-prise-en-charge-de-la-personne-agee",
            ],
        }
    ]
    out = scrape_all_trusted_sites(SITES, output_dir=os.path.join("outputs", "web_pages_json"))
    print(json.dumps(out, indent=2, ensure_ascii=False))





