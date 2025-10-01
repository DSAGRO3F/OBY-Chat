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
import json
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
from config.config import CHROMA_GLOBAL_DIR
print(f"🟧[DEBUG] CHROMA_GLOBAL_DIR = {CHROMA_GLOBAL_DIR.resolve()}")



# Audit des JSON web (sections / texte) ---
def debug_check_web_json(dir_path):
    p = Path(dir_path)
    total_files = 0
    files_with_sections = 0
    files_with_nonempty = 0
    total_nonempty_chunks = 0

    no_sections = []
    only_empty_sections = []
    examples_nonempty = []

    for fp in p.glob("*.json"):
        total_files += 1
        try:
            data = json.loads(fp.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"❌ {fp.name}: JSON invalide ({e})")
            continue

        fiches = data if isinstance(data, list) else [data]
        has_sections = False
        has_nonempty = False

        for fiche in fiches:
            sections = fiche.get("sections") or []
            if sections:
                has_sections = True
            for s in sections:
                texte = (s.get("texte") or "").strip()
                if texte:
                    has_nonempty = True
                    total_nonempty_chunks += 1
                    if len(examples_nonempty) < 5:
                        examples_nonempty.append((fp.name, fiche.get("titre", "Sans titre")))
        if not has_sections:
            no_sections.append(fp.name)
        elif not has_nonempty:
            only_empty_sections.append(fp.name)
        else:
            files_with_sections += 1
            files_with_nonempty += 1

    print("\n[🟧 WEB JSON AUDIT]")
    print(f"- Répertoire        : {p}")
    print(f"- Fichiers JSON     : {total_files}")
    print(f"- Avec sections     : {files_with_sections}")
    print(f"- Avec texte non vide (au moins 1 chunk) : {files_with_nonempty}")
    print(f"- Total de chunks non vides (somme)     : {total_nonempty_chunks}")

    if no_sections:
        print(f"• Sans sections ({len(no_sections)}): {no_sections[:5]}{' ...' if len(no_sections)>5 else ''}")
    if only_empty_sections:
        print(f"• Sections toutes vides ({len(only_empty_sections)}): {only_empty_sections[:5]}{' ...' if len(only_empty_sections)>5 else ''}")
    if examples_nonempty:
        print(f"• Exemples avec texte: {examples_nonempty[:5]}")





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
    # S'assurer que c'est bien un Path
    docx_dir = Path(INPUT_DOCX)

    #--- Si pas de modification dans les fiches docx
    # donc pas de lancement de conversion docx vers json
    # donc pas d'existence de la directory de sortie et des json
    # Or fichiers json réclamés pour embedding plus tard...
    docx_dir = Path(INPUT_DOCX)
    out_dir  = Path(JSON_HEALTH_DOC_BASE)
    out_dir.mkdir(parents=True, exist_ok=True)

    docx_count = len(list(docx_dir.glob("*.docx")))
    json_count = len(list(out_dir.glob("*.json")))
    print(f"[BOOT] DOCX={docx_count} | JSON(docx)={json_count} -> {out_dir}")

    if docx_count == 0:
        print(f"[BOOT] Aucun DOCX trouvé dans {docx_dir} — on passera l'étape DOCX.")
    elif json_count == 0:
        print("[BOOT] JSON(docx) absent → conversion DOCX → JSON…")
        try:
            convert_and_save_fiches(str(docx_dir), str(out_dir))
        except Exception as e:
            # on log l'erreur mais on laisse vivre le pipeline (web/chroma peuvent continuer)
            print(f"🔴 Erreur conversion DOCX→JSON : {type(e).__name__}: {e}")
        else:
            json_count = len(list(out_dir.glob("*.json")))
            print(f"[BOOT] JSON(docx) après conversion = {json_count}")

    # ---

    # Vérification ---
    print("🟡 Vérification existence dossier d'entrée DOCX...")
    if docx_dir.exists():
        sample = [p.name for p in docx_dir.glob("*.docx")]
        print("[CFG] DOCX trouvés (échantillon):", sample[:5])
    else:
        print("[CFG] INPUT_DOCX n'existe pas :", docx_dir)
    # ---

    # Compter les .docx, pas la "longueur" du Path
    docx_count = 0
    if docx_dir.exists():
        docx_count = sum(1 for _ in docx_dir.glob("*.docx"))

    print(f"🟡 Dossier d'entrée DOCX : {docx_dir} — {docx_count} fichier(s) .docx")

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

            # --- sortie absente/vide ⇒ conversion forcée ---
            out_dir = Path(JSON_HEALTH_DOC_BASE)
            needs_force = (not out_dir.exists()) or (not any(out_dir.glob("*.json")))
            if needs_force:
                print("[BOOT] Sortie DOCX JSON absente/vide → conversion forcée.")
                out_dir.mkdir(parents=True, exist_ok=True)
                try:
                    # Ici on convertit depuis le DOSSIER d'entrée (docx_dir),
                    # pour (re)générer l'ensemble des JSON attendus.
                    convert_and_save_fiches(str(docx_dir), str(out_dir))
                    print(f"[BOOT] JSON(docx) maintenant = {len(list(out_dir.glob('*.json')))}")
                except Exception as e:
                    print(f"🔴 Erreur conversion forcée DOCX→JSON : {type(e).__name__}: {e}")
            else:
                print("[BOOT] Sortie déjà présente → on applique l’heuristique 'pas modifié'.")
            # ---




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

    print("[DEBUG] Audit JSON web avant indexation :")
    debug_check_web_json(WEB_SITES_JSON_HEALTH_DOC_BASE)

    # --- ✅ Préparation des sources à indexer ---
    docx_json_dir = Path(JSON_HEALTH_DOC_BASE)
    web_json_dir = Path(WEB_SITES_JSON_HEALTH_DOC_BASE)

    # DOCX JSON
    if not docx_json_dir.exists():
        print(f"[INDEX] {docx_json_dir} n’existe pas — skip DOCX cette passe.")
        docx_json_files = []
    else:
        docx_json_files = sorted(docx_json_dir.glob("*.json"))
        if not docx_json_files:
            print(f"[INDEX] Aucun JSON DOCX trouvé dans {docx_json_dir} — skip DOCX.")

    # WEB JSON
    if not web_json_dir.exists():
        print(f"[INDEX] {web_json_dir} n’existe pas — skip WEB cette passe.")
        web_json_files = []
    else:
        web_json_files = sorted(web_json_dir.glob("*.json"))
        if not web_json_files:
            print(f"[INDEX] Aucun JSON WEB trouvé dans {web_json_dir} — skip WEB.")

    # Rien à indexer ? on sort proprement (et on laissera le scheduler relancer plus tard)
    if not docx_json_files and not web_json_files:
        print("[INDEX] Rien à indexer (sources vides) — fin de la passe.")
        return
    # ---


    # --- ✅ Construction index vectoriel si nécessaire
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
        rebuild_collection_from_disk(client, "docx", str(JSON_HEALTH_DOC_BASE))
        rebuild_collection_from_disk(client, "web", str(WEB_SITES_JSON_HEALTH_DOC_BASE))
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



