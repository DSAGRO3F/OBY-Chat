# src/utils/reset_data.p
"""
Réinitialise proprement l’environnement d’indexation Chroma et les artefacts locaux.

Ce module fournit `reset_all_data()` qui, sous verrou inter-processus,
efface le dossier Chroma, nettoie les JSON générés et réinitialise le
journal via une écriture atomique. Il supprime le ready-flag, pose le
flag `.force_full_index` (écriture atomique) et recrée les répertoires
avec des permissions minimales sûres. Aucun client Chroma direct n’est
instancié ici : le cache client global est d’abord invalidé pour éviter
les handles orphelins et les erreurs SQLite “readonly (1032)”.
"""

import os, shutil, sys, glob, stat, json
from pathlib import Path
from fasteners import InterProcessLock
import tempfile

from src.utils.chroma_client import reset_chroma_client_cache

from config.config import (CHROMA_GLOBAL_DIR,
                           JSON_HEALTH_DOC_BASE,
                           WEB_SITES_JSON_HEALTH_DOC_BASE,
                           INDEXED_FILES_JOURNAL_PATH,
                           INDEX_IPC_LOCK_PATH,
                           FORCE_FULL_INDEX_FLAG)

from src.utils.vector_db_utils import mark_index_ready_flag, clear_index_ready_flag


def _cleanup_sqlite_artifacts(dirpath: str | Path):
    p = Path(dirpath)
    for pattern in ("*.wal", "*.shm", "*.lock"):
        for f in p.glob(pattern):
            try:
                f.unlink()
            except Exception:
                pass

def _ensure_writable_dir(p: str | Path):
    d = Path(p)
    d.mkdir(parents=True, exist_ok=True)
    # RWX pour l’utilisateur
    try:
        os.chmod(d, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
    except Exception:
        pass

def _clean_dir_contents(dir_path: str | Path):
    d = Path(dir_path)
    if not d.exists():
        print(f"🟠 Dossier non trouvé (ok) : {d}")
        d.mkdir(parents=True, exist_ok=True)
        return
    # Supprime tout le contenu sans enlever le dossier racine
    for entry in d.iterdir():
        try:
            if entry.is_symlink():
                entry.unlink(missing_ok=True)
            elif entry.is_dir():
                shutil.rmtree(entry, ignore_errors=True)
            else:
                entry.unlink(missing_ok=True)
        except Exception as e:
            print(f"⚠️ Échec suppression {entry}: {e}", file=sys.stderr)
    # S’assure des permissions minimum
    try:
        os.chmod(d, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
    except Exception:
        pass


def _atomic_write_json(target_path: str | Path, data: dict):
    target = Path(target_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=target.parent, delete=False) as tf:
        json.dump(data, tf, ensure_ascii=False)
        tf.flush()
        os.fsync(tf.fileno())
        tmp_name = tf.name
    os.replace(tmp_name, target)   # atomic swap
    # fsync du dossier pour garantir la metadata
    dir_fd = os.open(target.parent, os.O_DIRECTORY)
    try:
        os.fsync(dir_fd)
    finally:
        os.close(dir_fd)


def _atomic_write_text(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as tf:
        tf.write(content)
        tf.flush()
        os.fsync(tf.fileno())
        tmp_name = tf.name
    os.replace(tmp_name, path)  # swap atomique


def reset_all_data():
    print("🔴 Réinitialisation des données...")

    # Empêcher toute course avec le scheduler/pipeline
    with InterProcessLock(INDEX_IPC_LOCK_PATH):
        # 1) UI doit passer immédiatement en "indexation en cours"
        try:
            clear_index_ready_flag()
            print("🔴 Flag 'index_ready' supprimé.")
        except Exception as e:
            print(f"🔴 Impossible de supprimer le flag 'index_ready' : {e}", file=sys.stderr)

        # 2) Invalider TOUT client Chroma en cache avant toute action disque
        try:
            reset_chroma_client_cache()
        except Exception as e:
            print(f"⚠️ Impossible de réinitialiser le cache Chroma : {e}", file=sys.stderr)

        # 3) Supprimer proprement le dossier Chroma (sans client ouvert)
        try:
            if os.path.exists(CHROMA_GLOBAL_DIR):
                # retirer éventuels artefacts SQLite qui bloquent la suppression
                _cleanup_sqlite_artifacts(CHROMA_GLOBAL_DIR)
                shutil.rmtree(CHROMA_GLOBAL_DIR, ignore_errors=True)
                print(f"✅ Dossier ChromaDB supprimé : {CHROMA_GLOBAL_DIR}")
        except Exception as e:
            print(f"⚠️ Impossible de supprimer {CHROMA_GLOBAL_DIR} : {e}", file=sys.stderr)

        # 4) Recréer le dossier et s’assurer des permissions
        _ensure_writable_dir(CHROMA_GLOBAL_DIR)


        # JSON locaux/web
        for path in [JSON_HEALTH_DOC_BASE, WEB_SITES_JSON_HEALTH_DOC_BASE]:
            for path in [JSON_HEALTH_DOC_BASE, WEB_SITES_JSON_HEALTH_DOC_BASE]:
                _clean_dir_contents(path)
                print(f"✅ Fichiers supprimés dans : {path}")

        try:
            _atomic_write_json(INDEXED_FILES_JOURNAL_PATH, {})
            print("✅ Fichier de suivi réinitialisé.")
        except Exception as e:
            print(f"⚠️ Impossible de réinitialiser le journal : {e}", file=sys.stderr)

        force_flag_path = FORCE_FULL_INDEX_FLAG
        try:
            _atomic_write_text(force_flag_path, "1")
            print("🏁 Flag de réindexation complète posé (.force_full_index).")
        except Exception as e:
            print(f"⚠️ Impossible d'écrire le flag de forçage : {e}", file=sys.stderr)

        print("✅ Réinitialisation faite.")
        print("➡️ Si l’application est arrêtée : relance-la avec `python -m src.app`.")
        print("➡️ Si l’application tourne : le scheduler détectera le flag et relancera l’indexation.")

