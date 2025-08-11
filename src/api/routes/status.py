# src/api/routes/status.py

from fastapi import APIRouter
from src.utils.vector_db_utils import is_chroma_index_ready
from pydantic import BaseModel

router = APIRouter()

class IndexStatusResponse(BaseModel):
    status: str
    disable_inputs: bool
    banner_text: str
    banner_color: str

@router.get("/indexing", response_model=IndexStatusResponse)
def check_index_status_api():
    """
    Vérifie si les index ChromaDB sont prêts à être interrogés.
    Renvoie le statut à l’interface OBY pour activer/désactiver les champs.
    """
    if is_chroma_index_ready():
        return IndexStatusResponse(
            status="ready",
            disable_inputs=False,
            banner_text="● Prêt",
            banner_color="green"
        )
    else:
        return IndexStatusResponse(
            status="indexing",
            disable_inputs=True,
            banner_text="● En cours d'indexation",
            banner_color="orange"
        )
