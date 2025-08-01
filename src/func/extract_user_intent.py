"""
Module extract_user_intent

Ce module permet de détecter l’intention principale d’un utilisateur à partir de sa requête textuelle.
La détection repose d’abord sur des correspondances par mots-clés, puis bascule sur un modèle de langage
(LLM) si aucune correspondance directe n’est trouvée.

Modifications apportées :
- Ajout d’une hiérarchie de priorité dans la détection par mots-clés pour résoudre les ambiguïtés.
- Ajout de docstrings conformes à la PEP 257.
- Refactorisation avec étapes explicites et commentaires clairs.
"""

from typing import Dict, Literal
from langchain_core.language_models import BaseLanguageModel
from src.llm_user_session.model import llm_model


IntentType = Literal["generate_ppa", "get_constants", "generate_recommendations", "unknown"]

# 🔑 Mots-clés associés à chaque intention
intent_keywords = {
    "generate_ppa": [
        "plan d'accompagnement", "ppa", "générer un ppa", "objectifs et actions", "proposer un plan",
        "élaborer un ppa", "plan personnalisé", "préparer le plan", "faire un plan pour le patient",
        "créer un plan", "rédiger le plan", "plan à mettre en place", "plan à faire",
        "prévois un accompagnement", "plan du patient", "mettre en place le suivi",
        "organiser le plan de soins", "définir un plan", "construire le plan"
    ],

    "get_constants": [
        "constantes", "tension", "poids", "température", "fréquence cardiaque", "graphique",
        "affiche les constantes", "évolution", "valeurs biologiques", "données de santé",
        "historique médical", "voir les courbes", "montre moi les constantes", "valeurs mesurées",
        "graphique du patient", "état de santé", "résumé médical", "suivi des constantes",
        "affiche les mesures", "statistiques de santé", "courbe de poids", "tendance médicale"
    ],

    "generate_recommendations": [
        "conduite à tenir", "prise en charge", "recommandations", "quoi faire", "traitement",
        "agir", "soins à apporter", "prévention", "risque", "urgence", "aide pour un cas",
        "prise de décision", "avis médical", "diagnostic", "que faire", "quelle démarche suivre",
        "comment réagir", "que dois-je faire", "orientation médicale", "décision médicale",
        "protocole à suivre", "réponse adaptée", "conseils de soins", "suggestion d’action",
        "mesures à prendre", "plan d’action à suivre"
    ]
}

# ⚖️ Priorité des intentions (plus haut = plus prioritaire)
intent_priority = {
    "get_constants": 1,
    "generate_ppa": 2,
    "generate_recommendations": 3
}


# Fonction de normalisation du texte
import unicodedata
import re

def normalize_text(text: str) -> str:
    """
    Nettoie et standardise une chaîne de texte en français pour faciliter la détection d’intention.

    Étapes :
    - Passage en minuscules
    - Remplacement des apostrophes typographiques
    - Suppression des accents
    - Suppression des caractères non alphanumériques utiles
    - Nettoyage des espaces multiples

    Args:
        text (str): Texte à normaliser

    Returns:
        str: Texte nettoyé et standardisé
    """
    if not text:
        return ""

    # Minuscule
    text = text.lower()

    # Uniformisation des apostrophes et caractères typographiques
    text = text.replace("’", "'").replace("‘", "'").replace("`", "'")

    # Suppression des accents (ex : é → e)
    text = ''.join(
        c for c in unicodedata.normalize('NFD', text)
        if unicodedata.category(c) != 'Mn'
    )

    # Suppression des caractères spéciaux inutiles sauf apostrophes et chiffres
    text = re.sub(r"[^a-z0-9' ]", " ", text)

    # Remplacement des espaces multiples par un seul
    text = re.sub(r"\s+", " ", text)

    # Trim final
    return text.strip()



def detect_user_intent(user_input: str) -> Dict[str, str]:
    """
    Détecte l’intention de l’utilisateur à partir de sa requête textuelle.

    La fonction effectue :
    1. Une détection par mots-clés avec hiérarchie de priorité si plusieurs intentions sont détectées.
    2. Un fallback par modèle de langage (LLM) si aucune correspondance n’est trouvée.

    Args:
        user_input (str): Requête utilisateur.

    Returns:
        dict: Dictionnaire contenant une seule clé "intent" avec l’une des valeurs suivantes :
              "generate_ppa", "get_constants", "generate_recommendations", ou "unknown".
    """
    if not user_input:
        return {"intent": "unknown"}

    user_input_norm = normalize_text(user_input)

    # 🔍 Étape 1 : Recherche des intentions par mots-clés
    matched_intents = []
    for intent, keywords in intent_keywords.items():
        for keyword in keywords:
            if keyword in user_input_norm:
                matched_intents.append(intent)
                break  # Un seul mot-clé suffit à activer une intention

    # ⚖️ Étape 2 : Sélection de l’intention dominante par priorité
    if matched_intents:
        selected_intent = max(matched_intents, key=lambda i: intent_priority[i])
        print(f"🔍 Intention détectée par mot-clé : {selected_intent}")
        return {"intent": selected_intent}

    # 🧠 Étape 3 : Fallback – classification via LLM
    print("🧠 Aucune correspondance simple trouvée, appel au LLM pour classification...")
    response = llm_intent_classification(user_input)

    # ✅ Vérification du résultat du LLM
    if response in intent_priority:
        return {"intent": response}

    print("⚠️ Intention non reconnue après passage au LLM.")
    return {"intent": "unknown"}



def llm_intent_classification(user_input: str, llm: BaseLanguageModel = None) -> IntentType:
    """
    Utilise un modèle de langage (LLM) pour inférer l’intention utilisateur si aucun mot-clé ne correspond.

    Args:
        user_input (str): Requête de l’utilisateur.
        llm (BaseLanguageModel, optional): Modèle LLM. Si None, le modèle par défaut est utilisé.

    Returns:
        IntentType: Intention détectée ("generate_ppa", "get_constants", "generate_recommendations", ou "unknown").
    """
    if llm is None:
        llm = llm_model

    # 🔧 Prompt système renforcé pour guider le modèle
    system_prompt = """
Tu es un assistant expert en classification d’intentions pour une application appelée OBY-IA.

L’utilisateur peut écrire en langage naturel comme s’il s’adressait à ChatGPT. Ta tâche est de lire sa requête et de déterminer l’intention principale à déclencher.

Voici les intentions disponibles :

- generate_ppa : si l’utilisateur veut générer un Plan Personnalisé d’Accompagnement (PPA) à partir d’un document patient.
- get_constants : si l’utilisateur veut afficher les constantes médicales (ex : tension, température, poids, fréquence cardiaque, graphiques…).
- generate_recommendations : si l’utilisateur veut obtenir des recommandations médicales, une conduite à tenir, un traitement, ou savoir comment agir.
- unknown : si la requête est trop floue ou ne correspond à aucun de ces cas.

Tu dois répondre **uniquement** avec le mot-clé correspondant, sans ponctuation, sans phrase, sans commentaire.

Exemples valides : generate_ppa / get_constants / generate_recommendations / unknown

Phrase utilisateur :
{user_input}

Intention :
""".strip()

    prompt = system_prompt.format(user_input=user_input.strip())

    try:
        response = llm.invoke(prompt).content.strip().lower()
        print(f"🤖 Intention détectée via LLM : {response}")
        return response if response in intent_priority else "unknown"
    except Exception as e:
        print(f"⚠️ Erreur LLM dans la détection d’intention : {e}")
        return "unknown"








# ==================================================
# Code insuffisant pour détection intention correcte
# ==================================================
# def llm_intent_classification(user_input: str, llm: BaseLanguageModel = None) -> IntentType:
#     """
#     Utilise un modèle de langage (LLM) pour inférer l’intention utilisateur si aucun mot-clé ne correspond.
#
#     Args:
#         user_input (str): Texte de l’utilisateur.
#         llm (BaseLanguageModel, optional): Modèle à utiliser. Si None, un modèle local est chargé.
#
#     Returns:
#         IntentType: Intention détectée, ou "unknown".
#     """
#     if llm is None:
#         llm = llm_model
#
#     # 🧾 Prompt système pour le classificateur d’intentions
#     system_prompt = """
# Tu es un classificateur d'intentions. Ton travail est de lire une phrase d'utilisateur et de déterminer l’intention parmi les choix suivants :
# - generate_ppa
# - get_constants
# - generate_recommendations
#
# Si aucune intention ne correspond, retourne "unknown".
#
# Réponds uniquement avec le mot-clé de l’intention.
# """
#
#     prompt = f"{system_prompt}\n\nPhrase utilisateur : {user_input}\n\nIntention :"
#
#     try:
#         response = llm.invoke(prompt).content.strip().lower()
#         print(f"🤖 Intention détectée via LLM : {response}")
#         return response if response in intent_priority else "unknown"
#     except Exception as e:
#         print(f"⚠️ Erreur LLM dans la détection d’intention : {e}")
#         return "unknown"
#





# ==================================================
# Code insuffisant pour détection intention correcte
# ==================================================
# IntentType = Literal["generate_ppa", "get_constants", "generate_recommendations", "unknown"]
#
# # ✅ Dictionnaire de mots-clés associés à chaque intention
# intent_keywords = {
#     "generate_ppa": [
#         "plan d'accompagnement", "ppa", "générer un ppa", "objectifs et actions", "proposer un plan",
#         "élaborer un ppa", "plan personnalisé"
#     ],
#     "get_constants": [
#         "constantes", "tension", "poids", "température", "fréquence cardiaque", "graphique",
#         "affiche les constantes", "évolution", "valeurs biologiques"
#     ],
#     "generate_recommendations": [
#         "conduite à tenir", "prise en charge", "recommandations", "quoi faire", "traitement",
#         "agir", "soins à apporter", "prévention", "risque", "urgence", "aide pour un cas",
#         "prise de décision", "avis médical", "diagnostic"
#     ],
# }
#
#
# def detect_user_intent(user_input: str) -> Dict[str, str]:
#     """
#     Détecte l’intention de l’utilisateur à partir de sa requête.
#
#     Effectue d'abord une recherche par mots-clés, puis utilise un LLM si aucune correspondance n’est trouvée.
#
#     Args:
#         user_input (str): Requête de l’utilisateur sous forme de texte.
#
#     Returns:
#         dict: Dictionnaire contenant une clé "intent" avec la valeur correspondante.
#               Exemple : {"intent": "get_constants"}
#     """
#     if not user_input:
#         return {"intent": "unknown"}
#
#     user_input_lower = user_input.lower()
#
#     # 🔍 Étape 1 : Matching par mots-clés simples
#     for intent, keywords in intent_keywords.items():
#         for keyword in keywords:
#             if keyword in user_input_lower:
#                 print(f"🔍 Intention détectée par mot-clé : {intent}")
#                 print(f'✔️type for intent output: {type(intent)}')
#                 return {"intent": intent}
#
#     # 🔍 Étape 2 : Fallback – classification LLM
#     print("🧠 Aucune correspondance simple trouvée, appel au LLM pour classification...")
#     response = llm_intent_classification(user_input)
#
#     if response is None:
#         print("⚠️ Le LLM n’a retourné aucune intention. Valeur None interceptée.")
#         return {"intent": "unknown"}
#
#     if response in ["generate_ppa", "get_constants", "generate_recommendations"]:
#         return {"intent": response}
#
#     print(f'type for intent output: {type(response)}')
#
#     return {"intent": "unknown"}
#
#
# def llm_intent_classification(user_input: str, llm: BaseLanguageModel = None) -> IntentType:
#     """
#     Utilise un LLM pour inférer l'intention quand aucun mot-clé ne correspond.
#
#     Args:
#         user_input (str): Message de l'utilisateur.
#         llm (BaseLanguageModel, optional): Modèle LangChain. Par défaut = modèle local.
#
#     Returns:
#         IntentType: Intention inférée.
#     """
#     if llm is None:
#         llm = llm_model()
#
#     system_prompt = """
# Tu es un classificateur d'intentions. Ton travail est de lire une phrase d'utilisateur et de déterminer l’intention parmi les choix suivants :
# - generate_ppa
# - get_constants
# - generate_recommendations
#
# Si aucune intention ne correspond, retourne "unknown".
#
# Réponds uniquement avec le mot-clé de l’intention.
# """
#     prompt = f"{system_prompt}\n\nPhrase utilisateur : {user_input}\n\nIntention :"
#
#     try:
#         response = llm.invoke(prompt).content.strip().lower()
#         print(f"🤖 Intention détectée via LLM : {response}")
#         if response in ["generate_ppa", "get_constants", "generate_recommendations"]:
#             return response  # type: ignore
#     except Exception as e:
#         print(f"⚠️ Erreur LLM dans la détection d'intention : {e}")
#
#     return "unknown"
