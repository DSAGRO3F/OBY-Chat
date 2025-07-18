"""
Module de conversion des données JSON d'un POA en texte structuré pour LLM.

Ce module extrait les informations pertinentes du dictionnaire JSON d’un plan
d’objectifs et d’actions (POA), notamment les données de la personne accompagnée,
ses contacts et les différentes sections thématiques (social, santé, autonomie).
Il génère un texte lisible destiné à être injecté dans un prompt pour un modèle LLM.

Utilisé pour formater proprement les données en amont d’une génération automatique
de synthèse ou de recommandations.
"""



from typing import Dict, Any, List

def convert_json_to_text(data: Dict[str, Any]) -> str:
    """
        Convertit un dictionnaire JSON représentant les données du POA en texte structuré pour le LLM.

        Cette fonction extrait les informations clés de la section "usager" du JSON (nom, prénom, sexe,
        date de naissance, situation familiale, adresse, contacts) et les formate sous forme de lignes de texte.
        Elle remplace les valeurs manquantes ou nulles par "Non renseigné" pour éviter des trous dans l'affichage.

        Args:
            data (Dict[str, Any]): Données du POA sous forme de dictionnaire JSON.

        Returns:
            str: Texte structuré prêt à être envoyé au LLM, avec les informations de présentation de la personne.

        Exemple de sortie :
            ### Présentation de la personne accompagnée
            - Nom : Dupont
            - Prénom : Jeanne
            - Sexe : Féminin
            - Date de naissance : 1945-09-15
            - Situation familiale : Veuve
            - Adresse : 10 avenue des Lilas, 02100 Saint Quentin
            - Tel. domicile : 0170872230
            - Tel. mobile : Non renseigné
            - Courriel : contact@example.org
        """

    lines = []

    # --- Présentation de la personne ---
    usager = data.get("usager", {})
    infos = usager.get("Informations d'état civil", {}).get("personnePhysique", {})
    adresse = usager.get("adresse", {})
    contact = usager.get("contactInfosPersonnels", {})
    print("🔍 Contact dans convert_json_to_text INITIALISATION :", contact)

    lines.append("### Présentation de la personne accompagnée")
    nom_famille = infos.get('nomFamille')
    lines.append(f"- Nom : {nom_famille if nom_famille else 'Non renseigné'}")

    prenom = infos.get('prenomUtilise')
    lines.append(f"- Prénom : {prenom if prenom else 'Non renseigné'}")

    sexe = infos.get('sexe')
    lines.append(f"- Sexe : {sexe if sexe else 'Non renseigné'}")

    date_naissance = infos.get('dateNaissance')
    lines.append(f"- Date de naissance : {date_naissance if date_naissance else 'Non renseigné'}")

    situation_famille = infos.get('situationFamiliale')
    lines.append(f"- Situation familiale : {situation_famille if situation_famille else 'Non renseigné'}")

    adresse_ligne = " ".join(filter(None, adresse.get("ligne", []))) or "Non renseigné"
    code_postal = adresse.get("codePostal", "Non renseigné")
    commune = adresse.get("libelleCommune", "Non renseigné")
    lines.append(f"- Adresse : {adresse_ligne}, {code_postal} {commune}")

    tel_domicile = contact.get('domicile')
    lines.append(f"- Tel. domicile : {tel_domicile if tel_domicile else 'Non renseigné'}")

    tel_mobile = contact.get('mobile')
    lines.append(f"- Tel. mobile : {tel_mobile if tel_mobile else 'Non renseigné'}")

    mail = contact.get('mail')
    lines.append(f"- Courriel : {mail if mail else 'Non renseigné'}")

    # --- Contacts ---
    contacts = usager.get("contacts", [])
    lines.append("\n### Contacts identifiés")
    for i, c in enumerate(contacts):
        nom = f"{c.get('prenom', '')} {c.get('nom', '')}".strip()
        roles = f"{c.get('lienParente', '')}, {c.get('role', '')}".strip(', ')
        lines.append(f"- Contact {i+1} : {nom} ({roles})")
        lines.append(f"  - Téléphone : {c.get('telephone', 'Non renseigné')}")
        lines.append(f"  - Email : {c.get('email', 'Non renseigné')}")

    # --- Blocs POA ---
    for section_name in ["poaSocial", "poaSante", "poaAutonomie"]:
        section = data.get(section_name, {})
        problemes = section.get("problemes", [])
        if problemes:
            lines.append(f"\n## Section {section_name}")
        for bloc in problemes:
            lines.append("\n---")
            lines.append(f"### 🧹 Bloc POA : {bloc.get('nomBloc', 'Inconnu')} (Statut : {bloc.get('statut', 'Inconnu')})")

            lines.append("#### Problème posé")
            lines.append(bloc.get("problemePose", "Non renseigné"))

            lines.append("\n#### Objectifs visés")
            lines.append(bloc.get("objectifs", "Non renseigné"))

            lines.append("\n#### Actions proposées")
            for action in bloc.get("planActions", []):
                lines.append(f"- **Action :** {action.get('nomAction', 'Non renseigné')}  ")
                lines.append(f"  **Responsable :** {action.get('personneChargeAction', 'Non renseigné')}  ")
                # Tu peux enrichir ici avec date, récurrence, etc. si besoin

    print(f"🔍 Contact dans convert_json_to_text : {contact}")

    return "\n".join(lines)
