import os
from pathlib import Path
from config.config import JSON_HEALTH_DOC_BASE, WEB_SITES_JSON_HEALTH_DOC_BASE
from src.func.index_documents_chromadb import get_chroma_client



def _count_json_recursive(base_dir: str) -> int:
    """Compte tous les fichiers .json dans base_dir (et sous-dossiers si jamais il y en a)."""
    if not base_dir or not os.path.exists(base_dir):
        return 0
    total = 0
    for root, _dirs, files in os.walk(base_dir):
        total += sum(1 for f in files if f.endswith(".json"))
    return total


def _get_first_existing_collection(client, names):
    """Retourne la première collection existante parmi une liste de noms candidates."""
    for name in names:
        try:
            return client.get_collection(name)
        except Exception:
            continue
    raise RuntimeError(f"Aucune collection trouvée parmi: {names}")


def get_chroma_index_stats() -> dict:
    stats = {
        "docx_files": 0, "docx_chunks": 0, "docx_json_files": 0,
        "web_files": 0,  "web_chunks": 0,  "web_json_files": 0,
    }

    # --- JSON sur disque (Path) ---
    docx_dir = Path(JSON_HEALTH_DOC_BASE)
    web_dir = Path(WEB_SITES_JSON_HEALTH_DOC_BASE)

    # ---- Comptage des JSON sur disque ----
    if docx_dir.exists():
        stats["docx_json_files"] = _count_json_recursive(JSON_HEALTH_DOC_BASE)
    if web_dir.exists():
        stats["web_json_files"]  = _count_json_recursive(WEB_SITES_JSON_HEALTH_DOC_BASE)

    # ---- Comptage Chroma ----
    try:
        client = get_chroma_client()
        for source_type, candidates in [
            ("docx", ["base_docx", "docx"]),  # fallback si le nom diffère entre local/prod
            ("web",  ["base_web",  "web"]),
        ]:
            col = None
            for name in candidates:
                try:
                    col = client.get_collection(name)
                    break
                except Exception:
                    continue
            if not col:
                continue

            count = col.count() or 0
            stats[f"{source_type}_chunks"] = count

            metas = col.get(include=["metadatas"]).get("metadatas", []) or []
            sources = {
                (m.get("source") or m.get("source_url") or m.get("file_path"))
                for m in metas if m
            }
            stats[f"{source_type}_files"] = len([s for s in sources if s])

    except Exception as e:
        print(f"⚠️ Stats Chroma indisponibles : {e}")

    return stats









