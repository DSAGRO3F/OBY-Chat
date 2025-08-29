"""
Module de génération d’un plan d’action structuré à partir du POA d’un patient.

Ce module est déclenché lorsque l’intention « generate_recommendations » est détectée.
Il extrait le nom du patient, charge et nettoie le document POA, anonymise les données,
puis interroge un modèle LLM avec un prompt enrichi pour générer des recommandations classées
(par type d'action : prévention, soins, traitements, etc.).
"""

from src.func.poa_loader import load_patient_file
from src.func.poa_cleaning import clean_patient_document
from src.func.detect_poa_file_path import extract_relevant_info
from src.llm_user_session.model import llm_model
from src.func.extract_patient_name import extract_patient_name_llm
from src.func.anonymizer import anonymize_patient_document
from src.func.anonymizer import deanonymize_fields
from src.utils.convert_json_text import convert_json_to_text
from src.func.llm_prompts import (rag_llm_prompt_template_medical_plan,
                                  rag_medical_response_from_llm)
from src.func.free_text_name_anonymizer import anonymize_name_mentions_in_free_text


import tiktoken
import json
import traceback



def generate_structured_medical_plan(user_input, system_prompt):
    """
    Génère un plan d’action structuré à partir du POA du patient mentionné dans la requête utilisateur.

    Étapes :
    - Extraction du nom du patient.
    - Chargement et nettoyage du fichier POA.
    - Anonymisation des données.
    - Conversion en texte structuré.
    - Génération de recommandations via un modèle LLM.
    - Désanonymisation de la réponse.

    Args:
        user_input (str): Requête utilisateur contenant le nom du patient.
        system_prompt (str): Prompt système de base transmis au modèle.

    Returns:
        tuple:
            - str : Recommandations structurées par type d’action médicale.
            - dict : Dictionnaire de mapping d’anonymisation utilisé.
    """

    print("📥 Début génération du plan structuré médical...")
    print(f'generate_structured_medical_plan.py/user_input: {user_input}')


    # ============================================
    # 1. Extraire le nom du patient
    # ============================================
    patient_name = extract_patient_name_llm(user_input)
    if not patient_name:
        return "❌ Impossible de déterminer le nom du patient à partir de la requête."

    print(f"🟢 Recherche du fichier avec patient_name = '{patient_name}'")



    # ============================================
    # 2. Récupérer le chemin du fichier patient
    # ============================================
    print(f'patient_name: {patient_name}')
    patient_file_path = extract_relevant_info(patient_name)
    print(f'patient_file_path: {patient_file_path}')
    if not patient_file_path:
        return f"❌ Fichier du patient {patient_name} introuvable."



    # ============================================
    # 3. Charger le fichier patient
    # ============================================
    try:
        raw_document = load_patient_file(patient_file_path)
        if not raw_document:
            print('No raw_document available')
    except FileNotFoundError:
        return f"❌ Impossible de charger le fichier du patient {patient_name}."
    print("✅ Chargement du document terminé.")
    # print("🔍 Aperçu du JSON brut :", json.dumps(raw_document, indent=2, ensure_ascii=False)[:1000])



    # ============================================
    # 4. Nettoyer le contenu du fichier (POA)
    # ============================================
    if not raw_document:
        print('No raw_document available')
    cleaned_document = clean_patient_document(raw_document)
    print("✅ Document nettoyé.")
    print(f"🟡 Type de l'output - Document nettoyé:, {type(cleaned_document)}")


    # ============================================
    # 4. Bis Anonymisation du POA + conversion dictionnaire en texte
    # ============================================
    anonymized_doc, dict_mapping = anonymize_patient_document(cleaned_document, debug=False)
    anonymized_doc, dict_mapping = anonymize_name_mentions_in_free_text(anonymized_doc, dict_mapping, debug=False)

    print("✅ Anonymisation effectuée.")
    print("🔍 Texte anonymisé :", json.dumps(anonymized_doc, indent=2, ensure_ascii=False)[0][:300])
    print("📌 Exemple de mapping :", list(dict_mapping.items())[:10])

    print(f"Après anonymisation -> {anonymized_doc}")

    anonymized_text = convert_json_to_text(anonymized_doc)
    print("✅ Conversion JSON → texte réussie.")
    # print("🔍 Prompt envoyé au modèle :", anonymized_text)



    # ============================================
    #5. encapsule le prompt de base pour ce type d'analyse médicale.
    # ============================================
    try:
        print("📄 Appel à rag_llm_prompt_template_medical_plan")
        prompt_template = rag_llm_prompt_template_medical_plan()
        print("🔎 Type réel de prompt_template :", type(prompt_template))
        print("✅ Variables attendues :", prompt_template.input_variables)

    except Exception as e:
        print(f"❌ Erreur lors de l’appel à rag_llm_prompt_template_medical_plan : {type(e).__name__} - {e}")
        traceback.print_exc()
        return "❌ Erreur lors de l'extraction du prompt_template.", dict_mapping



    print("📄 Appel à rag_medical_response_from_llm()")
    # ============================================
    # 6. centralise l'appel au modèle avec un StrOutputParser
    # ============================================
    try:
        print("📄 Appel à rag_medical_response_from_llm()")
        response = rag_medical_response_from_llm(prompt_template, user_input, anonymized_text)
        print("📄 Réponse obtenue du LLM")
        # print(f"🟢 Réponse brute du modèle : {response}")
    except Exception as e:
        print(f"❌ Erreur lors de l’appel à rag_medical_response_from_llm : {type(e).__name__} - {e}")
        traceback.print_exc()
        return "❌ Erreur lors de l'appel au modèle LLM pour les recommandations.", dict_mapping


    # ============================================
    # 7. response = llm_model.invoke(final_prompt)
    # ============================================
    try:
        deanonymized_response, reverse_mapping = deanonymize_fields(response, dict_mapping, debug=True)

    except Exception as e:
        print(f"❌ Erreur lors de la désanonymisation : {type(e).__name__} - {e}")
        traceback.print_exc()
        return "❌ Erreur lors de la désanonymisation des recommandations.", dict_mapping


    # ============================================
    # 8. Extraction propre du contenu
    # ============================================
    return deanonymized_response.strip(), dict_mapping


