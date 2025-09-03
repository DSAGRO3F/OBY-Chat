"""
Fichier de configuration globale pour le projet OBY-IA.

Ce module définit les chemins des répertoires de données, des documents de référence,
des fichiers patients, des sorties PDF et graphiques, ainsi que les paramètres liés
à l’indexation vectorielle (ChromaDB), au versioning, et à la journalisation.

Il contient également :
- des constantes pour les formats de date et les niveaux de log ;
- les identifiants de connexion utilisateur en phase de test ou démonstration ;
- les chemins pour les fichiers JSON générés à partir de documents `.docx` ou de pages web ;
- la configuration des polices utilisées pour les sorties PDF.

Toutes les variables sont conçues pour être importées et utilisées par les différents modules
du projet.
"""


import os
from pathlib import Path

# === Directories ===
# Base directory for the project (src/)
BASE_DIR = Path(__file__).resolve().parent.parent

# Assets and Fonts directory
ASSETS_DIR = BASE_DIR / 'assets'
FONTS_DIR = ASSETS_DIR / 'fonts' / 'dejavu-fonts-ttf-2.37' / 'ttf'
# Convert to string only when necessary
FONT_FILES_DIR = str(FONTS_DIR)

# Pages directory
PAGES_DIR = BASE_DIR/'src'/'pages'

# Documentary base (ensemble de fiches ou documents de référence transmis par BVIDF,
# format .docx)
docx_files_path = 'src/data/input/fiches_documentaires_docx/'
INPUT_DOCX = os.path.join(BASE_DIR, docx_files_path)

# Post traitement Documentary base (conversion docx en json)
generated_json_files_path = 'src/data/output/to_json_fiches_documentaires/'
JSON_HEALTH_DOC_BASE = os.path.join(BASE_DIR, generated_json_files_path)

# Autres documents issus du web
web_sites_path = 'src/data/input/trusted_web_sites/'
WEB_SITES_HEALTH_DOC_BASE = os.path.join(BASE_DIR, web_sites_path)
web_sites_module_name = 'trusted_web_sites_list.py'
WEB_SITES_MODULE_PATH = os.path.join(WEB_SITES_HEALTH_DOC_BASE, web_sites_module_name)

# Post traitement sites web (conversion pages html en json)
generated_json_from_html_files_path = 'src/data/output/to_json_web_sites/'
WEB_SITES_JSON_HEALTH_DOC_BASE = os.path.join(BASE_DIR, generated_json_from_html_files_path)

# Utiliser une base ChromaDB unique.
CHROMA_GLOBAL_DIR = os.path.join(BASE_DIR, "src","vector_db", "chromadb")

# Embedding model
EMBEDDING_MODEL_NAME = "BAAI/bge-large-en-v1.5"
NORMALIZE_EMBEDDINGS = True

# Fichier journal d’indexation
INDEXED_FILES_JOURNAL_PATH = BASE_DIR/ "src" / "data" / "output" / "indexation" / "indexed_files.json"

# Patient files directory (src/data/poa_patients)
PATIENT_FILES_DIR = BASE_DIR / "src"/"data" / "input"/"poa_patients"

# Path to the ChromaDB "index ready" flag
INDEX_READY_FLAG_PATH = BASE_DIR / "src" / "vector_db" / "index_ready.flag" #-> fonctionne pas sur Render
# INDEX_READY_FLAG_PATH = Path("/tmp/oby-chat/index_ready.flag")

# Path to assets directory
ASSETS_PATH = Path(__file__).parent.parent / "assets"

# Exports des fichiers markdown
MARKDOWN_CHAT_EXPORTS = BASE_DIR / "outputs"/"chat_exports"

# Documentation projet:
# TOOLS_MD_PATH: fichier input; OVERVIEW_MD_PATH: fichier output
TOOLS_MD_PATH = BASE_DIR/"docs"/"codebase"/"tools.md"
OVERVIEW_MD_PATH = BASE_DIR/"docs"/"codebase"/"overview.md"

# DB_CONSTANTES_SANTE
DB_CONSTANTES_SANTE = 'constantes_sante.db'

# Chemin racine où stocker les données ChromaDB
PERSIST_DIRECTORY = os.path.join(os.getcwd(), "src","generated", "chroma_db")

# === Versioning Settings ===
VERSIONING_DIR = os.path.join(BASE_DIR, "src","data", "output", "ppa_versions")

# === Logging and Debug ===
LOGGING_ENABLED = True
LOG_LEVEL = "INFO"  # Options: DEBUG, INFO, WARNING, ERROR

# === Constants ===
DEFAULT_DATE_FORMAT = "%Y-%m-%d"

# === user_id...====
USER_DATABASE = {
    "admin": "1234",
    "alice": "passalice",
    "bob": "passbob"
}

# Valeurs nb chunks
int_1 = 3
int_2 = 2

