"""
Module de détection du chemin du fichier patient.

Ce module fournit une fonction pour localiser automatiquement un fichier contenant les données
d’un patient, à partir de son nom, dans le dossier `src/data/poa_patients`.
"""

from config.config import PATIENT_FILES_DIR

def extract_relevant_info(patient_name: str) -> str | None:
    """
    Trouve un fichier patient (PDF, DOCX, json, etc.) dont le nom contient le nom du patient.

    Args :
        patient_name (str) : Nom du patient, ex : "Deloin"

    Returns :
        str | None : Chemin complet du fichier trouvé, sinon None
    """
    data_folder = PATIENT_FILES_DIR

    patient_name = patient_name.lower()

    for file in data_folder.iterdir():
        print(f"Comparaison : '{patient_name}' in '{file.stem.lower()}'")
        if file.is_file() and patient_name in file.stem.lower():
            print(f"✅ Fichier trouvé : {file.name}")
            print(f"Recherche de fichiers avec '{patient_name}' dans le chemin {file.stem}")
            return str(file.resolve())

    print(f"❌ Aucun fichier trouvé pour le patient {patient_name}")
    return None


