"""
Module de génération de prénoms anonymisés à partir du sexe renseigné.

Ce module permet de produire des prénoms fictifs cohérents avec le sexe (masculin, féminin ou inconnu)
dans le cadre d’un processus d’anonymisation de données personnelles.
Il inclut également des valeurs codées en dur pour compléter des structures anonymisées.
"""



from unidecode import unidecode
from typing import Dict, Any, List


HARDCODED_VALUES = {
    "usager.Informations d'état civil.clientId": "non renseigné",
    "usager.Informations d'état civil.personnePhysique.nomFamille": "Durand",
    "usager.Informations d'état civil.personnePhysique.prenomsActeNaissance": "Louis",
    "usager.Informations d'état civil.personnePhysique.premierPrenomActeNaissance": "Louis",
    "usager.Informations d'état civil.personnePhysique.nomUtilise": "Durand",
    "usager.Informations d'état civil.personnePhysique.prenomUtilise": "Louis",
    "usager.Informations d'état civil.personnePhysique.communeNaissance.libelleCommune": "Versailles",
    "usager.Informations d'état civil.personnePhysique.communeNaissance.codePostal": "78000",
    "usager.Informations d'état civil.personnePhysique.communeNaissance.inseeCommune": "78000",
    "usager.Informations d'état civil.personnePhysique.paysNaissance.libellePays": "France",
    "usager.Informations d'état civil.personnePhysique.paysNaissance.inseePays": "75000",
    "usager.Informations d'état civil.personnePhysique.situationFamiliale": "Non renseigné",

    "usager.adresse.ligne[0]": "10 avenue des Lilas",
    "usager.adresse.codePostal": "02100",
    "usager.adresse.libelleCommune": "Saint Quentin",
    "usager.adresse.commentaire": "Accès : null",

    "usager.contactInfosPersonnels.domicile": "non renseigné",
    "usager.contactInfosPersonnels.mobile": "non renseigné",
    "usager.contactInfosPersonnels.mail": "contact@societe.org",

    "usager.mouvement.service": "null",
    "usager.mouvement.secteur": "null",

    "contacts[0].typeContact": "Cercle d'aide et de soin",
    "contacts[0].personnePhysique.civilite": "Mme",
    "contacts[0].personnePhysique.nomUtilise": "Thierry",
    "contacts[0].personnePhysique.prenomUtilise": "Sabine",
    "contacts[0].personnePhysique.dateNaissance": "1960-01-15",

    "contacts[0].adresse.ligne[0]": "5 rue des Cerisiers",
    "contacts[0].adresse.codePostal": "13000",
    "contacts[0].adresse.libelleCommune": "Marseille",

    "contacts[0].contactInfosPersonnels.domicile": "null",
    "contacts[0].contactInfosPersonnels.mail": "sabine.thierry@example.com",
    "contacts[0].contactInfosPersonnels.mobile": "null",

    "contacts[0].titre": "Docteur",
    "contacts[0].role": "Médecin traitant",
    "contacts[0].numRpps": "null",
    "contacts[0].natureLien": "Médecin référent",
    "contacts[0].personneConfiance": "true",
    "contacts[0].responsableLegal": "false",

    "contacts[1].typeContact": "Cercle d'aide et de soin",
    "contacts[1].personnePhysique.civilite": "Mr",
    "contacts[1].personnePhysique.nomUtilise": "Durant",
    "contacts[1].personnePhysique.prenomUtilise": "Xavier",
    "contacts[1].personnePhysique.dateNaissance": "1960-01-15",

    "contacts[1].adresse.ligne[0]": "3 Allée des Roses",
    "contacts[1].adresse.codePostal": "13000",
    "contacts[1].adresse.libelleCommune": "Marseille",

    "contacts[1].contactInfosPersonnels.domicile": "null",
    "contacts[1].contactInfosPersonnels.mail": "xavier.durant@example.com",
    "contacts[1].contactInfosPersonnels.mobile": "null",

    "contacts[1].titre": "Monsieur",
    "contacts[1].role": "Ami proche",
    "contacts[1].numRpps": "null",
    "contacts[1].natureLien": "Ami",
    "contacts[1].personneConfiance": "false",
    "contacts[1].responsableLegal": "false",

    "contacts[2].typeContact": "Cercle d'aide et de soin",
    "contacts[2].personnePhysique.civilite": "Mme",
    "contacts[2].personnePhysique.nomUtilise": "Chatelier",
    "contacts[2].personnePhysique.prenomUtilise": "Sylvie",
    "contacts[2].personnePhysique.dateNaissance": "1990-01-15",

    "contacts[2].adresse.ligne[0]": "25 allée de la Loire",
    "contacts[2].adresse.codePostal": "45000",
    "contacts[2].adresse.libelleCommune": "Orléans",

    "contacts[2].contactInfosPersonnels.domicile": "null",
    "contacts[2].contactInfosPersonnels.mail": "sylvie.chatelier@example.com",
    "contacts[2].contactInfosPersonnels.mobile": "null",

    "contacts[2].titre": "Madame",
    "contacts[2].role": "Amie proche",
    "contacts[2].numRpps": "null",
    "contacts[2].natureLien": "Amie",
    "contacts[2].personneConfiance": "false",
    "contacts[2].responsableLegal": "false",

    "contacts[3].typeContact": "Entourage",
    "contacts[3].personnePhysique.civilite": "Mme",
    "contacts[3].personnePhysique.nomUtilise": "Papin",
    "contacts[3].personnePhysique.prenomUtilise": "Claire",
    "contacts[3].personnePhysique.dateNaissance": "1990-08-01",

    "contacts[3].adresse.ligne[0]": "2 Avenue des Cèdres",
    "contacts[3].adresse.codePostal": "49000",
    "contacts[3].adresse.libelleCommune": "Angers",

    "contacts[3].contactInfosPersonnels.domicile": "null",
    "contacts[3].contactInfosPersonnels.mail": "claire.papin@example.com",
    "contacts[3].contactInfosPersonnels.mobile": "null",

    "contacts[3].titre": "Madame",
    "contacts[3].role": "Amie proche",
    "contacts[3].numRpps": "null",
    "contacts[3].natureLien": "Amie",
    "contacts[3].personneConfiance": "true",
    "contacts[3].responsableLegal": "false",

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
