"""
Module d’accès centralisé au client ChromaDB pour l'application OBY-IA.

Ce module fournit une fonction utilitaire permettant d’instancier un client ChromaDB
persistant, configuré pour enregistrer les données dans le répertoire défini par
`CHROMA_GLOBAL_DIR`. Il garantit qu’une seule instance client est utilisée
grâce au décorateur `lru_cache`.

Utilisé dans l'ensemble du projet pour interagir avec la base Chroma.
"""





# src/utils/chroma_client.py
from chromadb import PersistentClient
from config.config import CHROMA_GLOBAL_DIR  # Unique base


def get_chroma_client():
    client = PersistentClient(path=str(CHROMA_GLOBAL_DIR))
    return client






