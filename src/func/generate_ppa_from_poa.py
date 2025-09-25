"""
Module de génération de PPA (Plan Personnalisé d’Accompagnement) à partir d’un document POA.

Ce module extrait le nom du patient depuis la requête utilisateur, charge et nettoie le document POA
correspondant, anonymise les données, formate le contenu pour le modèle LLM, puis génère un PPA structuré.
"""





from src.func.poa_loader import load_patient_file
from src.func.poa_cleaning import clean_patient_document
from src.func.detect_poa_file_path import extract_relevant_info
from src.llm_user_session.model import llm_model
from src.func.extract_patient_name import extract_patient_name_llm
from src.func.anonymizer import anonymize_patient_document
from src.func.anonymizer import deanonymize_fields
from src.utils.convert_json_text import convert_json_to_text
from src.func.llm_prompts import llm_prompt_template_medical_plan, medical_prompt_template, medical_response_from_llm
from src.func.free_text_name_anonymizer import anonymize_name_mentions_in_free_text

import tiktoken
import json



def process_ppa_request(user_input, system_prompt):
    """
    Traite une requête utilisateur pour générer un Plan Personnalisé d’Accompagnement (PPA) à partir d’un fichier POA.

    Étapes :
    - Extraction du nom du patient depuis la requête.
    - Chargement et nettoyage du fichier POA associé.
    - Anonymisation des champs sensibles.
    - Conversion du document nettoyé en texte pour le LLM.
    - Construction du prompt et génération de la réponse par le modèle.
    - Désanonymisation du résultat final.

    Args:
        user_input (str): La requête formulée par l'utilisateur.
        system_prompt (str): Le prompt système servant de base au modèle.

    Returns:
        tuple:
            - str: La réponse du modèle désanonymisée, formatée comme un PPA.
            - dict: Le dictionnaire de mapping d’anonymisation utilisé.
    """

    # 1. Extraire le nom du patient
    patient_name = extract_patient_name_llm(user_input)
    if not patient_name:
        return "❌ Impossible de déterminer le nom du patient à partir de la requête."

    print(f"🟢 Recherche du fichier avec patient_name = '{patient_name}'")

    # 2. Récupérer le chemin du fichier patient
    print(f'patient_name: {patient_name}')
    patient_file_path = extract_relevant_info(patient_name)
    print(f'patient_file_path: {patient_file_path}')
    if not patient_file_path:
        return f"❌ Fichier du patient {patient_name} introuvable."

    # 3. Charger le fichier patient
    try:
        raw_document = load_patient_file(patient_file_path)
        if not raw_document:
            print('No raw_document available')
    except FileNotFoundError:
        return f"❌ Impossible de charger le fichier du patient {patient_name}."
    print("✅ Chargement du document terminé.")
    # print("🔍 Aperçu du JSON brut :", json.dumps(raw_document, indent=2, ensure_ascii=False)[:1000])

    # 4. Nettoyer le contenu du fichier (POA)
    if not raw_document:
        print('No raw_document available')
    cleaned_document = clean_patient_document(raw_document)
    print("✅ Document nettoyé.")
    print("🟧 Aperçu du document nettoyé-avant anony. :", json.dumps(cleaned_document, indent=2, ensure_ascii=False)[0:1500])

    # --- test
    pp = cleaned_document.get("usager", {}) \
        .get("Informations d'état civil", {}) \
        .get("personnePhysique", {})
    print("[AFTER CLEAN] situationFamiliale:",
          "PRESENT" if "situationFamiliale" in pp else "ABSENTE",
          "->", pp.get("situationFamiliale", "<NO KEY>"))

    print("🟧 Aperçu (global) :", json.dumps(cleaned_document, indent=2, ensure_ascii=False)[0:3000])
    # ---

    # print("🟧 Aperçu du document nettoyé :", json.dumps(cleaned_document, indent=2, ensure_ascii=False)[:])

    # 4. Bis Anonymisation du POA + conversion dictionnaire en texte
    anonymized_doc, dict_mapping = anonymize_patient_document(cleaned_document, debug=False)
    anonymized_doc, dict_mapping = anonymize_name_mentions_in_free_text(anonymized_doc, dict_mapping, debug=False)

    print("✅ Anonymisation effectuée.")
    print("🟧 Texte anonymisé :", json.dumps(anonymized_doc, indent=2, ensure_ascii=False)[0:1500])
    # print("🟧 Texte anonymisé :", json.dumps(anonymized_text, indent=2, ensure_ascii=False)[:])

    print("🟧 Exemple de mapping :", list(dict_mapping.items())[:15])

    # print(f"🟧 Après anonymisation -> {anonymized_doc}")

    anonymized_text = convert_json_to_text(anonymized_doc)
    print("✅ Conversion JSON → texte réussie.")
    # print("🔍 Prompt envoyé au modèle :", anonymized_text)

    #5. encapsule le prompt de base pour ce type d'analyse médicale.
    user_prompt_template = llm_prompt_template_medical_plan()

    #6. construire dynamiquement d'autres prompts.
    prompt_template = medical_prompt_template(system_prompt, user_prompt_template)

    print("🟢 Envoi de la requête au LLM...")
    # 7. centralise l'appel au modèle avec un StrOutputParser
    response = medical_response_from_llm(prompt_template, user_input, anonymized_text)



    # ============================

    # NOMBRE TOKENS ENVOYES AU LLM
    # 1. Formatage du prompt final avec les variables
    final_prompt = prompt_template.format(
        user_input=user_input,
        poa_content=anonymized_text
    )

    # 2. Encodage avec tiktoken (compatible avec GPT, Mistral… selon ton modèle)
    enc = tiktoken.get_encoding("cl100k_base")  # ou adapte selon ton tokenizer
    num_tokens = len(enc.encode(final_prompt))

    print(" 🟢Nombre réel de tokens envoyés au LLM :", num_tokens)

    # ============================


    # response = llm_model.invoke(final_prompt)
    print(f"🟢 Réponse brute du modèle avt. dé-anonym. : {response}")
    deanonymized_response, reverse_mapping = deanonymize_fields(response, dict_mapping, debug=True)



    # ============================

    # NOMBRE TOKENS RECUS DU LLM
    # Comptage des tokens dans la réponse du LLM
    num_output_tokens = len(enc.encode(response))
    print(" 🟢Nombre réel de tokens reçus du LLM :", num_output_tokens)

    # ============================


    # 9. Extraction propre du contenu
    return deanonymized_response.strip(), dict_mapping




