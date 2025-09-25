# OBY-IA

Bienvenue dans la documentation du module d’intelligence artificielle intégré à l’application OBY.

## Objectif du projet

Le module **OBY-IA** est une brique d'intelligence artificielle embarquée dans l'application métier **OBY**, dédiée à l'accompagnement des personnes âgées à domicile.

Il a pour but de générer automatiquement des **Plans Personnalisés d’Accompagnement (PPA)** à partir de documents d’évaluation appelés **Plans d’Objectifs et d’Actions (POA)**. Il permet également d’assister les professionnels dans la prise de décision, l'analyse de données de santé et la planification des actions de soin.

---

## Fonctionnalités principales

- 💬 Interaction via un **chatbot intégré** à l’interface Dash de l’application.
- 📄 Anonymisation des valeurs liées au patient (nom, adresse, ...).
- 📄 Gestion multi sessions.
- 🔍 Analyse automatisée des documents **POA** (chargement, nettoyage, structuration).
- 🧠 Génération de **Plan Personnalisés d'Accompagnement** à l’aide d’un modèle de langage (LLM).
- 🧠 En rapport avec un contexte patient, génération de **recommandations médicales enrichies** via la recherche documentaire (RAG).
- 📈 Affichage des constantes d'un patient sous forme de graphes et de tables.
- 📈 Détection de **constantes vitales anormales**.
- 📄 Export des interactions utilisateur-OBY-IA en format Markdown.

---

## ✅ Schéma fonctionnel d'ensemble OBY-IA

Ce schéma présente une vue d'ensemble des blocs fonctionnels

```plantuml
@startuml
' ---- Style global ----
skinparam shadowing false
skinparam packageStyle rectangle
skinparam defaultTextAlignment left
skinparam componentStyle rectangle
skinparam monochrome false
skinparam wrapWidth 200
skinparam maxMessageSize 200

title OBY-IA — Vue d’ensemble des blocs fonctionnels

' ---- Légende des couleurs ----
legend left
|= Couleur |= Bloc fonctionnel |
|<#E0F7FA>| Interaction / Intention |
|<#E8F5E9>| Acquisition & Préparation (POA) |
|<#E3F2FD>| Génération PPA |
|<#F3E5F5>| Recommandations de soins |
|<#FFF8E1>| RAG & Connaissances |
|<#ECEFF1>| Export / Sorties |
endlegend

' ---- Blocs ----
package "Interaction & Intention" #E0F7FA {
  [chatbot_ui.py] as CHAT <<UI>>
  [extract_user_intent.py\n- detect_intent(generate_ppa / get_constants / generate_recommendations)] as INTENT <<NLU>>
  [main_api.py\nhandle_user_input_or_logout()] as API <<API>>
}

package "Acquisition & Préparation (POA)" #E8F5E9 {
  [poa_loader.py\n- load_patient_poa] as POA_LOAD <<Data>>
  [detect_poa_file_path.py\n- detect_poa_file_path] as POA_PATH <<Resolver>>
  [extract_patient_name.py\n- extract_patient_name] as PNAME <<NLP>>
  [poa_cleaning.py\n- clean_patient_document] as POA_CLEAN <<ETL>>
  [anonymizer.py\n- anonymize_patient_document] as ANON <<Privacy>>
  [convert_json_to_text.py\n- convert_json_to_text] as CONV <<Transform>>
}

package "Génération PPA" #E3F2FD {
  [generate_ppa_from_poa.py\n- pipeline: generate_ppa_from_poa] as PPA <<Pipeline>>
}

package "Recommandations de soins" #F3E5F5 {
  [generate_structured_medical_plan.py\n- pipeline: generate_structured_medical_plan] as RECO <<Pipeline>>
  [get_patient_constants_graphs.py\n- generate_graphs\n- generate_constants_table] as CONST_IO <<Inputs>>
  [analyze_constants.py\n- analyze_constants] as CONST_ANALYZE <<Analytics>>
}

package "RAG & Connaissances" #FFF8E1 {
  [llm_prompts.py\n- rag_llm_prompt_template_medical_plan] as PROMPT <<Prompt>>
  [rag_medical_response_from_llm.py\n- rag_medical_response_from_llm] as RAGCALL <<LLM>>
  [scrape_trusted_sites.py] as SCRAPER <<Crawler>>
  [run_full_indexing_pipeline.py] as PIPELINE <<Indexer>>
  [index_documents_chromadb.py] as INDEXER <<Index>>
  database "ChromaDB\n• base_docx\n• base_web" as CHROMA
}

package "Export / Sorties" #ECEFF1 {
  [export.py\n- build_pdf\n- save_markdown] as EXPORT <<Doc>>
  [serialize_figs.py\n- fig_to_image\n- embed_figs] as FIGS <<Assets>>
}

' ---- Flux principaux ----
API --> CHAT
CHAT --> INTENT : intention utilisateur\n(generate_ppa / get_constants / generate_recommendations)
INTENT --> PPA : si intention == generate_ppa
INTENT --> RECO : si intention == generate_recommendations
INTENT --> CONST_IO : si intention == get_constants

' Chaîne POA -> PPA
CHAT --> PNAME : nom du patient (extraction)
PNAME --> POA_PATH : résolution du fichier
POA_PATH --> POA_LOAD
POA_LOAD --> POA_CLEAN
POA_CLEAN --> ANON
ANON --> CONV
CONV --> PPA

' Constantes -> Recos
CONST_IO --> CONST_ANALYZE
CONST_ANALYZE --> RECO

' RAG
PROMPT --> RAGCALL
CHROMA --> RAGCALL : passages pertinents
RAGCALL --> RECO : texte structuré + bonnes pratiques

' Indexation des connaissances
SCRAPER --> PIPELINE
PIPELINE --> INDEXER
INDEXER --> CHROMA

' Exports
PPA --> EXPORT : PPA (Markdown/PDF)
RECO --> EXPORT : Recos (Markdown/PDF)
FIGS --> EXPORT : images/graphes

@enduml
```

---

## ✅ Schéma: exemple de génération de PPA

Ce schéma présente l'exemple d'un flux de génération de PPA.


```mermaid
flowchart TD
    subgraph "🔐 Authentification"
        A1["Saisie ID<br/>+ mot de passe<br/>(home.py)<br/>&nbsp;"] --> A2["Vérification<br/>&nbsp;"]
        A2 -->|Succès| A3["Session créée<br/>(session_manager.py)<br/>&nbsp;"]
        A3 --> A4["Interface utilisateur<br/>(chatbot_ui.py)<br/>&nbsp;"]
    end

    subgraph "💬 Interaction utilisateur"
        A4 --> B1["Saisie requête<br/>utilisateur<br/>&nbsp;"]
        B1 --> B2["Détection de<br/>l'intention<br/>&nbsp;"]
        B2 -->|Intent: Générer PPA| C0["Appel<br/>generate_ppa_from_poa.py<br/>&nbsp;"]
        B2 -->|Intent: Reco médicale| C1["Appel<br/>generate_structured_medical_plan.py<br/>&nbsp;"]
        B2 -->|Intent: Constantes patient| C2["Appel<br/>get_patient_constants_graphs.py<br/>&nbsp;"]
    end

    subgraph "🧠 IA / Génération PPA"
        C0 --> C3["Chargement POA<br/>(poa_loader)<br/>&nbsp;"]
        C3 --> C4["Nettoyage<br/>(poa_cleaning)<br/>&nbsp;"]
        C4 --> C5["Anonymisation<br/>(anonymizer)<br/>&nbsp;"]
        C5 --> C6["Préparation prompt<br/>(llm_prompts)<br/>&nbsp;"]
        C6 --> C7["Génération<br/>Plan structuré<br/>&nbsp;"]
        C7 --> C8["Désanonymisation<br/>(anonymizer)<br/>&nbsp;"]
        C8 --> C9["Affichage dans Dash<br/>(chatbot_ui)<br/>&nbsp;"]
    end

    classDef file fill:#f9f,stroke:#333,stroke-width:1px;
    classDef process fill:#bbf,stroke:#333,stroke-width:1px,text-wrap:wrap,padding:8px;
    class pdf_output,markdown_log file;
    class poa_loader,poa_cleaning,generate_ppa_from_poa,llm_prompts,generate_structured_medical_plan,serialize_figs,chatbot_ui,get_constants,analyze_constants,get_patient_constants_graphs,scrape_trusted_sites,run_full_indexing_pipeline,index_documents_chromadb,retrieve_relevant_chunks process;
```
