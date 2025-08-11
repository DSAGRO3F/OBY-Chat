# src/api/routes/export_chat.py
from fastapi import APIRouter
from pydantic import BaseModel
from src.llm_user_session.session_manager_instance import session_manager_instance
from src.utils.export_chat_response import export_llm_responses
from src.func.serialize_figs import deserialize_figs

router = APIRouter()

class ExportRequest(BaseModel):
    session_data: dict
    current_patient: str
    serialized_figs: list

@router.post("/export")
def export_chat_response_api(payload: ExportRequest):
    """
        Exporte l’historique de conversation OBY-IA au format Markdown et renvoie l’URL du fichier.

        Cette route :
        1) vérifie la présence d’une session valide (session_id),
        2) désérialise les éventuels graphiques des constantes (Plotly) fournis,
        3) appelle `export_llm_responses(...)` pour générer le fichier `.md` dans `outputs/...`,
        4) retourne une réponse JSON avec un lien web pointant vers la ressource statique
           (mappée par l’application vers `/static/...`).

        Paramètres
        ----------
        payload : ExportRequest
            Corps de requête contenant :
            - `session_data` : dict avec au minimum `session_id`,
            - `current_patient` : nom du patient (utilisé pour le nommage/chemin),
            - `serialized_figs` : liste des figures Plotly sérialisées (peut être vide).

        Returns
        -------
        dict
            Objet JSON avec :
            - `status` : "success" ou "error",
            - `message` : détail du résultat,
            - `markdown_file_url` : URL relative `/static/...` vers le fichier exporté, ou `None` en cas d’erreur.

        Notes
        -----
        - Cette route suppose que l’application FastAPI a monté un répertoire statique
          exposant `outputs/` sous le préfixe `/static/`.
        - Si aucun graphique n’est fourni, l’export Markdown se base uniquement sur l’historique
          de session (messages utilisateur / réponses OBY-IA) maintenu par `session_manager_instance`.
        """

    session_data = payload.session_data
    current_patient = payload.current_patient
    serialized_figs = payload.serialized_figs

    if not session_data:
        return {
            "status": "error",
            "message": "❌ Session non authentifiée. Veuillez vous reconnecter.",
            "markdown_file_url": None
        }

    session_id = session_data.get("session_id")

    try:
        constants_graphs = deserialize_figs(serialized_figs)
        file_path = export_llm_responses(
            session_manager_instance,
            session_id,
            current_patient,
            constants_graphs
        )

        # On retourne juste l’URL accessible depuis OBY
        relative_url = file_path.replace("outputs/", "/static/")
        return {
            "status": "success",
            "message": f"✅ Export Markdown enregistré.",
            "markdown_file_url": relative_url
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"❌ Erreur lors de l’export : {str(e)}",
            "markdown_file_url": None
        }
