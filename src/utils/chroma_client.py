""""
Utilitaires centralisés pour la couche vecteur (ChromaDB).

Fournit un client Chroma persistant (avec cache LRU) pointant vers le dossier
global de l’index, ainsi que des helpers pour réinitialiser le cache et tracer
les appels (mode debug). Ce module sert de point d’entrée unique pour obtenir
le client utilisé à l’indexation et à la recherche, afin d’assurer la cohérence.
"""


# src/utils/chroma_client.py
from chromadb import PersistentClient
from chromadb.config import Settings
from functools import lru_cache

from config.config import (
    EMBEDDING_PROVIDER, OPENAI_EMBEDDING_MODEL,
    EMBEDDING_MODEL_NAME, NORMALIZE_EMBEDDINGS,
    BASE_DOCX_COLLECTION, BASE_WEB_COLLECTION,
    CHROMA_GLOBAL_DIR, EMBEDDING_DEVICE
)


try:
    from langchain_openai import OpenAIEmbeddings
except Exception:
    OpenAIEmbeddings = None

# Essaie d'utiliser HF si provider=huggingface
try:
    from langchain_huggingface import HuggingFaceEmbeddings
except Exception:
    from langchain_community.embeddings import (
        HuggingFaceBgeEmbeddings as HuggingFaceEmbeddings
    )

@lru_cache(maxsize=1)
def get_embedding_model():
    """
    Retourne l’objet embedding (OpenAI ou HF) selon EMBEDDING_PROVIDER.
    C’est *la* source de vérité utilisée par l’indexation et par la recherche.
    """
    if EMBEDDING_PROVIDER.lower() == "openai":
        if OpenAIEmbeddings is None:
            raise RuntimeError("langchain-openai n'est pas installé.")
        # text-embedding-3-small (1536 dims) par défaut
        return OpenAIEmbeddings(model=OPENAI_EMBEDDING_MODEL)
    else:
        # fallback HF (ton ancien setup local)
        return HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL_NAME,
            encode_kwargs={"normalize_embeddings": NORMALIZE_EMBEDDINGS},
        )

def get_collection_names(source_type: str) -> str:
    """
    Centralise les noms des collections à utiliser côté indexation & retrieval.
    """
    if source_type not in {"docx", "web"}:
        raise ValueError(f"source_type invalide: {source_type!r} (attendus: 'docx' ou 'web')")
    return "base_docx" if source_type == "docx" else "base_web"


@lru_cache(maxsize=1)
def get_chroma_client():
    CHROMA_GLOBAL_DIR.mkdir(parents=True, exist_ok=True)
    return PersistentClient(
        path=str(CHROMA_GLOBAL_DIR),
        settings=Settings(anonymized_telemetry=False)
    )

def reset_chroma_client_cache():
    get_chroma_client.cache_clear()
    get_embedding_model.cache_clear()

