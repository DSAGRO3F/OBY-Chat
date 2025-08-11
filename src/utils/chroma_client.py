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
    client = PersistentClient(path=CHROMA_GLOBAL_DIR)
    return client















# # Dictionnaire interne pour mémoriser les instances selon leur dossier
# _chroma_clients = {}
#
# def get_chroma_client(source: str = "docx") -> Client:
#     """
#     Crée et retourne une instance de Chroma Client en fonction de la source documentaire.
#
#     Args:
#         source (str): 'docx' pour les documents Word, 'web' pour les pages web.
#
#     Returns:
#         Client: Instance configurée du client ChromaDB.
#     """
#     if source == "docx":
#         persist_dir = CHROMA_DOCX_DIR
#     elif source == "web":
#         persist_dir = CHROMA_WEB_DIR
#     else:
#         raise ValueError("Source inconnue. Utiliser 'docx' ou 'web'.")
#
#     if persist_dir not in _chroma_clients:
#         print(f"📦 Initialisation d’un nouveau client ChromaDB pour le dossier : {persist_dir}")
#         _chroma_clients[persist_dir] = Client(Settings(persist_directory=persist_dir))
#     else:
#         print(f"♻️ Client ChromaDB déjà initialisé pour : {persist_dir}")
#
#     return _chroma_clients[persist_dir]
