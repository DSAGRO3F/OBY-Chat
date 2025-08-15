# src/func/api_core.py

from typing import Any, Optional, Literal
from flask import session

from src.func.handle_user_requests import handle_initial_request, handle_confirmation_response
from src.llm_user_session.session_manager_instance import session_manager_instance
from src.api.models import ChatResponse, ChatRequest


def process_user_input(
    send_clicks: int,
    user_input: str,
    chat_history: list[Any],
    session_data: dict,
    current_patient: Optional[str] = None,
    output_mode: Literal["dash", "api"] = "dash"
) -> ChatResponse:
    """
    Fonction centrale appelée par l'API ou l'interface pour traiter la requête utilisateur.

    Args:
        send_clicks (int): Nombre de clics sur le bouton envoyer.
        user_input (str): Message saisi par l'utilisateur.
        chat_history (list): Historique des échanges.
        session_data (dict): Données de session utilisateur.
        current_patient (Optional[str]): Nom du patient actuellement sélectionné.

    Returns:
        dict: Dictionnaire contenant les résultats du traitement.
    """
    # 1. Vérification clic bouton
    if send_clicks is None or send_clicks == 0:
        return ChatResponse(status="no_click", message="Aucun clic détecté.")

    # 2. Vérification session active
    if not session_data or not isinstance(session_data, dict):
        return ChatResponse(status="unauthenticated",
                            message="❌ Session non authentifiée. Veuillez vous reconnecter.")

    # 3. Initialisations
    serialized_figs = None
    constants_graphs = []
    constants_table = ""
    anomaly_graphs = ""


    # 4. Récupération de session
    session_id = session_data.get("session_id")
    session = session_manager_instance.get_session(session_id)

    if not session:
        return ChatResponse(status="error", message="Session introuvable.")

    if not user_input:
        return ChatResponse(status="error", message="Entrée utilisateur vide.")

    # 5. Cas initial : intention pas encore confirmée
    if not session.get("intent_confirmation_pending", False):
        print('🟡Cas initial : intention pas encore confirmée...')
        print("🟢 Début du traitement de la requête initiale utilisateur")
        current_patient = current_patient or None
        chat_history = chat_history or []

        (
            chat_from_initial_request,
            figs_list,
            table_html,
            anomaly_block,
            updated_patient,
            serialized_figs,
            chat_history_display
        ) = handle_initial_request(
            user_input, session, session_data,
            chat_history, current_patient, output_mode=output_mode
        )

        # Vérification contenu chat_from_initial_request
        print(f'🔴Contenu et type chat from initial request: {chat_from_initial_request}, '
              f'🔴type: {type(chat_from_initial_request)}')

        partial_chat_from_user_request = chat_from_initial_request

        print("⏸️ Attente de confirmation utilisateur")
        print("🔴DEBUG awaiting:", len(partial_chat_from_user_request), "items")

        return ChatResponse(
            status="awaiting_confirmation",
            partial_chat_from_user_request=partial_chat_from_user_request,
            chat_history=chat_from_initial_request,
            figures_out=figs_list or [],
            table_html=table_html or "",
            anomaly_block=anomaly_block or "",
            current_patient=updated_patient,
            serialized_figs=None,  # pas utile en mode API
        )



    # 6. Cas confirmation : traitement final
    print('🟡 Cas confirmation : traitement final...')
    if session["intent_confirmation_pending"]:
        print("✅ Traitement de la réponse de confirmation utilisateur")

        (
            chat_from_confirmation_request,
            figures_out,
            table_html,
            anomaly_block,
            updated_patient,
            serialized_figs,
            chat_history_display
        ) = handle_confirmation_response(
            user_input, session, session_data,
            chat_history, current_patient, output_mode=output_mode
        )


        partial_chat_from_user_request = chat_from_confirmation_request

        return ChatResponse(
            status="response_processed",
            partial_chat_from_user_request=partial_chat_from_user_request,
            chat_history=chat_from_confirmation_request,
            figures_out=figures_out or [],
            table_html=table_html or "",
            anomaly_block=anomaly_block or "",
            current_patient=updated_patient,
            serialized_figs=serialized_figs if output_mode == "dash" else None,
        )

    return ChatResponse(status="no_action", message="Aucune action déterminée.")