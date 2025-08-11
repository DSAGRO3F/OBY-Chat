# src/api/models.py

"""
Ce fichier regroupe toutes les structures de données échangées avec l’API, basées sur pydantic.
🟡 Chemin : src/api/models.py
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict

# 🟡Données envoyées pour le chat
class ChatRequest(BaseModel):
    send_clicks: int
    user_input: str
    chat_history: list[Any]
    session_data: dict
    current_patient: Optional[str] = None

class ChatResponse(BaseModel):
    status: str
    message: Optional[str] = None
    chat_history: Optional[List[Any]] = None
    new_chat_history: Optional[List[Any]] = None
    full_chat_history: Optional[List[Any]] = None
    figures_out: Optional[List[Any]] = None # Mode API: list[dict] Plotly / Mode Dash: list[go.Figure]
    table_html: Optional[str] = None
    anomaly_block: Optional[str] = None
    current_patient: Optional[str] = None
    serialized_figs: Optional[Any] = None

    # Ce champ est utile uniquement dans Dash → on l’exclut de l'API
    chat_history_display: Optional[Any] = Field(default=None, exclude=True)

# 🟡 Login utilisateur
class LoginRequest(BaseModel):
    user_id: str
    password: str

class LoginResponse(BaseModel):
    message: str
    session_data: Dict[str, str]  # {"user_id": "...", "session_id": "..."}

# 🟡 Logout utilisateur
class LogoutRequest(BaseModel):
    user_id: str
    session_id: str

class LogoutResponse(BaseModel):
    message: str
    session_data: Optional[dict] = None
    chat_history: list
    current_patient: Optional[str] = None
    constants_graphs_store: Optional[dict] = None
    already_logged_out: bool = False


