"""
Module `chatbot_ui.py` – Interface conversationnelle de l'application OBY-IA (page `/chatbot`)

Ce module définit l'interface utilisateur du chatbot OBY-IA dans l'application Dash.

Il contient :
- Le layout complet de la page chatbot avec champ de saisie, historique des échanges,
  boutons d'envoi et de déconnexion, ainsi que les composants pour l'affichage des constantes.
- Le callback principal `handle_user_input_or_logout()` qui gère les requêtes utilisateur,
  la détection d’intention, la confirmation, l’affichage dynamique, et les réponses du LLM.
- L’intégration avec la gestion de session utilisateur et la logique métier de génération de plans de soins,
  d'extraction de constantes médicales ou de recommandations.

Ce module dépend de plusieurs composants de l'application OBY-IA :
- session_manager_instance : pour suivre l’état de la session utilisateur
- handle_initial_request() et handle_confirmation_response() : logique de traitement conversationnel
- get_constants(), generate_structured_medical_plan() : fonctions de génération de contenu
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

                dbc.Input(id="user_input", placeholder="Posez votre question...", type="text", className="mb-2", disabled=False),

                dbc.Button([
                    html.Img(src="/assets/icons/message.png", className="icon-inline"),
                    "Envoyer"
                ], id="send_button", color="success", className="me-2", disabled=False, n_clicks=0),

                dbc.Button([
                    html.Img(src="/assets/icons/signout.png", className="icon-inline"),
                    "Déconnexion"
                ], id="logout_button", color="danger", className="me-2", disabled=False, n_clicks=0),

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

from dash.development.base_component import Component

def collect_ids(component):
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

ids_in_chatbot_layout = collect_ids(layout)
print("🧩 ID présents dans le layout chatbot :", ids_in_chatbot_layout)


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
    State("chat_history", "data"),
    State("session_data", "data"),
    State("current_patient", "data"),
    prevent_initial_call=True
)
def handle_user_input_or_logout(send_clicks, user_input, chat_history, session_data, current_patient):

    """
    Gère la saisie utilisateur et les réponses du chatbot dans OBY-IA.

    Ce callback est déclenché à chaque clic sur le bouton d'envoi (`send_button`)
    et exécute l'une des deux logiques principales :
    - Si aucune intention n’est encore confirmée, il détecte l’intention (PPA, constantes, recommandations)
      et affiche une demande de confirmation.
    - Si une confirmation est attendue, il traite la réponse de l’utilisateur ("oui"/"non"),
      déclenche le pipeline correspondant et met à jour l’historique affiché.

    Le retour inclut :
    - L’historique enrichi (chat utilisateur + bot),
    - Les constantes affichées sous forme de graphiques ou tableau si la demande le requiert,
    - Le patient courant,
    - Les graphiques sérialisés (pour export),
    - Le contenu à afficher dans le `chat_history_display`.

    Args:
        send_clicks (int): Nombre de clics sur le bouton d'envoi.
        user_input (str): Requête saisie par l'utilisateur.
        chat_history (list): Historique actuel des messages affichés dans l'interface.
        session_data (dict): Données de la session utilisateur courante.
        current_patient (str | None): Nom du patient actuellement sélectionné.

    Returns:
        tuple:
            - chat_history (list) : Historique mis à jour (pour stockage),
            - constants_graphs (list[Graph]) : Graphiques des constantes (si applicables),
            - constants_table (str | html.Div) : Tableau HTML des constantes (si applicable),
            - anomaly_graphs (str | html.Div) : Bloc des anomalies détectées (si applicable),
            - current_patient (str | None) : Nom du patient mis à jour,
            - serialized_figs (list | None) : Liste des figures Plotly sérialisées pour export,
            - chat_history_display (html.Div) : Contenu HTML de l'historique à afficher à l'écran.

    Raises:
        dash.exceptions.PreventUpdate: Si aucun clic n’a été détecté ou si la session n’est pas active.

    """
    if send_clicks is None or send_clicks == 0:
        raise dash.exceptions.PreventUpdate


    # --- Vérification session ---
    if not session_data or not isinstance(session_data, dict):
        # ⚠️ Pas de session active
        return "❌ Session non authentifiée. Veuillez vous reconnecter.", "", "", "", dash.no_update


    # --- Initialisation des blocs d'affichage et variables de retour ---
    serialized_figs = None  # Valeur par défaut
    bot_msg = None
    constants_graphs = []
    constants_table = ""
    anomaly_graphs = ""
    chat_history_display = dash.no_update  # ⚠️ Ne pas réafficher s’il n’y a pas de nouvelle réponse
    full_chat_history = []

    # --- Si une session existe... ---
    session_id = session_data.get("session_id")
    session = session_manager_instance.get_session(session_id)


    if session:
        if user_input:

        # --- Si l'input correspond à la requête entrée par l'utilisateur ---
        # --- L'utilisateur n'a pas encore entré sa requête -> session["intent_confirmation_pending"] = False
            if not session["intent_confirmation_pending"]:
                print("📩 Début du traitement de la requête utilisateur")

                # ✅ Initialisations uniquement dans ce cas
                current_patient = current_patient or None
                chat_history = chat_history or []

                (
                chat_history, figs_list, table_html, anomaly_block,
                current_patient, serialized_figs,chat_history_display
                ) = handle_initial_request(
                    user_input, session, session_data, chat_history, current_patient
                )

                constants_graphs = [dcc.Graph(figure=fig) for fig in figs_list]
                constants_table = None if not table_html else html.Div(table_html)
                anomaly_graphs = None if not anomaly_block else html.Div(anomaly_block)

                print("⏸️ Attente de confirmation utilisateur")
                return chat_history, constants_graphs, constants_table, anomaly_graphs, current_patient, serialized_figs, chat_history_display


        # --- Si l'input correspond à une confirmation attendue suite à une requête ---
        # --- Récupération de la réponse de l'utilisateur + affichage ---
            if session["intent_confirmation_pending"]:
                print("✅ Traitement de la réponse de confirmation utilisateur")

                (
                new_chat_history, figs_list, table_html, anomaly_block,
                current_patient, serialized_figs, chat_history_display
                ) = handle_confirmation_response(
                    user_input, session, session_data, chat_history, current_patient
                )

                # Concaténation new mess + historique
                full_chat_history = chat_history + new_chat_history
                chat_history_display = html.Div(full_chat_history)

                constants_graphs = [dcc.Graph(figure=fig) for fig in figs_list]
                constants_table = None if not table_html else html.Div(table_html)
                anomaly_graphs = None if not anomaly_block else html.Div(anomaly_block)


    return full_chat_history, constants_graphs, constants_table, anomaly_graphs, current_patient, serialized_figs, chat_history_display



# print("✅ Callback handle_chat_request enregistré")


# ================================================================================================ #
# --------------------- Fonctions appelées par handle_user_input_or_logout() --------------------- #
# ================================================================================================ #
# 1/.
def handle_initial_request(user_input, session, session_data, chat_history, current_patient):
    # --- Si une demande utlisateur existe ---

    bot_response = "🤖 Je traite votre demande..."
    print("🚀 chatbot_ui.py chargé !")
    print(f'requête utilisateur {user_input}')

    # Détection intention
    intent_dict = detect_user_intent(user_input)
    nom = extract_patient_name_llm(user_input)
    intent = intent_dict.get("intent", "unknown")
    print(f'🟢Intention détectée: {intent}')

    # --- Affichage requête + concaténation chat_history ---
    user_msg = html.Div(f"👤 {user_input.strip()}", className="user-message")
    chat_history.append(user_msg)

    # En attente de confirmation par l'utlisateur
    session["intent_confirmation_pending"] = True
    session["intent_candidate"] = {"intent": intent, "name": nom, "full_user_input": user_input}

    # --- Étape affichage de l'intention ---
    if intent == "generate_ppa":
        text = "demande de génération de PPA"
        bot_response = f"Je comprends que vous souhaitez une {text}, est-ce que vous confirmez oui/non ?"

    elif intent == "get_constants":
        text = "demande de constantes patient"
        bot_response = f"Je comprends que vous souhaitez une {text}, est-ce que vous confirmez oui/non ?"

    elif intent == "get_recommendations":
        text = "demande de recommandations de soins"
        bot_response = f"Je comprends que vous souhaitez une {text}, est-ce que vous confirmez oui/non ?"

    else:
        # Requête hors contexte gérable
        bot_response = (
            "❌ Cette demande ne peut pas être traitée par OBY-IA, car elle sort du cadre de l'accompagnement des personnes âgées.\n\n"
            "Voici quelques exemples de requêtes que vous pouvez utiliser :\n"
            "- *Prépare-moi le plan d’aide pour Madame Dupont*\n"
            "- *Montre-moi les constantes du patient Martin sur le dernier mois*\n"
            "- *Quelles sont les recommandations en cas d’AVC ?*"
        )
    chat_history.append(html.Div(dcc.Markdown(bot_response), className="bot-response"))

    # Enregistrer l'échange (requête utilisateur + demande de confirmation)
    session = session_manager_instance.get_session(session_data["session_id"])
    session_obj = session.get("session_obj")
    if session_obj:
        session_obj.add_message(user_input, bot_response)


    # chat_history_display = dash.no_update  # Ne rien afficher tout de suite
    chat_history_display = chat_history

    return chat_history, [], "", "", current_patient, [], chat_history_display



# 2/.
def handle_confirmation_response(user_input, session, session_data, chat_history, current_patient):
    figs_list = []
    table_html = ""
    anomaly_block = ""
    serialized_figs = None
    bot_response = []
    user_id = session_data["user_id"]
    session_id = session_data["session_id"]


    print('⚠️Confirmation attendue...')
    answer = user_input.strip().lower()
    print(f"✅Réponse de l'utilisateur suite demande confirmation: {answer}")
    user_msg = html.Div(f"👤 {answer}", className="user-message")
    chat_history.append(user_msg)

    full_user_input = session["intent_candidate"]["full_user_input"]
    print(f'⚠️handle_confirmation_response/full_user_input: {full_user_input}')



    # Intention confirmée, -> changement état de intent_confirmation_pending
    if answer in ["oui", "yes", "ok", "c'est bien ça"]:
        session["intent_confirmation_pending"] = False
        intent = session["intent_candidate"]["intent"]
        nom = session["intent_candidate"]["name"]

        # Définition des flags
        ppa_requested = intent == "generate_ppa"
        constantes_requested = intent == "get_constants"
        recommandations_requested = intent == "generate_recommendations"
        print(f"✅ Intention confirmée par l’utilisateur : {intent}")

        print(f"🎯 Intentions détectées : "
              f"recommandations: {recommandations_requested},"
              f"constantes={constantes_requested}, "
              f"ppa={ppa_requested}, "
              f"nom patient={nom}")
        print(f'✅détection intention réussie')

        # On déclenche l'un des pipelines suivants selon l'intention détectée
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
                bot_response, dict_mapping = process_ppa_request(full_user_input, system_prompt)

                # Enregistrer le mapping renvoyé par la fonction dans la session
                # Le récupérer proprement via session_manager.get_anonymization_mapping()
                session_manager_instance.set_anonymization_mapping(session_id, dict_mapping)

                # Quand le LLM a donné une réponse (bot_response), ajout de la réponse dans la session
                session_manager_instance.append_llm_response(session_id, bot_response)

                # ✅ Ajouter l’échange complet (question + réponse)
                session = session_manager_instance.get_session(session_id)
                session_obj = session.get("session_obj")
                if session_obj:
                    session_obj.add_message(user_input, bot_response)

                figs_list, table_html, anomaly_block = [], "", ""

            except Exception as e:
                print(f"❌ Erreur dans process_ppa_request : {e}")
                bot_response = "Une erreur est survenue pendant la génération du PPA."
                figs_list, table_html, anomaly_block = "", "", ""


        # --- Traitement demande plan de soins ---
        elif recommandations_requested:
            print("📄 Appel à generate_structured_medical_plan() pour plan de soins")
            try:
                bot_response, dict_mapping = generate_structured_medical_plan(full_user_input,
                                                                              system_prompt_medical_plan)

                # Enregistrer le mapping renvoyé par la fonction dans la session
                # Le récupérer proprement via session_manager.get_anonymization_mapping()
                session_manager_instance.set_anonymization_mapping(session_id, dict_mapping)

                # Quand le LLM a donné une réponse (bot_response), ajout de la réponse dans la session
                session_manager_instance.append_llm_response(session_id, bot_response)

                # ✅ Ajouter l’échange complet (question + réponse)
                session = session_manager_instance.get_session(session_id)
                session_obj = session.get("session_obj")
                if session_obj:
                    session_obj.add_message(user_input, bot_response)

                figs_list, table_html, anomaly_block = [], "", ""

            except Exception as e:
                print(f"❌ Erreur dans generate_structured_medical_plan : {e}")
                bot_response = "Une erreur est survenue pendant l'extraction des recommandations de soins."
                figs_list, table_html, anomaly_block = [], "", ""



    else:
        # Rejet de l’intention
        session["intent_confirmation_pending"] = False
        session["intent_candidate"]["intent"] = {"intent": None, "name": None, "full_user_input": ""}

        bot_response = (
            "Compris. Voici quelques exemples de requêtes que vous pouvez utiliser :\n"
            "- *Prépare-moi le plan d’aide pour Madame Dupont*\n"
            "- *Montre-moi les constantes du patient Martin sur le dernier mois*\n"
            "- *Quelles sont les recommandations en cas d’AVC ?*"
        )

    if bot_response:
        bot_msg = html.Div(
            dcc.Markdown(str(bot_response), dangerously_allow_html=False),
            className="bot-response"
        )
        chat_history.append(bot_msg)

    chat_history_display = html.Div(chat_history)

    return chat_history, figs_list, table_html, anomaly_block, current_patient, serialized_figs, chat_history_display


# ==============================
# Production fichiers md
# ==============================
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



# ==============================
# Indexation bases chromadb
# ==============================
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
    # print(f"⏱️ Callback check_index_status déclenché avec n = {n}")
    # print("🔁 Vérification de l'état de l'indexation ChromaDB...")
    # print("📦 Index prêt ?", is_chroma_index_ready())

    if is_chroma_index_ready(verbose=True):
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



# ============================
# Gestion deconnexion
# ============================
@callback(
    Output("session_data", "data", allow_duplicate=True),
    Output("chat_history", "data", allow_duplicate=True),
    Output("current_patient", "data", allow_duplicate=True),
    Output("constants_graphs_store", "data", allow_duplicate=True),
    Input("logout_button", "n_clicks"),
    State("session_data", "data"),
    prevent_initial_call=True
)
def logout_user(n_clicks, session_data):
    if session_data:
        user_id = session_data.get("user_id")
        session_id = session_data.get("session_id")
        session_manager_instance.end_session(user_id, session_id)
        print(f"🔒 Session terminée pour {user_id} - ID: {session_id}")
        return None, [], None, None
    return None, [], None, None



# Tests
# print("✅ chatbot_ui.py chargé et exécuté")

# @callback(
#     Output("chat_history_display", "children"),
#     Input("send_button", "n_clicks"),
#     prevent_initial_call=True
# )
# def test_button(n_clicks):
#     print("✅ Callback test déclenché.")
#     return f"Bouton cliqué {n_clicks} fois"

