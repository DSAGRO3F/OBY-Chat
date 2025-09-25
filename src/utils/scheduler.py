# src/utils/scheduler.py
"""
Scheduler de réindexation Chroma : surveillance, sérialisation et relance sûres.

Ce module démarre un watchdog des dossiers d’entrée, scrute le flag
`.force_full_index` et lance le pipeline via `_run_pipeline_safely()`,
sous verrou inter-processus. Il effectue une probe d’écriture sans
embedder, n’exécute le pipeline que si la base est utilisable, et ne
pose le `index_ready.flag` qu’en cas de succès, en consommant le flag
de forçage ensuite. Il évite les accès concurrents à Chroma pendant
les resets/rebuilds et peut appliquer un backoff sur les relances.

"""
from __future__ import annotations
import os, stat, glob
import sys
import time
import threading
from pathlib import Path
from typing import Optional
from fasteners import InterProcessLock
import getpass

try:
    from chromadb.errors import InternalError
except Exception:
    class InternalError(Exception):
        pass

from config.config import (
                            CHROMA_GLOBAL_DIR,
                            INDEX_READY_FLAG_PATH,
                            FORCE_FULL_INDEX_FLAG,
                            INDEXING_FLAG_FILE,
                            INDEX_IPC_LOCK_PATH,
                           )

from src.func.run_full_indexing_pipeline import run_full_indexing_pipeline

# ✅ Centraliser l'accès client via utils/chroma_client (LRU + reset)
from src.utils.chroma_client import get_chroma_client, reset_chroma_client_cache

# -------------------------------------------------
# Directoires à surveiller (déjà définis chez toi)
# -------------------------------------------------
from config.config import INPUT_DOCX, WEB_SITES_HEALTH_DOC_BASE

WATCHED_DIRECTORIES = [
    INPUT_DOCX,
    WEB_SITES_HEALTH_DOC_BASE,
]

# -------------------------------------------------
# Flags et verrous
# -------------------------------------------------
INDEX_READY_FLAG = INDEX_READY_FLAG_PATH


# -------------------------------------------------
# Watchdog (avec debounce)
# -------------------------------------------------
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_AVAILABLE = True
except Exception:
    WATCHDOG_AVAILABLE = False

# ---

print(f"[scheduler] ready_flag={INDEX_READY_FLAG} force_flag={FORCE_FULL_INDEX_FLAG} lock={INDEX_IPC_LOCK_PATH}")


class _Debouncer:
    def __init__(self, wait_seconds: float = 2.0):
        self.wait = wait_seconds
        self._timer: Optional[threading.Timer] = None
        self._lock = threading.Lock()

    def trigger(self, fn, *args, **kwargs):
        def _fire():
            fn(*args, **kwargs)
        with self._lock:
            if self._timer and self._timer.is_alive():
                self._timer.cancel()
            self._timer = threading.Timer(self.wait, _fire)
            self._timer.daemon = True
            self._timer.start()


class _WatchHandler(FileSystemEventHandler):
    def __init__(self, debouncer: _Debouncer):
        super().__init__()
        self.debouncer = debouncer

    def on_any_event(self, event):
        p = getattr(event, "src_path", "") or ""
        name = os.path.basename(p)
        # ignorer fichiers cachés/temp
        if name.startswith(".") or name.endswith("~") or name.endswith(".tmp"):
            return
        self.debouncer.trigger(_run_pipeline_safely, reason=f"watchdog:{event.event_type}:{p}")


# -------------------------------------------------
# Robustesse: probe + wrapper pipeline
# -------------------------------------------------
def _probe_chroma_writable(client) -> None:
    """(DEBUG uniquement) Déclenche un write avec documents => peut appeler l'embedder."""
    name = f"healthcheck_{os.getpid()}_{int(time.time()*1000)}"
    col = client.get_or_create_collection(name=name)
    try:
        col.add(documents=["ok"], metadatas=[{}], ids=["probe"])
    finally:
        try:
            client.delete_collection(name)
        except Exception:
            pass


def probe_writable_no_embed(c):
    """
    Teste l'écriture sans déclencher d'embed serveur :
    - crée une collection temporaire NOM UNIQUE
    - ajoute 1 vecteur d'embedding "manuel"
    - supprime la collection
    Lève en cas d'échec (à gérer dans _run_pipeline_safely).
    """
    name = f"healthcheck_tmp_{os.getpid()}_{int(time.time()*1000)}"
    col = c.get_or_create_collection(name=name)
    try:
        col.add(embeddings=[[0.0]*8], metadatas=[{"k": "v"}], ids=["probe"])
        return True
    finally:
        try:
            c.delete_collection(name)
        except Exception:
            pass


def _ensure_writable_dir_now(p: Path):
    p.mkdir(parents=True, exist_ok=True)
    # Permissions minimales (u+rwx)
    try:
        os.chmod(p, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
    except Exception:
        pass
    # Test d'écriture FS (sans Chroma)
    probe = p / ".fs_write_probe"
    with open(probe, "w", encoding="utf-8") as f:
        f.write("ok")
    probe.unlink(missing_ok=True)

def _cleanup_sqlite_artifacts_now(p: Path):
    for pattern in ("*.wal", "*.shm", "*.lock"):
        for f in p.glob(pattern):
            try:
                f.unlink()
            except Exception:
                pass




INTERPROCESS_LOCK = InterProcessLock(INDEX_IPC_LOCK_PATH)

def _run_pipeline_safely(reason: str = "") -> None:
    """Lance run_full_indexing_pipeline() de façon sérialisée, avec verrou IPC, probe no-embed,
    reset client, et pose du ready-flag uniquement en cas de succès."""
    # Créer l'objet de lock IPC (une fois au module de préférence)
    global INTERPROCESS_LOCK
    try:
        INTERPROCESS_LOCK
    except NameError:
        from fasteners import InterProcessLock
        INTERPROCESS_LOCK = InterProcessLock(INDEX_IPC_LOCK_PATH)

    # Tenter de prendre le lock IPC sans bloquer
    acquired = INTERPROCESS_LOCK.acquire(blocking=False)
    if not acquired:
        print(f"⏭️ Rebuild ignoré (déjà en cours via lock IPC) — raison='{reason}'")
        return

    chroma_path = Path(CHROMA_GLOBAL_DIR)
    _cleanup_sqlite_artifacts_now(chroma_path)  # au cas où des verrous résiduels traînent
    _ensure_writable_dir_now(chroma_path)

    ok = False
    try:
        # Témoin d'activité (intra/proc et lisible)
        if INDEXING_FLAG_FILE.exists():
            print(f"⏭️ Rebuild ignoré (flag {INDEXING_FLAG_FILE.name} présent) — raison='{reason}'")
            return
        try:
            INDEXING_FLAG_FILE.touch(exist_ok=False)
        except Exception as e:
            print(f"⚠️ Impossible de créer le flag {INDEXING_FLAG_FILE}: {e}", file=sys.stderr)
            return  # on n'avance pas sans témoin fiable

        # Invalider le ready pendant le rebuild
        try:
            INDEX_READY_FLAG.unlink(missing_ok=True)
        except Exception:
            pass

        # Invalider le client avant toute opération
        reset_chroma_client_cache()

        st = os.stat(CHROMA_GLOBAL_DIR)
        print(f"[🟧 probe ctx] user={getpass.getuser()} path={CHROMA_GLOBAL_DIR} mode={oct(stat.S_IMODE(st.st_mode))}")
        print(f"[🟧 probe ctx] pid={os.getpid()} ipc_lock={INDEX_IPC_LOCK_PATH} "
              f"force={FORCE_FULL_INDEX_FLAG.exists()} indexing={INDEXING_FLAG_FILE.exists()} t={time.time():.0f}")

        # Probe écriture SANS embed; abort si KO
        try:
            client = get_chroma_client()
            probe_writable_no_embed(client)  # <— version "nom unique" adoptée
        except Exception as e:
            print(f"⚠️ Probe Chroma KO, abandon du pipeline: {e}", file=sys.stderr)
            reset_chroma_client_cache()
            return  # ne pas marquer ready

        # Pipeline (avec retry ciblé sur readonly/1032)
        try:
            print(f"🟡 Lancement pipeline (raison='{reason}')…")
            run_full_indexing_pipeline()
            ok = True
        except InternalError as e:
            msg = str(e).lower()
            print(f"🔴 InternalError pendant pipeline: {e}", file=sys.stderr)
            if "readonly" in msg or "1032" in msg:
                reset_chroma_client_cache()
                time.sleep(0.5)
                print("↻ Retry pipeline après reset client…")
                run_full_indexing_pipeline()
                ok = True
            else:
                ok = False
                return  # laisser le finally gérer sans poser ready
        except Exception as e:
            print(f"🔴 Échec pipeline: {e}", file=sys.stderr)
            ok = False
            return

        # Si on arrive ici et ok, poser le ready + consommer le force flag
        if ok:
            try:
                INDEX_READY_FLAG.write_text("ready\n", encoding="utf-8")
                print(f"[DEBUG ✅] Flag écrit à : {INDEX_READY_FLAG}")
            except Exception as e:
                print(f"⚠️ Impossible d’écrire le ready flag: {e}", file=sys.stderr)

            try:
                FORCE_FULL_INDEX_FLAG.unlink(missing_ok=True)
                print("[🟨 scheduler] force flag consumed")
            except Exception:
                pass

    finally:
        # Nettoyage du flag d’activité et release du lock
        try:
            INDEXING_FLAG_FILE.unlink(missing_ok=True)
        except Exception:
            pass
        try:
            INTERPROCESS_LOCK.release()
        except Exception:
            pass


def _collections_missing() -> bool:
    """True si base_docx ou base_web manquent (ou si Chroma est indisponible/occupée)."""
    # Évite de sonder Chroma pendant un rebuild en cours
    if INDEXING_FLAG_FILE.exists():
        return True
    try:
        client = get_chroma_client()
        names = [c.name for c in client.list_collections()]
        missing = {"base_docx", "base_web"} - set(names)
        if missing:
            print(f"🟠 Collections manquantes : {sorted(missing)}")
            return True
        return False
    except Exception as e:
        msg = str(e).lower()
        if "no such table: tenants" in msg or "readonly" in msg or "1032" in msg:
            print(f"🟠 Chroma non initialisée/readonly lors du listage: {e}", file=sys.stderr)
        else:
            print(f"⚠️ Impossible de lister les collections: {e}", file=sys.stderr)
        return True


# -------------------------------------------------
# Entrée principale
# -------------------------------------------------
def start_scheduler() -> None:
    """
    Démarre le scheduler de réindexation Chroma et la surveillance fichiers.

    Crée le répertoire de persistance au besoin, évalue l’état initial
    (présence du ready flag, collections manquantes, demande de rebuild)
    et déclenche une réindexation si nécessaire. Lance un watchdog
    (avec anti-rebond) sur les dossiers d’entrée, puis entre dans une
    boucle qui scrute `.force_full_index` et délègue à
    `_run_pipeline_safely()` sous verrou inter-processus. Cette fonction
    n’efface pas le flag de forçage (consommé en cas de succès par le pipeline)
    et arrête proprement l’observer sur interruption clavier.
    """

    print(f"🟢 CHROMA_GLOBAL_DIR = {CHROMA_GLOBAL_DIR}")

    # S'assurer que le dossier Chroma existe (permissions déjà gérées côté reset_all_data)
    chroma_dir = Path(CHROMA_GLOBAL_DIR)
    chroma_dir.mkdir(parents=True, exist_ok=True)

    # État initial : ne pas poser le ready.flag si un rebuild est demandé ou en cours
    if not INDEX_READY_FLAG.exists():
        print("ℹ️ Base présente mais flag 'ready' absent — vérification des collections…")
        if FORCE_FULL_INDEX_FLAG.exists() or INDEXING_FLAG_FILE.exists():
            print("ℹ️ Rebuild demandé/en cours — pas de ready.flag pour l’instant.")
        elif _collections_missing():
            print("🟠 Collections manquantes → relance du pipeline d’indexation.")
            _run_pipeline_safely(reason="startup_missing_ready_or_collections")
        else:
            try:
                INDEX_READY_FLAG.write_text("ready\n", encoding="utf-8")
                print(f"[DEBUG ✅] Flag écrit à : {INDEX_READY_FLAG}")
            except Exception as e:
                print(f"⚠️ Impossible d’écrire le ready flag: {e}", file=sys.stderr)
    else:
        print("✅ Index prêt (flag présent).")

    # Watchdog (surveillance temps réel des dossiers d'entrée)
    observer = None
    if not WATCHDOG_AVAILABLE:
        print("⚠️ Watchdog non disponible — aucune surveillance temps réel.")
    else:
        debouncer = _Debouncer(wait_seconds=2.0)
        handler = _WatchHandler(debouncer)
        observer = Observer()
        for raw in WATCHED_DIRECTORIES:
            if not raw:
                continue
            d = Path(raw)
            if not d.exists():
                print(f"⚠️ Dossier à surveiller introuvable : {d}")
                continue
            try:
                observer.schedule(handler, str(d), recursive=True)
                print(f"✅ Surveillance activée sur : {d}")
            except Exception as e:
                print(f"⚠️ Impossible de surveiller {d} : {e}")
        observer.daemon = True
        observer.start()

    # Boucle de poll du flag .force_full_index (consommation gérée par _run_pipeline_safely)
    try:
        backoff = 1.0
        while True:
            if FORCE_FULL_INDEX_FLAG.exists():
                print("\n🟢 Flag détecté à chaud → réindexation complète…")
                before = time.time()
                _run_pipeline_safely(reason="force_flag")
                # Si _run_pipeline_safely n'a pas consommé le flag (échec), on augmente un peu
                if FORCE_FULL_INDEX_FLAG.exists():
                    backoff = min(backoff * 1.5, 30.0)
                else:
                    backoff = 1.0
                elapsed = time.time() - before
                # dormir au moins 'backoff' (mais pas moins que 1s pour ne pas surchauffer)
                time.sleep(max(backoff - elapsed, 1.0))
            else:
                backoff = 1.0
                time.sleep(1.0)

    except KeyboardInterrupt:
        print("\n🛑 Arrêt de la surveillance demandé (Ctrl+C).")
        if observer:
            observer.stop()
            observer.join()

