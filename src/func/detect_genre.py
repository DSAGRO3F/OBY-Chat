"""
Module de génération de prénoms anonymisés à partir du sexe renseigné.

Ce module permet de produire des prénoms fictifs cohérents avec le sexe (masculin, féminin ou inconnu)
dans le cadre d’un processus d’anonymisation de données personnelles.
Il inclut également des valeurs codées en dur pour compléter des structures anonymisées.
"""



from unidecode import unidecode
from typing import Dict, Any, List


HARDCODED_VALUES = {
    "usager.Informations d'état civil.personnePhysique.situationFamiliale": "marié",
    "usager.Informations d'état civil.personnePhysique.nomFamille": "Durand",
    "usager.Informations d'état civil.personnePhysique.nomUtilise": "Durand",

    "usager.adresse.ligne[0]": "10 avenue des Lilas",
    "usager.adresse.codePostal": "02100",
    "usager.adresse.libelleCommune": "Saint Quentin",
    "usager.adresse.commentaire": "Accès : null",

    "usager.contactInfosPersonnels.domicile": "0170872230",
    "usager.contactInfosPersonnels.mobile": "0622446530",
    "usager.contactInfosPersonnels.mail": "contact@example.org",

    "contacts[0].personnePhysique.nomUtilise": "Martin",
    "contacts[0].personnePhysique.prenomUtilise": "Claire",
    "contacts[0].personnePhysique.dateNaissance": "1975-01-01",
    "contacts[0].adresse.ligne[0]": "5 rue des Cerisiers",
    "contacts[0].contactInfosPersonnels.domicile": "0601020304",
    "contacts[0].contactInfosPersonnels.mail": "claire.martin@example.com"
}


def generate_prenom_from_sexe(sexe: str) -> Dict[str, str]:

    """
    Génère un prénom fictif en fonction du sexe spécifié.

    Args:
        sexe (str): Valeur du sexe (ex. : "masculin", "féminin", ou autre).

    Returns:
        dict: Dictionnaire contenant trois champs :
            - "prenomsActeNaissance"
            - "premierPrenomActeNaissance"
            - "prenomUtilise"

        Les prénoms sont choisis pour correspondre au sexe indiqué ou être neutres si le sexe est inconnu.
    """

    sexe_normalized = (sexe or "").strip().lower()
    if sexe_normalized == "masculin":
        return {
            "prenomsActeNaissance": "Jean Baptiste",
            "premierPrenomActeNaissance": "Jean",
            "prenomUtilise": "Jean"
        }
    elif sexe_normalized == "féminin":
        return {
            "prenomsActeNaissance": "Anne Eugénie",
            "premierPrenomActeNaissance": "Anne",
            "prenomUtilise": "Anne"
        }
    else:
        # Si sexe inconnu, prénom neutre
        return {
            "prenomsActeNaissance": "Alex Morgan",
            "premierPrenomActeNaissance": "Alex",
            "prenomUtilise": "Alex"
        }
