from src.utils.chroma_client import get_chroma_client
from config.config import JSON_HEALTH_DOC_BASE, WEB_SITES_JSON_HEALTH_DOC_BASE
import os

def get_chroma_index_stats() -> dict:
    """
    Statistiques sur les données indexées dans ChromaDB et les fichiers JSON préparés.

    Returns:
        dict: {
            "docx_files": int,        # Fichiers uniques indexés depuis docx
            "web_files": int,         # Fichiers uniques indexés depuis web
            "docx_chunks": int,
            "web_chunks": int,
            "docx_json_files": int,   # Fichiers JSON générés depuis les DOCX
            "web_json_files": int     # Fichiers JSON générés depuis le web
        }
    """
    stats = {
        "docx_files": 0,
        "web_files": 0,
        "docx_chunks": 0,
        "web_chunks": 0,
        "docx_json_files": 0,
        "web_json_files": 0
    }

    client = get_chroma_client()

    for source_type, collection_name in [("docx", "base_docx"), ("web", "base_web")]:
        try:
            collection = client.get_collection(collection_name)
            results = collection.get(include=["metadatas"], limit=100_000)

            all_metadatas = results.get("metadatas", [])
            all_sources = set()

            for meta in all_metadatas:
                source_file = meta.get("source")
                if source_file:
                    all_sources.add(source_file)

            stats[f"{source_type}_files"] = len(all_sources)
            stats[f"{source_type}_chunks"] = len(all_metadatas)

        except Exception as e:
            print(f"⚠️ Collection {collection_name} inaccessible : {e}")

    # Comptage des fichiers JSON préparés
    if os.path.exists(JSON_HEALTH_DOC_BASE):
        stats["docx_json_files"] = len([
            f for f in os.listdir(JSON_HEALTH_DOC_BASE) if f.endswith(".json")
        ])

    if os.path.exists(WEB_SITES_JSON_HEALTH_DOC_BASE):
        stats["web_json_files"] = len([
            f for f in os.listdir(WEB_SITES_JSON_HEALTH_DOC_BASE) if f.endswith(".json")
        ])

    return stats
