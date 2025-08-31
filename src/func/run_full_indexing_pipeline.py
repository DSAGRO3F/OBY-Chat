"""
Module `run_full_indexing_pipeline.py` – Pipeline principal d’indexation documentaire pour OBY-IA.

Ce module exécute l’ensemble du processus de préparation de la base documentaire utilisée
par les agents RAG de OBY-IA, en assurant une indexation vectorielle actualisée dans ChromaDB.

Fonctionnalités couvertes :
1. **Détection de modifications** :
   - Identification des fichiers DOCX ou pages web récemment modifiés via calcul de hashs.
   - Détection des changements dans la définition des sites de confiance (`trusted_sites.py`).

2. **Conversion en JSON structuré** :
   - Transformation des fichiers DOCX en fichiers JSON exploitables.
   - Scraping et structuration des nouvelles pages web selon les règles définies.

3. **Indexation vectorielle dans ChromaDB** :
   - Indexation incrémentale ou complète des données selon les changements détectés.
   - Séparation des sources DOCX et web (`source_type`).

4. **Journalisation des indexations** :
   - Mise à jour du fichier de suivi (`indexed_files.json`) pour éviter les réindexations inutiles.

5. **Signalement de disponibilité** :
   - Écriture d’un fichier `index_ready.flag` permettant aux autres modules de savoir si l’index est prêt.

Ce pipeline peut être lancé :
- automatiquement (via un scheduler ou watchdog),
- ou manuellement (en exécutant ce fichier en tant que script).

Il constitue un composant critique du système OBY-IA pour garantir la fraîcheur et la cohérence
des bases documentaires utilisées dans les interactions LLM + RAG.
"""


from pathlib import Path
import os, sys

from src.utils.convert_fiches_docx_to_json import convert_and_save_fiches
from config.config import INPUT_DOCX, JSON_HEALTH_DOC_BASE, WEB_SITES_JSON_HEALTH_DOC_BASE
from src.func.indexed_health_related_files import (
    detect_changes_and_get_modified_files,
    update_index_journal,
)
from src.func.scrape_trusted_sites import scrape_all_trusted_sites
from src.func.index_documents_chromadb import index_documents
from src.utils.chroma_client import get_chroma_client
from src.utils.vector_db_utils import mark_index_ready_flag, clear_index_ready_flag
from src.func.index_documents_chromadb import _collection_name_for, rebuild_collection_from_disk


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

    clear_index_ready_flag()
    print("[DEBUG ✅] clear_index_ready_flag() appelé")

    print("🟡 Lancement du pipeline d'indexation...")
    print(f"🟡 Dossier d'entrée DOCX : {INPUT_DOCX}")

    # Détection des changements
    changes_dict = detect_changes_and_get_modified_files()
    docx_files_to_index = changes_dict.get("docx_files_to_index", [])
    web_files_to_index = changes_dict.get("web_files_to_index", [])
    trusted_sites_changed = changes_dict.get("trusted_sites_py_changed", False)
    current_docx_hashes = changes_dict.get("current_docx_hashes", {})
    current_web_hashes = changes_dict.get("current_web_hashes", {})
    current_py_hash = changes_dict.get("current_py_hash", None)
    docx_deleted_files = changes_dict.get("docx_deleted_files", [])
    web_deleted_files = changes_dict.get("web_deleted_files", [])


    print(f"🟠 DOCX à indexer : {len(docx_files_to_index)} fichiers")
    print(f"🟠 WEB à indexer : {len(web_files_to_index)} fichiers")
    print(f"🟠 Files trusted_sites.py modifié ? {trusted_sites_changed}")

    # Si un fichier docx est supprimé, suppression de son équivalent dans json
    docx_json_deleted = False
    for docx_path in docx_deleted_files:
        json_candidate = Path(JSON_HEALTH_DOC_BASE) / (Path(docx_path).stem + ".json")
        try:
            os.remove(json_candidate)
            print(f"✅ JSON dérivé supprimé (DOCX supprimé) : {json_candidate}")
            docx_json_deleted = True
        except FileNotFoundError:
            # Si rien fichier déjà absent, on poursuit
            pass
        except Exception as e:
            print(f"❌ Impossible de supprimer {json_candidate} : {e}", file=sys.stderr)



    # DOCX : Détection de fichiers DOCX + conversion en JSON et sauvegarde
    if not current_docx_hashes:
        print("⚠️ Aucun fichier DOCX détecté (aucune conversion à faire).")
    else:
        if docx_files_to_index:
            print("✅ Conversion des fiches DOCX modifiées...")
            for docx_file in docx_files_to_index:
                print(f"🟡 docx_file: {docx_file}")
                convert_and_save_fiches(str(docx_file), JSON_HEALTH_DOC_BASE)
        else:
            print("🟡 Aucun DOCX modifié — conversion non nécessaire.")



    # WEB : Détection & scraping si nécessaire si pas de json ou modif. liste sites web
    web_content_changed = False  # pour décider de (ré)indexer ou non
    if not current_web_hashes:
        # Aucun JSON web encore présent -> scraping initial
        print("⚠️ Aucun fichier JSON web détecté — scraping initial des sources de confiance...")
        scrape_all_trusted_sites()
        web_content_changed = True

    elif trusted_sites_changed:
        # La config des sites a changé -> on rescrape
        print("🟡 La liste des sites de confiance a changé — scraping complet...")
        scrape_all_trusted_sites()
        web_content_changed = True

    elif web_files_to_index:
        # Des JSON web ont été modifiés/ajoutés depuis le dernier journal
        # (ex: scraping précédent, ajout manuel, etc.) -> pas besoin de rescraper,
        print(f"🟡 {len(web_files_to_index)} fichier(s) JSON web modifié(s) — scraping non nécessaire.")
        web_content_changed = True

    else:
        print("✅ Aucun changement web — ni scraping ni réindexation nécessaires.")



    # Construction index vectoriel si nécessaire
    needs_reindex = (
            bool(docx_files_to_index) or
            bool(web_content_changed) or
            bool(docx_deleted_files) or
            bool(web_deleted_files)
    )

    if needs_reindex:
        print("🟡 Construction d'un nouvel index vectoriel...")
        client = get_chroma_client()

        # DOCX
        rebuild_collection_from_disk(
            client=client,
            source_type="docx",
            source_dir=JSON_HEALTH_DOC_BASE,
            drop_collection=False,  # passe à True si tu veux un drop complet
        )

        # WEB
        rebuild_collection_from_disk(
            client=client,
            source_type="web",
            source_dir=WEB_SITES_JSON_HEALTH_DOC_BASE,
            drop_collection=False,  # idem
        )
    else:
        print("✅ Aucun changement détecté, indexation non nécessaire.")


    # Mise à jour du journal des fichiers
    post_changes = detect_changes_and_get_modified_files()
    update_index_journal(
        new_docx_hashes=post_changes.get("current_docx_hashes", {}),
        new_web_hashes=post_changes.get("current_web_hashes", {}),
        new_py_hash=post_changes.get("current_py_hash", None),
    )
    print("✅ Journal d'index mis à jour.")
    print("✅ Pipeline terminé avec succès !")


    mark_index_ready_flag()
    print("[DEBUG ✅] mark_index_ready_flag() appelé")


# Pour exécution directe:
if __name__ == "__main__":
    run_full_indexing_pipeline()
    mark_index_ready_flag()



