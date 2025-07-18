"""
Module de nettoyage des documents POA (Plan d’Objectifs et d’Actions).

Ce module filtre les champs non informatifs ou vides dans les fichiers JSON représentant
les données patients, afin de faciliter leur traitement en aval.
"""



import json
import re
from typing import Dict, Any
from pathlib import Path




def clean_patient_document(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Nettoie récursivement un document JSON de patient en supprimant les champs vides ou non pertinents.

    Args:
        data (Dict[str, Any]): Dictionnaire représentant le contenu brut du document POA.

    Returns:
        Dict[str, Any]: Dictionnaire nettoyé, sans les champs vides, "non renseigné", ou "null".
    """

    cleaned_data = {}

    # Clés à exclure
    excluded_sections = set()

    for key, value in data.items():
        if key in excluded_sections:
            continue
        if isinstance(value, str):
            if value.lower() in {"non renseigné", "", "null"}:
                continue
            cleaned_data[key] = value
        elif isinstance(value, dict):
            cleaned_sub = clean_patient_document(value)
            if cleaned_sub:
                cleaned_data[key] = cleaned_sub
        elif isinstance(value, list):
            cleaned_list = [clean_patient_document(v) if isinstance(v, dict) else v for v in value]
            cleaned_list = [v for v in cleaned_list if v not in [None, "", "non renseigné", "null"]]
            if cleaned_list:
                cleaned_data[key] = cleaned_list
        else:
            cleaned_data[key] = value

    # print("✅ Document nettoyé.")
    # print("🔍 Aperçu du document nettoyé :", json.dumps(cleaned_data, indent=2, ensure_ascii=False)[:1000])

    return cleaned_data



