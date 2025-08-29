"""
Gestion des requêtes utilisateur pour OBY-IA (détection d’intention, confirmation et exécution).

Ce module centralise la logique conversationnelle « back-end » entre l’interface
et les pipelines métier d’OBY-IA. Il orchestre deux étapes clés :

1) handle_initial_request(...) :
   - Analyse l’input utilisateur (détection d’intention et extraction éventuelle
     du nom de patient).
   - Met en place un état de confirmation (session["intent_confirmation_pending"] = True)
     et prépare un message de confirmation.
   - Retourne les éléments nécessaires pour l’affichage / la réponse (historique,
     tableaux, graphiques, etc.), généralement vides à ce stade.

2) handle_confirmation_response(...) :
   - Interprète la confirmation (ex.: « oui / non ») lorsque l’intention est en attente.
   - Déclenche le pipeline adapté :
       • PPA (generate_ppa_from_poa.process_ppa_request),
       • Recommandations (generate_structured_medical_plan),
       • Constantes patient (process_patient_request_with_constants).
   - Met à jour l’état de session (réinitialisation du flag de confirmation,
     mémorisation du patient courant, etc.) et assemble la réponse finale.

Modes de sortie :
    Le paramètre `output_mode` permet d’adapter le format des objets retournés :
      - "dash" : le module peut retourner des composants Dash (html.Div, dcc.Markdown,
                 figures Plotly « go.Figure », etc.) pour l’UI interne.
      - "api"  : le module retourne des structures sérialisables (listes/dicts/strings),
                 adaptées à FastAPI / JSON (pas d’objets Dash).

Effets de bord :
    - Mise à jour de la session (ex. intent_confirmation_pending, intent_candidate).
    - Enrichissement de l’historique de conversation (chat_history / new_chat_history).

Dépendances principales :
    - src.llm_user_session.session_manager_instance
    - src.func.extract_user_intent, src.func.extract_patient_name
    - src.func.generate_ppa_from_poa, src.func.generate_structured_medical_plan
    - src.func.get_patient_constants_graphs
    - src.func.serialize_figs (sérialisation des figures)
    - (optionnel côté UI) dash.html / dash.dcc pour le mode "dash"

Convention de retour :
    Les fonctions retournent un 7-uplet :
        (chat_history_ou_new_chat_history,
         figures_out,
         table_html,
         anomaly_block,
         current_patient,
         serialized_figs,
         chat_history_display)

    * En mode "initial", chat_history est renvoyé (nouvel historique cumulé).
    * En mode "confirmation", new_chat_history est renvoyé (ajouts du tour courant).
    * Le « full_chat_history » est assemblé par l’appelant si nécessaire.

Ce module est conçu pour être appelé à la fois par l’interface Dash (UI)
et par la couche API (FastAPI) via une fonction « tronc commun ».
"""


import dash
from dash import dcc, html, callback, ctx, no_update
from typing import Literal

from src.llm_user_session.session_manager_instance import session_manager_instance
from src.func.generate_ppa_from_poa import process_ppa_request
from src.func.generate_structured_medical_plan import generate_structured_medical_plan
from src.func.llm_prompts import system_prompt, system_prompt_medical_plan
from src.func.extract_user_intent import detect_user_intent
from src.func.get_patient_constants_graphs import process_patient_request_with_constants
from src.func.extract_patient_name import extract_patient_name_llm
from src.func.serialize_figs import serialize_figs, deserialize_figs




# ================================================================================================ #
# --------------------- Fonctions appelées par handle_user_input_or_logout() --------------------- #
# ================================================================================================ #
# 1/.
def handle_initial_request(user_input, session,
                           session_data, chat_history,
                           current_patient, output_mode: Literal["dash", "api"] = "dash"):

    """
    Traite la requête initiale : détection d’intention et demande de confirmation.

    Cette fonction :
      1. Détecte l’intention de l’utilisateur (ex. generate_ppa, get_constants,
         get_recommendations) et tente d’identifier le patient mentionné.
      2. Met à jour la session pour indiquer qu’une confirmation est requise :
         - session["intent_confirmation_pending"] = True
         - session["intent_candidate"] = {"intent": <str>, "name": <str|None>, "full_user_input": <str>}
      3. Construit et ajoute au fil de conversation un message de confirmation
         (« Je comprends que vous souhaitez… confirmez-vous oui/non ? »).

    Paramètres
    ----------
    user_input : str
        Texte brut saisi par l’utilisateur.
    session : dict
        Objet de session récupéré via `session_manager_instance.get_session(...)`.
    session_data : dict
        Données de session de l’UI (ex. {"user_id": ..., "session_id": ...}).
    chat_history : list
        Historique courant de la conversation (format dépendant de `output_mode`).
    current_patient : str | None
        Patient courant, si déjà connu.
    output_mode : {"dash", "api"}, optionnel
        Mode de sortie. "dash" peut retourner des composants Dash ;
        "api" ne retourne que des structures JSON-sérialisables.

    Retours
    -------
    tuple
        Un 7-uplet :
            chat_history : list
                Historique mis à jour (intégrant le message de confirmation).
            figures_out : list
                Liste de figures (souvent vide à ce stade).
            table_html : str
                Table HTML (souvent vide à ce stade).
            anomaly_block : str
                Bloc d’anomalies (souvent vide à ce stade).
            current_patient : str | None
                Patient détecté ou patient courant.
            serialized_figs : list | None
                Figures sérialisées (si `output_mode="dash"` et si présent).
            chat_history_display : Any
                Représentation prête à l’affichage (UI), inutilisée en mode API.

    Notes
    -----
    - Aucun pipeline métier n’est exécuté à ce stade : la fonction se limite
      à préparer la confirmation d’intention.
    - L’appelant est responsable d’afficher `chat_history` et d’attendre la
      réponse de confirmation de l’utilisateur.
    """
    chat_history = []
    # --- Si une demande utlisateur existe ---

    bot_response = "🤖 Je traite votre demande..."
    print("🚀 chatbot_ui.py chargé !")
    print(f'🟡 requête utilisateur {user_input}')

    # Détection intention
    intent_dict = detect_user_intent(user_input)
    nom = extract_patient_name_llm(user_input)
    intent = intent_dict.get("intent", "unknown")
    print(f'🟢Intention détectée: {intent}')

    # --- Affichage requête + concaténation chat_history ---
    if output_mode == "dash":
        user_msg = html.Div(f"👤 {user_input.strip()}", className="user-message")
    else:
        user_msg = {"role": "user", "text": user_input.strip()}

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

    elif intent == "generate_recommendations":
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

    # Logique API ou Dash...
    if output_mode == "dash":
        chat_history.append(html.Div(dcc.Markdown(bot_response), className="bot-response"))
    else:
        # API-safe structure (pure JSON)
        chat_history.append({"role": "assistant", "markdown": str(bot_response)})


    # Enregistrer l'échange (requête utilisateur + demande de confirmation)
    session = session_manager_instance.get_session(session_data["session_id"])
    session_obj = session.get("session_obj")
    if session_obj:
        session_obj.add_message(user_input, bot_response)

    chat_history_display = None

    return chat_history, [], "", "", current_patient, [], chat_history_display



# 2/.
def handle_confirmation_response(user_input, session,
                                 session_data, chat_history,
                                 current_patient, output_mode: Literal["dash", "api"] = "dash"):

    """
    Traite la réponse de confirmation et exécute le pipeline métier approprié.

    Cette fonction :
      1. Lit l’état `session["intent_candidate"]` défini lors de la requête initiale,
         ainsi que la confirmation utilisateur (ex. « oui », « non »).
      2. En cas de confirmation :
         - Exécute le pipeline adapté selon l’intention détectée :
             * generate_ppa  → process_ppa_request(...)
             * get_constants → process_patient_request_with_constants(...)
             * get_recommendations → generate_structured_medical_plan(...)
         - Met à jour l’historique avec la réponse « bot », les tableaux/figures,
           et sérialise les figures si nécessaire (mode "dash").
         - Réinitialise l’état de confirmation dans la session.
      3. En cas de refus :
         - Réinitialise l’état de confirmation.
         - Ajoute un message d’aide avec des exemples de requêtes valides.

    Paramètres
    ----------
    user_input : str
        Texte brut saisi par l’utilisateur (confirmation et/ou compléments).
    session : dict
        Objet de session récupéré via `session_manager_instance.get_session(...)`.
    session_data : dict
        Données de session de l’UI (ex. {"user_id": ..., "session_id": ...}).
    chat_history : list
        Historique de conversation avant ce tour (format dépendant de `output_mode`).
    current_patient : str | None
        Patient courant, si déjà connu.
    output_mode : {"dash", "api"}, optionnel
        Mode de sortie. "dash" peut retourner des composants Dash ;
        "api" ne retourne que des structures JSON-sérialisables.

    Retours
    -------
    tuple
        Un 7-uplet :
            new_chat_history : list
                Messages ajoutés sur ce tour (à concaténer par l’appelant).
            figures_out : list
                Figures produites (listes de go.Figure en "dash", ou dict Plotly en "api").
            table_html : str
                Tableau HTML des constantes (si pertinent).
            anomaly_block : str
                Bloc d’anomalies (si pertinent).
            current_patient : str | None
                Patient courant (éventuellement mis à jour).
            serialized_figs : list | None
                Figures sérialisées (utiles au stockage / export en mode UI).
            chat_history_display : Any
                Représentation prête à l’affichage (UI), inutilisée en mode API.

    Exceptions
    ----------
    Peut lever des exceptions métiers/FS sous-jacentes (lecture des données,
    génération de graphique, etc.) qui doivent être gérées par l’appelant
    (selon le contexte UI ou API).

    Remarques
    ---------
    - L’appelant est responsable de former le `full_chat_history` en concaténant
      `chat_history + new_chat_history`.
    - La fonction remet à plat les drapeaux de confirmation dans `session`.
    """

    figs_list: list = []
    table_html = ""
    anomaly_block = ""
    serialized_figs = None
    figures_out: list = []
    bot_response: str = ""
    chat_history = []
    user_id = session_data["user_id"]
    session_id = session_data["session_id"]


    print('⚠️Confirmation attendue...')
    answer = user_input.strip().lower()
    print(f"✅Réponse de l'utilisateur suite demande confirmation: {answer}")
    if output_mode == "dash":
        user_msg = html.Div(f"👤 {answer}", className="user-message")
    else:
        user_msg = {"role": "user", "text": user_input.strip()}

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
                print(f"🔴 Changement de patient détecté : {current_patient} ➡️ {nom}")

                # ⚠️ Reset du delta SANS perdre le message utilisateur déjà capturé
                chat_history = [user_msg]
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

                if output_mode == "dash":
                    # ✅ Mode UI Dash: sérialisation pour dcc.Store
                    serialized_figs = serialize_figs(figs_list)
                    figures_out = figs_list  # pour construire dcc.Graph côté callback
                else:
                    # ✅ Mode API: JSON Plotly directement exploitable côté OBY
                    figures_out = [fig.to_plotly_json() for fig in figs_list]
                    serialized_figs = None

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

                # ✅ Ajout échange complet (question + réponse)
                session = session_manager_instance.get_session(session_id)
                session_obj = session.get("session_obj")
                if session_obj:
                    session_obj.add_message(user_input, bot_response)

                figs_list, table_html, anomaly_block = [], "", ""

            except Exception as e:
                print(f"❌ Erreur dans process_ppa_request : {e}")
                bot_response = "Une erreur est survenue pendant la génération du PPA."
                figs_list, table_html, anomaly_block = [], "", ""


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
                print("🔴before -> session_manager_instance.append_llm_response(session_id, bot_response")
                session_manager_instance.append_llm_response(session_id, bot_response)
                print("🔴after -> session_manager_instance.append_llm_response(session_id, bot_response")

                # ✅ Ajouter l’échange complet (question + réponse)
                print("🔴before -> session_manager_instance.get_session(session_id)")
                session = session_manager_instance.get_session(session_id)
                print("🔴after -> session_manager_instance.get_session(session_id)")
                session_obj = session.get("session_obj")
                if session_obj:
                    print("🔴before -> session_obj.add_message(user_input, bot_response)")
                    session_obj.add_message(user_input, bot_response)
                    print("🔴after -> session_obj.add_message(user_input, bot_response)")

                figs_list, table_html, anomaly_block = [], "", ""

            except Exception as e:
                print(f"❌ Erreur dans generate_structured_medical_plan : {e}")
                bot_response = "Une erreur est survenue pendant l'extraction des recommandations de soins."
                figs_list, table_html, anomaly_block = [], "", ""



    else:
        # Rejet de l’intention
        session["intent_confirmation_pending"] = False
        session["intent_candidate"] = {"intent": None, "name": None, "full_user_input": ""}

        bot_response = (
            "Compris. Voici quelques exemples de requêtes que vous pouvez utiliser :\n"
            "- *Prépare-moi le plan d’aide pour Madame Dupont*\n"
            "- *Montre-moi les constantes du patient Martin sur le dernier mois*\n"
            "- *Quelles sont les recommandations en cas d’AVC ?*"
        )

    if bot_response:
        if output_mode == "dash":
            bot_msg = html.Div(
                dcc.Markdown(str(bot_response), dangerously_allow_html=False),
                className="bot-response"
            )
            chat_history.append(bot_msg)
        else:
            chat_history.append({"role": "assistant", "markdown": str(bot_response)})

    chat_history_display = None


    return (chat_history, figures_out, table_html,
            anomaly_block, current_patient,
            serialized_figs, chat_history_display)
