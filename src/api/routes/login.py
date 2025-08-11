# src/api/routes/login.py

"""
Module de gestion de l'authentification utilisateur pour l'API OBY-IA.

Ce module expose un endpoint REST permettant aux clients de s'authentifier
à l'application via un identifiant et un mot de passe. En cas de succès,
une session utilisateur unique est créée et stockée dans le gestionnaire
de sessions.
"""

from fastapi import APIRouter, HTTPException
from uuid import uuid4

from config.config import USER_DATABASE
from src.api.models import LoginRequest, LoginResponse
from src.llm_user_session.session_manager_instance import session_manager_instance

router = APIRouter()

@router.post("/login", response_model=LoginResponse)
def authenticate_user_api(request: LoginRequest):
    """
    Authentifier un utilisateur et créer une nouvelle session.

    Vérifie si les identifiants fournis correspondent à un utilisateur
    valide dans la base locale. Si oui, génère un identifiant de session
    unique, initialise la session dans le gestionnaire centralisé, et
    retourne les données de session.

    Args:
        request (LoginRequest): Objet contenant `user_id` et `password`.

    Returns:
        LoginResponse: Message de confirmation et données de session.

    Raises:
        HTTPException: Si les champs sont manquants (400) ou si les
        identifiants sont invalides (401).
    """
    user_id_input = request.user_id
    password_input = request.password

    if not user_id_input or not password_input:
        # Requête mal formée / utilisateur n'a pas rempli les champs
        raise HTTPException(status_code=400, detail="❌ Veuillez remplir tous les champs.")

    # Vérification des identifiants
    if user_id_input in USER_DATABASE and USER_DATABASE[user_id_input] == password_input:
        # ⚠️ Utiliser un vrai identifiant de session unique
        session_id = str(uuid4())

        # Création + init session dans le singleton partagé
        session_manager_instance.create_session(user_id_input, session_id)
        session_manager_instance.reset_anonymization_mapping(session_id)

        print(f"✅ Session créée pour {user_id_input} - ID: {session_id}")

        return LoginResponse(
            message="✅ Authentification réussie.",
            session_data={
                "user_id": user_id_input,
                "session_id": session_id
            }
        )

    # Identifiants invalides
    raise HTTPException(status_code=401, detail="❌ Identifiants invalides. Veuillez réessayer.")



