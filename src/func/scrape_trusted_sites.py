# src/func/scrape_trusted_sites.py
"""
Scrape des sites de santé de confiance, extraction du contenu éditorial principal,
et sauvegarde en JSON normalisé pour l’indexation en aval.

Ce module parcourt une liste de sites web (chargée depuis
``WEB_SITES_MODULE_PATH``), collecte des pages du même site jusqu’à une
profondeur bornée, puis convertit leur contenu principal (titres, intertitres,
paragraphes, listes, tableaux, citations) dans un schéma JSON cohérent,
enregistré sous ``WEB_SITES_JSON_HEALTH_DOC_BASE``. Il est généralement appelé
par ``run_full_indexing_pipeline()`` sans argument via
``scrape_all_trusted_sites()``.

Fonctionnalités clés
--------------------
- Parcours en largeur (BFS) même-domaine avec normalisation du nom d’hôte
  (``example.com`` ≡ ``www.example.com``).
- Extraction ciblée dans les conteneurs de contenu (``main``, ``article``,
  ``[role=main]``, ``.entry-content``, ``.post-content``, ``.content``,
  ``#content``, ``#main``).
- Filtre de bruit conservateur (``is_irrelevant_text``) : conserve le texte
  substantiel même si des mots-clés “menu/cookies/footer” apparaissent ; rejette
  les fragments très courts/bruités.
- Conversion des tableaux en texte ; éléments de liste normalisés (``- <item>``).
- Double barrière contre le vide : les sections sont nettoyées/filtrées et les
  pages sans contenu utile ne sont **pas** écrites sur disque.
- Requêtes HTTP “polies” (User-Agent dédié, timeout, petite pause entre appels).

Configuration
-------------
- ``WEB_SITES_MODULE_PATH`` : chemin du fichier Python définissant ``trusted_sites``.
- ``WEB_SITES_JSON_HEALTH_DOC_BASE`` : dossier de sortie des fichiers JSON.
- Paramètres ajustables :
  - ``DEFAULT_MAX_DEPTH`` : profondeur BFS (défaut : 2).
  - ``DEFAULT_MAX_PAGES_PER_SITE`` : plafond par site pour éviter l’explosion.
  - ``REQUESTS_TIMEOUT_S`` / ``REQUESTS_SLEEP_S`` : paramètres réseau.

API publique
------------
- ``scrape_all_trusted_sites(trusted_sites: Optional[list]=None, output_dir: Optional[str]=None) -> None``
  Orchestration du crawl : charge les sites si nécessaire, explore les liens
  du même domaine, extrait le contenu et écrit les JSON. Retourne la liste
  des chemins écrits.

- ``extract_structured_content(page_url: str) -> tuple[str, list[dict]]``
  Retourne ``(title, sections)`` où chaque section est un dict
  ``{"tag": "h2|p|li|table|blockquote", "text": "<texte normalisé>"}``.
  Les sections vides/bruitées sont filtrées.

- ``extract_useful_links(start_url: str, base_url: str) -> list[str]``
  BFS même-domaine qui collecte les pages “utiles” (contenant du contenu
  éditorial non vide) jusqu’à la profondeur configurée.

- ``save_page_as_json(base_url, page_url, title, sections, outlinks, output_dir) -> str``
  Écrit un document JSON dans ``output_dir``.
  Retourne le chemin de sortie ou une chaîne vide si la page est ignorée.

- ``load_trusted_sites(module_path: str) -> list[dict]``
  Charge dynamiquement la liste ``trusted_sites`` depuis le module configuré.

- ``is_irrelevant_text(text: str) -> bool``
  Heuristique de filtrage pour les segments courts/bruités.

Schéma JSON
-----------
Chaque JSON sauvegardé a la forme :
::
    {
      "url": "<page_url>",
      "base_url": "<site_base_url>",
      "title": "<string>",
      "sections": [{"tag": "<h2|p|li|table|blockquote>", "text": "<string>"}],
      "outlinks": ["<url même site>", ...],
      "saved_at": "YYYY-MM-DDTHH:MM:SSZ"
    }

"""

from __future__ import annotations

import os
import re
import json
import time
import logging
import importlib.util
from dataclasses import dataclass
from typing import Iterable, List, Tuple, Dict, Optional
from urllib.parse import urlparse, urljoin

import requests
from bs4 import BeautifulSoup
from collections import deque

# ===================== #
# Config (inchangé)     #
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

# Profondeur max pour l'exploration (BFS)
DEFAULT_MAX_DEPTH = 2

# Nombre max de pages à traiter par site (cap anti-explosion)
DEFAULT_MAX_PAGES_PER_SITE = 200

# Petite politesse réseau
REQUESTS_TIMEOUT_S = 20
REQUESTS_SLEEP_S = 0.4

# Sélecteurs du conteneur principal de contenu éditorial
MAIN_SELECTORS = (
    "main, article, [role=main], "
    ".entry-content, .post-content, .article-content, .content, "
    "#content, #main"
)

# Mots-clés de bruit pour filtrage conservateur
IRRELEVANT_TEXT_KEYWORDS = {
    "menu", "navigation", "cookies", "cookie", "rgpd", "gdpr",
    "cgu", "cgv", "mentions", "légal", "légales", "footer",
    "newsletter", "partage", "share", "social", "abonnez-vous",
    "publicité", "sponsor", "breadcrumb", "fil d'ariane",
    "compte", "connexion", "login", "inscription",
}

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
        # strip fragments
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


def is_irrelevant_text(text: str) -> bool:
    """
    Filtre conservateur de bruit.
    - Rejette les blocs vides/ultra courts (< 8).
    - Si un mot-clé 'bruit' est présent, NE rejette que si le texte est court (< 60 chars).
    """
    try:
        if not text:
            return True
        t = text.strip()
        if not t:
            return True
        if len(t) < 8:
            return True
        low = t.lower()
        if len(low) >= 60:
            return False
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
    return _text(h1) if h1 else "Sans titre"


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
    Interface conservée: prend une URL, renvoie (title, sections).
    Chaque section est {'tag': <h2|p|li|...>, 'text': "..."}.
    Filtre les sections vides & bruit.
    """
    soup, final_url = _request_soup(page_url)
    if soup is None:
        return "Sans titre", []

    root = soup.select_one(MAIN_SELECTORS) or soup.body or soup
    sections: List[Dict[str, str]] = []

    # Titres / paragraphes / citations / items de listes
    for el in root.find_all(["h1", "h2", "h3", "h4", "p", "blockquote", "li"], recursive=True):
        txt = _text(el)
        if not txt:
            continue
        tag = el.name
        if tag == "li":
            txt = f"- {txt}"
        if is_irrelevant_text(txt):
            continue
        sections.append({"tag": tag, "text": txt})

    # Tables -> texte
    for table in root.find_all("table", recursive=True):
        ttxt = _table_to_text(table)
        if ttxt.strip():
            sections.append({"tag": "table", "text": ttxt})

    # Filtrage final des sections vides (double barrière)
    sections = [s for s in sections if s.get("text") and s["text"].strip()]

    title = _extract_title(soup)
    return title or "Sans titre", sections


def _extract_minimal_sections_for_bfs(soup: BeautifulSoup) -> List[Dict[str, str]]:
    """Version light pour estimer si une page a du contenu utile lors du BFS."""
    root = soup.select_one(MAIN_SELECTORS) or soup.body or soup
    sections = []
    for el in root.find_all(["h1", "h2", "h3", "h4", "p", "li", "blockquote"], recursive=True):
        txt = _text(el)
        if txt and len(txt) >= 8 and not is_irrelevant_text(txt):
            sections.append({"tag": el.name, "text": txt})
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
        non_empty = [s for s in secs if s.get("text") and s["text"].strip()]
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


def save_page_as_json(
    base_url: str,
    page_url: str,
    title: str,
    sections: List[Dict[str, str]],
    outlinks: List[str],
    output_dir: str,
) -> str:
    """
    Interface conservée.
    Sauvegarde un fichier JSON {url, base_url, title, sections, outlinks, saved_at}.
    Ne sauve rien si 'sections' est vide.
    """
    sections = [s for s in sections if s.get("text") and s["text"].strip()]
    if not sections:
        _log_print("warning", "[save] Page sans contenu utile, skip: %s", page_url)
        return ""

    os.makedirs(output_dir, exist_ok=True)
    fname = _safe_filename_from_url(page_url)
    dest = os.path.join(output_dir, fname)

    payload = {
        "url": page_url,
        "base_url": base_url,
        "title": title or "Sans titre",
        "sections": sections,
        "outlinks": list(sorted(set(outlinks or []))),
        "saved_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

    try:
        with open(dest, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        _log_print("info", "[save] %s", dest)
        return dest
    except Exception as e:
        _log_print("error", "[save] FAIL %s -> %s", dest, e)
        return ""


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
            raise ValueError("La variable 'trusted_sites' doit être une liste.")
        return sites
    except Exception as e:
        _log_print("error", "Impossible de charger la liste des sites depuis %s -> %s", module_path, e)
        return []


# =============================== #
# Fonction principale (wrapper)   #
# =============================== #

def scrape_all_trusted_sites(trusted_sites: Optional[List[Dict]] = None,
                             output_dir: Optional[str] = None) -> None:
    """
    Fonction principale appelée par run_full_indexing_pipeline() SANS ARGUMENT.
    - Charge la liste des sites depuis WEB_SITES_MODULE_PATH si besoin
    - Explore chaque start_page jusqu'à 2 niveaux (même site)
    - Extrait le contenu structuré
    - Sauvegarde en JSON dans WEB_SITES_JSON_HEALTH_DOC_BASE via save_page_as_json(...)
    Retourne la liste des chemins JSON écrits.
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
            _log_print("warning", "[site] %s: base_url ou start_pages manquant — skip", name)
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

            # pas plus que le cap global
            pages = pages[:DEFAULT_MAX_PAGES_PER_SITE]

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
                    _log_print("warning", "[page] Skip %s -> %s", page_url, e)

    _log_print("info", "[done] %d fichiers JSON écrits", len(written))
    return


# ===================== #
# Exécution directe     #
# ===================== #

if __name__ == "__main__":
    scrape_all_trusted_sites()













