# src/func/get_chroma_stats.py
import os
from pathlib import Path
from config.config import (
    JSON_HEALTH_DOC_BASE,
    WEB_SITES_JSON_HEALTH_DOC_BASE,
    FORCE_FULL_INDEX_FLAG,
    INDEXING_FLAG_FILE,
)
from src.utils.chroma_client import get_chroma_client, reset_chroma_client_cache

# --- Fonctions annexes ---
def _count_json_recursive(base_dir: str) -> int:
    if not base_dir or not os.path.exists(base_dir):
        return 0
    total = 0
    for _root, _dirs, files in os.walk(base_dir):
        total += sum(1 for f in files if f.endswith(".json"))
    return total

def _is_http_url(v: str) -> bool:
    return isinstance(v, str) and v.lower().startswith("http")

def _unique_from_collection(col, key_getter, step=5000) -> int:
    seen, offset = set(), 0
    while True:
        batch = col.get(include=["metadatas"], limit=step, offset=offset)
        metas = batch.get("metadatas") or []
        if not metas:
            break
        for m in metas:
            v = None
            try:
                v = key_getter(m) if m else None
            except Exception:
                pass
            if v:
                seen.add(v)
        offset += step
    return len(seen)

# ---- WEB ----
def _web_pages_count(col):
    def get_url(m):
        u = (m.get("url") or m.get("source_url") or "").strip()
        if _is_http_url(u): return u
        s = (m.get("source") or "").strip()
        return s if _is_http_url(s) else None
    return _unique_from_collection(col, get_url)

def _web_domains_count(col):
    from urllib.parse import urlparse
    def get_domain(m):
        d = (m.get("domain") or "").strip()
        if d: return d
        for k in ("url", "source_url", "source"):
            u = (m.get(k) or "").strip()
            if _is_http_url(u):
                try: return urlparse(u).netloc
                except Exception: return None
        return None
    return _unique_from_collection(col, get_domain)


# ---- DOCX ----
def _docx_files_count(col):
    def get_src(m):
        for k in ("source_group", "source_doc", "source"):
            v = (m.get(k) or "").strip()
            if v and not _is_http_url(v):
                return v
        return None
    return _unique_from_collection(col, get_src)

def _docx_fiches_count(col):
    def get_fiche(m):
        for k in ("fiche_id", "source_path", "source_basename"):
            v = (m.get(k) or "").strip()
            if v: return v
        return None
    return _unique_from_collection(col, get_fiche)

# ---- Fonction principale ----
def get_chroma_index_stats() -> dict:
    """
    Collecte et expose des statistiques d’index Chroma pour l’UI.

    Ce module fournit une fonction principale, :func:`get_chroma_index_stats`, qui
    retourne des compteurs utiles à l’interface (nb de fichiers/chunks DOCX & Web,
    nb de JSON locaux, etc.) sans perturber l’indexation en cours.

    Comportement clé
    ----------------
    - **Aucun accès Chroma pendant l’indexation** : si l’un des drapeaux
      ``FORCE_FULL_INDEX_FLAG`` ou ``INDEXING_FLAG_FILE`` est présent, la fonction
      n’instancie pas de client Chroma et renvoie simplement les compteurs de fichiers
      JSON présents sur disque, avec ``indexing=True``.
    - **Accès Chroma en lecture seule sinon** : une fois l’index prêt
      (flags absents), le cache client est invalidé puis un client Chroma est créé
      pour lire les collections (``base_docx`` / ``base_web``) et calculer les
      compteurs (chunks, fichiers, domaines).
    - **Aucun effet de bord à l’import** : le module n’ouvre jamais Chroma au
      chargement. Toute lecture Chroma se fait *uniquement* à l’appel de la fonction.

    Valeur de retour
    ----------------
    La fonction :func:`get_chroma_index_stats` renvoie un ``dict`` du type :

        {
            "docx_files": int,
            "docx_chunks": int,
            "docx_json_files": int,
            "web_files": int,
            "web_chunks": int,
            "web_json_files": int,
            "docx_fiches": int,
            "web_domains": int,
            "indexing": bool,  # True si un rebuild est demandé/en cours
        }

    Dans les cas d’erreur de lecture Chroma, la fonction reste tolérante et
    renvoie simplement les compteurs JSON avec les autres valeurs à 0.

    Dépendances & conventions
    -------------------------
    - Ce module s’appuie sur les chemins/flags centralisés dans ``config.config`` :
      ``FORCE_FULL_INDEX_FLAG``, ``INDEXING_FLAG_FILE``, ``JSON_HEALTH_DOC_BASE``,
      ``WEB_SITES_JSON_HEALTH_DOC_BASE``.
    - L’accès client est **centralisé** via ``src.utils.chroma_client`` :
      ``get_chroma_client`` et ``reset_chroma_client_cache``.
    - Les noms de collections attendues sont ``base_docx`` et ``base_web``.

    """
    stats = {
        "docx_files": 0, "docx_chunks": 0, "docx_json_files": 0,
        "web_files": 0,  "web_chunks": 0,  "web_json_files": 0,
        "docx_fiches": 0, "web_domains": 0,
        "indexing": False,  # <- nouveau champ explicite pour l'UI
    }

    # Comptage JSON sur disque (toujours OK, indépendant de Chroma)
    docx_dir = Path(JSON_HEALTH_DOC_BASE)
    web_dir  = Path(WEB_SITES_JSON_HEALTH_DOC_BASE)
    if docx_dir.exists():
        stats["docx_json_files"] = _count_json_recursive(str(docx_dir))
    if web_dir.exists():
        stats["web_json_files"]  = _count_json_recursive(str(web_dir))

    # Si un rebuild est demandé/en cours, ne pas interroger Chroma
    if FORCE_FULL_INDEX_FLAG.exists() or INDEXING_FLAG_FILE.exists():
        stats["indexing"] = True
        return stats

    # (Option) Après disparition des flags, on reset le cache client pour repartir proprement
    reset_chroma_client_cache()

    # Lecture Chroma en best-effort (aucun write)
    try:
        client = get_chroma_client()

        # DOCX
        docx_col = None
        for name in ("base_docx", "docx"):
            try:
                docx_col = client.get_collection(name)
                break
            except Exception:
                pass
        if docx_col:
            try:
                stats["docx_chunks"] = docx_col.count() or 0
                stats["docx_files"]  = _docx_files_count(docx_col)
                stats["docx_fiches"] = _docx_fiches_count(docx_col)
            except Exception:
                # Laisse les valeurs par défaut si ça échoue
                pass

        # WEB
        web_col = None
        for name in ("base_web", "web"):
            try:
                web_col = client.get_collection(name)
                break
            except Exception:
                pass
        if web_col:
            try:
                stats["web_chunks"]  = web_col.count() or 0
                stats["web_files"]   = _web_pages_count(web_col)
                stats["web_domains"] = _web_domains_count(web_col)
            except Exception:
                pass

    except Exception:
        # Si Chroma est indisponible (ex: tout juste recréée), on retourne
        # simplement les compteurs JSON et indexing=False (l’UI sait gérer).
        pass

    return stats

# Audit chromadb
from collections import Counter

def sample_key_presence(col, n=200):
    rows = col.get(include=["metadatas"], limit=n)
    metas = rows.get("metadatas") or []
    c = Counter()
    for m in metas:
        if not m:
            c["__empty__"] += 1
            continue
        for k in ("url","source_url","source","domain","fiche_id","source_path","source_basename"):
            if m.get(k): c[k] += 1
    return c, metas[:3]  # compteur + 3 exemples


def debug_dump_collections() -> None:
    """
    N'affiche les infos Chroma que si l'index N'EST PAS en cours de rebuild.
    À appeler manuellement (ex: python -m src.func.get_chroma_stats).
    """
    if FORCE_FULL_INDEX_FLAG.exists() or INDEXING_FLAG_FILE.exists():
        print("[debug_dump_collections] Indexation en cours — skip lecture Chroma.")
        return

    # repartir avec un client propre après un rebuild
    reset_chroma_client_cache()

    try:
        c = get_chroma_client()
    except Exception as e:
        print(f"[debug_dump_collections] Impossible d'obtenir le client Chroma : {e}")
        return

    for name in ("base_docx", "base_web"):
        try:
            col = c.get_collection(name)
            count = col.count()
            keys, examples = sample_key_presence(col)
            print(f"\n== {name} ({count} docs) ==")
            print(keys)
            print("ex:", examples)
        except Exception as e:
            print(f"{name} absente: {e}")

if __name__ == "__main__":
    # Exécution manuelle uniquement, pas à l'import du module
    debug_dump_collections()

