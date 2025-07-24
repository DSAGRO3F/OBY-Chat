"""
Module `home.py` – Page d'accueil, authentification et interface d'administration de OBY-IA.

Ce module Dash gère les fonctionnalités suivantes :
1. **Authentification utilisateur** :
   - Vérification des identifiants via une base interne (`USER_DATABASE`).
   - Création et stockage de la session via `dcc.Store` et `session_manager_instance`.
   - Affichage conditionnel de l'interface selon le rôle (utilisateur ou admin).

2. **Déconnexion et gestion de session** :
   - Suppression propre de la session en cours.
   - Réinitialisation du mappage d’anonymisation à la connexion.

3. **Contrôles d'administration (admin uniquement)** :
   - Réinitialisation des bases : ChromaDB, fichiers JSON extraits du web, index de suivi.
   - Interface de déclenchement réservée aux administrateurs.

4. **Accès à la documentation du projet** :
   - Vérification en temps réel de la disponibilité du serveur MkDocs (`http://127.0.0.1:8000`).
   - Redirection automatique vers la documentation si disponible.

5. **Visualisation des statistiques d’indexation ChromaDB** :
   - Affichage du nombre de fichiers indexés (DOCX, web), de chunks, et de fichiers JSON associés.
   - Rafraîchissement manuel ou automatique de ces statistiques à l’ouverture.

Ce module constitue la page d’accueil et d’entrée principale de l’application OBY-IA.
"""


import dash
from dash import html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc
from src.llm_user_session.session_manager_instance import session_manager_instance
from config.config import USER_DATABASE
from src.func.get_chroma_stats import get_chroma_index_stats
from src.utils.vector_db_utils import is_chroma_index_ready

dash.register_page(__name__, path="/")

print(f"📄 Chargement du module : {__name__}")




layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H2("AUTHENTIFICATION", className="text-center mb-4"),
            html.Hr(),
            html.P("Pour continuer, veuillez vous authentifier."),
            html.Label([
                html.Img(src="/assets/icons/user.png", className="icon-inline"),
                "Identifiant utilisateur :"
            ], className="label-with-icon"),

            dbc.Input(id="user_id_input", type="text", placeholder="Entrez votre identifiant", className="mb-2"),

            html.Label([
                html.Img(src="/assets/icons/lock.png", className="icon-inline"),
                "Mot de passe :"
            ], className="label-with-icon"),

            dbc.Input(id="password_input", type="password", placeholder="Mot de passe", className="mb-2"),
            dbc.Button("Valider", id="login_button", color="primary", className="mb-2 w-100"),
            html.Div(id="auth_feedback", style={"color": "red", "marginBottom": "10px"}),

            html.Hr(),

            html.Div(id="admin-controls", style={"marginTop": "20px"}),

            html.Div(id="reset-feedback", style={"marginTop": "10px", "color": "green"}),

        ], width=3),

        dbc.Col([
            html.H2("Bienvenue sur OBY-IA", className="text-center mb-4"),
            dbc.Row([
                dbc.Button("📘 Accéder à la documentation", id="open-docs-btn", color="info", className="me-2"),
                html.Span(id="doc-access-message", style={"marginLeft": "10px"}),

                html.Hr(),

                html.Div(id="chroma-stats-box", className="mb-3"),
                html.Button("🔄 Rafraîchir les statistiques", id="refresh-stats-btn", n_clicks=0, className="custom-reset-button"),
            ]),
            dcc.Interval(id="check-doc-status", interval=5000, n_intervals=0),
            dcc.Location(id="redirect-docs", refresh=True),
        ], width=9)
    ]),
    dcc.Store(id="session_data", storage_type="session")
], fluid=True)


# ===============================================#
# Callback de gestion de l’authentification
# ===============================================#
@dash.callback(
    Output("auth_feedback", "children"),
    Output("session_data", "data"),
    Input("login_button", "n_clicks"),
    State("user_id_input", "value"),
    State("password_input", "value"),
    prevent_initial_call=True
)
def authenticate_user(n_clicks, user_id_input, password_input):
    """
    Authentifie un utilisateur à partir de ses identifiants.

    Vérifie si l'identifiant et le mot de passe fournis correspondent à une
    entrée valide dans la base des utilisateurs. Si oui, crée une session et
    retourne les données associées.

    Args:
        n_clicks (int) : Nombre de clics sur le bouton "Valider".
        user_id_input (str) : Identifiant saisi par l'utilisateur.
        password_input (str) : Mot de passe saisi par l'utilisateur.

    Returns:
        tuple :
            - Message de retour (str),
            - Données de session utilisateur (dict) ou dash.no_update.
    """

    if user_id_input and password_input:
        if user_id_input in USER_DATABASE and USER_DATABASE[user_id_input] == password_input:
            session_id = user_id_input  # Pour l'instant : user_id == session_id
            session_manager_instance.create_session(user_id_input, session_id)
            session_manager_instance.reset_anonymization_mapping(session_id)  # 🆕 Reset mapping au début de session
            print(f"✅ Session créée pour {user_id_input} - ID: {session_id}")
            session_data = {
                "user_id": user_id_input,
                "session_id": session_id
            }
            return "✅ Authentification réussie.", session_data
        else:
            print("❌ Identifiants invalides")
            return "❌ Identifiants invalides. Veuillez réessayer.", dash.no_update
    return "❌ Veuillez remplir tous les champs.", dash.no_update


# ===============================================#
# Callback pour la déconnexion
# ===============================================#
@dash.callback(
    Output("auth_feedback", "children", allow_duplicate=True),
    Output("session_data", "data", allow_duplicate=True),
    Input("logout_button", "n_clicks"),
    State("session_data", "data"),
    prevent_initial_call=True
)
def logout_user(n_clicks, session_data):
    """
    Met fin à la session utilisateur en cours.

    Supprime la session active à partir des informations enregistrées,
    et réinitialise les données côté client.

    Args:
        n_clicks (int) : Nombre de clics sur le bouton "Déconnexion".
        session_data (dict) : Données de session utilisateur en cours.

    Returns:
        tuple :
            - Message de confirmation (str),
            - None pour réinitialiser `session_data`.
    """

    if session_data:
        user_id = session_data.get("user_id")
        session_id = session_data.get("session_id")
        session_manager_instance.end_session(user_id, session_id)
        print(f"🔒 Session terminée pour {user_id} - ID: {session_id}")
        return "✅ Déconnexion réussie.", None
    return "❌ Aucune session active.", None




from src.utils.reset_data import reset_all_data
# ===============================================#
# script dédié pour réinitialiser :
# ===============================================#
# ✅ La base vectorielle ChromaDB (par exemple base_web, base_docx)
# ✅ Le répertoire JSON contenant les pages extraites (to_json_web_sites/)
# ✅ Le fichier de suivi indexed_files.json
# → qui empêche la réindexation si les fichiers n'ont pas changé
@callback(
    Output("reset-feedback", "children"),
    Input("reset-button", "n_clicks"),
    prevent_initial_call=True
)
def trigger_reset(n_clicks):
    """
    Réinitialise toutes les bases et fichiers d'indexation de l'application.

    Fonction réservée à l'administrateur. Elle supprime les données de
    ChromaDB, les fichiers JSON extraits depuis le web, et le fichier
    `indexed_files.json` utilisé pour suivre les indexations.

    Args:
        n_clicks (int) : Nombre de clics sur le bouton "Réinitialiser les bases".

    Returns:
        str : Message de confirmation après la réinitialisation.
    """

    reset_all_data()
    return "✅ Réinitialisation effectuée."



# ===============================================#
# Sécuriser l'accès au bouton de réinitialisation.
# ===============================================#
# 1. Limiter l’accès au bouton dans le layout :
# 2. Afficher le bouton "Réinitialiser les bases" uniquement si l’utilisateur est admin.
# → Vérifier dans le callback que seul "admin" peut exécuter l’action de reset (double sécurité côté backend).
# → Reposer sur session_manager.py pour lire la session actuelle.

@callback(
    Output("admin-controls", "children"),
    Input("session_data", "data")
)
def display_admin_controls(session_data):
    """
    Affiche les contrôles d'administration si l'utilisateur est un admin.

    Cette fonction affiche dynamiquement le bouton "Réinitialiser les bases"
    uniquement pour les utilisateurs ayant l'identifiant `admin`.

    Args:
        session_data (dict) : Données de session contenant `user_id`.

    Returns:
        list : Composants Dash (bouton de réinitialisation) ou liste vide.
    """

    if session_data and session_data.get("user_id") == "admin":
        return [
            html.Hr(),
            html.Button(
                "Réinitialiser les bases",
                id="reset-button",
                className="custom-reset-button",
                n_clicks=0
            ),
            html.Div(id="reset-feedback", style={"marginTop": "10px", "color": "green"})
        ]
    return []


# ===============================================#
# Gestion de l'accès à la documentation du projet.
# 1. Callback pour vérifier si "mkdocs serve" est actif
# ===============================================#
import requests
from dash import ctx, no_update

@callback(
    Output("doc-access-message", "children"),
    Input("check-doc-status", "n_intervals"),
)
def check_mkdocs_status(_):
    """
    Vérifie si le site de documentation MkDocs est disponible localement.
    Affiche un message en vert (accessible) ou rouge (inaccessible).
    """
    try:
        response = requests.get("http://127.0.0.1:8000", timeout=0.5)
        if response.status_code == 200:
            return html.Span("✅ Documentation disponible", style={"color": "green"})
    except requests.RequestException:
        pass
    return html.Span("❌ Documentation indisponible – lancez `mkdocs serve`", style={"color": "red"})


# 2. Callback pour déclencher l’ouverture dans un nouvel onglet
@callback(
    Output("redirect-docs", "href"),
    Input("open-docs-btn", "n_clicks"),
    prevent_initial_call=True
)
def open_docs_site(n_clicks):
    """
    Redirige vers le site local de documentation s'il est accessible.
    """
    try:
        response = requests.get("http://127.0.0.1:8000", timeout=0.5)
        if response.status_code == 200:
            return "http://127.0.0.1:8000"
    except requests.RequestException:
        pass
    return no_update


# ===============================================#
# Statistiques ChromaDB dynamiques
# ===============================================#
# Afficher dans home.py :
# - Nombre de fichiers DOCX indexés
# - Nombre de pages web indexées
# - Nombre total de chunks indexés (par source)
# - Composant Dash rafraîchi à l’ouverture de la page (ou manuellement via bouton)

@dash.callback(
    Output("chroma-stats-box", "children"),
    Input("refresh-stats-btn", "n_clicks")
)
def update_chroma_stats(_):
    stats = get_chroma_index_stats()
    return html.Div([
        html.Div([
            html.Img(src="/assets/icons/statistics.png?v=1", className="icon-inline"),
            html.H4("Statistiques de l'indexation ChromaDB", className="d-inline-block ms-2")
        ], className="d-flex align-items-center mb-3"),

        html.Ul([
            html.Li([
                html.Img(src="/assets/icons/message.png?v=1", className="icon-inline me-2"),
                f"Fichiers DOCX indexés : {stats['docx_files']} fichiers – {stats['docx_chunks']} sections"
            ]),
            html.Li([
                html.Img(src="/assets/icons/robot.png?v=1", className="icon-inline me-2"),
                f"Pages web indexées : {stats['web_files']} URLs – {stats['web_chunks']} sections"
            ]),
            html.Li([
                html.Img(src="/assets/icons/table.png?v=1", className="icon-inline me-2"),
                f"Fichiers JSON issus de DOCX : {stats['docx_json_files']}"
            ]),
            html.Li([
                html.Img(src="/assets/icons/table.png?v=1", className="icon-inline me-2"),
                f"Fichiers JSON issus du web : {stats['web_json_files']}"
            ]),
        ])
    ])




