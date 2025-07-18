"""
Module de conversion de fiches documentaires DOCX en fichiers JSON exploitables.

Ce module permet d’extraire le contenu textuel structuré de fichiers Word (.docx)
présents dans un répertoire donné, et de les convertir en dictionnaires JSON.
Ces JSON sont ensuite utilisés dans l’application OBY-IA pour l’indexation
et la recherche sémantique de recommandations.

Fonctionnalités :
- Lecture et traitement de fichiers `.docx`.
- Nettoyage et normalisation du contenu.
- Export en fichiers `.json` avec le même nom de base.
"""


import os
import json
import re
from docx import Document
from datetime import datetime
from pathlib import Path
# INPUT_DOCX directory des fichiers docx à traiter, JSON_HEALTH_DOC_BASE directory de sortie des fichiers après traitement.
from config.config import INPUT_DOCX, JSON_HEALTH_DOC_BASE



def convert_fiches_docx_to_json(INPUT_DOCX):
    """
    Convertit toutes les fiches DOCX d’un répertoire en dictionnaires JSON.

    Parcourt les fichiers `.docx` du dossier spécifié, extrait leur contenu
    sous forme de paragraphes structurés, puis les formate en paires
    (titre, contenu) dans une liste de dictionnaires.

    Args:
        input_dir (str) : Chemin vers le répertoire contenant les fichiers DOCX.

    Returns:
        List[Dict[str, str]] : Liste de dictionnaires contenant les textes extraits
        de chaque fiche, prêts à être sauvegardés ou indexés.
    """
    print(f"📥 Étape 2 - Lecture du fichier : {INPUT_DOCX}")

    try:
        doc = Document(INPUT_DOCX)
    except Exception as e:
        print(f"❌ Erreur d'ouverture du fichier {INPUT_DOCX} : {type(e).__name__} - {e}")
        return []

    full_text = "\n".join([para.text.strip() for para in doc.paragraphs if para.text.strip()])

    fiche_pattern = r"(Fiche(?:\s+(?:Recommandation|arbre\s+décisionnel))?\s+0*\d{1,3})"
    split_points = [m.start() for m in re.finditer(fiche_pattern, full_text, flags=re.IGNORECASE)]
    split_points.append(len(full_text))

    fiches = []
    for i in range(len(split_points) - 1):
        bloc = full_text[split_points[i]:split_points[i + 1]].strip()

        match_id = re.match(r"Fiche(?:\s+(?:Recommandation|arbre\s+décisionnel))?\s+0*(\d{1,3})", bloc, re.IGNORECASE)
        fiche_id = match_id.group(1).zfill(3) if match_id else f"{i:03d}"

        titre_match = re.search(r"Fiche(?:\s+(?:Recommandation|arbre\s+décisionnel))?\s+0*\d{1,3}\s*[-:]?\s*(.+)", bloc, re.IGNORECASE)
        titre = titre_match.group(1).strip() if titre_match else f"Fiche {fiche_id}"

        print(f"✅ Fiche détectée : ID={fiche_id} | Titre={titre}")

        fiche = {
            "fiche_id": fiche_id,
            "titre": titre,
            "type_document": "recommendation_structured",
            "source_doc": os.path.basename(INPUT_DOCX),
            "date_indexation": datetime.today().strftime("%Y-%m-%d"),
            "texte_complet": bloc
        }
        fiches.append(fiche)

    return fiches




def save_fiches_to_json(fiches, JSON_HEALTH_DOC_BASE):
    """
    Sauvegarde une liste de fiches au format JSON dans un répertoire donné.

    Crée un fichier `.json` pour chaque fiche, nommé à partir de son titre,
    dans le dossier de destination spécifié.

    Args:
        fiches (List[Dict[str, str]]) : Liste de dictionnaires représentant les fiches.
        JSON_HEALTH_DOC_BASE (str) : Répertoire où sauvegarder les fichiers JSON.
    """
    print('appel fonction save_fiches_to_json (step 3)...')

    for fiche in fiches:
        filename = f"fiche_{fiche['fiche_id']}.json"
        filepath = os.path.join(JSON_HEALTH_DOC_BASE, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(fiche, f, ensure_ascii=False, indent=2)



def convert_and_save_fiches(INPUT_DOCX, JSON_HEALTH_DOC_BASE):
    """
    Convertit toutes les fiches DOCX d’un répertoire et les enregistre au format JSON.

    Enchaîne les étapes de traitement :
        1. Lecture et conversion des fichiers `.docx` en dictionnaires.
        2. Sauvegarde des résultats dans des fichiers `.json` individuels.

    Args:
        INPUT_DOCX (str) : Répertoire contenant les fichiers DOCX source.
        JSON_HEALTH_DOC_BASE (str) : Répertoire de destination des fichiers JSON générés.
    """
    print("📌 Étape 1 - Appel convert_and_save_fiches")
    fiches = convert_fiches_docx_to_json(INPUT_DOCX)

    if not fiches:
        print(f"⚠️ Aucune fiche extraite depuis {INPUT_DOCX}")
        return

    for fiche in fiches:
        fiche_id = fiche["fiche_id"]
        output_path = Path(JSON_HEALTH_DOC_BASE) / f"fiche_{fiche_id}.json"
        with open(output_path, "w", encoding="utf-8") as f:
            import json
            json.dump(fiche, f, indent=2, ensure_ascii=False)

    print(f"💾 {len(fiches)} fiches sauvegardées dans {JSON_HEALTH_DOC_BASE}")


if __name__ == "__main__":
    fiches = convert_fiches_docx_to_json(INPUT_DOCX)
    save_fiches_to_json(fiches, JSON_HEALTH_DOC_BASE)
    print(f"✔ {len(fiches)} fiches extraites et enregistrées dans '{JSON_HEALTH_DOC_BASE}'.")
