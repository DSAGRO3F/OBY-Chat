"""
Module de réinitialisation des données indexées de l'application OBY-IA.

Ce module fournit une fonction utilitaire permettant de nettoyer l’environnement
de travail en supprimant :
- les collections ChromaDB (ex. : `base_docx`, `base_web`),
- les fichiers JSON issus de l’extraction documentaire locale et web,
- le fichier journal qui suit les fichiers déjà indexés.

Utile pour remettre à zéro l’état de l’index avant un nouveau traitement complet.
"""



# src/utils/reset_data.py
import os
import shutil
import json
from chromadb import PersistentClient
from config.config import (CHROMA_GLOBAL_DIR,
                        JSON_HEALTH_DOC_BASE,
                        WEB_SITES_JSON_HEALTH_DOC_BASE,
                        INDEXED_FILES_JOURNAL_PATH)

def reset_all_data():
    """
    Réinitialise toutes les données indexées par l'application OBY-IA.

    1. Supprime les collections ChromaDB (logiques + fichiers).
    2. Supprime les fichiers JSON locaux/web extraits.
    3. Réinitialise le fichier de journalisation.
    """

    print("🧹 Réinitialisation des données...")

    # 1. Réinitialiser ChromaDB (logique)
    client = PersistentClient(path=CHROMA_GLOBAL_DIR)
    for collection_name in ["base_docx", "base_web"]:
        try:
            client.delete_collection(collection_name)
            print(f"✅ Collection supprimée : {collection_name}")
        except Exception as e:
            print(f"⚠️ Impossible de supprimer {collection_name} : {e}")

    # 1b. Supprimer aussi physiquement les dossiers persistés de ChromaDB
    if os.path.exists(CHROMA_GLOBAL_DIR):
        try:
            shutil.rmtree(CHROMA_GLOBAL_DIR)
            print(f"🧹 Dossier physique ChromaDB supprimé : {CHROMA_GLOBAL_DIR}")
        except Exception as e:
            print(f"⚠️ Impossible de supprimer {CHROMA_GLOBAL_DIR} : {e}")

    # 2. Supprimer les fichiers JSON
    for path in [JSON_HEALTH_DOC_BASE, WEB_SITES_JSON_HEALTH_DOC_BASE]:
        if os.path.exists(path):
            for file in os.listdir(path):
                os.remove(os.path.join(path, file))
            print(f"🗑 Fichiers supprimés dans : {path}")
        else:
            print(f"⚠️ Dossier non trouvé : {path}")

    # 3. Réinitialiser le fichier de suivi
    with open(INDEXED_FILES_JOURNAL_PATH, "w", encoding="utf-8") as f:
        json.dump({}, f)
    print("📄 Fichier de suivi réinitialisé.")

    print("✅ Réinitialisation terminée.")






# def reset_all_data():
#     """
#         Réinitialise toutes les données indexées par l'application OBY-IA.
#
#         Cette fonction effectue les opérations suivantes :
#         1. Suppression des collections ChromaDB (`base_docx`, `base_web`) si elles existent.
#         2. Suppression des fichiers JSON dans les répertoires locaux et web d’extraction documentaire.
#         3. Réinitialisation du fichier de journalisation des fichiers indexés (fichier JSON vide).
#
#         Utile pour repartir d’un environnement vierge avant un nouveau cycle d’indexation.
#
#         Effets :
#             - Modifie le système de fichiers local (suppression de fichiers).
#             - Supprime des données persistantes dans ChromaDB.
#         """
#     print("🧹 Réinitialisation des données...")
#
#     # 1. Réinitialiser ChromaDB
#     client = PersistentClient(path=CHROMA_GLOBAL_DIR)
#     for collection_name in ["base_docx", "base_web"]:
#         try:
#             client.delete_collection(collection_name)
#             print(f"✅ Collection supprimée : {collection_name}")
#         except Exception as e:
#             print(f"⚠️ Impossible de supprimer {collection_name} : {e}")
#
#     # 2. Supprimer les fichiers JSON
#     for path in [JSON_HEALTH_DOC_BASE, WEB_SITES_JSON_HEALTH_DOC_BASE]:
#         if os.path.exists(path):
#             for file in os.listdir(path):
#                 os.remove(os.path.join(path, file))
#             print(f"🗑 Fichiers supprimés dans : {path}")
#         else:
#             print(f"⚠️ Dossier non trouvé : {path}")
#
#     # 3. Réinitialiser le fichier de suivi
#     with open(INDEXED_FILES_JOURNAL_PATH, "w", encoding="utf-8") as f:
#         json.dump({}, f)
#     print("📄 Fichier de suivi réinitialisé.")
#
#     print("✅ Réinitialisation terminée.")
