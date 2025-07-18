"""
Module d'anonymisation et de désanonymisation des données patient.

Ce module permet :
- d'anonymiser des champs sensibles dans une structure JSON (ex. : prénoms, adresses, contacts),
- de générer un dictionnaire de correspondance entre valeurs originales et anonymisées,
- de désanonymiser un texte produit à partir des données en réinjectant les valeurs originales.

L’anonymisation repose à la fois sur des règles dynamiques (ex. : prénom selon le sexe)
et sur des valeurs codées en dur (HARDCODED_VALUES).
"""




import re
from typing import Any, Dict, Tuple
from src.func.detect_genre import generate_prenom_from_sexe
from src.func.detect_genre import HARDCODED_VALUES



def _anonymize_dict(data: Any, mapping: Dict[str, str], path: str = "", parent_sexe: str = None) -> Any:
    """
    Fonction récursive interne pour anonymiser une structure JSON.

    Args:
        data (Any): Données JSON à traiter (dictionnaire, liste, ou valeur).
        mapping (Dict[str, str]): Dictionnaire des correspondances anonymisées.
        path (str, optional): Chemin courant dans la structure (pour les règles HARDCODED).
        parent_sexe (str, optional): Sexe hérité pour générer les prénoms si nécessaire.

    Returns:
        Any: Données anonymisées.
    """

    if isinstance(data, dict):
        result = {}
        # Détecter le sexe à ce niveau ou hériter
        sexe = data.get("sexe", parent_sexe)

        for key, value in data.items():
            new_path = f"{path}.{key}" if path else key

            # Anonymisation dynamique des prénoms selon le sexe
            if key in {"prenomsActeNaissance", "premierPrenomActeNaissance", "prenomUtilise"} and sexe:
                prenoms_dyn = generate_prenom_from_sexe(sexe)
                fake_prenom = prenoms_dyn.get(key, "Non renseigné")
                mapping[fake_prenom] = value if value is not None else "Non renseigné"
                result[key] = fake_prenom
            else:
                result[key] = _anonymize_dict(value, mapping, new_path, sexe)

        return result

    elif isinstance(data, list):
        return [
            _anonymize_dict(item, mapping, f"{path}[{i}]", parent_sexe)
            for i, item in enumerate(data)
        ]

    elif isinstance(data, str):
        # Exemple d'exclusion (date naissance usager) si tu veux le garder non anonymisé
        normalized_path = path.lower()
        if normalized_path == "usager.informations d'état civil.personnephysique.datenaissance":
            return data

        # HARDCODED_VALUES : anonymisation statique
        if path in HARDCODED_VALUES:
            anonymized = HARDCODED_VALUES[path]
            mapping[anonymized] = data
            return anonymized

        return data

    elif data is None:
        # Si HARDCODED_VALUES a une valeur même pour ce chemin
        if path in HARDCODED_VALUES:
            anonymized = HARDCODED_VALUES[path]
            mapping[anonymized] = "Non renseigné"
            return anonymized
        return data

    return data



def anonymize_fields(data: Any) -> Tuple[Any, Dict[str, str]]:
    """
    Anonymise une structure JSON complète.

    Cette fonction applique les règles d’anonymisation dynamiques et statiques,
    et retourne les données anonymisées avec leur dictionnaire de correspondance.

    Args:
        data (Any): Données JSON à anonymiser.

    Returns:
        Tuple[Any, Dict[str, str]]: Données anonymisées et mapping {valeur_anonymisée: valeur_originale}.
    """

    mapping = {}
    anonymized_data = _anonymize_dict(data, mapping)
    return anonymized_data, mapping


def deanonymize_fields(text: str, mapping: Dict[str, str]) -> Tuple[str, Dict[str, str]]:
    """
    Remplace dans un texte les valeurs anonymisées par leurs équivalents originaux.

    Args:
        text (str): Texte contenant des valeurs anonymisées.
        mapping (Dict[str, str]): Dictionnaire des correspondances anonymisées → originales.

    Returns:
        Tuple[str, Dict[str, str]]: Texte désanonymisé et dictionnaire utilisé.
    """

    print("🟣 Début désanonymisation")
    for anonymized, original in mapping.items():
        if original in ["None", None]:
            original = ""

        # Forcer str pour éviter des erreurs
        original = str(original)

        print(f"🔄 Remplacement : {anonymized} --> {original}")

        pattern = re.compile(re.escape(anonymized), flags=re.IGNORECASE)
        new_text, n_replacements = pattern.subn(original, text)

        if n_replacements > 0:
            print(f"✅ {n_replacements} remplacement(s) effectué(s) pour : {anonymized}")

        text = new_text

    print("🟣 Désanonymisation terminée")
    return text, mapping


