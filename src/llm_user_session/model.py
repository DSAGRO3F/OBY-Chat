"""
Module de configuration du modèle LLM pour l'application OBY-IA.

Ce module initialise un modèle de langage basé sur les clés API disponibles dans
les variables d'environnement. L'ordre de priorité est le suivant :
    1. OpenAI (ChatOpenAI) en fallback si Mistral n'est pas disponible
    2. Mistral (ChatMistralAI)


Il gère la sécurisation via des blocs try/except afin d'éviter un plantage en cas
d'erreur d'initialisation (clé manquante, modèle indisponible, etc.). Tous les
événements importants sont journalisés via le module standard `logging`.

Attributs:
    llm_model (ChatMistralAI | ChatOpenAI | None):
        Instance unique du modèle de langage, ou None si aucune initialisation
        n'a pu être réalisée.
"""

import os
import logging
from dotenv import load_dotenv
from langchain_mistralai import ChatMistralAI
from langchain_openai import ChatOpenAI

# --- Configuration du logger ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# --- Chargement des variables d'environnement ---
load_dotenv()

open_ai_api_key = os.getenv("OPENAI_API_KEY")
mistral_api_key = os.getenv("MISTRAL_API_KEY")

logger.info(f"Clé API OpenAI chargée ? {'✅' if open_ai_api_key else '❌'}")
logger.info(f"Clé API Mistral chargée ? {'✅' if mistral_api_key else '❌'}")

# --- Initialisation du modèle ---
llm_model = None

try:
    if open_ai_api_key:
        llm_model=ChatOpenAI(
            model="gpt-4.1",
            api_key=open_ai_api_key,
            temperature=0,
            max_tokens=10000,
        )
        logger.info("✅ Modèle OpenAI initialisé avec succès.")
    elif mistral_api_key:
        llm_model = ChatMistralAI(
            model="mistral-large-2407",
            api_key=mistral_api_key,
            temperature=0,
            max_tokens=10000,
        )

        logger.warning("⚠️ Pas de clé PenAI, utilisation du modèle Mistral.")
    else:
        logger.error("❌ Aucune clé API trouvée (ni Mistral ni OpenAI). Impossible d’initialiser un modèle.")

except Exception as e:
    logger.exception("❌ Erreur lors de l’instanciation du modèle : %s", str(e))
    llm_model = None



