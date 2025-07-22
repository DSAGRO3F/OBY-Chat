# OBY-IA

Bienvenue dans la documentation du module d’intelligence artificielle intégré à l’application OBY.

## Objectif du projet

Le module **OBY-IA** est une brique d'intelligence artificielle embarquée dans l'application métier **OBY**, dédiée à l'accompagnement des personnes âgées à domicile.

Il a pour but de générer automatiquement des **Plans Personnalisés d’Accompagnement (PPA)** à partir de documents d’évaluation appelés **Plans d’Objectifs et d’Actions (POA)**. Il permet également d’assister les professionnels dans la prise de décision, l'analyse de données de santé et la planification des actions de soin.

---

## Fonctionnalités principales

- 🔍 Analyse automatisée des documents **POA** (chargement, nettoyage, structuration).
- 🧠 Génération de **PPA personnalisés** à l’aide d’un modèle de langage (LLM).
- 🧾 Intégration de **recommandations médicales enrichies** via la recherche documentaire (RAG).
- 📈 Détection de **constantes vitales anormales** et visualisation graphique.
- 🗓️ Planification automatique des actions à mener sur 15 jours.
- 💬 Interaction via un **chatbot intégré** à l’interface Dash de l’application.
- 📄 Export PDF des synthèses et enregistrement en journal Markdown.

---

## 🧠 Schéma fonctionnel d'OBY-IA

Ce schéma présente les flux de données et l'organisation des modules techniques.

```mermaid
flowchart TD
    %% Entrées
    POA[📄 Document POA (.docx)] -->|Chargement| poa_loader
    poa_loader -->|Nettoyage| poa_cleaning
    poa_cleaning -->|Texte nettoyé| generate_ppa_from_poa
    generate_ppa_from_poa -->|Plan structuré| llm_prompts

    %% Constantes patients
    DB[(🧬 Base SQLite constantes)] --> get_constants
    get_constants --> analyze_constants
    analyze_constants --> get_patient_constants_graphs

    %% IA / Génération médicale
    llm_prompts --> generate_structured_medical_plan
    generate_structured_medical_plan --> serialize_figs

    %% Indexation documentaire
    scrape_trusted_sites --> run_full_indexing_pipeline
    run_full_indexing_pipeline --> index_documents_chromadb
    index_documents_chromadb --> retrieve_relevant_chunks
    retrieve_relevant_chunks --> generate_structured_medical_plan

    %% Interface utilisateur
    generate_structured_medical_plan --> chatbot_ui
    get_patient_constants_graphs --> chatbot_ui
    chatbot_ui --> app[🎛️ Interface Dash]

    %% Exports
    serialize_figs --> pdf_output[📄 PDF Synthèse]
    chatbot_ui --> markdown_log[📝 Journal Markdown]

    %% Styles
    classDef file fill:#f9f,stroke:#333,stroke-width:1px;
    classDef process fill:#bbf,stroke:#333,stroke-width:1px;
    class pdf_output,markdown_log file;
    class poa_loader,poa_cleaning,generate_ppa_from_poa,llm_prompts,generate_structured_medical_plan,serialize_figs,chatbot_ui,get_constants,analyze_constants,get_patient_constants_graphs,scrape_trusted_sites,run_full_indexing_pipeline,index_documents_chromadb,retrieve_relevant_chunks process;
```
