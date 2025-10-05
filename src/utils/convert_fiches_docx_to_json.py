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
import re
import json
from datetime import datetime
# INPUT_DOCX directory des fichiers docx à traiter, JSON_HEALTH_DOC_BASE directory de sortie des fichiers après traitement.
from config.config import INPUT_DOCX, JSON_HEALTH_DOC_BASE
from typing import Iterable, List, Union
from docx import Document
from pathlib import Path



def convert_fiches_docx_to_json(input_path: Union[str, Path]) -> List[dict]:
    """
    Convertit une OU plusieurs fiches DOCX en dictionnaires JSON.
    - Si `input_path` est un fichier .docx -> convertit ce fichier.
    - Si `input_path` est un dossier      -> parcourt tous les *.docx du dossier.
    """
    p = Path(input_path)

    if not p.exists():
        print(f"❌ Chemin introuvable : {p}")
        return []

    # Liste des .docx à traiter
    if p.is_file():
        if p.suffix.lower() != ".docx":
            print(f"⚠️ Fichier ignoré (pas .docx) : {p}")
            return []
        docx_files = [p]
    else:  # dossier
        docx_files = sorted(x for x in p.glob("*.docx") if x.is_file())
        if not docx_files:
            print(f"🟡 Aucun .docx trouvé dans {p}")
            return []

    all_fiches: List[dict] = []

    # --- logique de conversion pour UN .docx ---
    fiche_pattern = r"(Fiche(?:\s+(?:Recommandation|arbre\s+décisionnel))?\s+0*\d{1,3})"

    for docx_path in docx_files:
        print(f"✅ Lecture du fichier : {docx_path}")
        try:
            doc = Document(str(docx_path))
        except Exception as e:
            print(f"❌ Erreur d'ouverture du fichier {docx_path} : {type(e).__name__} - {e}")
            continue

        full_text = "\n".join([para.text.strip() for para in doc.paragraphs if para.text.strip()])

        split_points = [m.start() for m in re.finditer(fiche_pattern, full_text, flags=re.IGNORECASE)]
        split_points.append(len(full_text))

        for i in range(len(split_points) - 1):
            bloc = full_text[split_points[i]:split_points[i + 1]].strip()

            match_id = re.match(r"Fiche(?:\s+(?:Recommandation|arbre\s+décisionnel))?\s+0*(\d{1,3})", bloc, re.IGNORECASE)
            fiche_id = match_id.group(1).zfill(3) if match_id else f"{i:03d}"

            titre_match = re.search(
                r"Fiche(?:\s+(?:Recommandation|arbre\s+décisionnel))?\s+0*\d{1,3}\s*[-:]?\s*(.+)",
                bloc, re.IGNORECASE
            )
            titre = titre_match.group(1).strip() if titre_match else f"Fiche {fiche_id}"

            print(f"✅ Fiche détectée : ID={fiche_id} | Titre={titre}")

            # (facultatif mais utile pour l’indexation granulaire)
            paragraphs = [pp.strip() for pp in bloc.split("\n") if pp.strip()]
            subchunks, buf = [], ""
            for pp in paragraphs:
                if len(buf) + len(pp) + 1 > 1000:
                    subchunks.append(buf); buf = pp
                else:
                    buf = (buf + "\n" + pp) if buf else pp
            if buf:
                subchunks.append(buf)

            fiche = {
                "fiche_id": fiche_id,
                "titre": titre,
                "type_document": "recommendation_structured",
                "source_doc": docx_path.name,
                "date_indexation": datetime.today().strftime("%Y-%m-%d"),
                "texte_complet": bloc,
                "paragraphs": paragraphs,
                "subchunks_approx_1k": subchunks
            }
            all_fiches.append(fiche)

    return all_fiches




def save_fiches_to_json(fiches: list[dict], output_dir: str) -> None:
    """
    Sauvegarde une liste de fiches au format JSON dans un répertoire donné.

    Crée un fichier `.json` pour chaque fiche, nommé à partir de son titre,
    dans le dossier de destination spécifié.

    Args:
        fiches (List[Dict[str, str]]) : Liste de dictionnaires représentant les fiches.
        JSON_HEALTH_DOC_BASE (str) : Répertoire où sauvegarder les fichiers JSON.
    """
    print('appel fonction save_fiches_to_json...')

    output_dir = Path(output_dir)

    print(f"🟠 Vérification type 'output_dir': {type(output_dir)}")
    output_dir.mkdir(parents=True, exist_ok=True)


    written: list[str] = []
    for fiche in fiches:
        # fiche_id sûr et zéro-paddé
        fid = str(fiche.get("fiche_id", "000")).zfill(3)
        output_path = output_dir / f"fiche_{fid}.json"
        print(f"🟠 Vérification type 'output_dir': {type(output_path)}")

        # On écrit dans un .tmp puis on remplace
        tmp_path = output_path.with_suffix(".json.tmp")
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(fiche, f, indent=2, ensure_ascii=False)
        os.replace(tmp_path, output_path)

        written.append(str(output_path))

    print(f"🟢 {len(written)} fiches sauvegardées dans {output_dir}")
    return



PathLike = Union[str, Path]
def convert_and_save_fiches(input_dir: PathLike, output_dir: PathLike) -> None:
    """
    Convertit des fiches DOCX en JSON et les enregistre.
    - Si `input_path` est un fichier .docx -> convertit ce fichier.
    - Si `input_path` est un dossier      -> parcourt tous les *.docx

    Enchaîne les étapes de traitement :
        1. Lecture et conversion des fichiers `.docx` en dictionnaires.
        2. Sauvegarde des résultats dans des fichiers `.json` individuels.

    Args:
        INPUT_DOCX (str) : Répertoire contenant les fichiers DOCX source.
        JSON_HEALTH_DOC_BASE (str) : Répertoire de destination des fichiers JSON générés.
    """

    input_path = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Déterminer la liste des fichiers à traiter
    if input_path.is_file():
        if input_path.suffix.lower() != ".docx":
            print(f"⚠️ Fichier ignoré (pas .docx): {input_path}")
            return
        docx_files: List[Path] = [input_path]

    elif input_path.is_dir():
        docx_files = sorted(p for p in input_path.glob("*.docx") if p.is_file())
        if not docx_files:
            print(f"🟡 Aucun .docx trouvé dans {input_path}")
            return
    else:
        print(f"🔴 Chemin introuvable: {input_path}")
        return

    total_fiches = 0
    for f in docx_files:
        try:
            print(f"✅ Lecture du fichier : {f}")
            fiches = convert_fiches_docx_to_json(str(f))  # ← convertit UN .docx
            if not fiches:
                print("🟠 Aucune fiche extraite (conversion vide).")
                continue

            # logs utiles (facultatif): afficher quelques IDs/titres si tu veux
            # for fiche in fiches[:3]:
            #     print(f"  ↳ fiche id={fiche.get('id')} | titre={fiche.get('titre')!r}")

            save_fiches_to_json(fiches, str(output_dir))
            total_fiches += len(fiches)

        except Exception as e:
            # on log l'erreur mais on continue avec les autres fichiers
            print(f"🔴 Erreur conversion {f.name}: {type(e).__name__}: {e}")

    print(f"🟢 {total_fiches} fiches sauvegardées dans {output_dir}")




if __name__ == "__main__":
    convert_and_save_fiches(INPUT_DOCX, JSON_HEALTH_DOC_BASE)
    print(f"✔ Conversion terminée vers '{JSON_HEALTH_DOC_BASE}'.")
