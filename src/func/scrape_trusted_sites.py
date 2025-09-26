# src/func/scrape_trusted_sites.py
"""
    Module de scraping des sites de confiance.

    Il extrait un contenu structuré (titres h1–h4, paragraphes, listes, blockquotes, tables),
    enregistre les hyperliens par section, et explore en BFS (profondeur 2) limité au même
    domaine et à un nombre de pages par site. Les pages sont enrichies de métadonnées
    (titre, dates, auteur, URL canonique, source originelle) et sauvegardées en JSON dans
    le répertoire configuré. L’ingestion de PDF peut être activée pour des domaines autorisés,
    tout en conservant un format de sortie stable pour le pipeline d’indexation.

"""

from __future__ import annotations

import os
import re
import json
import time
import logging
import importlib.util
from pathlib import Path
from typing import Iterable, List, Tuple, Dict, Optional, Any
from urllib.parse import urlparse, urljoin
from datetime import datetime
import requests
import hashlib
from bs4 import BeautifulSoup
from bs4.element import Tag
from collections import deque

# ===================== #
# Config                #
# ===================== #
from config.config import (
    WEB_SITES_MODULE_PATH,
    WEB_SITES_JSON_HEALTH_DOC_BASE,
)

# ===================== #
# Logging               #
# ===================== #
logger = logging.getLogger(__name__)
if not logger.handlers:
    h = logging.StreamHandler()
    fmt = logging.Formatter("%(levelname)s - %(message)s")
    h.setFormatter(fmt)
    logger.addHandler(h)
logger.setLevel(logging.INFO)

# ===================== #
# Constantes            #
# ===================== #

# Constantes liées à la gestion des PDF
ALLOW_PDF = True  # Feature flag global
PDF_ALLOWED_DOMAINS = {
    "has-sante.fr",
    "pour-les-personnes-agees.gouv.fr",
    "msdmanuals.com",
    "sfgg.org",
    "sfcardio.fr",
    "societe-francaise-neurovasculaire.fr",
    # SPLF (pdf hébergés sur un sous-domaine dédié)
    "splf.fr",           # (HTML)
    "docs.splf.fr",      # (PDF)
    # INCa (nouveau site) + ancien domaine par prudence
    "cancer.fr",
    "e-cancer.fr",
    # SPILF (infectiologie) – PDF sur le domaine principal
    "infectiologie.com",
    # Cerba – PDFs sur un sous-domaine
    "lab-cerba.com",             # (HTML)
    "documents.lab-cerba.com",   # (PDF)
    # MedG / RecoMedicales (principalement HTML, mais on autorise au cas où)
    "medg.fr",
    "recomedicales.fr",
}


# Contraintes appliquées aux PDF (25 MO, 20 pages, délai réponse: 15secondes)
PDF_MAX_BYTES = 25 * 1024 * 1024
PDF_MAX_PAGES = 20

# Autres types de constantes
# Profondeur max pour l'exploration (BFS)
DEFAULT_MAX_DEPTH = 2

# Nombre max de pages à traiter. Limite fixée pour chaque start_page
DEFAULT_MAX_PAGES_PER_SITE = 200

# Réseau
REQUESTS_TIMEOUT_S = 20
REQUESTS_SLEEP_S = 0.4

# Sélecteurs du conteneur principal de contenu éditorial
MAIN_SELECTORS = [
    # Drupal (cancer.fr, Cerba…)
    "#block-mainpagecontent", ".node__content", ".region--content",
    # Corps d’article génériques
    ".content__body", ".article-body", ".article-content",
    ".entry-content", ".post-content", ".content-area", ".single-content", ".content",
    # WordPress/Elementor (SFGG…)
    ".elementor", ".elementor-section",
    # MSD Manuals (corps principal)
    "#topic",
    # Généraux/HTML5
    "main", "article", "[role=main]",
    # Fallbacks communs
    "#content", "#main",
    # Ajouts proposés (faible risque, haute utilité)
    ".main-content", ".page-content",
]


# Mots-clés de bruit pour filtrage conservateur
IRRELEVANT_TEXT_KEYWORDS = {
    "menu", "navigation", "cookies", "cookie", "rgpd", "gdpr",
    "cgu", "cgv", "mentions", "légal", "légales", "footer",
    "newsletter", "partage", "share", "social", "abonnez-vous",
    "publicité", "sponsor", "breadcrumb", "fil d'ariane",
    "compte", "connexion", "login", "inscription",
}

# =====================================================#
#                                                      #
# Fonctions de gestion détection, extraction texte PDF #
#                                                      #
# =====================================================#
# 1. Détection des PDF et téléchargement binaire

def _is_pdf_url(url: str) -> bool:
    """Détection naïve par extension."""
    return url.lower().split("?", 1)[0].endswith(".pdf")

def _normalize_host(host: str) -> str:
    host = host.lower().strip()
    if host.startswith("www."):
        host = host[4:]
    return host

def _is_allowed_pdf_domain(url: str) -> bool:
    host = _normalize_host(urlparse(url).netloc)
    return host in PDF_ALLOWED_DOMAINS

def _head_content_type(url: str) -> Optional[str]:
    """HEAD rapide pour typer la ressource (best effort)."""
    try:
        r = requests.head(url, allow_redirects=True, timeout=REQUESTS_TIMEOUT_S)
        ct = r.headers.get("Content-Type", "").split(";")[0].strip().lower()
        return ct or None
    except Exception:
        return None


# 2. Chargement des binaires
def _download_binary(url: str) -> Tuple[Optional[bytes], Optional[str], Dict[str, str]]:
    """
    Télécharge en binaire (GET). Retourne (bytes, final_url, headers).
    Garde-fous sur taille.
    """
    try:
        with requests.get(url, stream=True, allow_redirects=True, timeout=REQUESTS_TIMEOUT_S) as r:
            r.raise_for_status()
            final_url = r.url
            headers = {k: v for k, v in r.headers.items()}
            total = 0
            chunks = []
            for chunk in r.iter_content(1024 * 64):
                if chunk:
                    chunks.append(chunk)
                    total += len(chunk)
                    if total > PDF_MAX_BYTES:
                        _log_print("warning", "[🟧 PDF] Abandon: taille > %d bytes: %s", PDF_MAX_BYTES, url)
                        return None, final_url, headers
            return b"".join(chunks), final_url, headers
    except Exception as e:
        _log_print("warning", "[🟧 PDF] Téléchargement échoué: %s -> %s", url, e)
        return None, None, {}


# 3. Extraction texte PDF → sections
from io import BytesIO
from pdfminer.high_level import extract_text

def _pdf_to_sections(pdf_bytes: bytes, max_pages: int = PDF_MAX_PAGES) -> Tuple[str, List[Dict[str, str]], Dict[str, Any]]:
    """
    Extrait un texte brut depuis un PDF et le transforme en sections compatibles.
    - Heuristique simple: split par double sauts de ligne -> paragraphes.
    - Retourne (titre, sections, meta_pdf) ; 'titre' = 1ère ligne non vide.
    """
    try:
        # Texte global (limitation du nb de pages via laparams non trivial ici ; on applique plutôt un 'cut' après)
        text = extract_text(BytesIO(pdf_bytes)) or ""
        if not text.strip():
            # Probablement un PDF scanné ; on laisse un message clair
            return "Titre non disponible (PDF non textuel)", [], {"page_count": None, "textual": False}

        # Normalisation
        raw = text.replace("\r", "\n")
        # Heuristique: couper par blocs (2+ sauts) puis nettoyer les hyphens de fin de ligne
        blocks = [b.strip() for b in raw.split("\n\n") if b.strip()]
        # Titre = 1er bloc court si pertinent
        title = "Titre non disponible"
        for b in blocks[:5]:
            if 3 <= len(b.split()) <= 20:
                title = b.strip()
                break

        sections: List[Dict[str, str]] = []
        for b in blocks:
            # Dé-hyphénation simple
            b = b.replace("-\n", "").replace("\n", " ").strip()
            if not b:
                continue
            # Si gros blocs => on coupe en phrases/segments pour éviter les chunks monstrueux
            if len(b) > 2000:
                parts = [p.strip() for p in b.split(". ") if p.strip()]
                for p in parts:
                    if p:
                        sections.append({"tag": "p", "texte": p})
            else:
                sections.append({"tag": "p", "texte": b})

        # Métadonnées PDF minimales
        meta = {
            "source_format": "pdf",
            "textual": True,
            "sha256": hashlib.sha256(pdf_bytes).hexdigest(),
            "filesize": len(pdf_bytes),
        }
        return title, sections, meta
    except Exception as e:
        _log_print("warning", "[PDF] Parsing échoué: %s", e)
        return "Sans titre (PDF erreur)", [], {"source_format": "pdf", "textual": None}



# ===================== #
# Utils                 #
# ===================== #

def _log_print(level: str, msg: str, *args):
    try:
        if level == "info":
            logger.info(msg, *args)
        elif level == "warning":
            logger.warning(msg, *args)
        elif level == "error":
            logger.error(msg, *args)
        else:
            logger.debug(msg, *args)
    except Exception:
        # logging must never break pipeline
        pass


def _normalize_space(s: str) -> str:
    return " ".join(s.split())


def _text(el) -> str:
    return _normalize_space(el.get_text(" ", strip=True)) if el else ""


def _normalized_netloc(url: str) -> str:
    try:
        netloc = urlparse(url).netloc.lower()
        return netloc[4:] if netloc.startswith("www.") else netloc
    except Exception:
        return url


def _same_site(a: str, b: str) -> bool:
    return _normalized_netloc(a) == _normalized_netloc(b)


def _normalize_url(href: str, base_url: str) -> str:
    try:
        href = urljoin(base_url, href)
        u = urlparse(href)
        return u._replace(fragment="").geturl()
    except Exception:
        return href


def _blocked_by_stop_patterns(href: str) -> bool:
    if not href:
        return True
    # évite mailto:, tel:, fichiers binaires, etc.
    if href.startswith(("mailto:", "tel:", "javascript:", "#")):
        return True
    # extensions à ignorer
    if re.search(r"\.(pdf|zip|rar|7z|png|jpg|jpeg|gif|svg|mp3|mp4|avi|mov)(\?|$)", href, re.I):
        return True
    return False


def _pick_root(soup: BeautifulSoup) -> Tag:
    for sel in MAIN_SELECTORS:
        node = soup.select_one(sel)
        if node:
            return node
    return soup.body or soup



def is_irrelevant_text(text: str) -> bool:
    try:
        if not text:
            return True
        t = text.strip()
        if not t:
            return True
        if len(t) < 5:
            return True
        low = t.lower()
        # si assez long, on garde
        if len(low) >= 60:
            return False
        # mots-clés de bruit -> on rejette seulement si court
        if any(k in low for k in IRRELEVANT_TEXT_KEYWORDS):
            return True
        return False
    except Exception:
        return False


# ===================== #
# HTTP / Parsing        #
# ===================== #

_DEFAULT_HEADERS = {
    "User-Agent": "OBY-IA Scraper (+https://oby-chat.onrender.com)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

def _request_soup(url: str) -> Tuple[Optional[BeautifulSoup], Optional[str]]:
    try:
        r = requests.get(url, headers=_DEFAULT_HEADERS, timeout=REQUESTS_TIMEOUT_S)
        r.raise_for_status()
        time.sleep(REQUESTS_SLEEP_S)
        soup = BeautifulSoup(r.text, "html.parser")
        final_url = str(r.url)
        _log_print("info", "[_request_soup] GET %s", final_url)
        return soup, final_url
    except Exception as e:
        _log_print("warning", "[_request_soup] FAIL %s -> %s", url, e)
        return None, None


def _extract_title(soup: BeautifulSoup) -> str:
    for sel in ('meta[property="og:title"]', 'meta[name="twitter:title"]'):
        m = soup.select_one(sel)
        if m and m.get("content"):
            return m["content"].strip()
    if soup.title and soup.title.string:
        return soup.title.string.strip()
    h1 = soup.select_one("main h1, article h1, h1")
    return _text(h1) if h1 else "Titre non disponible"


def _table_to_text(table) -> str:
    rows = []
    for tr in table.find_all("tr"):
        cells = [_text(td) for td in tr.find_all(["th", "td"])]
        if any(cells):
            rows.append(" | ".join(cells))
    return "\n".join(rows)


def _collect_same_site_links(soup: BeautifulSoup, base_url: str) -> List[str]:
    out = set()
    for a in soup.find_all("a", href=True):
        href = _normalize_url(a["href"], base_url)
        if _same_site(base_url, href) and not _blocked_by_stop_patterns(href):
            out.add(href)
    return list(out)


# ===================== #
# Extraction contenu    #
# ===================== #

def extract_structured_content(page_url: str) -> Tuple[str, List[Dict[str, str]]]:
    """
    Prend une URL, renvoie (title, sections).
    - Si HTML : extraction actuelle.
    - Si PDF autorisé : extraction texte PDF → sections 'p'.
    """
    # 1) Si c’est un PDF explicite et domaine autorisé
    if ALLOW_PDF and (_is_pdf_url(page_url) or (_head_content_type(page_url) == "application/pdf")):
        if not _is_allowed_pdf_domain(page_url):
            _log_print("info", "[PDF] Domaine non autorisé, skip: %s", page_url)
            return "Titre non disponible", []
        data, final_url, headers = _download_binary(page_url)
        if not data:
            return "Titre non disponible", []
        title, sections, meta_pdf = _pdf_to_sections(data)
        lang = headers.get("Content-Language") or headers.get("content-language")
        if lang:
            pass
        return title or "Titre non disponible", sections

    # 2) Sinon, HTML (chemin actuel)
    soup, final_url = _request_soup(page_url)
    if soup is None:
        return "Titre non disponible", []

    root = _pick_root(soup)
    sections: List[Dict[str, str]] = []

    for el in root.find_all(["h1", "h2", "h3", "h4", "p", "blockquote", "li"], recursive=True):
        txt = _text(el)
        if not txt:
            continue
        tag = el.name
        if tag == "li":
            txt = f"- {txt}"
        if is_irrelevant_text(txt):
            continue
        sections.append({"tag": tag, "texte": txt})

    for table in root.find_all("table", recursive=True):
        ttxt = _table_to_text(table)
        if ttxt.strip():
            sections.append({"tag": "table", "texte": ttxt})

    sections = [s for s in sections if s.get("texte") and s["texte"].strip()]
    title = _extract_title(soup)
    return title or "Titre non disponible", sections


def _extract_minimal_sections_for_bfs(soup: BeautifulSoup) -> List[Dict[str, str]]:
    """Pour estimer si une page a du contenu utile lors du BFS."""
    root = _pick_root(soup)
    sections = []
    for el in root.find_all(["h1", "h2", "h3", "h4", "p", "li", "blockquote"], recursive=True):
        txt = _text(el)
        if txt and len(txt) >= 8 and not is_irrelevant_text(txt):
            sections.append({"tag": el.name, "texte": txt})
            if len(sections) >= 5:
                break
    return sections


# ===================== #
# BFS liens utiles      #
# ===================== #

def extract_useful_links(start_url: str, base_url: str) -> List[str]:
    """
    BFS même site (base_url vs href normalisés) jusqu'à DEFAULT_MAX_DEPTH.
    Renvoie une liste de pages jugées 'utiles' (incluant potentiellement la start_url).
    """
    visited = set()
    results: List[str] = []
    q = deque([(start_url, 0)])

    while q and len(visited) < DEFAULT_MAX_PAGES_PER_SITE:
        url, depth = q.popleft()
        if url in visited:
            continue
        visited.add(url)

        soup, final_url = _request_soup(url)
        if soup is None:
            continue

        # Page courante utile ?
        secs = _extract_minimal_sections_for_bfs(soup)
        non_empty = [s for s in secs if s.get("texte") and s["texte"].strip()]
        if non_empty:
            results.append(final_url or url)

        # Collecter liens du même site
        if depth < DEFAULT_MAX_DEPTH:
            for href in _collect_same_site_links(soup, base_url):
                if href not in visited:
                    q.append((href, depth + 1))

        if len(results) >= DEFAULT_MAX_PAGES_PER_SITE:
            break

    _log_print("info", "[extract_useful_links] %d liens retournés", len(results))
    return results


# ===================== #
# Sauvegarde JSON       #
# ===================== #

def _safe_filename_from_url(url: str) -> str:
    u = urlparse(url)
    base = (u.netloc + u.path).strip("/")
    base = re.sub(r"[^\w\-\/\.]+", "_", base)
    base = base.replace("/", "_")
    if not base:
        base = "index"
    return f"{base}.json"


def _collect_links_per_section_from_dom(soup: BeautifulSoup, page_url: str) -> List[List[Dict[str, str]]]:
    """
    Rejoue la même itération DOM que extract_structured_content pour collecter,
    pour chaque section, la liste des liens internes/externes qu'elle contient.
    Retourne une liste de même longueur que les sections attendues (idéalement).
    """
    root = _pick_root(soup)
    per_section_links: List[List[Dict[str, str]]] = []

    # Même ordre / même set de tags que dans extract_structured_content
    for el in root.find_all(["h1", "h2", "h3", "h4", "p", "blockquote", "li"], recursive=True):
        links_here: List[Dict[str, str]] = []
        for a in el.find_all("a", href=True):
            href = urljoin(page_url, a["href"])
            anchor = a.get_text(" ", strip=True) or ""
            links_here.append({"href": href, "anchor": anchor})
        per_section_links.append(links_here)

    # Ajout des liens pour les tables (dans le même ordre que _table_to_text est appelé)
    for table in root.find_all("table", recursive=True):
        links_here: List[Dict[str, str]] = []
        for a in table.find_all("a", href=True):
            href = urljoin(page_url, a["href"])
            anchor = a.get_text(" ", strip=True) or ""
            links_here.append({"href": href, "anchor": anchor})
        per_section_links.append(links_here)

    return per_section_links


# Meilleure normalisation des dates si dispo
try:
    from dateutil import parser as dateparser
except Exception:
    dateparser = None


def _norm(s: Optional[str]) -> Optional[str]:
    if not s:
        return None
    # Nettoyage léger
    s = s.strip()
    return s or None

def _pick(*vals: Optional[str]) -> Optional[str]:
    for v in vals:
        v = _norm(v)
        if v:
            return v
    return None

def _safe_get_attr(el, *attrs: str) -> Optional[str]:
    for a in attrs:
        if el and el.has_attr(a):
            v = el.get(a)
            if isinstance(v, str):
                return _norm(v)
    return None

def _text_of(el) -> Optional[str]:
    if not el:
        return None
    return _norm(el.get_text(" ").strip())

def _try_parse_date(raw: Optional[str]) -> Optional[str]:
    if not raw:
        return None
    raw = raw.strip()
    if dateparser:
        try:
            dt = dateparser.parse(raw)
            # Formatage ISO 8601 normalisé
            return dt.isoformat()
        except Exception:
            pass
    # Heuristique : déjà ISO-like ? Si oui, on la renvoie
    if re.match(r"^\d{4}-\d{2}-\d{2}", raw):
        return raw
    return raw  # on renvoie brut si non parsable

def _extract_from_jsonld(soup: BeautifulSoup) -> Dict[str, Optional[str]]:
    meta: Dict[str, Optional[str]] = {"published": None, "modified": None, "author": None, "title": None, "site_name": None}
    try:
        for tag in soup.find_all("script", {"type": "application/ld+json"}):
            try:
                data = json.loads(tag.string or "")
            except Exception:
                continue
            # normaliser en liste
            items = data if isinstance(data, list) else [data]
            for obj in items:
                if not isinstance(obj, dict):
                    continue
                typ = obj.get("@type") or obj.get("@type".lower())
                # On cible Article / NewsArticle / BlogPosting / WebPage
                if isinstance(typ, list):
                    types = [t.lower() for t in typ if isinstance(t, str)]
                else:
                    types = [str(typ).lower()] if typ else []
                if any(t in ("article", "newsarticle", "blogposting", "webpage") for t in types):
                    meta["title"]     = _pick(meta.get("title"), obj.get("headline"), obj.get("name"))
                    meta["published"] = _pick(meta.get("published"), _try_parse_date(obj.get("datePublished")))
                    meta["modified"]  = _pick(meta.get("modified"),  _try_parse_date(obj.get("dateModified")))
                    # auteur peut être str ou objet { "name": ... } ou liste
                    author = obj.get("author")
                    if isinstance(author, dict):
                        meta["author"] = _pick(meta.get("author"), author.get("name"))
                    elif isinstance(author, list) and author:
                        # on prend le premier "name" présent
                        for a in author:
                            if isinstance(a, dict) and a.get("name"):
                                meta["author"] = _pick(meta.get("author"), a.get("name"))
                                break
                            if isinstance(a, str):
                                meta["author"] = _pick(meta.get("author"), a)
                                break
                    elif isinstance(author, str):
                        meta["author"] = _pick(meta.get("author"), author)
    except Exception:
        pass
    return meta


def _extract_metadata(soup: BeautifulSoup, url: str) -> Dict[str, Optional[str]]:
    """Extrait des métadonnées communes (titre, description, auteur, dates, canonique, langue, site, provenance)."""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc

        # --- Balises classiques ---
        title_tag = soup.find("title")
        h1_tag    = soup.find("h1")
        og_title  = soup.find("meta", attrs={"property": "og:title"})
        og_desc   = soup.find("meta", attrs={"property": "og:description"})
        meta_desc = soup.find("meta", attrs={"name": "description"})
        meta_auth = soup.find("meta", attrs={"name": "author"}) or soup.find("meta", attrs={"property": "article:author"}) \
                    or soup.find("meta", attrs={"name": "dc.creator"}) or soup.find("meta", attrs={"name": "dcterms.creator"})
        meta_pub  = soup.find("meta", attrs={"property": "article:published_time"}) or soup.find("meta", attrs={"itemprop": "datePublished"}) \
                    or soup.find("meta", attrs={"name": "date"}) or soup.find("meta", attrs={"name": "dcterms.created"})
        meta_mod  = soup.find("meta", attrs={"property": "article:modified_time"}) or soup.find("meta", attrs={"itemprop": "dateModified"}) \
                    or soup.find("meta", attrs={"name": "last-modified"}) or soup.find("meta", attrs={"name": "dcterms.modified"})
        canonical = soup.find("link", rel="canonical")
        og_url    = soup.find("meta", attrs={"property": "og:url"})
        og_site   = soup.find("meta", attrs={"property": "og:site_name"})
        html_lang = soup.html.get("lang") if (soup and soup.html and soup.html.has_attr("lang")) else None

        # --- JSON-LD (si présent) ---
        ld = _extract_from_jsonld(soup)

        # --- Assemblage avec fallback (ordre: JSON-LD, OG, balises, h1, title) ---
        title = _pick(ld.get("title"), _safe_get_attr(og_title, "content"), _text_of(h1_tag), _text_of(title_tag))
        desc  = _pick(_safe_get_attr(og_desc, "content"), _safe_get_attr(meta_desc, "content"))
        auth  = _pick(ld.get("author"), _safe_get_attr(meta_auth, "content"))
        pub   = _pick(ld.get("published"), _try_parse_date(_safe_get_attr(meta_pub, "content")))
        mod   = _pick(ld.get("modified"),  _try_parse_date(_safe_get_attr(meta_mod, "content")))
        canon = _pick(_safe_get_attr(canonical, "href"), _safe_get_attr(og_url, "content"))
        site  = _pick(_safe_get_attr(og_site, "content"), domain)

        return {
            "title": title,
            "description": desc,
            "author": auth,
            "published": pub,
            "modified": mod,
            "canonical": canon,
            "lang": _norm(html_lang),
            "site_name": site,
            "source_url": url,
            "source_domain": domain,
        }
    except Exception as e:
        # En cas d'erreur, on renvoie a minima la provenance
        try:
            domain = urlparse(url).netloc
        except Exception:
            domain = None
        return {
            "title": None, "description": None, "author": None,
            "published": None, "modified": None, "canonical": None,
            "lang": None, "site_name": None,
            "source_url": url, "source_domain": domain
        }



def save_page_as_json(base_url: str,
                      page_url: str,
                      title: str,
                      sections: list,
                      outlinks: list,
                      output_dir: Optional[str] = None) -> Optional[Path]:
    """Sauvegarde la page en JSON (métadonnées + liens par section).

    - Format de `sections` conservé ; on ajoute la clé `links` au moment de l’écriture JSON.
    - `output_dir` est optionnel.
    - Retourne le chemin du fichier écrit (Path) ou None si échec.
    """
    try:
        # 1) Normaliser le répertoire de sortie
        if not output_dir:
            output_dir = os.path.join("outputs", "web_pages_json")
        os.makedirs(output_dir, exist_ok=True)

        # 2) Résoudre l’URL finale et récupérer des métadonnées HTML
        #    Pas de parsing lourd si ça échoue : resolved_url = page_url, metadata = {}
        resolved_url = page_url
        metadata = {}
        soup, maybe_final = _request_soup(page_url)
        if maybe_final:
            resolved_url = maybe_final
        if soup is not None:
            try:
                metadata = _extract_metadata(soup, page_url) or {}
            except Exception as e:
                _log_print("warning", "[save_page_as_json] _extract_metadata KO pour %s -> %s", page_url, e)
                metadata = {}
        else:
            metadata = {}

        # 3) Calculer les liens par section (alignés sur l’ordre de extract_structured_content)
        sections_links: List[List[Dict[str, str]]] = []
        if soup is not None:
            try:
                sections_links = _collect_links_per_section_from_dom(soup, resolved_url)
            except Exception as e:
                _log_print("warning", "[save_page_as_json] collect links per section KO (%s) -> %s", page_url, e)
                sections_links = []

        # Sécuriser l’alignement (même longueur que sections)
        if not sections_links or len(sections_links) != len(sections):
            # Fallback simple : pas de liens par section (on ne casse rien)
            sections_links = [[] for _ in sections]

        # 4) Construire un nom de fichier
        parsed = urlparse(page_url)
        safe_path = (parsed.path or "/").rstrip("/").replace("/", "_")
        if not safe_path:
            safe_path = "index"
        fname = f"{parsed.netloc}{safe_path}.json"
        dest_path = Path(output_dir) / fname

        # 5) Construire le payload
        payload = {
            "base_url": base_url,
            "page_url": page_url,
            "resolved_url": resolved_url,
            "title": title or "Titre non disponible",
            "metadata": metadata,
            "sections": [
                {**sec, "links": sections_links[i] if i < len(sections_links) else []}
                for i, sec in enumerate(sections)
            ],
            "outlinks": outlinks or [],
            "saved_at": datetime.utcnow().isoformat() + "Z",
        }

        # 6) Écrire
        with open(dest_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

        _log_print("info", "[Écrit] %s", dest_path)
        return dest_path

    except Exception as e:
        _log_print("❌ error", "[save_page_as_json] Échec pour %s -> %s", page_url, e)
        return None


# ===================== #
# Chargement des sites  #
# ===================== #

def load_trusted_sites(module_path: str) -> List[Dict]:
    """
    Charge le module Python 'trusted_web_sites_list.py' et retourne trusted_sites.
    """
    try:
        spec = importlib.util.spec_from_file_location("trusted_web_sites_list", module_path)
        mod = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(mod)
        sites = getattr(mod, "trusted_sites", None) or getattr(mod, "TRUSTED_SITES", None)
        if not isinstance(sites, list):
            raise ValueError("🟧 La variable 'trusted_sites' doit être une liste.")
        return sites
    except Exception as e:
        _log_print("❌ error", "Impossible de charger la liste des sites depuis %s -> %s", module_path, e)
        return []


# =============================== #
# Fonction principale (wrapper)   #
# =============================== #

def scrape_all_trusted_sites(trusted_sites: Optional[List[Dict]] = None,
                             output_dir: Optional[str] = None) -> None:
    """
    Scrape l’ensemble des sites de confiance et sauvegarde chaque page utile en JSON.

    Args:
        trusted_sites (list[dict] | None): Liste de sites à scruter (name, base_url, start_pages).
            Si None, la liste est chargée depuis la configuration.
        output_dir (str | pathlib.Path | None): Dossier de sortie des JSON ; si None, utilise
            le chemin configuré (WEB_SITES_JSON_HEALTH_DOC_BASE).

    Returns:
        list[pathlib.Path]: La liste des chemins des fichiers JSON écrits (vide si rien n’a été produit).
    """
    if trusted_sites is None:
        trusted_sites = load_trusted_sites(WEB_SITES_MODULE_PATH)
    if output_dir is None:
        output_dir = WEB_SITES_JSON_HEALTH_DOC_BASE

    os.makedirs(output_dir, exist_ok=True)

    written: List[str] = []

    for site in trusted_sites or []:
        name = site.get("name", "unknown")
        base_url = site.get("base_url") or site.get("domain") or ""
        start_pages = site.get("start_pages") or site.get("start_urls") or []

        if not base_url or not start_pages:
            _log_print("🟧 warning", "[site] %s: base_url ou start_pages manquant — skip", name)
            continue

        _log_print("info", "[site] Traitement du site : %s (%s)", name, base_url)

        for sp in start_pages:
            _log_print("info", "  > Page de départ : %s", sp)
            # BFS pour collecter des pages utiles du même site
            links = extract_useful_links(sp, base_url)

            # inclure la start_page en priorité si utile
            pages = []
            if sp not in links:
                pages.append(sp)
            pages.extend(links)

            # Limité à la contrainte fixée plus haut
            pages = pages[: site.get("max_pages", DEFAULT_MAX_PAGES_PER_SITE)]

            for page_url in pages:
                try:
                    title, sections = extract_structured_content(page_url)
                    # collecte des outlinks pour contexte (limités au même site)
                    soup, _ = _request_soup(page_url)
                    outlinks = _collect_same_site_links(soup, base_url) if soup else []
                    dest = save_page_as_json(base_url, page_url, title, sections, outlinks, output_dir)
                    if dest:
                        written.append(dest)
                except Exception as e:
                    _log_print("🟧 warning", "[page] Skip %s -> %s", page_url, e)

    _log_print("info", "[done] %d fichiers JSON écrits", len(written))
    return

# ===================== #
# Exécution directe     #
# ===================== #

if __name__ == "__main__":
    scrape_all_trusted_sites()













