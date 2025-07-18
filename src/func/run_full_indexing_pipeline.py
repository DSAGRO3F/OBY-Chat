"""
Module principal pour exécuter le pipeline complet d’indexation documentaire.

Ce pipeline détecte les fichiers DOCX et les pages web modifiés, les convertit en JSON,
et les indexe dans ChromaDB via LangChain. Il peut être lancé automatiquement
(avec un scheduler) ou manuellement.
"""




from src.utils.convert_fiches_docx_to_json import convert_and_save_fiches
from config.config import INPUT_DOCX, JSON_HEALTH_DOC_BASE, WEB_SITES_JSON_HEALTH_DOC_BASE
from pathlib import Path
from src.func.indexed_health_related_files import (
    detect_changes_and_get_modified_files,
    update_index_journal,
)
from src.func.scrape_trusted_sites import scrape_all_trusted_sites
from src.func.index_documents_chromadb import index_documents
from src.utils.chroma_client import get_chroma_client


def run_full_indexing_pipeline():
    """
    Exécute le pipeline complet d’indexation des documents médicaux.

    Ce pipeline effectue les étapes suivantes :
    1. Détection des fichiers modifiés (DOCX, JSON web, fichier des sites de confiance).
    2. Conversion des fichiers DOCX en JSON.
    3. Scraping et structuration des pages web si nécessaire.
    4. Indexation vectorielle des fichiers convertis (DOCX et web) dans ChromaDB.
    5. Mise à jour du journal des fichiers indexés.

    Ce processus permet d'assurer que la base documentaire est à jour pour les requêtes RAG.
    """

    print("🚀 1.Lancement du pipeline d'indexation...")
    print(f"📂 2. Dossier d'entrée DOCX : {INPUT_DOCX}")

    # Étape 1 – Détection des changements
    changes_dict = detect_changes_and_get_modified_files()
    docx_files_to_index = changes_dict.get("docx_files_to_index", [])
    web_files_to_index = changes_dict.get("web_files_to_index", [])
    trusted_sites_changed = changes_dict.get("trusted_sites_py_changed", False)
    current_docx_hashes = changes_dict.get("current_docx_hashes", {})
    current_web_hashes = changes_dict.get("current_web_hashes", {})
    current_py_hash = changes_dict.get("current_py_hash", None)

    print(f"🔍 DOCX à indexer : {len(docx_files_to_index)} fichiers")
    print(f"🔍 WEB à indexer : {len(web_files_to_index)} fichiers")
    print(f"🔍 Files trusted_sites.py modifié ? {trusted_sites_changed}")

    # DOCX : indexation initiale ou incrémentale
    if not current_docx_hashes:
        print("🆕 Première indexation des fichiers DOCX...")
        all_docx_files = list(Path(INPUT_DOCX).glob("*.docx"))


        print(f"📂 Dossier d'entrée DOCX : {INPUT_DOCX}")
        print(f"📄 Fichiers trouvés : {all_docx_files}")

        for docx_file in all_docx_files:
            convert_and_save_fiches(str(docx_file), JSON_HEALTH_DOC_BASE)
    else:
        if docx_files_to_index:
            print("🛠️ 3. Conversion des fiches DOCX modifiées...")
            for docx_file in docx_files_to_index:
                print(f'4. docx_file: {docx_file}')
                convert_and_save_fiches(str(docx_file), JSON_HEALTH_DOC_BASE)

    # WEB : indexation initiale ou conditionnelle
    if not current_web_hashes or trusted_sites_changed:
        print("🌐 Indexation complète des sources web...")
        scrape_all_trusted_sites()
    elif web_files_to_index:
        print("🌐 Indexation partielle : nouvelles pages web détectées...")
        scrape_all_trusted_sites()

    # Étape 4 – Construction index vectoriel si nécessaire
    if docx_files_to_index or web_files_to_index or trusted_sites_changed:
        print("📚 Construction d'un nouvel index vectoriel...")
        client = get_chroma_client()
        index_documents(JSON_HEALTH_DOC_BASE, source_type="docx", client=client)
        index_documents(WEB_SITES_JSON_HEALTH_DOC_BASE, source_type="web", client=client)
    else:
        print("✅ Aucun changement détecté, indexation non nécessaire.")

    # Étape 5 – Mise à jour du journal des fichiers
    update_index_journal(
        new_docx_hashes=current_docx_hashes,
        new_web_hashes=current_web_hashes,
        new_py_hash=current_py_hash,
    )
    print("✅ Pipeline terminé avec succès !")


# Exécution directe possible
if __name__ == "__main__":
    run_full_indexing_pipeline()
