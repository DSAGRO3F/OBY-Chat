"""
Module pour l'extraction du nom du patient à partir d'une requête utilisateur.

Ce module utilise un LLM pour analyser une phrase en langage naturel
et en extraire uniquement le nom de famille du patient mentionné.
"""





from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from src.llm_user_session.model import llm_model


def extract_patient_name_llm(user_input):
    """
    Extrait le nom de famille du patient à partir d'une requête utilisateur en langage naturel.

    Utilise un modèle LLM pour identifier le nom de famille mentionné dans une phrase.
    Si aucun nom n’est détecté ou si plusieurs mots sont retournés, la fonction retourne `None`.

    Args:
        user_input (str): Phrase saisie par l’utilisateur.

    Returns:
        str | None: Nom du patient détecté (capitalisé), ou None si non détectable.
    """

    # TODO: Modifier NOM/VERSUS NOM + PRENOM
    pass


    template = """Tu es un extracteur de données.  
À partir de la phrase ci-dessous, tu dois EXTRAIRE UNIQUEMENT le nom de famille du patient, sans aucune autre phrase ni explication.

- Si tu trouves un nom, écris uniquement ce nom.
- Si aucun nom n'est trouvé, écris exactement : "Nom patient introuvable".

Phrase :
```
{phrase}
```


"""
    print(f'extract_patient_name/user_input: {user_input}')

    prompt_template = ChatPromptTemplate.from_template(template)
    prompt_value = prompt_template.format_messages(phrase=user_input)
    response = llm_model.invoke(prompt_value)
    result_text = response.content.strip()

    print(f"🟢 Nom détecté par le modèle : '{result_text}'")

    if "Nom patient introuvable" in result_text or len(result_text.split()) > 1:
        return None

    return result_text.capitalize()
