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

from pathlib import Path
import os

# Emplacement de ce fichier: .../<repo>/config/config.py
CONFIG_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CONFIG_DIR.parent            # .../<repo>
SRC_DIR = PROJECT_ROOT / "src"              # .../<repo>/src

# Base logique de l'app = dossier 'src'
BASE_DIR = SRC_DIR

# --- Pages (choisit le bon dossier existant) ---
PAGES_DIR = SRC_DIR / "pages"

# --- Assets (si tu les gardes sous src/assets) ---
ASSETS_PATH = PROJECT_ROOT / "assets"
FONTS_DIR = ASSETS_PATH / 'fonts' / 'dejavu-fonts-ttf-2.37' / 'ttf'

# --- Données DOCX / JSON ---
INPUT_DOCX = SRC_DIR / "data" / "input" / "fiches_documentaires_docx"
JSON_HEALTH_DOC_BASE = SRC_DIR / "data" / "output" / "to_json_fiches_documentaires"

# --- Web (liste & JSON) ---
WEB_SITES_HEALTH_DOC_BASE = SRC_DIR / "data" / "input" / "trusted_web_sites"
WEB_SITES_MODULE_PATH = WEB_SITES_HEALTH_DOC_BASE / "trusted_web_sites_list.py"
WEB_SITES_JSON_HEALTH_DOC_BASE = SRC_DIR / "data" / "output" / "to_json_web_sites"

# --- Journal d’index ---
INDEXED_FILES_JOURNAL_PATH = SRC_DIR / "data" / "output" / "indexation" / "indexed_files.json"

# --- Dossiers patients ---
PATIENT_FILES_DIR = SRC_DIR / "data" / "input" / "poa_patients"

# Base chromadb
CHROMA_GLOBAL_DIR = BASE_DIR / "vector_db" / "chromadb"

# Embedding model
EMBEDDING_MODEL_NAME = "BAAI/bge-m3"
NORMALIZE_EMBEDDINGS = True
EMBEDDING_DEVICE = "cpu"   # au lieu de "mps" ou auto
# === Provider d'embeddings ===
EMBEDDING_PROVIDER = "openai"  # "openai" | "huggingface"
OPENAI_EMBEDDING_MODEL = "text-embedding-3-small"  # (1536 dims) ou "text-embedding-3-large" (3072)
BASE_DOCX_COLLECTION = "base_docx"
BASE_WEB_COLLECTION  = "base_web"



# Cheminns des flags
# --- Flag 'index ready' (fallback possible via env en prod) ---
INDEX_READY_FLAG_PATH = Path(os.environ.get(
    "OBY_FLAG_PATH",
    str(SRC_DIR / "vector_db" / "index_ready.flag")
))

FORCE_FULL_INDEX_FLAG = Path(CHROMA_GLOBAL_DIR) / ".force_full_index"
INDEXING_FLAG_FILE = Path(CHROMA_GLOBAL_DIR).parent / "indexing.lock"
INDEX_IPC_LOCK_PATH = "/tmp/oby_index.lock"      # inter-process (commun avec reset_all_data)


# --- Exports & docs ---
MARKDOWN_CHAT_EXPORTS = SRC_DIR / "outputs" / "chat_exports"
TOOLS_MD_PATH = PROJECT_ROOT / "docs" / "codebase" / "tools.md"
OVERVIEW_MD_PATH = PROJECT_ROOT / "docs" / "codebase" / "overview.md"

# --- Persistance ChromaDB (éviter os.getcwd()) ---
PERSIST_DIRECTORY = SRC_DIR / "generated" / "chroma_db"

# DB_CONSTANTES_SANTE
DB_CONSTANTES_SANTE = 'constantes_sante.db'

# --- Versioning ---
VERSIONING_DIR = SRC_DIR / "data" / "output" / "ppa_versions"

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
int_1 = 5
int_2 = 3

# Valeur de mesure de complémentarité des textes web vs. docx
sim_threshold = 0.60
nov_min = 0.30
nov_max = 0.75

MAX_CHARS_PER_PASSAGE = 800
MAX_PASSAGES_FINAL     = 8
MAX_PASSAGES_PER_SRC   = 2
CANDIDATE_WEB_CAP      = 30
