# src/api/routes/poa_patients.py
"""
Module API pour la gestion des dossiers patients POA dans OBY-IA.

Ce module expose plusieurs endpoints sécurisés pour :
    - Lister les fichiers patients disponibles.
    - Lire un dossier patient au format JSON.
    - Créer un nouveau dossier patient.
    - Mettre à jour un dossier patient existant.
    - Supprimer un dossier patient.

Seuls les utilisateurs authentifiés disposant des droits d'édition
(actuellement : `admin`) peuvent effectuer ces opérations.

Endpoints :
    GET    /patients           → Liste les fichiers patients.
    GET    /patients/{file}    → Retourne le contenu JSON d’un patient.
    POST   /patients           → Crée un nouveau dossier patient.
    PUT    /patients/{file}    → Met à jour un dossier patient existant.
    DELETE /patients/{file}    → Supprime un dossier patient.

Sécurité :
    Les appels nécessitent les en-têtes HTTP :
        X-User-Id    : identifiant utilisateur
        X-Session-Id : identifiant de session obtenu via /auth/login
"""

import os
import json
import re
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Header, Depends
from pydantic import BaseModel, Field

from src.llm_user_session.session_manager_instance import session_manager_instance
from config.config import PATIENT_FILES_DIR
router = APIRouter()

# ---------- Modèles ----------
class PatientData(BaseModel):
    """Modèle Pydantic pour les mises à jour de dossier patient."""
    content: dict = Field(..., description="Contenu JSON complet du dossier patient")

class CreatePatientRequest(BaseModel):
    """Modèle Pydantic pour la création d'un nouveau dossier patient."""
    filename: str = Field(..., description="Nom du fichier .json à créer (ex: DUPONT_JEAN_2025-01-20.json)")
    content: dict = Field(..., description="Contenu JSON du dossier patient")

# ---------- Utilitaires FS ----------
_FILENAME_RE = re.compile(r"^[A-Za-z0-9_\-\.]+\.json$")

def ensure_data_dir():
    """Crée le répertoire de stockage des patients s’il n’existe pas."""
    os.makedirs(PATIENT_FILES_DIR, exist_ok=True)

def validate_filename(filename: str) -> str:
    """
        Valide que le nom de fichier est conforme et retourne le nom validé.

        Args:
            filename (str): Nom du fichier .json à valider.

        Returns:
            str: Nom de fichier validé.

        Raises:
            HTTPException: Si le nom de fichier est invalide.
        """
    if not _FILENAME_RE.match(filename or ""):
        raise HTTPException(status_code=400, detail="Nom de fichier invalide. Utilisez un .json sans chemin.")
    return filename

def fs_path_for(filename: str) -> str:
    """
        Retourne le chemin absolu pour un fichier patient donné.

        Args:
            filename (str): Nom de fichier patient.

        Returns:
            str: Chemin absolu vers le fichier.
        """
    ensure_data_dir()
    safe = validate_filename(filename)
    return os.path.join(PATIENT_FILES_DIR, safe)

# ---------- Sécurité via session ----------
def require_editor_session(
    x_user_id: str = Header(..., alias="X-User-Id"),
    x_session_id: str = Header(..., alias="X-Session-Id"),
):
    """
    Retourne le chemin absolu pour un fichier patient donné.

    Args:
        filename (str): Nom de fichier patient.

    Returns:
        str: Chemin absolu vers le fichier.
    """
    if not x_user_id or not x_session_id:
        raise HTTPException(status_code=401, detail="En-têtes X-User-Id / X-Session-Id requis.")

    session = session_manager_instance.get_session(x_session_id)
    if not session or session.get("user_id") != x_user_id:
        raise HTTPException(status_code=401, detail="Session invalide ou expirée.")

    # Autorisation simple: seul admin a les droits d'édition
    if x_user_id != "admin":
        raise HTTPException(status_code=403, detail="Droits insuffisants pour cette opération.")

    return True

# ---------- Endpoints ----------
@router.get("/patients", response_model=List[str], dependencies=[Depends(require_editor_session)])
def list_patients():
    """
    Retourne la liste des fichiers patients (.json) disponibles.

    Returns:
        List[str]: Liste triée des noms de fichiers patients.

    Raises:
        HTTPException: Si le répertoire patient est introuvable.
    """
    ensure_data_dir()
    try:
        return sorted([f for f in os.listdir(PATIENT_FILES_DIR) if f.endswith(".json")])
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Répertoire patient introuvable.")

@router.get("/patients/{filename}", dependencies=[Depends(require_editor_session)])
def get_patient(filename: str):
    """
    Retourne le contenu JSON d’un dossier patient.

    Args:
        filename (str): Nom du fichier patient.

    Returns:
        dict: Contenu JSON du dossier patient.

    Raises:
        HTTPException: Si le fichier n’existe pas ou si le JSON est invalide.
    """
    path = fs_path_for(filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Fichier patient introuvable.")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Fichier JSON invalide.")

@router.post("/patients", dependencies=[Depends(require_editor_session)])
def create_patient(req: CreatePatientRequest):
    """
    Crée un nouveau fichier patient.

    Args:
        req (CreatePatientRequest): Modèle contenant le nom et le contenu du dossier.

    Returns:
        dict: Statut de création.

    Raises:
        HTTPException: Si le fichier existe déjà ou en cas d'erreur d'écriture.
    """
    path = fs_path_for(req.filename)
    if os.path.exists(path):
        raise HTTPException(status_code=409, detail="Le fichier existe déjà.")
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(req.content, f, ensure_ascii=False, indent=2)
        return {"status": "success", "message": f"✅ Fichier {req.filename} créé."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'écriture: {e}")

@router.put("/patients/{filename}", dependencies=[Depends(require_editor_session)])
def update_patient(filename: str, data: PatientData):
    """
    Met à jour le contenu d’un dossier patient existant.

    Args:
        filename (str): Nom du fichier patient.
        data (PatientData): Contenu JSON à sauvegarder.

    Returns:
        dict: Statut de mise à jour.

    Raises:
        HTTPException: Si le fichier n’existe pas ou en cas d'erreur d'écriture.
    """
    path = fs_path_for(filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Fichier patient introuvable.")
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data.content, f, ensure_ascii=False, indent=2)
        return {"status": "success", "message": f"✅ Fichier {filename} mis à jour."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'écriture: {e}")

@router.delete("/patients/{filename}", dependencies=[Depends(require_editor_session)])
def delete_patient(filename: str):
    """
    Supprime un fichier patient.

    Args:
        filename (str): Nom du fichier patient à supprimer.

    Returns:
        dict: Statut de suppression.

    Raises:
        HTTPException: Si le fichier n’existe pas ou en cas d'erreur de suppression.
    """
    path = fs_path_for(filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Fichier patient introuvable.")
    try:
        os.remove(path)
        return {"status": "success", "message": f"🗑️ Fichier {filename} supprimé."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la suppression: {e}")
