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
import time
from datetime import datetime
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
        print(f"\n▶️ Changement détecté : {event.src_path} ({event.event_type})")
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 🔄 Lancement de l’indexation suite à un changement...\n")
        run_full_indexing_pipeline()


def start_scheduler():
    from config.config import CHROMA_GLOBAL_DIR
    import os, sys

    # Vérifier si une indexation initiale est nécessaire
    try:
        # Cas 1 : le dossier n'existe pas -> indexation initiale
        if not os.path.exists(CHROMA_GLOBAL_DIR):
            print(f"\n🟢 Initialisation des bases ChromaDB (premier démarrage) : {CHROMA_GLOBAL_DIR} n'existe pas.")
            run_full_indexing_pipeline()

        else:
            # Cas 2 : le dossier existe -> vérification vide ou non
            try:
                is_empty = (len(os.listdir(CHROMA_GLOBAL_DIR)) == 0)
            except PermissionError as e:
                # Si droits insuffisants pour lister le contenu
                print(
                    "\n⛔ Droits insuffisants sur le répertoire ChromaDB.\n"
                    f"   Répertoire : {CHROMA_GLOBAL_DIR}\n"
                    f"   Détail     : {e}\n"
                    "   Check :\n"
                    "   - Vérifiez que l'utilisateur courant a les droits de lecture et d'exécution sur ce dossier.\n",
                    file=sys.stderr
                )
                # Arrêt scheduler pour éviter état incohérent
                return

            if is_empty:
                # Lancement run_full_indexing_pipeline() pour indexation initiale
                print(f"\n🟢 Initialisation des bases ChromaDB (répertoire vide) : {CHROMA_GLOBAL_DIR}")
                run_full_indexing_pipeline()
            else:
                # Si base non vide pas d'exécution d'indexation
                print(f"\n✅ Base ChromaDB déjà existante. Surveillance uniquement ({CHROMA_GLOBAL_DIR}).")

    except Exception as e:
        # Si autres erreurs inattendues d'accès
        print(
            "\n⛔ Erreur lors de la vérification initiale de ChromaDB.\n"
            f"   Répertoire : {CHROMA_GLOBAL_DIR}\n"
            f"   Détail     : {e}\n",
            file=sys.stderr
        )
        return

    # Activer la surveillance des fichiers
    print("🟢 Démarrage de la surveillance des fichiers (Watchdog)...")
    event_handler = IndexingEventHandler()
    observer = Observer()

    for directory in WATCHED_DIRECTORIES:
        os.makedirs(directory, exist_ok=True)
        observer.schedule(event_handler, path=directory, recursive=True)
        print(f"✅ Surveillance activée sur : {directory}")

    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

