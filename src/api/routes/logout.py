# src/api/routes/logout.py

"""
Module de gestion de la déconnexion utilisateur pour l'API OBY-IA.

Ce module expose un endpoint REST permettant aux clients de mettre fin
à leur session active. Il gère également les cas de déconnexion multiple
(idempotence), en indiquant si la session était déjà terminée.
"""

from fastapi import APIRouter
from src.api.models import LogoutRequest, LogoutResponse
from src.llm_user_session.session_manager_instance import session_manager_instance

router = APIRouter()

@router.post("/logout", response_model=LogoutResponse)
def logout_user_api(request: LogoutRequest):
    """
    Déconnecter un utilisateur et réinitialiser sa session.

    Supprime la session identifiée par `user_id` et `session_id` du
    gestionnaire centralisé. Retourne un indicateur `already_logged_out`
    pour signaler si la session était déjà inexistante.

    Args:
        request (LogoutRequest): Objet contenant `user_id` et `session_id`.

    Returns:
        LogoutResponse: Message de confirmation, état des données de
        session, et indicateur `already_logged_out`.

    Raises:
        HTTPException: Si la requête est invalide (400) ou si les champs
        obligatoires sont absents.
    """

    user_id = request.user_id
    session_id = request.session_id

    session = session_manager_instance.get_session(session_id)
    if session:
        session_manager_instance.end_session(user_id, session_id)
        message = "✅ Déconnexion réussie."
        already_logged_out = False
    else:
        # Idempotent: OK même si la session n'existait pas/plus
        message = "✅ Déconnexion réussie (aucune session active)."
        already_logged_out = True

    return LogoutResponse(
        message=message,
        session_data=None,
        chat_history=[],
        current_patient=None,
        constants_graphs_store=None,
        already_logged_out=already_logged_out,  # <-- ajoute ce champ dans le modèle
    )