"""
Point d’accès centralisé au client Chroma avec cache et reset sûrs.

Ce module expose `get_chroma_client()` (LRU-caché) pour créer un client
unique et cohérent sur tout le projet, ainsi que `reset_chroma_client_cache()`
pour invalider ce cache lors des resets/rebuilds. L’objectif est d’éviter
les handles orphelins et les états SQLite en lecture seule, en garantissant
une seule façon d’instancier le client (p. ex. PersistentClient) et des
chemins/flags unifiés via `config.config`. Peut inclure un logging de debug
optionnel pour tracer les appels au client pendant l’indexation.
"""


# src/utils/chroma_client.py
from chromadb import PersistentClient
from config.config import CHROMA_GLOBAL_DIR, FORCE_FULL_INDEX_FLAG, INDEXING_FLAG_FILE
from functools import lru_cache
from chromadb.config import Settings
import os, time, threading, traceback, getpass
DEBUG_CHROMA_CALLS = True  # passe à False après debug


@lru_cache(maxsize=1)
def get_chroma_client():
    if DEBUG_CHROMA_CALLS:
        print(
            f"[CHROMA GET] t={time.time():.0f} pid={os.getpid()} tid={threading.get_ident()} "
            f"user={getpass.getuser()} force={FORCE_FULL_INDEX_FLAG.exists()} "
            f"indexing={INDEXING_FLAG_FILE.exists()}",
            "".join(traceback.format_stack(limit=4)).rstrip()
        )
    CHROMA_GLOBAL_DIR.mkdir(parents=True, exist_ok=True)
    return PersistentClient(path=str(CHROMA_GLOBAL_DIR),
                            settings=Settings(anonymized_telemetry=False))


def reset_chroma_client_cache():
    get_chroma_client.cache_clear()




