"""
Initialisation des modèles de langage utilisés dans l'application OBY-IA.

Ce module charge les clés API depuis le fichier `.env` et instancie un modèle
de langage compatible avec LangChain, en fonction de la configuration disponible.

Actuellement :
- Le modèle `ChatOpenAI` (GPT-4.1) est utilisé par défaut, en raison de la limitation
  de tokens rencontrée avec Mistral lors du traitement de documents volumineux.
- Le modèle `ChatMistralAI` reste présent en commentaire à des fins de test ou migration future.

Variables :
    llm_model : Instance unique du modèle LLM utilisé pour répondre aux requêtes utilisateur.
"""

from langchain_mistralai import ChatMistralAI # import ChatMistralAI class
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv

load_dotenv()  # Charge le fichier .env

open_ai_api_key = os.getenv("OPENAI_API_KEY")
print(f"Clé API chargée ? {'✅' if open_ai_api_key else '❌'}")

mistral_api_key = os.getenv("MISTRAL_API_KEY")
print(f"Clé API chargée ? {'✅' if mistral_api_key else '❌'}")



# Pb: POA + réponse LLM > 53K tokens -> triop pour mistral ==> migre vers chatgpt 4.o
# Instance unique du modèle mistral
# llm_model = ChatMistralAI(
#     model='mistral-large-latest',
#     api_key=os.environ.get('MISTRAL_API_KEY'),
#     temperature=0
# )




# Instance unique du modèle chatgpt
llm_model = ChatOpenAI(
    model="gpt-4.1-2025-04-14",
    temperature=0.0,
    max_tokens=16000,
    api_key=open_ai_api_key,
)
