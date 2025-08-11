# src/api/routes/chat.py

"""
chat.py : gérer les échanges utilisateur ⇄ OBY-IA
📁 Chemin : src/api/routes/chat.py
"""


from fastapi import APIRouter
from src.api.models import ChatResponse, ChatRequest
from src.func.api_core import process_user_input
router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def handle_chat_api(payload: ChatRequest):
    """
    chat.py — Routes API pour la gestion des échanges entre l'utilisateur et OBY-IA.

    📁 Chemin : src/api/routes/chat.py

    Ce module définit les endpoints FastAPI permettant d'interagir avec l'agent
    conversationnel OBY-IA via API.
    Il gère la réception des requêtes utilisateur, la transmission au moteur
    de traitement (`process_user_input`) et le renvoi des réponses formatées.

    Fonctionnalités principales :
    - Point d'entrée `/chat` (méthode POST) pour envoyer un message et recevoir une réponse.
    - Conversion automatique de la requête JSON en modèle `ChatRequest`.
    - Utilisation du modèle `ChatResponse` pour structurer la réponse API.
    - Passage des données de session, historique de chat et contexte patient
      au moteur de traitement.

    Imports :
    - `APIRouter` : gestion des routes FastAPI.
    - `ChatResponse`, `ChatRequest` : modèles Pydantic pour la validation des données.
    - `process_user_input` : fonction cœur de traitement des requêtes.

    Usage :
        POST /chat
        Body : ChatRequest (JSON)
        Retour : ChatResponse (JSON)
    """

    result = process_user_input(
        send_clicks=payload.send_clicks,
        user_input=payload.user_input,
        chat_history=payload.chat_history,
        session_data=payload.session_data,
        current_patient=payload.current_patient,
        output_mode="api",
    )
    return result
