# 🧠 Vue d'ensemble des modules OBY-IA

Ce document présente une vue hiérarchique des composants du projet OBY-IA. Chaque module est replacé dans le contexte de son rôle fonctionnel dans l’application.

---

## 🎯 Point d’entrée de l’application

### `app.py`
- **Rôle** : Lance l’application Dash et le scheduler Watchdog.
- **Responsabilités** :
  - Charge les pages `home.py` et `chatbot_ui.py`.
  - Démarre la surveillance automatique des fichiers pour l’indexation.
  - Active le serveur Dash.

---

## 🖥️ Interface Utilisateur (Dash)

### `pages/home.py`
- **Rôle** : Page d’accueil de l’application.
- **Fonction** : Authentification de l’utilisateur.

### `pages/chatbot_ui.py`
- **Rôle** : Interface du chatbot.
- **Fonctions principales** :
  - Réception des requêtes utilisateur.
  - Appel aux fonctions d’IA adaptées.
  - Affichage des réponses et graphiques.
  - Export des résultats via `export_chat_response()`.

---

## 🧠 Traitement des Requêtes Utilisateur (IA)

### `func.extract_user_intent.py`
- **Rôle** : Détection de l’intention utilisateur (ex. : générer un PPA, analyser des constantes…).

### `func.generate_ppa_from_poa.py`
- **Rôle** : Génère un plan personnalisé d’accompagnement à partir d’un POA.
- **Fonction appelée** : `process_ppa_request()`
  - Extraction du nom du patient.
  - Chargement et nettoyage du POA.
  - Anonymisation + conversion en texte.
  - Génération via LLM.

### `func.generate_structured_medical_plan.py`
- **Rôle** : Produit un plan médical enrichi via RAG.
- **Fonction appelée** : `generate_structured_medical_plan()`
  - Similaire à `process_ppa_request`, avec ajout d’enrichissement par documents ChromaDB.

### `func.get_patient_constants_graphs.py`
- **Rôle** : Analyse et visualisation des constantes.
- **Fonction appelée** : `process_patient_request_with_constants()`
  - Conversion des constantes.
  - Détection d’anomalies.
  - Génération de courbes + tableau.

---

## 📁 Accès et Préparation des Données Patient

### `func.extract_patient_name.py`
- **Rôle** : Identification du patient depuis la requête.

### `func.extract_relevant_info.py`
- **Rôle** : Localisation et chargement du fichier POA.

### `func.poa_loader.py`
- **Rôle** : Chargement brut du document POA.

### `func.poa_cleaning.py`
- **Rôle** : Nettoyage des sections non pertinentes (par ex. : annexes, mentions inutiles).

### `func.anonymizer.py`
- **Rôle** : Remplacement des données sensibles par des tokens anonymes.

### `utils.convert_json_text.py`
- **Rôle** : Conversion du dictionnaire anonymisé en texte structuré pour le LLM.

### `func.detect_genre.py`
- **Rôle** : Détection automatique du genre à partir du prénom.

---

## 🧩 Génération LLM et Prompts

### `func.llm_prompts.py`
- **Rôle** : Génère les templates de prompt pour la génération LLM.
- **Appelle** : `retrieve_relevant_chunks()` dans le cadre RAG.

### `func.retrieve_relevant_chunks.py`
- **Rôle** : Récupère les passages pertinents depuis ChromaDB pour enrichir les réponses.

### `func.serialize_figs.py`
- **Rôle** : Sérialise les graphiques générés pour affichage et export.

---

## 📚 Indexation & RAG

### `func.run_full_indexing_pipeline.py`
- **Rôle** : Pipeline complet d’indexation (DOCX, pages web).
- **Étapes** :
  - Détection des fichiers modifiés.
  - Conversion DOCX → JSON.
  - Scraping des sites.
  - Indexation ChromaDB.

### `func.scrape_trusted_sites.py`
- **Rôle** : Récupère les recommandations de santé sur les sites référencés.

### `func.index_documents_chromadb.py`
- **Rôle** : Indexation vectorielle des fichiers JSON.

### `func.indexed_health_related_files.py`
- **Rôle** : Suivi de l’état des fichiers indexés (hashs, journaux…).

### `utils.scheduler.py`
- **Rôle** : Lance automatiquement l’indexation à chaque changement (via Watchdog).

---

## 🧰 Utilitaires & Configuration

### `utils.convert_fiches_docx_to_json.py`
- **Rôle** : Convertit les fiches .docx en fichiers JSON lisibles par le LLM.

### `utils.export_chat_response.py`
- **Rôle** : Génère un fichier Markdown à partir de la session du chatbot (textes + graphiques).

### `utils.reset_data.py`
- **Rôle** : Réinitialise les états (utilisé en debug/test).

### `utils.chroma_client.py`
- **Rôle** : Initialise le client ChromaDB.

---

## 👥 Sessions & Historique

### `llm_user_session/model.py`
- **Rôle** : Définition du modèle de session utilisateur.

### `llm_user_session/session_manager.py`
- **Rôle** : Création, sauvegarde et gestion des sessions.

### `llm_user_session/session_manager_instance.py`
- **Rôle** : Singleton partagé entre modules pour la gestion de session.

---
