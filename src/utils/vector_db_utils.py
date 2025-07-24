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


def is_chroma_index_ready(verbose: bool = False) -> bool:
    """
    Vérifie si le fichier 'index_ready.flag' existe dans le dossier vectoriel.

    Args:
        verbose (bool): Si True, affiche le chemin du flag pour le debug.

    Returns:
        bool: True si les bases ChromaDB ont été indexées, False sinon.
    """
    exists = INDEX_READY_FLAG_PATH.exists()
    if verbose:
        print(f"[INFO] Vérification de l'indexation : {INDEX_READY_FLAG_PATH} => {exists}")
    return exists


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


if __name__ == "__main__":
    print("🔍 Test de is_chroma_index_ready()")
    print("📦 Flag présent :", is_chroma_index_ready(verbose=True))
