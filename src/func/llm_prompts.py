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
        - Exemple de format :  
        - **Respecte exactement les plages horaires (8h00-9h30, 10h00-11h00, etc.) dans l’ordre donné.**
        - Si tu omets une plage horaire, la réponse est considérée comme incomplète.
        - Ne change pas la structure du tableau.

        **Semaine 1.**
        | Heure        | Lundi                            | Mardi                            | Mercredi                         | Jeudi                            | Vendredi                         | Samedi                           | Dimanche                         |
        |:-------------|:---------------------------------|:---------------------------------|:---------------------------------|:---------------------------------|:---------------------------------|:---------------------------------|:---------------------------------|
        | 8h00-9h30    | aide au lever, toilette complète | aide au lever, toilette complète | ...                              | ...                              | ...                              | ...                              | ...                              |
        | 10h00-11h00  | change, élimination, stimulation  | change, élimination, stimulation  | ...                              | ...                              | ...                              | ...                              | ...                              |
        | 12h00-13h00  | ...                              | ...                              | ...                              | ...                              | ...                              | ...                              | ...                              |
        | 14h00-15h30  | ...                              | ...                              | ...                              | ...                              | ...                              | ...                              | ...                              |
        | 16h00-17h00  | ...                              | ...                              | ...                              | ...                              | ...                              | ...                              | ...                              |
        | 18h00-19h30  | ...                              | ...                              | ...                              | ...                              | ...                              | ...                              | ...                              |
        | 20h00-21h00  | ...                              | ...                              | ...                              | ...                              | ...                              | ...                              | ...                              |
        | nuit         | ...                              | ...                              | ...                              | ...                              | ...                              | ...                              | ...                              |
    
        ---
        
        **Semaine 2.**
        Suit le format du tableau **Semaine 1.**     

    - Les **tableaux des services et prestations mobilisés** doivent obligatoirement **reprendre les plages horaires suivantes** pour chaque jour de la semaine :
      - 8h00-9h30
      - 10h00-11h00
      - 12h00-13h00
      - 14h00-15h30
      - 16h00-17h00
      - 18h00-19h30
      - 20h00-21h00
      - nuit

    - Chaque plage horaire doit apparaître **même si certaines cellules sont vides** (remplacer par "Non renseigné").
    
    - Ne pas regrouper ou fusionner les horaires (pas de "Matin", "Après-midi", etc.).
    
    - **Ces horaires doivent toujours être explicitement mentionnés dans le tableau final**.
        
    - Les tableaux doivent avoir un axe horizontal (jours de la semaine) et un axe vertical (heures de la journée).  
    
    - Mets dans les cellules les actions à faire pour chaque plage horaire du jour de la semaine.
    
    - Les contenus de cellule sont séparés par des virgules `,` ou points-virgules `;` pour énumérer plusieurs actions.
      
    - **Aucune balise `<br>` ni HTML** ne doit être insérée, les retours à la ligne sont remplacés par des séparateurs standards (`,` ou `;`). 
    
    - Pour améliorer la lisibilité, ajoute des retours à la ligne (\n) après chaque virgule dans les cellules longues. 
        
    - Les titres de colonnes (`|:---|`) doivent être présents et correctement alignés.  
    
    - Les tableaux doivent être parfaitement fermés par `|` à la fin de chaque ligne.
        
    - Laisser un espace entre les tableaux pour la clarté visuelle
    

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

        💡 **Instructions importantes** :
        - Appuie ta réponse sur les extraits ci-dessus.
        - **Mentionne dans ta réponse le numéro de fiche, le titre et/ou la source** chaque fois que tu utilises une information issue de ces documents.
        - **Si tu t’appuies sur un extrait en particulier, mentionne le titre et la source de l’extrait utilisé dans ta réponse.** 
        - Si aucune source ne correspond, indique-le clairement.
        
        À partir de ces informations, rédige directement la réponse en respectant la demande de l'utilisateur.
        N'ajoute aucune remarque sur l'absence d'informations. Si une information n'est pas présente, indique-le simplement dans la réponse.
        """)
    ])

    return prompt_template



"""
-------------------------------
"""


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

    print("📥 Étape 1 : récupération des chunks")
    retrieved_chunks = retrieve_relevant_chunks(query=poa_content, top_k_docx=5, top_k_web=3, separator="\n\n")
    print("🔍 retrieved_chunks OK")

    print("📥 Étape 2 : création des messages")
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

    print("📤 Envoi au modèle")

    try:
        print("\n====== MESSAGE FINAL ENVOYÉ AU LLM ======\n")
        print(messages)
        print("=========================================\n")

        response = llm_model.invoke(messages).content
        print("✅ Réponse modèle OK")
        return response

    except Exception as e:
        print("❌ Erreur dans llm_model.invoke :", e)
        traceback.print_exc()
        return "❌ Erreur lors de l'appel au modèle LLM (invoke)."


# /////////////////////////////////////////////////////////////////////////////






"génère le contenu initial de index.md, architecture.md et les fichiers agent.md, tools.md en fonction de mon projet"
"Prépare un docstring de module conforme à la norme PEP 257, en français, pour le fichier"

"Prépare un Plan Personnalisé d'Accompagnement du patient Deloin"
"Monsieur Deloin vient de faire une chute, donne moi la conduite à tenir"
"Fais une recherche sur le web concernant les points de vigilance à observer suite à un AVC"
"Prépare la section 1 du Plan Personnalisé d'Accompagnement du patient Deloin"
"Prépare la section 3 du Plan Personnalisé d'Accompagnement du patient Deloin"
"Affiche les constantes du patient Deloin"
"Prépare une synthèse du plan personnalisé d'accompagnement pour le patient Deloin"
"Fais une recherche sur les aides financières pour les patients GIR 4"

# Lanement Docker: reconstruction image + construction container
# 1. docker compose down
# 2. docker compose up --build ou docker compose build --no-cache
# 3. docker compose up

# Lancement site doc
# mkdocs serve

# Lancement construction site statique doc projet
# mkdocs build