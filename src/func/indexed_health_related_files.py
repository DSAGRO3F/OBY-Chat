"""
Module de suivi et de détection des changements dans les fichiers de santé.

Il permet de :
- Calculer le hash des fichiers (DOCX, JSON, Python) pour en détecter les modifications.
- Comparer l’état actuel à un journal enregistré.
- Déterminer quels fichiers nécessitent une réindexation.
"""





import hashlib
import json
from pathlib import Path
from typing import List, Dict
from datetime import datetime

from config.config import (INPUT_DOCX,
    WEB_SITES_JSON_HEALTH_DOC_BASE,
    WEB_SITES_MODULE_PATH,
    INDEXED_FILES_JOURNAL_PATH)


def compute_file_hash(file_path: Path) -> str:
    """Calcule le hash SHA256 d’un fichier texte ou binaire."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        content = f.read()
        hasher.update(content)
    return hasher.hexdigest()


def load_indexed_files_journal() -> Dict:
    """Charge l'état précédent des fichiers indexés."""
    if INDEXED_FILES_JOURNAL_PATH.exists():
        with open(INDEXED_FILES_JOURNAL_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "json_docx_files": {},
        "json_web_files": {},
        "trusted_sites_py": None,
        "last_update": None
    }

def save_indexed_files_journal(journal: Dict):
    """Sauvegarde l'état actuel des fichiers indexés."""
    journal["last_update"] = datetime.now().isoformat()
    with open(INDEXED_FILES_JOURNAL_PATH, "w", encoding="utf-8") as f:
        json.dump(journal, f, indent=2)


from typing import Dict, List
from pathlib import Path

def detect_changes_and_get_modified_files() -> Dict[str, List[Path]]:
    """
    Détecte les fichiers de santé modifiés depuis la dernière indexation.

    Vérifie les fichiers :
    - DOCX dans `INPUT_DOCX`
    - JSON web dans `WEB_SITES_JSON_HEALTH_DOC_BASE`
    - Le fichier `trusted_web_sites_list.py`

    Returns:
        dict: Dictionnaire contenant :
            - `docx_files_to_index`: fichiers DOCX ajoutés/modifiés
            - `web_files_to_index`: fichiers JSON web ajoutés/modifiés
            - `trusted_sites_py_changed`: booléen indiquant une modification du fichier Python
            - `current_docx_hashes`: nouveaux hash DOCX
            - `current_web_hashes`: nouveaux hash JSON
            - `current_py_hash`: nouveau hash du fichier `.py`
            - `docx_deleted_files`: liste des DOCX supprimés depuis le dernier journal
            - `web_deleted_files`: liste des JSON web supprimés depuis le dernier journal
    """

    journal = load_indexed_files_journal()
    modified_docx_files: List[Path] = []
    modified_web_files: List[Path] = []
    trusted_sites_changed = False

    # --- DOCX ---
    current_docx_files = list(Path(INPUT_DOCX).glob("*.docx"))
    current_docx_hashes = {f.name: compute_file_hash(f) for f in current_docx_files}
    prev_docx_hashes = journal.get("docx_files", {}) or {}

    # Ajouts / Modifs
    for fname, h in current_docx_hashes.items():
        if prev_docx_hashes.get(fname) != h:
            modified_docx_files.append(Path(INPUT_DOCX) / fname)

    # Suppressions DOCX
    prev_docx_names = set(prev_docx_hashes.keys())
    current_docx_names = set(current_docx_hashes.keys())
    deleted_docx_names = prev_docx_names - current_docx_names
    docx_deleted_files = [Path(INPUT_DOCX) / fname for fname in deleted_docx_names]

    # WEB JSON
    current_web_files = list(Path(WEB_SITES_JSON_HEALTH_DOC_BASE).glob("*.json"))
    current_web_hashes = {f.name: compute_file_hash(f) for f in current_web_files}
    prev_web_hashes = journal.get("json_web_files", {}) or {}

    # Ajouts / Modifs
    for fname, h in current_web_hashes.items():
        if prev_web_hashes.get(fname) != h:
            modified_web_files.append(Path(WEB_SITES_JSON_HEALTH_DOC_BASE) / fname)

    # Suppressions WEB JSON
    prev_web_names = set(prev_web_hashes.keys())
    current_web_names = set(current_web_hashes.keys())
    deleted_web_names = prev_web_names - current_web_names
    web_deleted_files = [Path(WEB_SITES_JSON_HEALTH_DOC_BASE) / fname for fname in deleted_web_names]

    # liste sites web
    current_py_hash = None
    if Path(WEB_SITES_MODULE_PATH).exists():
        current_py_hash = compute_file_hash(Path(WEB_SITES_MODULE_PATH))
        if journal.get("trusted_sites_py") != current_py_hash:
            trusted_sites_changed = True

    return {
        "docx_files_to_index": modified_docx_files,
        "web_files_to_index": modified_web_files,
        "trusted_sites_py_changed": trusted_sites_changed,
        "current_docx_hashes": current_docx_hashes,
        "current_web_hashes": current_web_hashes,
        "current_py_hash": current_py_hash,
        "docx_deleted_files": docx_deleted_files,
        "web_deleted_files": web_deleted_files,
    }



def update_index_journal(new_docx_hashes: Dict, new_web_hashes: Dict, new_py_hash: str = None):
    """
    Met à jour le journal des fichiers indexés avec les nouveaux hash.

    Args:
        new_docx_hashes (dict): Hash des fichiers DOCX après indexation.
        new_web_hashes (dict): Hash des fichiers JSON web après indexation.
        new_py_hash (str, optional): Hash du fichier `trusted_web_sites_list.py`.
    """

    journal = {
        "docx_files": new_docx_hashes,
        "json_web_files": new_web_hashes,
        "trusted_sites_py": new_py_hash,
        "last_update": datetime.now().isoformat()
    }
    save_indexed_files_journal(journal)


