"""
Module `chatbot_ui.py` – Interface conversationnelle de l'application OBY-IA (page `/chatbot`)

Ce module Dash définit la page chatbot de OBY-IA, qui permet aux professionnels de santé
d’interagir avec un agent intelligent pour obtenir :

1. **Analyse des constantes médicales du patient** :
   - Extraction et affichage des constantes sous forme de graphiques et tableaux.
   - Détection automatique des anomalies.
   - Sérialisation et désérialisation des graphiques pour l’exportation.

2. **Interaction en langage naturel avec le LLM** :
   - Détection de l’intention utilisateur (consultation, génération de PPA, recommandations).
   - Extraction du nom du patient à partir de la requête.
   - Génération de contenu médical structuré via des prompts spécialisés.
   - Historisation des messages utilisateur/LLM et affichage dynamique.

3. **Export des résultats** :
   - Génération d’un fichier Markdown résumant la session (réponses LLM + graphiques).

4. **Contrôle de disponibilité de l’index ChromaDB** :
   - Affichage d’une bannière d’attente tant que l’index n’est pas prêt.
   - Activation différée des composants de saisie utilisateur.

Composants techniques :
- Utilise `session_manager_instance` pour la gestion d’état (session, mapping, historique).
- Repose sur les modules fonctionnels : `extract_user_intent`, `generate_ppa_from_poa`,
  `generate_structured_medical_plan`, `get_patient_constants_graphs`, `export_chat_response`, etc.

Cette page est au cœur de l’expérience utilisateur de OBY-IA, combinant interface conviviale
et logique métier intelligente.
"""





import dash
from dash import dcc, html, callback, ctx
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import markdown
from dash import MATCH



from src.llm_user_session.session_manager_instance import session_manager_instance
from src.func.extract_patient_name import extract_patient_name_llm
from src.func.generate_ppa_from_poa import process_ppa_request
from src.func.generate_structured_medical_plan import generate_structured_medical_plan
from src.func.llm_prompts import system_prompt, system_prompt_medical_plan
from src.func.extract_user_intent import detect_user_intent
from src.func.get_patient_constants_graphs import process_patient_request_with_constants
from src.func.get_patient_constants_graphs import analyze_constants
from src.func.extract_patient_name import extract_patient_name_llm
from src.utils.export_chat_response import export_llm_responses
from src.func.serialize_figs import serialize_figs, deserialize_figs
from src.utils.vector_db_utils import is_chroma_index_ready

from config.config import USER_DATABASE


dash.register_page(__name__, path="/chatbot")


# Layout
layout = dbc.Container([

    dcc.Store(id="session_data", storage_type="session"),
    dcc.Store(id="current_patient"),
    dcc.Store(id="constants_graphs_store", data=None),
    dcc.Store(id="chat_history", data=[], storage_type="session"),

dcc.Interval(id="index_check_interval", interval=2000, n_intervals=0),

html.Div(
    id="index_banner_container",
    children=html.Span(
        id="index_banner_text",
        children=[
            html.Span("●", id="index_status_dot", style={"marginRight": "5px"}),
            "Vérification de l'état..."
        ],
        style={"fontWeight": "bold", "fontSize": "14px"}
    ),
    style={
        "position": "absolute",
        "top": "10px",
        "right": "20px",
        "zIndex": "1000",
        "padding": "6px 12px",
        "borderRadius": "12px",
        "backgroundColor": "#f8f9fa",
        "boxShadow": "0 1px 3px rgba(0,0,0,0.2)",
    }
),
    dbc.Row([
        # Colonne gauche : Chat principal
        dbc.Col([
            html.H2("OBY - CHAT", className="text-center mb-4"),

            html.Div([
                html.P("Bonjour, comment puis-je vous aider ?", style={"fontStyle": "italic", "color": "#555"}),

                dbc.Input(id="user_input", placeholder="Posez votre question...", type="text", className="mb-2", disabled=True),

                dbc.Button([
                    html.Img(src="/assets/icons/message.png", className="icon-inline"),
                    "Envoyer"
                ], id="send_button", color="success", className="me-2", disabled=True),

                dbc.Button([
                    html.Img(src="/assets/icons/signout.png", className="icon-inline"),
                    "Déconnexion"
                ], id="logout-btn", color="danger", className="me-2", disabled=True),

                dcc.Loading(
                    id="loading_spinner",
                    type="circle",
                    children=[
                        html.Div(id="chat_history_display", className="chat-history")
                    ]
                ),
                # → Ajout : Zone export
                html.Div([
                    html.Label("Exporter l'historique du LLM :", style={"marginTop": "10px"}),
                    dbc.Button(
                        "💾 Exporter en Markdown",
                        id="export_button",
                        color="info",
                        className="mt-2",
                        style={"width": "100%"}
                    ),
                    html.Div(id="export_feedback", className="mt-2", style={"color": "green"})
                ]),
            ],
                style={
                    "border": "1px solid #ccc",
                    "borderRadius": "10px",
                    "padding": "15px",
                    "boxShadow": "2px 2px 10px rgba(0,0,0,0.1)"
                })
        ], width=7),

        # Colonne droite : Données médicales
        dbc.Col([
            html.Div([
                html.Img(src="/assets/icons/medical_aid.png", className="icon-inline me-2"),
                html.H4("-- SUIVI MEDICAL --", className="mb-0")
            ], className="d-flex align-items-center justify-content-center mb-3"),

            dbc.Accordion([
                dbc.AccordionItem(
                    children=html.Div(id="constants_graphs"),
                    title=html.Div([
                        html.Img(src="/assets/icons/arrow_green.png", className="icon-inline me-2"),
                        "GRAPHIQUE DES CONSTANTES"
                    ])
                ),
                dbc.AccordionItem(
                    children=html.Div(id="constants_table"),
                    title=html.Div([
                        html.Img(src="/assets/icons/arrow_green.png", className="icon-inline me-2"),
                        "TABLEAU DES CONSTANTES"
                    ])
                ),
                dbc.AccordionItem(
                    children=html.Div(id="anomalies_summary"),
                    title=html.Div([
                        html.Img(src="/assets/icons/arrow_green.png", className="icon-inline me-2"),
                        "ANOMALIES POTENTIELLES DETECTEES"
                    ])
                )
            ], start_collapsed=True)
        ], width=5)
    ]),
],
fluid=True)

@callback(
    Output("chat_history", "data"),
    Output("constants_graphs", "children"),
    Output("constants_table", "children"),
    Output("anomalies_summary", "children"),
    Output("current_patient", "data"),
    Output("constants_graphs_store", "data"),
    Output("chat_history_display", "children"),


    Input("send_button", "n_clicks"),
    State("user_input", "value"),


    Input("logout_button", "n_clicks"),
    State("chat_history", "data"),

    State("session_data", "data"),
    State("current_patient", "data"),
    prevent_initial_call=True
)
def handle_user_input_or_logout(send_clicks, user_input, logout_clicks, chat_history, session_data, current_patient):
    """
    Callback principal de gestion des interactions utilisateur.

    Cette fonction gère :
    - la déconnexion de l’utilisateur,
    - la détection de l’intention (consultation de constantes, génération de PPA ou plan de soins),
    - l’appel au modèle LLM pour produire une réponse appropriée,
    - l’affichage et la mise à jour de l’historique et des données patient.

    Args:
        send_clicks (int) : Nombre de clics sur le bouton "Envoyer".
        user_input (str) : Message saisi par l’utilisateur.
        logout_clicks (int) : Nombre de clics sur le bouton "Déconnexion".
        chat_history (list) : Liste des messages actuellement affichés.
        session_data (dict) : Données de session utilisateur (user_id, session_id).
        current_patient (str) : Nom du patient actuellement sélectionné.

    Returns:
        tuple : Mise à jour de :
            - l'historique du chat,
            - les graphiques et tableaux des constantes,
            - le résumé des anomalies,
            - le nom du patient actif,
            - les figures sérialisées,
            - l’affichage du chat.
    """

    triggered = ctx.triggered_id
    print(f"📌 Callback triggered by: {triggered}")

    # --- Gestion de la déconnexion ---
    if triggered == "logout_button":
        print("🔴 Déconnexion demandée")
        if session_data:
            session_manager_instance.end_session(session_data["user_id"], session_data["session_id"])
        return "", "", "", "", None


    # --- Vérification session ---
    if not session_data or not isinstance(session_data, dict):
        # ⚠️ Pas de session active
        return "❌ Session non authentifiée. Veuillez vous reconnecter.", "", "", "", dash.no_update

    print("🚀 chatbot_ui.py chargé !")

    # --- Initialisation des blocs d'affichage et variables de retour ---
    figs_list = []
    table_html = ""
    anomaly_block = ""
    user_id = session_data.get("user_id")
    session_id = session_data.get("session_id")
    serialized_figs = None  # Valeur par défaut
    bot_response = []  # Liste pour pouvoir itérer même si vide
    bot_msg = None




        # --- Initialisation demande ---
    bot_response = "🤖 Je traite votre demande..."


    # --- Extraction de l’intention ---
    print(f'⚠️démarrage détection intentions-chatbot-ui.py...')
    intent_dict = detect_user_intent(user_input)

    nom = extract_patient_name_llm(user_input)

    intent = intent_dict.get("intent", "unknown")

    ppa_requested = intent == "generate_ppa"
    constantes_requested = intent == "get_constants"
    recommandations_requested = intent == "generate_recommendations"

    print(f"🎯 Intentions détectées : "
          f"recommandations: {recommandations_requested},"
          f"constantes={constantes_requested}, "
          f"ppa={ppa_requested}, "
          f"nom patient={nom}")
    if ppa_requested or constantes_requested or recommandations_requested:
        print(f'✅détection intention réussie')


    # --- Réinitialisation si changement de patient ---
    if nom and (ppa_requested or constantes_requested or recommandations_requested):
        if nom and nom != current_patient:
            print(f"🆕 Changement de patient détecté : {current_patient} ➡️ {nom}")
            chat_history = []
            figs_list = []
            table_html = ""
            anomaly_block = ""
            current_patient = nom
            # Remet à zéro le mapping d’anonymisation
            session_manager_instance.reset_anonymization_mapping(user_id)
            session_manager_instance.set_current_patient(session_id, nom)

        else:
            print(f"✅ Patient conservé : {current_patient}")



    # --- Traitement des constantes ---
    if constantes_requested:
        try:
            print("📊 Appel à process_patient_request_with_constants()")
            bot_response, figs_list, table_html, anomaly_block = process_patient_request_with_constants(nom)
            serialized_figs = serialize_figs(figs_list)
        except Exception as e:
            print(f"❌ Erreur dans process_patient_request_with_constants : {e}")
            bot_response = "Une erreur est survenue pendant le traitement des constantes."
            figs_list, table_html, anomaly_block = [], "", ""


    # --- Traitement demande PPA ---
    elif ppa_requested:
        print("📄 Appel à process_ppa_request() pour le PPA")
        try:
            bot_response, dict_mapping= process_ppa_request(user_input, system_prompt)

            # Enregistrer le mapping renvoyé par la fonction dans la session
            # Le récupérer proprement via session_manager.get_anonymization_mapping()
            session_manager_instance.set_anonymization_mapping(session_id, dict_mapping)

            # Quand le LLM a donné une réponse (bot_response), ajout de la réponse dans la session
            session_manager_instance.append_llm_response(session_id, bot_response)

            figs_list, table_html, anomaly_block = [], "", ""

        except Exception as e:
            print(f"❌ Erreur dans process_ppa_request : {e}")
            bot_response = "Une erreur est survenue pendant la génération du PPA."
            figs_list, table_html, anomaly_block = "", "", ""



    # --- Traitement demande plan de soins ---
    elif recommandations_requested:
        print("📄 Appel à generate_structured_medical_plan() pour plan de soins")
        try:
            bot_response, dict_mapping= generate_structured_medical_plan(user_input, system_prompt_medical_plan)

            # Enregistrer le mapping renvoyé par la fonction dans la session
            # Le récupérer proprement via session_manager.get_anonymization_mapping()
            session_manager_instance.set_anonymization_mapping(session_id, dict_mapping)

            # Quand le LLM a donné une réponse (bot_response), ajout de la réponse dans la session
            session_manager_instance.append_llm_response(session_id, bot_response)

            figs_list, table_html, anomaly_block = [], "", ""

        except Exception as e:
            print(f"❌ Erreur dans generate_structured_medical_plan : {e}")
            bot_response = "Une erreur est survenue pendant l'extraction des recommandations de soins."
            figs_list, table_html, anomaly_block = [], "", ""


    # Test
    if not any([ppa_requested, constantes_requested, recommandations_requested]):
        print("❗ Aucune intention détectée dans la requête utilisateur.")


    # --- Correspondance avec Output() du layout ---
    constants_graphs = [dcc.Graph(figure=fig) for fig in figs_list]
    constants_table = None if not table_html else html.Div(table_html)
    anomaly_graphs = None if not anomaly_block else html.Div(anomaly_block)

    # 💡 Ajout de la requête utilisateur
    user_input_str = str(user_input).strip() if user_input else ""
    print(f"user_input brut: {user_input}")
    print(f"user_input_str après nettoyage: '{user_input_str}'")

    # Si l'input est vide, on bloque l'exécution
    if not user_input_str:
        print("⚠️ Aucun texte saisi, arrêt du traitement.")
        return (
            dash.no_update, constants_graphs, constants_table, anomaly_graphs,
            current_patient, serialized_figs
        )

    user_msg = html.Div(f"👤 {user_input_str}", className="user-message")
    chat_history.append(user_msg)

    # 💡 Cas PPA / constantes / web
    if bot_response:
        bot_msg = html.Div(
            dcc.Markdown(str(bot_response), dangerously_allow_html=False),
            className="bot-response"
        )
        chat_history.append(bot_msg)

    chat_history_display = chat_history

    # 💡 Retour de l'ensemble : un seul historique pour affichage + store
    return chat_history, constants_graphs, constants_table, anomaly_graphs, current_patient, serialized_figs, chat_history_display




@callback(
    Output("export_feedback", "children"),
    Input("export_button", "n_clicks"),
    State("session_data", "data"),
    State("current_patient", "data"),
    State("constants_graphs_store", "data"),
    prevent_initial_call=True
)
def export_chat_response(n_clicks, session_data, current_patient, serialized_figs):
    """
    Callback de gestion de l’export de l’historique du LLM au format Markdown.

    Cette fonction est appelée lorsqu’un utilisateur clique sur le bouton
    "Exporter". Elle désérialise les graphiques, récupère les réponses enregistrées
    dans la session, puis appelle la fonction `export_llm_responses`.

    Args:
        n_clicks (int) : Nombre de clics sur le bouton d’export.
        session_data (dict) : Données de session (user_id, session_id).
        current_patient (str) : Nom du patient actif.
        serialized_figs (list) : Graphiques des constantes sérialisés.

    Returns:
        str : Message de confirmation ou d’erreur selon le succès de l’export.
    """

    if not session_data:
        return "❌ Session non authentifiée. Veuillez vous reconnecter."

    session_id = session_data["session_id"]

    try:
        constants_graphs = deserialize_figs(serialized_figs)
        file_path = export_llm_responses(
            session_manager_instance,
            session_id,
            current_patient,
            constants_graphs
        )
        return f"✅ Export Markdown enregistré : {file_path}"
    except Exception as e:
        return f"❌ Erreur lors de l’export : {e}"


@callback(Output("index_banner_text", "children"),
    Output("index_banner_container", "style"),
    Output("user_input", "disabled"),
    Output("send_button", "disabled"),
    Input("index_check_interval", "n_intervals"),
)
def check_index_status(n):
    """
        Met à jour dynamiquement l'indicateur visuel d'indexation ChromaDB.

        Ce callback est déclenché périodiquement via un composant dcc.Interval pour vérifier
        si les bases vectorielles ChromaDB sont prêtes à être interrogées.

        Lorsque l'indexation est encore en cours :
            - Affiche un point orange accompagné du texte "En cours d'indexation".
            - Désactive les champs d'entrée utilisateur et le bouton d'envoi.

        Lorsque l'indexation est terminée :
            - Affiche un point vert avec le texte "Prêt".
            - Active les champs d'entrée utilisateur et le bouton d'envoi.

        Args:
            n (int): Nombre d'intervalles écoulés depuis le démarrage de l'application.

        Returns:
            tuple:
                - children (list): Contenu HTML du texte de la bannière.
                - style (dict): Style CSS du point d'état (couleur).
                - user_input.disabled (bool): True si l'entrée doit être désactivée.
                - send_button.disabled (bool): True si le bouton doit être désactivé.
        """

    if is_chroma_index_ready():
        return (
            [html.Span("●", id="index_status_dot", style={"marginRight": "5px"}), "Prêt"],
            {"color": "green", "marginRight": "5px"},
            False,
            False
        )
    else:
        return (
            [html.Span("●", id="index_status_dot", style={"marginRight": "5px"}), "En cours d'indexation"],
            {"color": "orange", "marginRight": "5px"},
            True,
            True
        )
