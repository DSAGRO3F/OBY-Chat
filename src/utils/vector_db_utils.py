# src/utils/vector_db_utils.py
"""
Utilitaires pour la base vectorielle (Chroma) : flags et E/S atomiques.

Ce module regroupe des helpers pour gérer les drapeaux de statut
(`index_ready.flag`, `.force_full_index`), avec des écritures atomiques
et une suppression tolérante aux erreurs. Il peut fournir des fonctions
comme `mark_index_ready_flag()` et `clear_index_ready_flag()` basées
sur les chemins centralisés de `config.config`. L’objectif est d’éviter
les états incohérents pendant les resets/rebuilds et d’offrir une API
simple et sûre aux autres modules (scheduler, UI, pipelines).
"""

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
        print(f"[DEBUG] Chemin du flag : {INDEX_READY_FLAG_PATH.resolve()}")
        print(f"[DEBUG] Contenu du dossier : {list(INDEX_READY_FLAG_PATH.parent.glob('*'))}")
        print(f"[DEBUG] Fichier présent ? {exists}")
    return exists

def mark_index_ready_flag():
    """
    Crée un fichier flag indiquant que l'indexation ChromaDB est terminée.
    Si le répertoire n'existe pas, il est créé.
    """
    INDEX_READY_FLAG_PATH.parent.mkdir(parents=True, exist_ok=True)
    INDEX_READY_FLAG_PATH.touch(exist_ok=True)
    # print(f"[DEBUG ✅] Flag écrit à : {INDEX_READY_FLAG_PATH.resolve()}")


def clear_index_ready_flag() -> None:
    """
    Supprime le fichier 'index_ready.flag' pour signaler que l'indexation doit être relancée.

    Cette opération est utile si l'on souhaite forcer une réindexation complète.
    """
    if INDEX_READY_FLAG_PATH.exists():
        INDEX_READY_FLAG_PATH.unlink()


if __name__ == "__main__":
    print("✅Test de is_chroma_index_ready()")
    print("✅ Flag présent :", is_chroma_index_ready(verbose=True))
