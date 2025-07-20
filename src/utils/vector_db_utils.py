"""
Module utilitaire pour la gestion de l'état de l'indexation ChromaDB.

Ce module contient des fonctions permettant de :
- Vérifier si l'indexation ChromaDB est terminée (via un fichier flag).
- Créer ou supprimer ce flag selon les besoins.

Ce mécanisme permet à l'application (ex. interface Dash) de savoir si les bases
vectorielles sont prêtes à être interrogées par les utilisateurs.
"""

from pathlib import Path
from config.config import INDEX_READY_FLAG_PATH

# Chemin du fichier flag
# INDEX_READY_FLAG_PATH = Path("src/vector_db/index_ready.flag")

def is_chroma_index_ready() -> bool:
    """
    Vérifie si le fichier 'index_ready.flag' existe dans le dossier vectoriel.

    Returns:
        bool: True si les bases ChromaDB ont été indexées, False sinon.
    """
    return INDEX_READY_FLAG_PATH.exists()


def mark_index_ready_flag():
    """
    Crée un fichier flag indiquant que l'indexation ChromaDB est terminée.
    Si le répertoire n'existe pas, il est créé.
    """
    INDEX_READY_FLAG_PATH.parent.mkdir(parents=True, exist_ok=True)
    INDEX_READY_FLAG_PATH.touch(exist_ok=True)


def clear_index_ready_flag() -> None:
    """
    Supprime le fichier 'index_ready.flag' pour signaler que l'indexation doit être relancée.

    Cette opération est utile si l'on souhaite forcer une réindexation complète.
    """
    if INDEX_READY_FLAG_PATH.exists():
        INDEX_READY_FLAG_PATH.unlink()
