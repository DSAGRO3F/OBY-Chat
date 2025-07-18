"""
Module de chargement des fichiers POA (Plan d’Objectifs et d’Actions) au format JSON.

Ce module permet de localiser et lire un fichier patient stocké dans le dossier `data/poa_patients/`.
"""



from pathlib import Path
import os
import json
import re
from typing import Dict, Any
from config.config import PATIENT_FILES_DIR

json_path = PATIENT_FILES_DIR/'DELOIN_ALAIN_24_04_2025.json'


def load_patient_file(json_path: str) -> Dict[str, Any]:
    """
    Charge un fichier POA au format JSON.

    Args:
        json_path (str): Chemin absolu ou relatif vers le fichier JSON du patient.

    Returns:
        dict: Contenu du fichier JSON, sous forme de dictionnaire Python.
    """

    with open(json_path, 'r', encoding='utf-8-sig') as f:
        data = json.load(f)

    # print("✅ Chargement du document terminé.")
    # print("🔍 Aperçu du JSON brut :", json.dumps(data, indent=2, ensure_ascii=False)[:1000])

    return data




















