"""
    Module `run_full_indexing_pipeline.py` – Pipeline principal d’indexation documentaire pour OBY-IA.

    Pipeline d'indexation ChromaDB pour OBY-IA.

    Ce module orchestre la maintenance de l’index vectoriel à partir de deux sources :
    1) des fiches au format DOCX (converties en JSON),
    2) des pages web de confiance (scrapées en JSON).

    Il a pour objectif d'être appelé au démarrage et à chaque événement Watchdog.

    Fonctionnement, synthèse :
    - Détection des changements via `detect_changes_and_get_modified_files()` :
      ajouts, modifications, suppressions de fichiers DOCX/WEB, changement de
      `trusted_web_sites_list.py`.
    - Nettoyage :
      - suppression des JSON dérivés de DOCX supprimés,
      - purge défensive des JSON web si la configuration des sites change.
    - Production des données :
      - conversion DOCX → JSON si des DOCX ont changé,
      - scraping complet/partiel des sites web si nécessaire.
    - Reconstruction des index ChromaDB :
      - réindexation des collections à partir des dossiers JSON présents sur disque.
    - Mise à jour du journal et pose d’un « ready flag ».

    Dépendances (importées ailleurs dans le projet) :
    - `detect_changes_and_get_modified_files`, `update_index_journal`
    - `convert_and_save_fiches`
    - `scrape_all_trusted_sites`
    - `get_chroma_client`, `index_documents` (ou `rebuild_collection_from_disk`)
    - constantes de chemins : `INPUT_DOCX`, `JSON_HEALTH_DOC_BASE`,
      `WEB_SITES_JSON_HEALTH_DOC_BASE`, `WEB_SITES_MODULE_PATH`, `BASE_DIR`

    Notes :
    - Les purges de répertoires sont précédées de vérifications de chemin
      (résolution absolue, inclusion sous `BASE_DIR`).
    - Les erreurs critiques d’E/S sont loguées sur STDERR.

"""

from pathlib import Path
import os, sys, shutil

from src.utils.convert_fiches_docx_to_json import convert_and_save_fiches
from config.config import INPUT_DOCX, JSON_HEALTH_DOC_BASE, WEB_SITES_JSON_HEALTH_DOC_BASE, BASE_DIR
from src.func.indexed_health_related_files import (
    detect_changes_and_get_modified_files,
    update_index_journal,
)
from src.func.scrape_trusted_sites import scrape_all_trusted_sites
from src.utils.chroma_client import get_chroma_client
from src.utils.vector_db_utils import mark_index_ready_flag, clear_index_ready_flag
from src.func.index_documents_chromadb import rebuild_collection_from_disk


def run_full_indexing_pipeline():
    """
    Exécute le pipeline complet de supervision et (ré)indexation.

    Objectifs :
        1. Détecte l’état courant et les diffs (ajouts/modifs/suppressions).
        2. Supprime les JSON orphelins issus de DOCX supprimés.
        3. Si la configuration des sites change, purge les JSON web puis lance
           un scraping complet ; sinon, scraping conditionnel si nécessaire.
        4. Reconstruit l’index ChromaDB à partir des JSON présents sur disque
           (DOCX et WEB), si des changements ont été détectés.
        5. Recalcule les hachages et met à jour le journal d’indexation.
        6. Pose le « ready flag » marquant la fin réussie du processus.

    Notes :
        - Écrit/écrase des fichiers JSON (conversion DOCX, scraping web).
        - Purge de dossiers JSON (web) en cas de changement de configuration.
        - (Ré)initialise des collections ChromaDB.
        - Met à jour le journal d’indexation et le drapeau « ready ».

    Raises:
        RuntimeError: si une incohérence de chemin est détectée lors d’une purge.
        OSError: en cas d’erreurs E/S non gérées par les « ignore_errors ».
        Exception: toutes exceptions non interceptées par les appels sous-jacents.

    Returns:
        None
    """

    clear_index_ready_flag()
    print("[DEBUG ✅] clear_index_ready_flag() appelé")

    print("🟡 Lancement du pipeline d'indexation...")
    print(f"🟡 Dossier d'entrée DOCX + nb files: {INPUT_DOCX}, {len(INPUT_DOCX)}")

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


    # Si un fichier web est supprimé, suppression de son équivalent dans json
    web_json_deleted = False
    for web_json_path in web_deleted_files:  # éléments de type Path pointant vers WEB_SITES_JSON_HEALTH_DOC_BASE/xxx.json
        try:
            if web_json_path.exists():
                os.remove(web_json_path)
                print(f"✅ JSON web supprimé (journal signale une suppression) : {web_json_path}")
                web_json_deleted = True
        except Exception as e:
            print(f"❌ Impossible de nettoyer {web_json_path} : {e}", file=sys.stderr)


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



    # WEB : Détection & scraping si nécessaire si pas de json ou modif. de la liste sites web
    web_content_changed = False  # pour décider de (ré)indexer ou non
    if not current_web_hashes:
        # Aucun JSON web encore présent -> scraping initial
        print("⚠️ Aucun fichier JSON web détecté — scraping initial des sources de confiance...")
        scrape_all_trusted_sites()
        web_content_changed = True

    elif trusted_sites_changed:
        # La config des sites a changé implique nouveau scrape
        print("🟡 La liste des sites de confiance a changé — scraping complet...")

        # on vérifie que path (chemin à purger) commence par le chemin absolu de BASE_DIR.
        # => On ne purge que si la cible est bien dans le répertoire racine attendu.
        # Si pas le cas → “Chemin inattendu, purge annulée”.



        base = Path(BASE_DIR).resolve()
        path = WEB_SITES_JSON_HEALTH_DOC_BASE  # str ou Path vers le dossier à purger
        target = Path(path).resolve()

        # Vérifie que target == base ou est un sous-dossier de base
        if not (target == base or base in target.parents):
            raise RuntimeError(f"Chemin inattendu (hors {base}) : purge annulée → {target}")


        shutil.rmtree(WEB_SITES_JSON_HEALTH_DOC_BASE, ignore_errors=True)
        os.makedirs(WEB_SITES_JSON_HEALTH_DOC_BASE, exist_ok=True)
        scrape_all_trusted_sites()
        web_content_changed = True

    elif web_files_to_index:
        # Des JSON web ont été modifiés/ajoutés depuis le dernier journal
        # (ex: scraping précédent, ajout manuel, etc.) -> pas besoin nouveau scrape
        print(f"🟡 {len(web_files_to_index)} fichier(s) JSON web modifié(s) — scraping non nécessaire.")
        web_content_changed = True

    else:
        print("✅ Aucun changement web — ni scraping ni réindexation nécessaires.")


    # Construction index vectoriel si nécessaire

    needs_reindex = (
            bool(docx_files_to_index)
            or bool(web_content_changed)
            or bool(docx_deleted_files)
            or bool(web_deleted_files)
            or bool(docx_json_deleted)
            or bool(web_json_deleted)
    )


    if needs_reindex:
        print("🟡 Reconstruction de l'index vectoriel...")
        client = get_chroma_client()
        rebuild_collection_from_disk(client, "docx", JSON_HEALTH_DOC_BASE)
        rebuild_collection_from_disk(client, "web", WEB_SITES_JSON_HEALTH_DOC_BASE)
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



