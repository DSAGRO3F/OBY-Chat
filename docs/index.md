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

## 🧠 Schéma fonctionnel d'OBY-IA

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
