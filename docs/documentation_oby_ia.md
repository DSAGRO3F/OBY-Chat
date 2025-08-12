
# Documentation des blocs fonctionnels – OBY-IA

Cette documentation décrit les blocs fonctionnels du système OBY-IA. Pour chaque bloc, vous trouverez :
- Le rôle du module
- Le docstring principal
- La fonction principale et son comportement
- Les fonctions appelées et leur documentation

---

## 🔐 Module `home.py` – Authentification et interface d'administration

**Rôle :** Authentification utilisateur, gestion des sessions, interface d’administration.

**Docstring :**
Ce module Dash gère :
- l’authentification via `USER_DATABASE`,
- la gestion de session via `session_manager_instance`,
- les actions administratives comme la réinitialisation des bases (ChromaDB, JSON, index),
- l’accès à la documentation MkDocs,
- l’affichage de statistiques ChromaDB.

**Fonctions :**
- `authenticate_user` : Authentifie l’utilisateur à partir des identifiants saisis.
- `trigger_reset` : Réinitialise les bases ChromaDB et fichiers JSON.
- `display_admin_controls` : Affiche les boutons admin si l’utilisateur est `admin`.
- `check_mkdocs_status` : Vérifie la disponibilité du serveur MkDocs local.
- `open_docs_site` : Redirige vers la documentation locale.
- `update_chroma_stats` : Affiche les statistiques d’indexation de ChromaDB.

---

## 💬 Module `chatbot_ui.py` – Interface conversationnelle

**Rôle :** Affichage du chatbot et génération dynamique de contenu.

**Docstring :**
Ce module Dash gère :
- les interactions en langage naturel avec le LLM,
- l’analyse des constantes (graphes, tableaux, anomalies),
- la détection d’intention (`generate_ppa`, `get_constants`, `generate_recommendations`),
- l’export Markdown de session,
- la gestion de session (connexion/déconnexion),
- la vérification de disponibilité de l’index ChromaDB.

**Fonctions :**
- `handle_user_input_or_logout` : Gère les interactions avec le chatbot, les réponses LLM et traite la déconnexion.
- `export_chat_response` : Exporte les réponses et graphiques en fichier Markdown.
- `check_index_status` : Active l’interface dès que l’index est prêt.

---

## 🎯 Module `extract_user_intent.py` – Détection d’intention

**Rôle :** Détection de l’intention à partir de la requête utilisateur.

**Docstring :**
Le module détecte l’intention par mots-clés (priorisés), ou via LLM si aucun mot-clé ne correspond.

**Fonctions :**
- `detect_user_intent(user_input)` : Retourne un `intent` de type `"generate_ppa"`, `"get_constants"`, etc.
- `llm_intent_classification(user_input)` : Utilise un LLM pour classifier l’intention.

---

## 📄 Module `generate_ppa_from_poa.py` – Génération du PPA

**Rôle :** Génère un Plan Personnalisé d’Accompagnement (PPA) à partir du POA d’un patient.

**Fonction principale :**
- `process_ppa_request(user_input, system_prompt)`
  - Extraction du nom du patient
  - Chargement et nettoyage du document POA
  - Anonymisation des champs
  - Génération du PPA avec un LLM
  - Désanonymisation

**Fonctions appelées :**
- `extract_patient_name_llm` : Extraction du nom depuis l’entrée utilisateur.
- `extract_relevant_info`, `load_patient_file`, `clean_patient_document`
- `_anonymize_dict`, `anonymize_fields`, `deanonymize_fields`
- `convert_json_to_text`
- `llm_prompt_template_medical_plan`, `medical_response_from_llm`

---

## 🩺 Module `generate_structured_medical_plan.py` – Recommandations médicales

**Rôle :** Génère un plan d’actions médicales structuré (prévention, soins...) enrichi par RAG.

**Fonction principale :**
- `generate_structured_medical_plan(user_input, system_prompt)`
  - Extraction du nom
  - Chargement POA
  - Anonymisation
  - Génération via prompt RAG
  - Désanonymisation

**Fonctions appelées :**
- `extract_patient_name_llm`, `extract_relevant_info`, `load_patient_file`, `clean_patient_document`
- `_anonymize_dict`, `anonymize_fields`, `deanonymize_fields`
- `convert_json_to_text`
- `rag_llm_prompt_template_medical_plan`, `rag_medical_response_from_llm`

---

## 📊 Module `get_patient_constants_graphs.py` – Analyse des constantes

**Rôle :** Traite les constantes du patient, produit tableaux et graphiques, détecte des anomalies.

**Fonction principale :**
- `process_patient_request_with_constants(nom)`
  - Charge les constantes depuis SQLite
  - Détecte les anomalies
  - Crée les graphiques Plotly et tableaux HTML

**Fonctions appelées :**
- `get_available_constantes`
- `get_constantes_patient`
- `convert_constants_to_dataframe`
- `analyze_constants`
- `generate_graphs`
- `generate_constants_table`

---

## 🧠 Module `run_full_indexing_pipeline.py` – Indexation documentaire RAG

**Rôle :** Prépare et indexe la base documentaire pour le RAG dans ChromaDB.

**Fonction principale :**
- `run_full_indexing_pipeline()`
  - Détection des fichiers modifiés (DOCX / Web)
  - Conversion DOCX → JSON
  - Scraping des sites web
  - Indexation dans ChromaDB
  - Mise à jour du journal
  - Marquage `index_ready.flag`

**Fonctions appelées :**
- `detect_changes_and_get_modified_files`
- `convert_and_save_fiches`
- `scrape_all_trusted_sites`
- `index_documents`
- `get_chroma_client`
- `mark_index_ready_flag`

---
