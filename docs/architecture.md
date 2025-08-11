## **Architecture fonctionnelle — OBY-IA**
Cette page présente l’architecture par objectifs métier : pour chaque objectif, on liste les blocs fonctionnels, les modules et leurs fonctions clés qui, ensemble, réalisent la valeur attendue (ex. générer un PPA patient).
Cette page est référencée dans la navigation MkDocs sous Architecture fonctionnelle, comme défini dans mkdocs.yml. 
---
### **1)Vue d’ensemble**
OBY-IA s’appuie sur 6 familles de capacités :
Accueil & Authentification (UI)
Interface conversationnelle & Orchestration
Détection d’intention (LLM)
Génération de livrables (PPA, Plan de soins)
Analyse des constantes patient
Indexation documentaire (RAG)
Des routes API exposent ces capacités pour l’intégration avec l’application OBY.
---
### **2) Objectifs métier et blocs impliqués**
#### A. Se connecter, administrer et accéder aux indicateurs
Objectif métier : authentifier un utilisateur, contrôler l’accès aux fonctions d’admin (reset index), afficher l’état de la doc et des index ChromaDB.
Module : home.py — Page d’accueil (Dash)
Rôle & périmètre : Authentification, gestion de session, boutons admin, accès doc MkDocs, stats ChromaDB.
Fonctions clés :
authenticate_user() — login & création session ; logout_user() — déconnexion.
display_admin_controls() — boutons admin visibles pour admin.
trigger_reset() — réinitialisation ChromaDB + JSON + journal d’indexation.
check_mkdocs_status() / open_docs_site() — disponibilité + redirection doc.
update_chroma_stats() — métriques d’indexation. 
---
#### B. Interagir en langage naturel et orchestrer les pipelines
Objectif métier : à partir d’une saisie libre, comprendre ce que veut l’utilisateur, lancer le pipeline adapté (constantes, PPA, plan de soins), puis afficher/rendre les résultats et permettre l’export.
Module : chatbot_ui.py — UI Chat (Dash)
Rôle & périmètre : interface de conversation, historisation, déclenchement des pipelines, export, disponibilité index.
Fonctions clés :
handle_user_input_or_logout() — boucle principale (déconnexion, détection d’intention, appel LLM/pipelines, mises à jour affichage).
export_chat_response() — export Markdown (réponses LLM + visuels).
check_index_status() — active l’UI quand l’index RAG est prêt.
Dans la logique d’orchestration (décrite dans la doc), on distingue deux étapes internes :
1) préparation de la requête et demande de confirmation (détection d’intention, patient, etc.),
2) exécution du pipeline métier approprié après confirmation. 
Module : extract_user_intent.py — Détection d’intention
Rôle & périmètre : détection par mots-clés priorisés, puis fallback LLM si ambiguïté.
Fonctions clés :
detect_user_intent(user_input) — renvoie "generate_ppa", "get_constants", "generate_recommendations" ou "unknown".
llm_intent_classification(user_input, llm=None). 
---
#### C. Produire un Plan Personnalisé d’Accompagnement (PPA)
Objectif métier : à partir d’un POA (Plan d’Objectifs et d’Actions) d’un patient, générer un PPA structuré prêt à l’usage.
Module : generate_ppa_from_poa.py — Pipeline PPA
Fonction principale : process_ppa_request(user_input, system_prompt)
Chaîne de traitement :
Extraire le nom du patient,
Charger & nettoyer le POA,
Anonymiser les données,
Convertir en texte LLM-ready,
Construire le prompt & interroger le LLM,
Désanonymiser la réponse et retourner le PPA.
Fonctions contribuant au pipeline :
extract_patient_name_llm, extract_relevant_info, load_patient_file,
clean_patient_document, _anonymize_dict, anonymize_fields,
convert_json_to_text, llm_prompt_template_medical_plan,
medical_response_from_llm, deanonymize_fields.
---
#### D. Générer un Plan d’actions de soins structuré (recommandations)
Objectif métier : produire un plan classé (prévention, soins, traitements…) enrichi si nécessaire par des éléments documentaires (RAG).
Module : generate_structured_medical_plan.py — Pipeline Recos
Fonction principale : generate_structured_medical_plan(user_input, system_prompt)
Chaîne de traitement : Extraction patient, chargement/clean POA, anonymisation, conversion texte, prompt RAG, génération LLM, désanonymisation.
Fonctions contribuant au pipeline :
extract_patient_name_llm, extract_relevant_info, load_patient_file,
clean_patient_document, _anonymize_dict, anonymize_fields,
convert_json_to_text, rag_llm_prompt_template_medical_plan,
rag_medical_response_from_llm, deanonymize_fields.
---
#### E. Consulter et analyser les constantes patient
Objectif métier : visualiser les constantes, détecter anomalies, fournir graphiques et tableaux exploitables.
Module : get_patient_constants_graphs.py
Fonction principale : process_patient_request_with_constants(nom) — pipeline de bout en bout.
Fonctions contribuant au pipeline :
get_available_constantes, get_constantes_patient,
convert_constants_to_dataframe, analyze_constants,
generate_graphs, generate_constants_table.
---
#### F. Alimenter le RAG : Indexation documentaire
Objectif métier : détecter les fichiers mis à jour, convertir (DOCX→JSON), scraper les sites de confiance, et indexer dans ChromaDB.
Module : run_full_indexing_pipeline.py
Fonction principale : run_full_indexing_pipeline() — pipeline complet.
Étapes : détection des changements, conversion DOCX→JSON, scraping web, indexation dans ChromaDB (sources DOCX & web), mise à jour du journal, signalement de disponibilité (index_ready.flag).
Fonctions & modules contributeurs :
detect_changes_and_get_modified_files, convert_and_save_fiches,
scrape_all_trusted_sites, index_documents, get_chroma_client,
mark_index_ready_flag.
---
#### G. Intégration API (FastAPI)
Objectif métier : exposer les capacités OBY-IA à l’application OBY et autres clients.
src/api/routes/chat.py — POST /chat
Délègue à process_user_input (mode "api") et retourne ChatResponse. 
src/api/routes/export.py — POST /chat/export
Exporte l’historique (réponses LLM + figures) en Markdown et renvoie une URL statique. 
src/api/routes/login.py — POST /auth/login
Vérifie l’utilisateur, crée un session_id (UUID), renvoie session_data. 
src/api/routes/logout.py — POST /auth/logout
Termine la session (idempotent), vide les stores côté client. 
src/api/routes/poa_patients.py — CRUD fichiers patients (POA)
GET/POST/PUT/DELETE (sécurisé via en-têtes X-User-Id / X-Session-Id).
Utilitaires : ensure_data_dir, fs_path_for, require_editor_session,
list_patients, get_patient, create_patient, update_patient, delete_patient. 
src/api/main_api.py — point d’entrée FastAPI (routes, CORS, middlewares). 
src/api/models.py — schémas Pydantic des entrées/sorties.
---
### **3) Parcours types (diagrammes PlantUML)**
Ces schémas apparaîtront si ton mkdocs.yml est configuré avec plantuml_markdown (serveur public activé). 
#### 3.1. Générer un PPA
@startuml
title Parcours "Générer un PPA"

actor Utilisateur
participant "chatbot_ui.py" as UI
participant "extract_user_intent.py" as Intent
participant "generate_ppa_from_poa.py" as PPA

Utilisateur -> UI : saisie libre (nom + besoin)
UI -> Intent : detect_user_intent()
Intent --> UI : intent = generate_ppa
UI -> PPA : process_ppa_request()
PPA --> UI : PPA (texte structuré)
UI --> Utilisateur : Affichage + Export
@enduml

---

#### 3.2. Consulter les constantes d’un patient
@startuml
title Parcours "Consulter les constantes"

actor Utilisateur
participant "chatbot_ui.py" as UI
participant "extract_user_intent.py" as Intent
participant "get_patient_constants_graphs.py" as Const

Utilisateur -> UI : "Montre les constantes de Mme Dupont"
UI -> Intent : detect_user_intent()
Intent --> UI : intent = get_constants
UI -> Const : process_patient_request_with_constants(nom)
Const --> UI : Graphiques + Tableau + Résumé anomalies
UI --> Utilisateur : Affichage + Export
@enduml

---

#### 3.3. Indexer la base documentaire
@startuml
title Parcours "Indexer la base documentaire"

participant "run_full_indexing_pipeline.py" as Pipeline
participant "convert_and_save_fiches" as Convert
participant "scrape_trusted_sites" as Scrape
participant "index_documents" as Index

Pipeline -> Pipeline : detect_changes_and_get_modified_files()
Pipeline -> Convert : DOCX -> JSON
Pipeline -> Scrape : pages web -> JSON
Pipeline -> Index : JSON -> ChromaDB
Pipeline -> Pipeline : update_index_journal() + index_ready.flag
@enduml

---

### **4) Traçabilité**
Navigation & rendu : la présente page est enregistrée dans nav sous Architecture fonctionnelle et le rendu PlantUML est opéré via plantuml_markdown (serveur public activé). 
Descriptions détaillées des modules et fonctions : voir le document source consolidé (documentation_oby_ia.rtf).

---

### **5) Notes de lecture**
Les fonctions listées par bloc ne sont pas un DAG exhaustif d’appels, mais les éléments déterminants pour l’objectif métier.
Les routes API encapsulent les fonctions internes pour une intégration stable côté OBY.
