import os
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

    # ---- Comptage des JSON sur disque ----
    stats["docx_json_files"] = _count_json_recursive(JSON_HEALTH_DOC_BASE)
    stats["web_json_files"]  = _count_json_recursive(WEB_SITES_JSON_HEALTH_DOC_BASE)

    # ---- Comptage Chroma ----
    try:
        client = get_chroma_client()
        for source_type, candidates in [
            ("docx", ["base_docx", "docx"]),  # fallback si le nom diffère entre local/prod
            ("web",  ["base_web",  "web"]),
        ]:
            try:
                col = _get_first_existing_collection(client, candidates)
                # nombre de chunks
                count = col.count() or 0
                stats[f"{source_type}_chunks"] = count

                # nombre de fichiers uniques (si métadonnées disponibles)
                metas = col.get(include=["metadatas"]).get("metadatas", []) or []
                unique_sources = {
                    (m.get("source") or m.get("source_url") or m.get("file_path"))
                    for m in metas if m
                }
                stats[f"{source_type}_files"] = len([s for s in unique_sources if s])
            except Exception:
                # collection absente : laissons 0 par défaut
                pass
    except Exception:
        # client indisponible : laissons 0 par défaut
        pass

    return stats











# from src.func.index_documents_chromadb import get_chroma_client
# from config.config import JSON_HEALTH_DOC_BASE, WEB_SITES_JSON_HEALTH_DOC_BASE
# import os
#
# def get_chroma_index_stats() -> dict:
#     """
#     Statistiques sur les données indexées dans ChromaDB et les fichiers JSON préparés.
#
#     Returns:
#         dict: {
#             "docx_files": int,        # Fichiers uniques indexés depuis docx
#             "web_files": int,         # Fichiers uniques indexés depuis web
#             "docx_chunks": int,
#             "web_chunks": int,
#             "docx_json_files": int,   # Fichiers JSON générés depuis les DOCX
#             "web_json_files": int     # Fichiers JSON générés depuis le web
#         }
#     """
#     stats = {
#         "docx_files": 0,
#         "web_files": 0,
#         "docx_chunks": 0,
#         "web_chunks": 0,
#         "docx_json_files": 0,
#         "web_json_files": 0
#     }
#
#     client = get_chroma_client()
#
#     for source_type, collection_name in [("docx", "base_docx"), ("web", "base_web")]:
#         try:
#             collection = client.get_collection(collection_name)
#             results = collection.get(include=["metadatas"], limit=100_000)
#
#             all_metadatas = results.get("metadatas", [])
#             all_sources = set()
#
#             for meta in all_metadatas:
#                 source_file = meta.get("source")
#                 if source_file:
#                     all_sources.add(source_file)
#
#             stats[f"{source_type}_files"] = len(all_sources)
#             stats[f"{source_type}_chunks"] = len(all_metadatas)
#
#         except Exception as e:
#             print(f"⚠️ Collection {collection_name} inaccessible : {e}")
#
#     # Comptage des fichiers JSON préparés
#     if os.path.exists(JSON_HEALTH_DOC_BASE):
#         stats["docx_json_files"] = len([
#             f for f in os.listdir(JSON_HEALTH_DOC_BASE) if f.endswith(".json")
#         ])
#
#     if os.path.exists(WEB_SITES_JSON_HEALTH_DOC_BASE):
#         stats["web_json_files"] = len([
#             f for f in os.listdir(WEB_SITES_JSON_HEALTH_DOC_BASE) if f.endswith(".json")
#         ])
#
#     return stats
