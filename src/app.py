"""
Module principal de l'application OBY-IA.

Ce module initialise l'application Dash, configure la navigation entre les pages,
et vérifie la disponibilité de la base de données des constantes médicales.

Fonctionnalités principales :
- Chargement des variables d'environnement depuis un fichier `.env` à la racine.
- Vérification et génération automatique de la base SQLite (`constantes_sante.db`).
- Initialisation de l'application Dash avec gestion des pages (`use_pages=True`).
- Mise en place d'une barre de navigation et d'un conteneur de pages dynamiques.
- Démarrage d'un planificateur de tâches (scheduler) dans un thread dédié au lancement.

Ce fichier doit être exécuté pour lancer le serveur Dash : `python -m src.app`
"""


import os
import time
import sqlite3
import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
from dotenv import load_dotenv
from pathlib import Path

# Charger .env depuis la racine du projet
env_path = Path(__file__).resolve().parents[1] / '.env'
load_dotenv(dotenv_path=env_path)

# Base de données
db_path = Path(__file__).resolve().parents[1] / "constantes_sante.db"


def check_and_generate_database():
    """Vérifie la base et génère si besoin."""
    if not db_path.exists():
        print("⚙️ Base manquante, création...")
        from src.data.constant_generator import generate_database

        generate_database(db_path)
    else:
        from src.data.constant_generator import generate_database
        generate_database(db_path)
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tension'")
        table_exists = cur.fetchone()

        if not table_exists:
            print("⚙️ Table tension manquante, régénération de la base...")
            from src.data.constant_generator import generate_database
            generate_database(db_path)
        else:
            cur.execute("SELECT COUNT(*) FROM tension")
            count = cur.fetchone()[0]
            if count == 0:
                print("⚙️ Table tension vide, régénération de la base...")
                from src.data.constant_generator import generate_database
                generate_database(db_path)
            else:
                print("✅ Base de données prête avec des données.")
        conn.close()

# Toujours vérifier la base au démarrage
check_and_generate_database()

# Dash App
from config.config import ASSETS_PATH, PAGES_DIR


app = dash.Dash(
    __name__,
    use_pages=True,
    pages_folder=str(PAGES_DIR),
    suppress_callback_exceptions=True,
    external_stylesheets=[
        dbc.themes.LUX,
        dbc.icons.FONT_AWESOME,
    ],
    assets_folder=str(ASSETS_PATH),
)


app.layout = html.Div([
    dbc.NavbarSimple(
        brand="OBY IA",
        brand_href="/",
        color="primary",
        dark=True,
        children=[
            dbc.NavItem(dcc.Link("Accueil", href="/", className="nav-link")),
            dbc.NavItem(dcc.Link("Chatbot", href="/chatbot", className="nav-link")),
        ],
        className="mb-4"
    ),
    dash.page_container
])

print("✅Pages enregistrées :", dash.page_registry.keys())

from dash.development.base_component import Component

def collect_ids(component):
    """Récupère récursivement tous les IDs d'un layout Dash."""
    ids = []
    if isinstance(component, Component):
        if hasattr(component, 'id') and component.id is not None:
            ids.append(component.id)
        if hasattr(component, 'children') and component.children:
            children = component.children
            if isinstance(children, list):
                for child in children:
                    ids.extend(collect_ids(child))
            else:
                ids.extend(collect_ids(children))
    return ids

# Check -> Lister tous les IDs dans le layout global
ids_in_layout = collect_ids(app.layout)
print("ID présents dans le layout global :", ids_in_layout)




if __name__ == "__main__":
    import threading
    from src.utils.scheduler import start_scheduler

    # Lancer le scheduler dans un thread à part
    scheduler_thread = threading.Thread(target=start_scheduler, daemon=True)
    scheduler_thread.start()

    time.sleep(1)

    port = int(os.environ.get("PORT", 8050))
    debug_flag = os.environ.get("APP_DEBUG", "0") == "1"
    # Si APP_DEBUG=1 => debug/reloader ON, sinon OFF
    app.run(
        host="0.0.0.0",
        port=port,
        debug=debug_flag,
        use_reloader=debug_flag
    )
