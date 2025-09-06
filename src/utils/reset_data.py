"""
Module de réinitialisation des données indexées de l'application OBY-IA.

Ce module fournit une fonction utilitaire permettant de nettoyer l’environnement
de travail en supprimant :
- les collections ChromaDB (ex. : `base_docx`, `base_web`),
- les fichiers JSON issus de l’extraction documentaire locale et web,
- le fichier journal qui suit les fichiers déjà indexés.

Utile pour remettre à zéro l’état de l’index avant un nouveau traitement complet.
"""

import os, shutil, json, threading, sys
from chromadb import PersistentClient
from config.config import CHROMA_GLOBAL_DIR, JSON_HEALTH_DOC_BASE, WEB_SITES_JSON_HEALTH_DOC_BASE, INDEXED_FILES_JOURNAL_PATH
from src.func.run_full_indexing_pipeline import run_full_indexing_pipeline
from src.utils.vector_db_utils import mark_index_ready_flag, clear_index_ready_flag
from pathlib import Path

def reset_all_data():
    """
    Réinitialise toutes les données indexées par l'application OBY-IA et relance l’indexation.
    Étapes :
      - Clear du flag “ready”.
      - Suppression des collections + dossiers ChromaDB persistés.
      - Suppression des JSON locaux/web.
      - Réinit du journal d’indexation.
      - Démarrage de la (ré)indexation en arrière-plan.
    """

    print("🔴 Réinitialisation des données...")

    # Flag “ready” doit disparaître immédiatement → l’UI passe en “En cours d’indexation”
    try:
        clear_index_ready_flag()
        print("🔴 Flag 'index_ready' supprimé.")
    except Exception as e:
        print(f"🔴 Impossible de supprimer le flag 'index_ready' : {e}", file=sys.stderr)

    # ChromaDB : logique + fichiers
    try:
        client = PersistentClient(path=str(CHROMA_GLOBAL_DIR))
        for collection_name in ["base_docx", "base_web"]:
            try:
                Path(CHROMA_GLOBAL_DIR).mkdir(parents=True, exist_ok=True)
                client.delete_collection(collection_name)
                print(f"✅ Collection supprimée : {collection_name}")
            except Exception as e:
                print(f"🟠Suppression collection ignorée ({collection_name}) : {e}")
    except Exception as e:
        print(f"⚠️ Client ChromaDB indisponible : {e}")

    if os.path.exists(CHROMA_GLOBAL_DIR):
        try:
            shutil.rmtree(CHROMA_GLOBAL_DIR, ignore_errors=True)
            print(f"✅ Dossier ChromaDB supprimé : {CHROMA_GLOBAL_DIR}")
        except Exception as e:
            print(f"⚠️ Impossible de supprimer {CHROMA_GLOBAL_DIR} : {e}", file=sys.stderr)

    # JSON locaux/web
    for path in [JSON_HEALTH_DOC_BASE, WEB_SITES_JSON_HEALTH_DOC_BASE]:
        if os.path.isdir(path):
            try:
                for file in os.listdir(path):
                    try:
                        os.remove(os.path.join(path, file))
                    except IsADirectoryError:
                        shutil.rmtree(os.path.join(path, file), ignore_errors=True)
                print(f"✅ Fichiers supprimés dans : {path}")
            except Exception as e:
                print(f"⚠️ Problème en nettoyant {path} : {e}", file=sys.stderr)
        else:
            print(f"🟠 Dossier non trouvé (ok) : {path}")

    # Journal
    try:
        os.makedirs(os.path.dirname(INDEXED_FILES_JOURNAL_PATH), exist_ok=True)
        with open(INDEXED_FILES_JOURNAL_PATH, "w", encoding="utf-8") as f:
            json.dump({}, f)
        print("✅ Fichier de suivi réinitialisé.")
    except Exception as e:
        print(f"⚠️ Impossible de réinitialiser le journal : {e}", file=sys.stderr)

    # Relancer le pipeline en arrière-plan (ne pas bloquer l’UI)
    def _rerun_pipeline():
        try:
            print("✅ Relance du pipeline d’indexation...")
            run_full_indexing_pipeline()  # marquera le flag 'ready' à la fin
        except Exception as e:
            print(f"❌ Échec de la réindexation post-reset : {e}", file=sys.stderr)

    threading.Thread(target=_rerun_pipeline, daemon=True).start()
    print("✅ Réinitialisation terminée (réindexation en cours).")

