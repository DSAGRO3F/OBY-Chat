"""
Module de déclenchement automatique de l'indexation documentaire.

Vérifie les modifications dans les fichiers DOCX et les pages web médicales,
et lance l'indexation via ChromaDB uniquement si des changements sont détectés.
"""

import os
from pathlib import Path
from config.config import (
    JSON_HEALTH_DOC_BASE,
    WEB_SITES_JSON_HEALTH_DOC_BASE,
)
from src.func.index_documents_chromadb import index_documents
from src.func.indexed_health_related_files import detect_changes_and_get_modified_files


def auto_index():
    """
    Déclenche l'indexation conditionnelle des documents médicaux.

    Détecte les modifications dans :
    - les fichiers DOCX structurés,
    - les fichiers web convertis en JSON,
    - le fichier de configuration des sites de confiance.

    Lance l’indexation avec `index_documents()` uniquement si des fichiers ont été modifiés.
    """

    print("📦 Vérification des changements dans les documents à indexer...")

    results = detect_changes_and_get_modified_files()

    docx_files_to_index = results.get("docx_files_to_index", [])
    web_files_to_index = results.get("web_files_to_index", [])
    trusted_sites_py_changed = results.get("trusted_sites_py_changed", False)

    if docx_files_to_index:
        print(f"📘 {len(docx_files_to_index)} fichier(s) DOCX à indexer.")
        index_documents(source_dir=JSON_HEALTH_DOC_BASE, source_type="docx")

    else:
        print("✅ Aucun changement détecté dans les fichiers DOCX.")

    if trusted_sites_py_changed or web_files_to_index:
        print(f"🌐 Indexation des documents web ({len(web_files_to_index)} page(s)).")
        index_documents(source_dir=WEB_SITES_JSON_HEALTH_DOC_BASE, source_type="web")

    else:
        print("✅ Aucun changement détecté dans les fichiers web.")

    print("🎯 Indexation terminée.\n")
