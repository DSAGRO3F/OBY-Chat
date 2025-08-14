# src/func/api_core.py

from typing import Any, Optional, Literal

from flask import session

from src.func.handle_user_requests import handle_initial_request, handle_confirmation_response
from src.llm_user_session.session_manager_instance import session_manager_instance
from src.api.models import ChatResponse, ChatRequest

# Imports non nécessaires ? à vérifier
# from src.func.generate_ppa_from_poa import process_ppa_request
# from src.func.generate_structured_medical_plan import generate_structured_medical_plan
# from src.func.llm_prompts import system_prompt, system_prompt_medical_plan
# from src.func.extract_user_intent import detect_user_intent
# from src.func.get_patient_constants_graphs import process_patient_request_with_constants
# from src.func.extract_patient_name import extract_patient_name_llm
# from src.func.serialize_figs import serialize_figs
# from src.utils.vector_db_utils import is_chroma_index_ready
#

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
    base_history = ""
    chat_history_display = ""
    full_chat_history = []
    prev_patient = current_patient or None

    # 4. Récupération de session
    session_id = session_data.get("session_id")
    session = session_manager_instance.get_session(session_id)

    if not session:
        return ChatResponse(status="error", message="Session introuvable.")

    if not user_input:
        return ChatResponse(status="error", message="Entrée utilisateur vide.")

    # 5. Cas initial : intention pas encore confirmée
    if not session.get("intent_confirmation_pending", False):
        print("🟢 Début du traitement de la requête utilisateur")
        current_patient = current_patient or None
        chat_history = chat_history or []

        (
            new_chat_items,
            figs_list,
            table_html,
            anomaly_block,
            updated_patient,
            serialized_figs,
            _  # chat_history_display ignoré
        ) = handle_initial_request(
            user_input, session, session_data,
            chat_history, current_patient, output_mode=output_mode
        )

        # Historique "avant"
        base_history = chat_history or []

        # 🔁 Reset si changement de patient détecté à ce tour
        if updated_patient and updated_patient != prev_patient:
            base_history = []

        full_chat_history = base_history + (new_chat_items or [])

        print("⏸️ Attente de confirmation utilisateur")

        return ChatResponse(
            status="awaiting_confirmation",
            full_chat_history=full_chat_history,  # ✅ toujours fournir le "full"
            chat_history=new_chat_items,  # ✅ delta (optionnel mais utile)
            figures_out=figs_list or [],
            table_html=table_html or "",
            anomaly_block=anomaly_block or "",
            current_patient=updated_patient,
            serialized_figs=None,  # pas utile en mode API
        )

# ==============================
# Ancien code...en attente de confirmation
# ==============================

        # (
        #     new_chat_items,
        #     figs_list,
        #     table_html,
        #     anomaly_block,
        #     current_patient,
        #     serialized_figs,
        #     chat_history_display
        # ) = handle_initial_request(
        #     user_input, session, session_data,
        #     chat_history, current_patient, output_mode=output_mode
        # )

        # base_history = chat_history or []
        # full_chat_history = base_history + (new_chat_items or [])
        #
        # print("⏸️ Attente de confirmation utilisateur")
        #
        # return ChatResponse(
        #     status="awaiting_confirmation",
        #     chat_history=full_chat_history,
        #     figures_out=figs_list or [],
        #     table_html=table_html or "",
        #     anomaly_block=anomaly_block or "",
        #     current_patient=current_patient,
        #     serialized_figs= None,
        #     # chat_history_display=chat_history_display -> pas utile si mode API
        # )

# ==============================
# ==============================


    # 6. Cas confirmation : traitement final
    if session["intent_confirmation_pending"]:
        print("✅ Traitement de la réponse de confirmation utilisateur")

        (
            new_chat_items,
            figures_out,
            table_html,
            anomaly_block,
            updated_patient,
            serialized_figs,
            _  # chat_history_display ignoré (same logic as above)
        ) = handle_confirmation_response(
            user_input, session, session_data,
            chat_history, current_patient, output_mode=output_mode
        )

        base_history = chat_history or []

        # 🔁 Reset si changement de patient détecté pendant la confirmation
        if updated_patient and updated_patient != prev_patient:
            base_history = []

        full_chat_history = base_history + (new_chat_items or [])

        return ChatResponse(
            status="response_processed",
            full_chat_history=full_chat_history,
            figures_out=figures_out or [],
            table_html=table_html or "",
            anomaly_block=anomaly_block or "",
            current_patient=updated_patient,
            serialized_figs=serialized_figs if output_mode == "dash" else None,
        )

# ==============================
# Ancien code...en attente de confirmation
# ==============================


       # (
        #     new_chat_items,
        #     figures_out,
        #     table_html,
        #     anomaly_block,
        #     current_patient,
        #     serialized_figs,
        #     chat_history_display
        # ) = handle_confirmation_response(
        #     user_input, session, session_data,
        #     chat_history, current_patient, output_mode=output_mode
        # )
        #
        # full_chat_history = chat_history + new_chat_items
        #
        # return ChatResponse(
        #     status="response_processed",
        #     full_chat_history=full_chat_history,
        #     figures_out=figures_out,
        #     table_html=table_html,
        #     anomaly_block=anomaly_block,
        #     current_patient=current_patient,
        #     serialized_figs=serialized_figs if output_mode == "dash" else None,
        #     chat_history_display=chat_history_display
        # )

# ==============================
# ==============================

    return ChatResponse(status="no_action", message="Aucune action déterminée.")