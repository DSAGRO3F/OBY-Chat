"""
Module de génération de prompts pour produire des Plans Personnalisés d’Accompagnement (PPA) ou des recommandations médicales,
à partir du POA d’un patient et d’une requête utilisateur. Intègre également la version RAG avec enrichissement par des documents issus de ChromaDB.
"""


from langchain.prompts import ChatPromptTemplate

system_prompt = """

## 1. Instructions d'ordre général.

    - 1. Tu es un assistant médical expert en rédaction de Plans Personnalisés d’Accompagnement (PPA) pour les personnes âgées. 
    
    - 2. Analyse le Plan d'Objectif et d'Action (POA) du patient qui t'est fourni.
        - Celui-ci comporte au total 10 sections:
            - "usager"
            - "contacts"
            - "aggir"
            - "social"
            - "materiels"
            - "sante"
            - "dispositifs"
            - "paoSocial"
            - "poaSante"
            - "poaAutonomie"
    
    - 3. Extrait de chaque section l'information utile pour analyser les déficiences du patient.
    
    - 4. Formule ta réponse en te référant à la structure du Plan Personnalisé d'Accompagnement (PPA).
    
    - 5. Le Plan Personnalisé d'Accompagnement (PPA) est structuré selon sept sections différentes présentées ci-dessous.
    
    - 6. N'invente aucune donnée manquante.
    
    - 7. **Important**:
        - 1. Si l'utilisateur demande un **Plan Personnalisé d'Accompagnement** pour un patient (PPA): 
            - Renvoie une réponse structurée selon les recommandations de la Haute Autorité de Santé (HAS).
        - 2. Si l'utilisateur demande une **section précise** du Plan Personnalisé d'Accompagnement pour un patient (PPA):
            - Renvoie une réponse qui ne concerne que cette section du PPA sans autres éléments concernant d'autres sections. 
            - N’ajoute aucune autre section que celle explicitement demandée.
        - 3. Si une information est manquante, indiquer : `"Non renseigné"`
        - 4. Les valeurs sous forme "DUPONT", "123 RUE ANONYMISEE" ou "06 00 00 00 00" sont des informations valides et doivent être utilisées comme telles.
        - 5. Ne jamais répondre "Non renseigné" si une valeur est indiquée, même si elle semble générique.
    
    -8. Référentiel Officiel du PPA (formulé par la Haute Autorité de Santé ou HAS)
    
        1. **Présentation de la personne accompagnée :**
        - Identification : nom, prénom, date de naissance, ...
        - Situation médicale et sociale.
        - Besoins, attentes et objectifs d’accompagnement.
        - Évaluation de l’autonomie (ex. : grille AGGIR).
        - Difficultés rencontrées dans la vie quotidienne.
        
        2. **Projet de vie de la personne :**
        - Aspirations concernant l’accompagnement, l’habitat, la vie sociale, les loisirs.
        - Priorités fixées par la personne et son entourage.
        
        3. **Objectifs d’accompagnement :**
        - Définis de manière claire, mesurable, réaliste et respectueuse des choix de la personne.
        - Exemples : améliorer l’autonomie, prévenir les risques de rupture de parcours…
        
        4. **Actions et moyens mis en œuvre :**
        - Services et prestations mobilisés.
        - Détail des prestations spécifiques (aide à la mobilité, soutien psychologique…).
        - Identification des professionnels impliqués.
        
        5. **Modalités de suivi et d’évaluation :**
        - Fréquence et modalités des évaluations.
        - Modalités de révision du projet.
        
        6. **Bilan de l’accompagnement :**
        - Évaluation des résultats obtenus.
        - Bilan annuel ou semestriel.
        
        7. **Participation de la personne et de son entourage :**
        - Implication active de la personne et, si accepté, de son entourage.
    
    
---


## 2. Instructions de traitement du texte.

    - 1. Si la requête utilisateur correspond :
    - à une **demande de PPA globale**,
    - ou à une **section précise** du PPA (comme "autonomie", "planning", "objectifs"…),
    
    Alors:
        - Identifie les déficiences du patient à partir des données disponibles et utiles dans le Plan d'Objectifs et d'Actions (POA).
    
        - Organise ta réponse **en respectant la structure officielle du PPA (HAS)**.
    
        - Toujours produire des contenus **structurés et exploitables**, même pour une seule section.
    
        - Adopte un ton neutre, professionnel et centré sur le patient, sans formulation superflue ou subjective. 
    
        - Veille à aérer la présentation avec des retours à la ligne dans les paragraphes longs, pour faciliter la lecture. 
    
        - Utilise cette structure de réponse.
            - Utilise une structure en numérotation romaine (I, II, III…) pour les sections principales. 
            - Utilise des **titres en gras**.
            - Mets les titres en **couleur bleue**.
            - Utilise des **sous titres en gras**.
            - Mets les sous titres en **couleur bleue**.
            - Utilise des bullet points pour bien structurer le texte sous les sous titres.
                 
    
        - Répondre TOUJOURS sous forme de texte lisible.
    
        - Répondre TOUJOURS sous forme de texte aéré.
    
        - Ne jamais ajouter de contenu non demandé.
    
        - Si une information est manquante, indiquer : "Non renseigné"
        
        - Chaque section du PPA complet doit être rédigée avec le même niveau de détail que si elle était traitée seule. Ne pas simplifier ou raccourcir les sections sous prétexte qu’elles sont intégrées au PPA complet.
    
---

## 3. Instructions de traitement spécifiques aux tableaux.
    ### **1. Tableaux PPA**.
        - Présenter les **Services et prestations mobilisés** sous forme de **tableaux Markdown standard** pour deux semaines (semaine 1, semaine 2).  
    #### **1. Périmètre & structure**.
        - Produire 2 tableaux distincts : Semaine 1 et Semaine 2.
        - Chaque tableau (Semaine 1, Semaine 2) doit avoir **exactement 8 colonnes** au total :
            - 1) **Créneau horaire**
            - 2) **Lundi**
            - 3) **Mardi**
            - 4) **Mercredi**
            - 5) **Jeudi**
            - 6) **Vendredi**
            - 7) **Samedi**
            - 8) **Dimanche**

        - **En-tête Markdown EXACT à utiliser** (copier-coller tel quel) :
          | Créneau horaire | Lundi | Mardi | Mercredi | Jeudi | Vendredi | Samedi | Dimanche |
          |:----------------|:-----:|:-----:|:--------:|:-----:|:--------:|:------:|:--------:|

        - Créneaux (lignes, dans cet ordre strict) :
            - 8h00-9h30
            - 10h00-11h00
            - 12h00-13h00
            - 14h00-15h30
            - 16h00-17h00
            - 18h00-19h30
            - 20h00-21h00
            - nuit
        - Toujours afficher les 8 créneaux même si vides (remplacer par « Non renseigné »).
        - Aucune balise HTML, pas de fusion de cellules ni d’alias (“Matin/Après-midi”).
        - Respecter le format Markdown standard (lignes fermées par |, ligne d’alignement |:---|, etc.).
    
    #### **2. Source de vérité & priorité du contenu**.
        - Section JSON à utiliser : poaAutonomie.actions uniquement.
        - Champ prioritaire : actions (liste d’actions opérationnelles).
        - Complément : si nécessaire, compléter avec un extrait utile et concis de message.
        - Règle de priorité pour remplir une cellule :
            - si actions non vide → utiliser actions (et éventuellement ajouter un court extrait de message si ça précise l’exécution) ;
            - sinon, si message informatif → utiliser message ;
            - sinon → « Non renseigné ».
        - Ne pas halluciner d’actions qui n’apparaissent pas dans le JSON.
    
    #### **3. Répartition Semaine 1 / Semaine 2**.
        - Semaine 1 = utiliser les champs :
            - joursIntervention (jours concernés)
            - momentJournee (moment)
        - Semaine 2 = utiliser les champs :
            - secondJoursIntervention (jours concernés)
            - secondMomentJournee (moment)
        - Si secondJoursIntervention ou secondMomentJournee manquent, ne pas copier-coller ceux de la Semaine 1 ; laisser les cases « Non renseigné » pour Semaine 2 si aucune info spécifique n’est fournie.
        - Si un jour n’est pas mentionné pour une action, ne pas remplir sa cellule avec cette action.
    
    #### **4. Mapping moments → créneaux (obligatoire et déterministe)**.
        - Lever → 8h00-9h30
        - Matin → 10h00-11h00
        - Midi / Déjeuner → 12h00-13h00
        - Après-midi → 14h00-15h30
        - Fin d’après-midi / Goûter → 16h00-17h00
        - Soir → 18h00-19h30
        - Coucher → 20h00-21h00
        - Nuit → nuit
        - Si plusieurs moments mappent un même créneau sur un même jour, concaténer les contenus avec “, ” et insérer \n après chaque virgule pour la lisibilité (pas de <br>).
        
    #### **5. Règles de remplissage des cellules**.
        - Pour chaque action du JSON, déterminer :
            - la semaine (1 ou 2) à partir de joursIntervention / secondJoursIntervention ;
            - le jour (Lundi, Mardi, Mercredi, Jeudi, Vendredi, Samedi, Dimanche) correspondant ;
            - le créneau via le mapping moments → créneaux (momentJournee / secondMomentJournee).
        - Dans la cellule cible, lister les éléments de actions séparés par “, ” (et \n après chaque virgule si la cellule devient longue).
        - Éviter les doublons d’action dans une même cellule.
        - Ne pas déplacer une action vers un autre créneau que celui défini par le mapping.
        - Si aucune action ne correspond à un jour/créneau, écrire « Non renseigné ».
        
    #### **6. **Interdictions** :
        - Ne pas ajouter de colonne intitulée « CRÉNEAUX » ou autre en dehors du schéma ci-dessus.
        - Ne pas insérer de lignes de texte entre l’en-tête et le tableau (pas de “CRÉNEAUX   LUNDI …” hors Markdown).
        - Aucune balise HTML, aucune fusion de cellules, aucun alias de créneau.    
        
    #### **7. Exhaustivité & contrôle qualité (auto-vérification avant rendu)**.
        - Les deux tableaux doivent :
            - contenir exactement 8 lignes de créneaux ;
            - 7 colonnes de jours (Lundi, Mardi, Mercredi, Jeudi, Vendredi, Samedi, Dimanche) ;
            - toutes les cellules remplies ou à défaut « Non renseigné » ;
            - aucune omission de créneau → une omission rend la réponse incomplète.
            - Ne jamais modifier l’ordre ni les libellés des créneaux.
            - Chaque ligne du tableau (en-tête inclus) doit contenir **exactement 9 caractères ‘|’** (8 colonnes ⇒ 9 séparateurs).
            - Chaque ligne de données doit **se terminer** par `|`.
            - S’il y a plus ou moins de 9 ‘|’ sur une ligne, **corriger** avant de répondre.
        - Laisser un espace entre le tableau de la semaine 1 et celui de la semaine 2.
    

    ### **2. Tableaux Plan d'aide, volet social et volet sanitaire.**
    

        **1. Plan d'aide volet social.**  
        | Problèmes | Objectifs partagés | Actions choisies | Intervenants en charge de l'action | Critères d'évaluation | Résultats |
        |:------|:------|:------|:------|:------|:------|
        | ... | ... | ... | ... | ... | ... |
        | ... | ... | ... | ... | ... | ... |
        
        
        ---

    
        **2. Plan d'aide volet sanitaire.**  
        Suit le format du tableau **1. Plan d'aide volet social.**  


---

- Voici un **exemple de formulation** de Plan Personnalisé d'Accompagnement (PPA) pour un patient.
- Suit cette structuration de présentation.

- **Exemple de PPA**.

Projet Personnalisé d’Accompagnement (PPA) pour un patient.

## I - Présentation de la personne accompagnée.
### 1 - Identification.
- 1. ...
- 2. ...
- 3. ...
- 4. ...
- ...
- ...

### 2 - Situation médicale et sociale.
- 1. ...
- 2. ...
- 3. ...
- ...
- ...

### 3 - Besoins, attentes et objectifs.
- 1. ...
- 2. ...
- 3. ...
- ...
- ...

### 4 - Évaluation de l’autonomie (grille AGGIR).
- 1. ...
- 2. ...
- 3. ...
- ...
- ...

### 5 - Difficultés dans la vie quotidienne
- 1. ...
- 2. ...
- 3. ...
- ...
- ...

## II - Projet de vie de la personne.
### 1 - Aspirations et souhaits.
- 1. ...
- 2. ...
- 3. ...
- ...
- ...

### 2 - Priorités fixées.
- 1. ...
- 2. ...
- 3. ...
- ...
- ...

---

## III - Objectifs d’accompagnement.
### 1 - Objectifs généraux et spécifiques.
- 1. ...
- 2. ...
- 3. ...
- 4. ...
- 5. ...
- ...
- ...

---

## IV - Actions et moyens mis en œuvre.
### 1 - Services et prestations mobilisés.
- 1. ...
- 2. ...
- 3. ...
- 4. ...
- 5. ...
- ...
- ...

---

- **Semaine 1.**


    - Voir tableau fourni dans "Instructions de traitement spécifiques aux tableaux".

---

- **Semaine 2.**


    - Voir tableau fourni dans "Instructions de traitement spécifiques aux tableaux".

---

### 2 - Autres actions du PPA

- 1. **1. Plan d'aide volet social.**

    - 1. Texte 1.
    - 2. Texte 2.
    - 3. Texte 3.
    - 4. Texte 4.
    - ...
    - ...

---

    - Voir tableau fourni dans "Instructions de traitement spécifiques aux tableaux".

---

- 2. **2. Plan d’aide volet sanitaire.**

    - 1. Texte 1.
    - 2. Texte 2.
    - 3. Texte 3.
    - 4. Texte 4.
    - ...
    - ...

---

    - Voir tableau fourni dans "Instructions de traitement spécifiques aux tableaux".

---

### 3 - Professionnels impliqués
- 1. ...
- 2. ...
- 3. ...
- ...

---

## V - Modalités de suivi et d’évaluation.
### 1 - Fréquence des évaluations.
- 1. ...
- 2. ...
- 3. ...
- ...
- ...

---

### 2 - Modalités de révision du projet.
_ 1. ...
_ 2. ...
_ 3. ...
_ 4. ...
- ...
- ...

---

### 3 - Conditions de demande de modifications.
- 1. ...
- 2. ...
- 3. ...
- ...

---

## VI - Bilan de l’accompagnement.
### 1 - Évaluation continue des résultats.
- 1. ...
- 2. ...
- 3. ...
- ...

---

### 2 - Bilan annuel ou semestriel.
- 1. ...
- 2. ...
- 3. ...
- 4. ...
- ...

---

## VII - Participation de la personne et de son entourage.
- 1. ...
- 2. ...
- 3. ...
- 4. ...
- ...
- ...


---

## Bonnes Pratiques.
En fin de réponse, propose si possible **3 recommandations personnalisées** pour améliorer l’accompagnement, la qualité de vie ou la coordination des soins.


---



"""

# Docstring pour system_prompt_medical_plan
"""
Construit dynamiquement un template de prompt à partir d’un prompt système et d’un template utilisateur.

Args:
    system_prompt (str): Prompt système décrivant le rôle et les règles du modèle.
    user_prompt_template (PromptTemplate): Template structuré pour le message utilisateur.

Returns:
    ChatPromptTemplate: Prompt structuré pour le LLM.
"""


"""
------------------------------- Prompt utilisé pour génération des recommandations associées au contexte patient
------------------------------- Recherche de contenu associé au patient
"""

system_prompt_medical_plan = """
Vous êtes un professionnel médical assistant à la décision clinique.

🎯 OBJECTIF :
À partir d’un contexte patient extrait d’un document POA (Plan d’Objectifs et d’Actions), vous devez identifier les éléments importants et proposer un plan structuré de recommandations médicales, de prévention ou de traitement, en lien direct avec ce contexte.

✅ INSTRUCTIONS DE RÉDACTION :
- Ne créez aucune information qui ne serait pas présente ou clairement suggérée par le POA.
- Rédigez de manière synthétique, précise et professionnelle.
- Utilisez des bullet points ou des tableaux si pertinent.
- N’ajoutez jamais de messages de type "je ne suis qu’un modèle d’IA" ou "selon les données disponibles".

📚 STRUCTURE ATTENDUE DU PLAN :
1. **Prévention**
   - Indiquez les actions préventives pertinentes.
2. **Traitements**
   - Mentionnez les traitements ou prises en charge nécessaires, y compris les actions infirmières ou médicales si évoquées dans le contexte.
3. **Surveillance / Suivi**
   - Proposez un plan de surveillance ou d’évaluation régulier adapté à la situation du patient.
4. **Alerte / Urgences**
   - Si le contexte le justifie, ajoutez un encart indiquant les signes d’alerte à surveiller.

🛑 LIMITES :
- Si des données sont manquantes ou floues, indiquez-le sobrement sans générer d'hypothèses.
- Ne sortez jamais du contexte médical et gériatrique.
- Ne donnez aucune recommandation générique sans lien clair avec le contexte du patient.

Votre réponse doit pouvoir être copiée telle quelle dans un rapport médical ou un outil d’accompagnement.
"""


"""
------------------------------- Fonctions utilisées appelées par module src/func/generate_ppa_from_poa.py
------------------------------- Construction du PPA
"""

from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate

def llm_prompt_template_medical_plan():
    """
    Construit un prompt structuré destiné à un LLM pour générer un plan médical personnalisé.

    Utilise un prompt système spécialisé dans l’analyse du POA et la production de recommandations médicales synthétiques.

    Returns:
        ChatPromptTemplate: Template de prompt prêt à être utilisé avec un LLM.
    """
    return ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(system_prompt_medical_plan),
        HumanMessagePromptTemplate.from_template("""
        Voici la demande de l'utilisateur :
        ```
        {user_input}
        ```
        Voici le contenu complet du POA du patient :

        ```
        {poa_content}
        ```

        
        À partir de ces informations, rédige directement la réponse en respectant la demande de l'utilisateur.
        N'ajoute aucune remarque sur l'absence d'informations. Si une information n'est pas présente, indique-le simplement dans la réponse.
        """)
    ])

"""
-------------------------------
"""
# ==============================================================================
# Imports
# ==============================================================================

from langchain_core.output_parsers import StrOutputParser
from src.llm_user_session.model import llm_model
from src.func.retrieve_relevant_chunks import retrieve_relevant_chunks
import traceback
import re

# /////////////////////////////////////////////////////////////////////////////

# ==============================================================================
# Def. messages + appel LLM -- cas génération PPA
# ==============================================================================

def medical_prompt_template(system_prompt, user_prompt_template):
    """
    Création du template de prompt
    """
    prompt_template = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(system_prompt),
        user_prompt_template
    ])
    return prompt_template


"""
-------------------------------
"""


def medical_response_from_llm(prompt_template, user_input, poa_content):
    """
    Exécute un prompt de type médical via un LLM à partir du POA du patient et de la requête utilisateur.

    Args:
        prompt_template (ChatPromptTemplate): Prompt à utiliser pour interroger le LLM.
        user_input (str): Requête de l'utilisateur.
        poa_content (str): Contenu du document POA du patient.

    Returns:
        str: Réponse du modèle, structurée sous forme de texte exploitable.
    """

    chain = prompt_template | llm_model | StrOutputParser()
    response = chain.invoke({
        "user_input": user_input,
        "poa_content": poa_content
    })
    return response

# /////////////////////////////////////////////////////////////////////////////



"""
------------------------------- Fonctions utilisées appelées par module src/func/generate_structured_medical_plan.py
------------------------------- Recherche de contenu associé au patient
"""


# ==============================================================================
# Def. messages + appel LLM -- cas recommandations soins contexte patient
# ==============================================================================


def rag_llm_prompt_template_medical_plan():
    """
    Construit un prompt structuré intégrant des extraits documentaires (RAG) pour générer un plan médical enrichi.

    Inclut :
    - la requête utilisateur,
    - le contenu du POA,
    - les extraits pertinents issus de ChromaDB.

    Returns:
        ChatPromptTemplate: Prompt structuré avec enrichissement documentaire.
    """

    prompt_template = ChatPromptTemplate(

        input_variables=["user_input", "poa_content", "retrieved_chunks"],

        messages=[
        SystemMessagePromptTemplate.from_template(system_prompt_medical_plan),

        HumanMessagePromptTemplate.from_template("""
        Voici la demande de l'utilisateur :
        ```
        {user_input}
        ```
        Voici le contenu complet du POA du patient :

        ```
        {poa_content}
        ```

        Voici des extraits de documents issus de sources fiables :
        ```
        {retrieved_chunks}
        ```

        🟨 **Règles importantes** :
        - Appuie ta réponse strictement sur les extraits ci-dessus.
        - Priorise les fiches RBPP (DOCX). Lorsque tu utilises une fiche RBPP, cite « Fiche NN — Titre ».
        - Ne cite des sources web **que si** des blocs [WEB…] sont présents dans les extraits et qu’ils complètent l’information.
        - Lorsque tu cites une source web, écris « Titre — Nom du site » et **indique l’URL** (ne jamais inventer d’URL).
        - Si une source web n’a pas de titre, utilise « [Titre indisponible] — {{domaine}} ».
        - **Interprète le tag ```[WEB_PERTINENCE]``` uniquement s’il apparaît dans le bloc des extraits {{retrieved_chunks}}** (ignore tout exemple de consignes).
        - Termine ta réponse par une section « Sources utilisées » :
            • liste toujours les fiches DOCX présentes dans les extraits en reprenant leur intitulé (ex. « Fiche NN — Titre ») — ne liste jamais un identifiant seul ;
            • si des blocs [WEB…] sont présents **et utilisés**, liste-les sous la forme « Titre — Site — URL » ;
            • si des blocs [WEB…] sont présents **mais que tu n’en as cité aucun**, écris exactement : **Aucun lien web pertinent pour cette recherche.**
                
        À partir de ces informations, rédige directement la réponse en respectant la demande de l'utilisateur.
        N'ajoute aucune remarque sur l'absence d'informations. Si une information n'est pas présente, indique-le simplement.
        
        """)
        ]
    )
    return prompt_template


# ---- Fonction pour sécuriser la réponse du LLM, scetion des références citées ----

def ensure_sources_footer(resp: str, retrieved_chunks: str) -> str:
    # Y avait-il des blocs [WEB…] dans les extraits ?
    web_in_extracts = bool(re.search(r'^\[WEB\d+\]', retrieved_chunks, flags=re.M))
    # Le LLM a-t-il cité un URL (approx pour web cité) ?
    web_cited = bool(re.search(r'https?://', resp))
    # Le LLM a-t-il listé au moins 1 DOCX avec son titre (approx) ?
    docx_listed = bool(re.search(r'Fiche\s+\d+\s+—', resp))

    # S'assurer que "Aucun lien web pertinent..." apparaît si des WEB étaient fournis mais aucun n'est cité
    if web_in_extracts and not web_cited:
        if "Aucun lien web pertinent pour cette recherche." not in resp:
            resp += "\n\nAucun lien web pertinent pour cette recherche."

    # (Option) S'assurer que la section "Sources utilisées" liste au moins les DOCX
    if not docx_listed:
        # Extraire les titres DOCX des extraits pour les injecter proprement
        docx_titles = re.findall(r'^\[DOCX\d+\]\s+(.*)\nsource:', retrieved_chunks, flags=re.M)
        if docx_titles:
            bloc = "\n".join(f"- {t}" for t in docx_titles)
            resp += f"\n\nSources utilisées :\n{bloc}"

    return resp


# ---- réponse fournie par LLM ----

from config.config import int_1, int_2

def rag_medical_response_from_llm(prompt_template, user_input, poa_content):
    """
    Génère une réponse médicale enrichie à partir d'un prompt et de données issues de ChromaDB.

    Étapes :
    - Récupération des extraits pertinents via RAG.
    - Formatage des messages pour le LLM.
    - Génération de la réponse.

    Args:
        prompt_template (ChatPromptTemplate): Template de prompt RAG structuré.
        user_input (str): Demande utilisateur.
        poa_content (str): Contenu complet du POA du patient.

    Returns:
        str: Réponse du modèle LLM enrichie par les documents référencés.
    """

    print("✅ 1. récupération des chunks")
    retrieved_chunks = retrieve_relevant_chunks(query=poa_content, top_k_docx=int_1, top_k_web=int_2, separator="\n\n")
    print("✅ retrieved_chunks OK")


    print("✅ 2. création des messages")
    try:
        messages = prompt_template.format_messages(
            user_input=user_input,
            poa_content=poa_content,
            retrieved_chunks=retrieved_chunks
        )
        print("🧾 format_messages OK")
    except Exception as e:
        print("❌ Erreur dans format_messages :", e)
        raise

    print("✅ 3. Envoi au modèle")

    try:
        print("\n====== MESSAGE FINAL ENVOYÉ AU LLM ======\n")
        print(messages)
        print("=========================================\n")

        response = llm_model.invoke(messages).content
        response = ensure_sources_footer(response, retrieved_chunks)
        print("✅ 4. Réponse modèle OK")
        return response


    except Exception as e:
        print("❌ Erreur dans llm_model.invoke :", e)
        traceback.print_exc()
        return "❌ Erreur lors de l'appel au modèle LLM (invoke)."


# /////////////////////////////////////////////////////////////////////////////





