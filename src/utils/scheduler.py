"""
Module de surveillance des fichiers pour l'indexation automatique.

Ce module utilise Watchdog pour observer les répertoires contenant des documents à indexer
(docx, données web, versions de plans). Lorsqu’un changement est détecté, le pipeline
d’indexation complet est automatiquement relancé pour mettre à jour les bases vectorielles.

Fonctions :
- start_scheduler : Démarre la surveillance continue via Watchdog.

Classes :
- IndexingEventHandler : Handler personnalisé déclenchant l’indexation à chaque événement.
"""



from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading
import schedule
import time
from datetime import datetime
import os
from src.func.run_full_indexing_pipeline import run_full_indexing_pipeline
from config.config import INPUT_DOCX, WEB_SITES_HEALTH_DOC_BASE, WEB_SITES_MODULE_PATH

# Répertoires à surveiller
WATCHED_DIRECTORIES = [
    INPUT_DOCX,
    WEB_SITES_HEALTH_DOC_BASE
]


class IndexingEventHandler(FileSystemEventHandler):
    """
    Handler personnalisé déclenchant l’indexation lors de changements dans les fichiers.

    Cette classe hérite de FileSystemEventHandler et surcharge la méthode on_any_event
    pour appeler `run_full_indexing_pipeline()` dès qu’un fichier est ajouté, modifié
    ou supprimé dans l’un des répertoires surveillés.
    """

    def on_any_event(self, event):
        if event.is_directory:
            return
        print(f"\n📂 Changement détecté : {event.src_path} ({event.event_type})")
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 🔄 Lancement de l’indexation suite à un changement...\n")
        run_full_indexing_pipeline()



def start_scheduler():
    """
    Démarre la surveillance des fichiers via Watchdog.

    Si les bases ChromaDB n’existent pas ou sont vides, lance une indexation initiale.
    Ensuite, observe les répertoires définis et relance automatiquement l’indexation
    si un fichier est ajouté, modifié ou supprimé.

    Cette fonction est appelée au démarrage de l’application dans un thread dédié.
    """

    from config.config import CHROMA_GLOBAL_DIR

    # Étape 1 : Vérifier si une indexation initiale est nécessaire
    if not os.path.exists(CHROMA_GLOBAL_DIR) or not os.listdir(CHROMA_GLOBAL_DIR):
        print(f"\n🚀 Initialisation des bases ChromaDB (premier démarrage)...")
        run_full_indexing_pipeline()
    else:
        print(f"\n📚 Base ChromaDB déjà existante. Surveillance uniquement.")

    # Étape 2 : Activer la surveillance des fichiers
    print("👁️ Démarrage de la surveillance des fichiers (Watchdog)...")
    event_handler = IndexingEventHandler()
    observer = Observer()

    for directory in WATCHED_DIRECTORIES:
        observer.schedule(event_handler, path=directory, recursive=True)
        print(f"📁 Surveillance activée sur : {directory}")

    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()




