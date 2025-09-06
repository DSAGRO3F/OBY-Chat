# src/utils/scheduler.py
"""
Surveillance des répertoires et (ré)indexation ChromaDB.

- Au démarrage :
  * Si CHROMA_GLOBAL_DIR est absent ou vide → pipeline d'indexation initiale.
  * Sinon, si le flag 'index_ready' est absent :
      - Vérifie la présence des collections 'base_docx' et 'base_web'.
      - Si elles manquent → relance le pipeline.
      - Sinon → marque le flag 'ready'.
  * Si le flag est présent → simple surveillance.

- En fonctionnement :
  - Watchdog surveille INPUT_DOCX et WEB_SITES_HEALTH_DOC_BASE.
  - Au moindre changement fichier, déclenche une indexation en empêchant les exécutions simultanées.
"""

from __future__ import annotations

import os
import sys
import time
import threading
from datetime import datetime

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from config.config import CHROMA_GLOBAL_DIR
from src.func.run_full_indexing_pipeline import run_full_indexing_pipeline
from src.utils.vector_db_utils import is_chroma_index_ready, mark_index_ready_flag
from src.utils.chroma_client import get_chroma_client

from config.config import (
    INPUT_DOCX,
    WEB_SITES_HEALTH_DOC_BASE,
)

from chromadb.errors import NotFoundError

# Répertoires à surveiller
WATCHED_DIRECTORIES = [
    INPUT_DOCX,
    WEB_SITES_HEALTH_DOC_BASE
]

# Lock global pour éviter des exécutions simultanées du pipeline
_PIPELINE_LOCK = threading.Lock()

class DebouncedIndexer:
    """Déclenche `run_full_indexing_pipeline` avec un debounce et un lock global."""

    def __init__(self, wait_seconds: float = 2.0):
        self.wait_seconds = wait_seconds
        self._timer: threading.Timer | None = None
        self._timer_lock = threading.Lock()

    def trigger(self) -> None:
        """Planifie (ou replanifie) l’exécution de l’indexation."""
        with self._timer_lock:
            if self._timer is not None:
                self._timer.cancel()
            self._timer = threading.Timer(self.wait_seconds, self._run_once_locked)
            self._timer.daemon = True
            self._timer.start()

    def _run_once_locked(self) -> None:
        """Exécute le pipeline si aucun autre run n’est en cours."""
        if not _PIPELINE_LOCK.acquire(blocking=False):
            print("⛔️ Indexation déjà en cours — déclenchement ignoré.")
            return
        try:
            print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] 🔄 Lancement (debounced) du pipeline...")
            run_full_indexing_pipeline()
        except Exception as e:
            print(f"❌ Erreur dans l’indexation : {e}", file=sys.stderr)
        finally:
            _PIPELINE_LOCK.release()


class IndexingEventHandler(FileSystemEventHandler):
    """Handler Watchdog qui déclenche une (ré)indexation sur tout changement fichier."""

    def __init__(self, debouncer: DebouncedIndexer):
        super().__init__()
        self.debouncer = debouncer

    def on_any_event(self, event):
        if event.is_directory:
            return
        print(
            f"\n🟠 Changement détecté : {event.src_path} ({event.event_type})\n"
            f"[{datetime.now():%Y-%m-%d %H:%M:%S}] 🔄 Demande d’indexation (debounced)...\n"
        )
        self.debouncer.trigger()


def _has_chroma_storage() -> bool:
    """Vérifie l’existence d’un stockage Chroma (dossier présent ET listable et non vide)."""
    try:
        if not os.path.exists(CHROMA_GLOBAL_DIR):
            return False
        # os.listdir peut lever PermissionError
        return bool(os.listdir(CHROMA_GLOBAL_DIR))
    except PermissionError as e:
        print(
            f"⚠️ Accès refusé à {CHROMA_GLOBAL_DIR} : {e} — considéré comme 'absent'.",
            file=sys.stderr,
        )
        return False
    except Exception as e:
        print(
            f"⚠️ Échec listage {CHROMA_GLOBAL_DIR} : {e} — considéré comme 'absent'.",
            file=sys.stderr,
        )
        return False


def _ensure_ready_flag_or_reindex() -> None:
    """
    Si le flag 'ready' est absent mais que le dossier Chroma existe :
      - tente de valider la présence des collections,
      - si OK → marque le flag,
      - sinon → relance du pipeline.
    """
    if is_chroma_index_ready():
        print("✅ Flag 'ready' présent.")
        return

    print("ℹ️ Base présente mais flag 'ready' absent — vérification des collections...")
    try:
        client = get_chroma_client()
        client.get_collection("base_docx")
        client.get_collection("base_web")
    except NotFoundError:
        print("🟠 Collections manquantes → relance du pipeline d’indexation.")
        run_full_indexing_pipeline()
    except Exception as e:
        # Si autre erreur (client inaccessible, etc.), on tente une réindexation propre
        print(f"⚠️ Impossible de valider les collections ({e}) — relance du pipeline.", file=sys.stderr)
        run_full_indexing_pipeline()
    else:
        print("✅ Collections 'base_docx' et 'base_web' présentes — marquage du flag.")
        try:
            mark_index_ready_flag()
        except Exception as e:
            print(f"⚠️ Impossible d’écrire le flag 'ready' : {e}", file=sys.stderr)



def start_scheduler() -> None:
    """
    Démarre la surveillance Watchdog + gère la remise en cohérence initiale.

    - Si aucun stockage Chroma → pipeline initial.
    - Si stockage présent et flag absent → vérifie les collections, marque le flag ou relance le pipeline.
    - Sinon → surveillance seule.
    """
    # Étape 1 : Remise en cohérence initiale
    if not _has_chroma_storage():
        print("\n🟢 Initialisation des bases ChromaDB (premier démarrage ou stockage manquant)...")
        run_full_indexing_pipeline()
    else:
        # Stockage présent : valider le flag/collections avant de passer en simple surveillance
        _ensure_ready_flag_or_reindex()
        if is_chroma_index_ready():
            print("\n✅ Base ChromaDB prête. Surveillance uniquement.")

    # Étape 2 : Activer la surveillance des fichiers
    print("🟢 Démarrage de la surveillance des fichiers (Watchdog)...")
    debouncer = DebouncedIndexer(wait_seconds=2.0)
    event_handler = IndexingEventHandler(debouncer=debouncer)
    observer = Observer()



    for directory in WATCHED_DIRECTORIES:
        # Crée le dossier si absent pour éviter les erreurs de Watchdog
        try:
            os.makedirs(directory, exist_ok=True)
        except Exception as e:
            print(f"⚠️ Impossible de créer {directory} : {e}", file=sys.stderr)
        observer.schedule(event_handler, path=directory, recursive=True)
        print(f"✅ Surveillance activée sur : {directory}")

    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Arrêt de la surveillance demandé (Ctrl+C).")
        observer.stop()
    observer.join()

