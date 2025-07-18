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
        "élaborer un ppa", "plan personnalisé"
    ],
    "get_constants": [
        "constantes", "tension", "poids", "température", "fréquence cardiaque", "graphique",
        "affiche les constantes", "évolution", "valeurs biologiques"
    ],
    "generate_recommendations": [
        "conduite à tenir", "prise en charge", "recommandations", "quoi faire", "traitement",
        "agir", "soins à apporter", "prévention", "risque", "urgence", "aide pour un cas",
        "prise de décision", "avis médical", "diagnostic"
    ],
}

# ⚖️ Priorité des intentions (plus haut = plus prioritaire)
intent_priority = {
    "get_constants": 1,
    "generate_ppa": 2,
    "generate_recommendations": 3
}


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

    user_input_lower = user_input.lower().strip()

    # 🔍 Étape 1 : Recherche des intentions par mots-clés
    matched_intents = []
    for intent, keywords in intent_keywords.items():
        for keyword in keywords:
            if keyword in user_input_lower:
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
        user_input (str): Texte de l’utilisateur.
        llm (BaseLanguageModel, optional): Modèle à utiliser. Si None, un modèle local est chargé.

    Returns:
        IntentType: Intention détectée, ou "unknown".
    """
    if llm is None:
        llm = llm_model()

    # 🧾 Prompt système pour le classificateur d’intentions
    system_prompt = """
Tu es un classificateur d'intentions. Ton travail est de lire une phrase d'utilisateur et de déterminer l’intention parmi les choix suivants :
- generate_ppa
- get_constants
- generate_recommendations

Si aucune intention ne correspond, retourne "unknown".

Réponds uniquement avec le mot-clé de l’intention.
"""

    prompt = f"{system_prompt}\n\nPhrase utilisateur : {user_input}\n\nIntention :"

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
