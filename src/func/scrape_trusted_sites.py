"""
Module de scraping des sites web de confiance en santé.

Ce module permet :
- de charger dynamiquement la liste des sites référencés,
- d’extraire les liens utiles à partir de pages de départ,
- de structurer le contenu HTML pertinent (titres, paragraphes, listes),
- et de sauvegarder les pages web sous forme de fichiers JSON pour indexation.

Utilisé pour alimenter une base documentaire de recommandations en santé.
"""




import os
import sys
import importlib.util
from pathlib import Path
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import json

from config.config import WEB_SITES_MODULE_PATH, WEB_SITES_JSON_HEALTH_DOC_BASE

# ---------------------------
# Paramètres globaux ajustables
# ---------------------------
KEYWORDS = [
    # Soins à domicile
    "soin", "recommandation", "fragilité", "domicile", "aidant",
    "autonomie", "personne-agee", "personnes-agees", "vigilance", "dependance",
    "maintien à domicile", "vieillissement", "gérontologie", "gériatrie",

    # Recommandations cliniques / parcours de soin
    "prise en charge", "parcours de soin", "protocoles", "réglementation", "guides",
    "évaluation clinique", "bonne pratique", "dossier médical", "plan de soin",

    # Pathologies fréquentes / spécifiques aux personnes âgées
    "chute", "dénutrition", "déshydratation", "incontinence", "ulcère",
    "douleur", "démence", "alzheimer", "troubles cognitifs", "perte d'autonomie",
    "état confusionnel", "sarcopénie", "fatigue chronique",

    # Recommandations médicales et infirmières
    "traitement", "dosage", "médicament", "prescription", "arbre décisionnel",
    "infirmier", "soins palliatifs", "intervention", "consultation médicale",
    "aide à la toilette", "suivi thérapeutique", "protocole de soins",

    # Sécurité / vigilance sanitaire
    "vigilance sanitaire", "infection", "iatrogénie", "effet secondaire",
    "effets indésirables", "risque médical", "sécurité du patient"
]

MIN_TEXT_LENGTH = 30
MAX_LINKS_PER_START_PAGE = 30


# ---------------------------
# 1. Chargement des sites de confiance
# ---------------------------
def load_trusted_sites(module_path):
    try:
        spec = importlib.util.spec_from_file_location("trusted_web_sites", module_path)
        trusted_sites = importlib.util.module_from_spec(spec)
        sys.modules["trusted_web_sites"] = trusted_sites
        spec.loader.exec_module(trusted_sites)
        return trusted_sites.trusted_sites
    except Exception as e:
        print(f"[ERREUR] Impossible de charger la liste des sites : {e}")
        return []


# ---------------------------
# 2. Filtrage des liens pertinents
# ---------------------------
def is_relevant_link(link):
    return any(kw in link.lower() for kw in KEYWORDS)


def extract_useful_links(start_url, base_url):
    try:
        response = requests.get(start_url, timeout=10)
        soup = BeautifulSoup(response.content, "html.parser")
        links = set()
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            if href.startswith("/") or base_url in href:
                full_url = urljoin(base_url, href)
                if urlparse(full_url).netloc == urlparse(base_url).netloc:
                    if is_relevant_link(full_url):
                        links.add(full_url)
                        if len(links) >= MAX_LINKS_PER_START_PAGE:
                            break
        return list(links)
    except Exception as e:
        print(f"[ERREUR] Échec extraction liens depuis {start_url} : {e}")
        return []


# ---------------------------
# 3. Extraction structurée avec filtrage de sections
# ---------------------------
def is_irrelevant_text(text):
    patterns = ["télécharger", "partager", "cookie", "connexion", "contact", "mention légale"]
    return any(p in text.lower() for p in patterns)


def extract_structured_content(page_url):
    try:
        response = requests.get(page_url, timeout=10)
        soup = BeautifulSoup(response.content, "html.parser")

        title = soup.find("h1").get_text(strip=True) if soup.find("h1") else "Titre inconnu"
        sections = []
        current_section = {"titre_section": None, "texte": ""}

        for tag in soup.find_all(["h2", "h3", "p", "ul"]):
            if tag.name in ["h2", "h3"]:
                # Sauvegarde la section précédente si elle est pertinente
                if current_section["texte"].strip() and len(current_section["texte"].strip()) >= MIN_TEXT_LENGTH:
                    sections.append(current_section)
                current_section = {"titre_section": tag.get_text(strip=True), "texte": ""}
            elif tag.name == "p":
                text = tag.get_text(strip=True)
                if not is_irrelevant_text(text):
                    current_section["texte"] += text + "\n"
            elif tag.name == "ul":
                items = "\n".join([li.get_text(strip=True) for li in tag.find_all("li")])
                current_section["texte"] += items + "\n"

        # Dernière section
        if current_section["texte"].strip() and len(current_section["texte"].strip()) >= MIN_TEXT_LENGTH:
            sections.append(current_section)

        return title, sections
    except Exception as e:
        print(f"[ERREUR] Extraction contenu depuis {page_url} : {e}")
        return None, []


# ---------------------------
# 4. Sauvegarde du contenu structuré
# ---------------------------
def save_page_as_json(base_url, page_url, title, sections):
    try:
        parsed_url = urlparse(page_url)
        filename = parsed_url.path.strip("/").replace("/", "_") or "index"
        filepath = os.path.join(WEB_SITES_JSON_HEALTH_DOC_BASE, f"{filename}.json")
        json_data = {
            "titre": title,
            "type_document": "web_recommendation",
            "source_url": page_url,
            "source_site": parsed_url.netloc,
            "date_indexation": datetime.now().strftime("%Y-%m-%d"),
            "nb_sections": len(sections),
            "longueur_totale": sum(len(s["texte"]) for s in sections),
            "sections": sections
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        print(f"[INFO] Fichier JSON sauvegardé : {filepath}")
    except Exception as e:
        print(f"[ERREUR] Sauvegarde JSON échouée pour {page_url} : {e}")


# ---------------------------
# 5. Pipeline principal de scraping
# ---------------------------
def scrape_all_trusted_sites():
    trusted_sites = load_trusted_sites(WEB_SITES_MODULE_PATH)
    for site in trusted_sites:
        name = site.get("name")
        base_url = site.get("base_url")
        start_pages = site.get("start_pages", [])
        print(f"\n[INFO] Traitement du site : {name} ({base_url})")
        for start_page in start_pages:
            print(f"  > Page de départ : {start_page}")

            # 🔽 1. Toujours extraire le contenu de la page de départ elle-même
            title, sections = extract_structured_content(start_page)
            if sections:
                save_page_as_json(base_url, start_page, title, sections)
            else:
                print(f"[WARN] Aucun contenu utile trouvé pour page de départ : {start_page}")

            # 🔽 2. Ensuite, explorer les liens internes filtrés
            links = extract_useful_links(start_page, base_url)
            print(f"    - {len(links)} liens retenus (filtrés)")
            for page_url in links:
                title, sections = extract_structured_content(page_url)
                if sections:
                    save_page_as_json(base_url, page_url, title, sections)
                else:
                    print(f"[WARN] Aucun contenu utile trouvé pour {page_url}")


