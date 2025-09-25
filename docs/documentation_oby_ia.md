# Liste des blocs fonctionnels OBY-IA.

## **Nom: app.py (src/app.py)**
### Rôle: initialise l'application Dash
### Docstring:
  - Ce module initialise l'application Dash, configure la navigation entre les pages, et vérifie la disponibilité de la base de données des constantes médicales.

  - **Fonctionnalités principales :**
    - Chargement des variables d'environnement depuis un fichier `.env` à la racine. 
    - Vérification et génération automatique de la base SQLite (`constantes_sante.db`). 
    - Initialisation de l'application Dash avec gestion des pages (`use_pages=True`). 
    - Mise en place d'une barre de navigation et d'un conteneur de pages dynamiques. 
    - Démarrage d'un planificateur de tâches (scheduler) dans un thread dédié au lancement. 
    - Ce fichier doit être exécuté pour lancer le serveur Dash : `python -m src.app`
  
### **Module appelé par le module app.py:**
   - scheduler.py (src/utils/scheduler.py)
   - Scheduler de réindexation Chroma : surveillance, sérialisation et relance sûres.
   - Ce module démarre un watchdog des dossiers d’entrée, scrute le flag`.force_full_index` et lance le pipeline via `_run_pipeline_safely()`, sous verrou inter-processus.
   - Il effectue une probe d’écriture sans embedder, n’exécute le pipeline que si la base est utilisable, et ne pose le `index_ready.flag` qu’en cas de succès, en consommant le flag de forçage ensuite.
   - Il évite les accès concurrents à Chroma pendant les resets/rebuilds et peut appliquer un backoff sur les relances.
   - #### **Fonctions appelées par le module scheduler.py**
     - _probe_chroma_writable(client) -> None:
     - probe_writable_no_embed(c):
     - _ensure_writable_dir_now(p: Path):
     - _cleanup_sqlite_artifacts_now(p: Path):
     - _run_pipeline_safely(reason: str = "") -> None:
     - _collections_missing() -> bool:
     - start_scheduler() -> None: Fonction principale.
       - docstring:
         - Démarre le scheduler de réindexation Chroma et la surveillance fichiers. 
         - Crée le répertoire de persistance au besoin, évalue l’état initial (présence du ready flag, collections manquantes, demande de rebuild) et déclenche une réindexation si nécessaire. Lance un watchdog (avec anti-rebond) sur les dossiers d’entrée, puis entre dans une boucle qui scrute `.force_full_index` et délègue à `_run_pipeline_safely()` sous verrou inter-processus.
         - Cette fonction n’efface pas le flag de forçage (consommé en cas de succès par le pipeline) et arrête proprement l’observer sur interruption clavier.

## **Nom: reset_data.py (src/utils/reset_data.py)**
### Rôle: Réinitialise proprement l’environnement d’indexation Chroma et les artefacts locaux.
### Docsting:
  - Ce module fournit `reset_all_data()` qui, sous verrou inter-processus, efface le dossier Chroma, nettoie les JSON générés et réinitialise le journal via une écriture atomique. Il supprime le ready-flag, pose le flag `.force_full_index` (écriture atomique) et recrée les répertoires avec des permissions minimales sûres.
  - Aucun client Chroma direct n’est instancié ici : le cache client global est d’abord invalidé pour éviter les handles orphelins et les erreurs SQLite “readonly (1032)”.
  - #### **Module appelé par le module reset_data.py**
    - vector_db_utils.py (src/utils/vector_db_utils.py)
    - ##### **Fonctions appelées par le module vector_db_utils.py**
      - is_chroma_index_ready(verbose: bool = False) -> bool:
      - mark_index_ready_flag():
      - clear_index_ready_flag() -> None:

## **Nom: get_chroma_stats.py (src/func/get_chroma_stats.py)**
### Rôle: Collecte et expose des statistiques d’index Chroma pour l’UI.
### Docsting:
  - Ce module fournit une fonction principale, :func:`get_chroma_index_stats`, qui retourne des compteurs utiles à l’interface (nb de fichiers/chunks DOCX & Web, nb de JSON locaux, etc.) sans perturber l’indexation en cours.
  - Comportement clé:
    - **Aucun accès Chroma pendant l’indexation** : si l’un des drapeaux "FORCE_FULL_INDEX_FLAG" ou "INDEXING_FLAG_FILE" est présent, la fonction n’instancie pas de client Chroma et renvoie simplement les compteurs de fichiers JSON présents sur disque, avec "indexing=True".
    - **Accès Chroma en lecture seule sinon** : une fois l’index prêt (flags absents), le cache client est invalidé puis un client Chroma est créé pour lire les collections ("base_docx" / "base_web") et calculer les compteurs (chunks, fichiers, domaines).
    - **Aucun effet de bord à l’import** : le module n’ouvre jamais Chroma au chargement. Toute lecture Chroma se fait *uniquement* à l’appel de la fonction.
  - Returns:
    - La fonction :func:"get_chroma_index_stats" renvoie un "dict" du type :
    ```{
      "docx_files": int,
      "docx_chunks": int,
      "docx_json_files": int,
      "web_files": int,
      "web_chunks": int,
      "web_json_files": int,
      "docx_fiches": int,
      "web_domains": int,
      "indexing": bool,  # True si un rebuild est demandé/en cours
    }```
  - Dans les cas d’erreur de lecture Chroma, la fonction reste tolérante et renvoie simplement les compteurs JSON avec les autres valeurs à 0.
  - Dépendances & conventions:
    - Ce module s’appuie sur les chemins/flags centralisés dans "config.config" :
      - "FORCE_FULL_INDEX_FLAG", "INDEXING_FLAG_FILE", "JSON_HEALTH_DOC_BASE", "WEB_SITES_JSON_HEALTH_DOC_BASE".
      - L’accès client est **centralisé** via "src.utils.chroma_client" :
        - "get_chroma_client" et "reset_chroma_client_cache".
        - Les noms de collections attendues sont "base_docx" et "base_web".

## **Nom: home.py (src/pages/home.py)**
### Rôle: authentification utilisateur et cloisonnement des interactions OBY-IA et utilisateur
### Docstring:
  - Module `home.py` – Page d'accueil, authentification et interface d'administration de OBY-IA.
  - Ce module Dash gère les fonctionnalités suivantes :
    - **Authentification utilisateur** :
      - Vérification des identifiants via une base interne (`USER_DATABASE`).
      - Création et stockage de la session via `dcc.Store` et `session_manager_instance`.
      - Affichage conditionnel de l'interface selon le rôle (utilisateur ou admin).
	- **Déconnexion et gestion de session** :
      - Suppression propre de la session en cours.
      - Réinitialisation du mappage d’anonymisation à la connexion.
	- **Contrôles d'administration (admin uniquement)** :
      - Réinitialisation des bases : ChromaDB, fichiers JSON extraits du web, index de suivi.
      - Interface de déclenchement réservée aux administrateurs.
	- **Accès à la documentation du projet** :
      - Vérification en temps réel de la disponibilité du serveur MkDocs (`http://127.0.0.1:8000`).
      - Redirection automatique vers la documentation si disponible.
	- **Visualisation des statistiques d’indexation ChromaDB** :
      - Affichage du nombre de fichiers indexés (DOCX, web), de chunks, et de fichiers JSON associés.
      - Rafraîchissement manuel ou automatique de ces statistiques à l’ouverture.
  - Ce module constitue la page d’accueil et d’entrée principale de l’application OBY-IA.

### **Fonctions appelées par le module home.py**
  - authenticate_user
    - Authentifie un utilisateur à partir de ses identifiants.
    - Vérifie si l'identifiant et le mot de passe fournis correspondent à une entrée valide dans la base des utilisateurs. Si oui, crée une session et retourne les données associées.
    - Args:
      - n_clicks (int) : Nombre de clics sur le bouton "Valider".
      - user_id_input (str) : Identifiant saisi par l'utilisateur.
      - password_input (str) : Mot de passe saisi par l'utilisateur.
    - Returns:
      - tuple :
        - Message de retour (str),
        - Données de session utilisateur (dict) ou dash.no_update.
	  
  - trigger_reset
     - Réinitialise toutes les bases et fichiers d'indexation de l'application.
     - Fonction réservée à l'administrateur. Elle supprime les données de ChromaDB, les fichiers JSON extraits depuis le web, et le fichier `indexed_files.json` utilisé pour suivre les indexations.
     - Args:
      - n_clicks (int) : Nombre de clics sur le bouton "Réinitialiser les bases".
      - Returns:
        - str : Message de confirmation après la réinitialisation.    
    
  - display_admin_controls
    - Affiche les contrôles d'administration si l'utilisateur est un admin.
      - Cette fonction affiche dynamiquement le bouton "Réinitialiser les bases" uniquement pour les utilisateurs ayant l'identifiant `admin`.
      - Args:
       - session_data (dict) : Données de session contenant `user_id`.
      - Returns:
       - list : Composants Dash (bouton de réinitialisation) ou liste vide.
       - check_mkdocs_status
       - Vérifie si le site de documentation MkDocs est disponible localement.
       - Affiche un message en vert (accessible) ou rouge (inaccessible).
	      
  - get_chroma_index_stats
    - La fonction :func:"get_chroma_index_stats" renvoie un "dict" du type :
     ```{
      "docx_files": int,
      "docx_chunks": int,
      "docx_json_files": int,
      "web_files": int,
      "web_chunks": int,
      "web_json_files": int,
      "docx_fiches": int,
      "web_domains": int,
      "indexing": bool,  # True si un rebuild est demandé/en cours
     }```

## **Nom: chatbot_ui.py (src/pages/chatbot_ui.py)**
### Rôle: Affichage de l’historique de l’interaction OBY-IA et utilisateur.
### Docstring:
  - Module `chatbot_ui.py` – Interface conversationnelle de l'application OBY-IA (page `/chatbot`)
  - Ce module Dash définit la page chatbot de OBY-IA, qui permet aux professionnels de santé d’interagir avec un agent intelligent pour obtenir :
    - **Analyse des constantes médicales du patient** :
      - Extraction et affichage des constantes sous forme de graphiques et tableaux.
    - Détection automatique des anomalies.
    - Sérialisation et désérialisation des graphiques pour l’exportation.
    - **Interaction en langage naturel avec le LLM** :
      - Détection de l’intention utilisateur (consultation, génération de PPA, recommandations).
      - Extraction du nom du patient à partir de la requête.
      - Génération de contenu médical structuré via des prompts spécialisés.
      - Historisation des messages utilisateur/LLM et affichage dynamique.
    - **Export des résultats** :
      - Génération d’un fichier Markdown résumant la session (réponses LLM + graphiques).
    - **Contrôle de disponibilité de l’index ChromaDB** :
      - Affichage d’une bannière d’attente tant que l’index n’est pas prêt.
      - Activation différée des composants de saisie utilisateur.
  - **Composants techniques :**
    - Utilise `session_manager_instance` pour la gestion d’état (session, mapping, historique).
    - Repose sur les modules fonctionnels : `extract_user_intent`, `generate_ppa_from_poa`, `generate_structured_medical_plan`, `get_patient_constants_graphs`, `export_chat_response`, etc.
    - Cette page est au cœur de l’expérience utilisateur de OBY-IA, combinant interface conviviale et logique métier intelligente.

### **Fonctions appelées par le module chatbot_ui.py**
  - Fonction principale:
    - handle_user_input_or_logout
      - Callback principal de gestion des interactions utilisateur.
	    - Cette fonction gère :
	      - la déconnexion de l’utilisateur,
	      - la détection de l’intention (consultation de constantes, génération de PPA ou plan de soins),
	      - l’appel au modèle LLM pour produire une réponse appropriée,
	      - l’affichage et la mise à jour de l’historique et des données patient.
	    - Args:
	      - send_clicks (int) : Nombre de clics sur le bouton "Envoyer".
	      - user_input (str) : Message saisi par l’utilisateur.
	      - logout_clicks (int) : Nombre de clics sur le bouton "Déconnexion".
	      - chat_history (list) : Liste des messages actuellement affichés.
	      - session_data (dict) : Données de session utilisateur (user_id, session_id).
	      - current_patient (str) : Nom du patient actuellement sélectionné.
	    - Returns:
	      - tuple : Mise à jour de :
	        - l'historique du chat,
	        - les graphiques et tableaux des constantes,
	        - le résumé des anomalies,
	        - le nom du patient actif,
	        - les figures sérialisées,
	        - l’affichage du chat.
	  - **Fonction appelée par handle_user_input_or_logout:**
	    - process_user_input
	      - Docstring:
	        - Fonction centrale appelée par l'API ou l'interface pour traiter la requête utilisateur.
	        - Args:
	          - send_clicks (int): Nombre de clics sur le bouton envoyer.
	          - user_input (str): Message saisi par l'utilisateur.
	          - chat_history (list): Historique des échanges.
	          - session_data (dict): Données de session utilisateur.
	          - current_patient (Optional[str]): Nom du patient actuellement sélectionné.
	        - Returns:
	          - dict: Dictionnaire contenant les résultats du traitement.

          - **Fonctions appelées par process_user_input**
	        - handle_initial_request (src/func/handle_user_requests.py)
	          - Prépare la phase pré-confirmation : détecte l’intention et le patient, met à jour la session et renvoie le delta d’affichage (requête + question de confirmation).
              - Paramètres:
                - user_input (str)
                - session (dict)
                - session_data (dict avec "user_id","session_id")
                - chat_history (list)
                - current_patient (str|None)
                - output_mode (Literal["dash","api"]).
              - Retourne un tuple:
                - (chat_history: list, figures_out: list, table_html: str, anomaly_block: str, current_patient: str|None, serialized_figs: list|None, chat_history_display: Any|None).
              - Ne lance aucun pipeline métier; lève ValueError si session_data est incomplet.
              - Les messages ajoutés sont tagués (patient_key, user_id, msg_type).

              - #### **Fonctions appelées par handle_initial_request(...)**
                - tag_user_div(text: str, patient_key: str, user_id: str, msg_type: str):
                - tag_bot_div_markdown(md_text: str, patient_key: str, user_id: str, msg_type: str):
                - _extract_role_text_type(msg):

            - **Module appelé par handle_initial_request:**
	            - extract_user_intent.py (src/func/extract_user_intent.py)
	              - Docstring:
	                - Ce module permet de détecter l’intention principale d’un utilisateur à partir de sa requête textuelle.
	                - La détection repose d’abord sur des correspondances par mots-clés, puis bascule sur un modèle de langage (LLM) si aucune correspondance directe n’est trouvée.
	              - Fonctions appelées par extract_user_intent.py:
	                - detect_user_intent
	                  - Détecte l’intention de l’utilisateur à partir de sa requête textuelle.
	                  - La fonction effectue :
	                    - Une détection par mots-clés avec hiérarchie de priorité si plusieurs intentions sont détectées.
	                    - Un fallback par modèle de langage (LLM) si aucune correspondance n’est trouvée.
	                  - Args:
	                    - user_input (str): Requête utilisateur.
	                  - Returns:
	                    - dict: Dictionnaire contenant une seule clé "intent" avec l’une des valeurs suivantes : "generate_ppa", "get_constants", "generate_recommendations", ou "unknown".

	                - llm_intent_classification
	                  - Utilise un modèle de langage (LLM) pour inférer l’intention utilisateur si aucun mot-clé ne correspond.
	                  - Args:
	                    - user_input (str): Texte de l’utilisateur.
	                    - llm (BaseLanguageModel, optional): Modèle à utiliser. Si None, un modèle local est chargé.
	                  - Returns:
	                    - IntentType: Intention détectée, ou "unknown".

	        - handle_confirmation_response (src/func/handle_user_requests.py)
	          - Traite la réponse de confirmation (oui/non), exécute le pipeline demandé et prépare l’affichage.
              - Paramètres:
                - user_input (str)
                - session (dict)
                - session_data (dict avec "user_id","session_id")
                - chat_history (list, snapshot UI)
                - current_patient (str|None)
                - output_mode (Literal["dash","api"])
              - Filtre/retague l’historique par (patient_key, user_id), reconstruit la paire [user_request, confirm_prompt], ajoute le delta [confirm_answer, bot_response], gère le changement de patient et réinitialise les flags d’intention.
              - Retourne un tuple :
                - (chat_history: list, figures_out: list, table_html: str, anomaly_block: str, current_patient: str|None, serialized_figs: list|None, chat_history_display: Any).
              - Lève ValueError si session_data est incomplet.

              - #### Fonctions appelées par handle_confirmation_response(...)
                - filter_history_by_patient_and_user(history: list, patient_key: str, user_id: str) -> list:
                - retag_last_turn_by_type(prev_history: list, final_patient_key: str) -> None:
                - keep_last_request_plus_confirm(history_filtered: list) -> list:
                - _types(lst):

	- export_chat_response (src/pages/chatbot_ui.py)
	  - Callback de gestion de l’export de l’historique du LLM au format Markdown.
	  - Cette fonction est appelée lorsqu’un utilisateur clique sur le bouton "Exporter". Elle désérialise les graphiques, récupère les réponses enregistrées dans la session, puis appelle la fonction `export_llm_responses`.
	  - Args:
	    - n_clicks (int) : Nombre de clics sur le bouton d’export.
	    - session_data (dict) : Données de session (user_id, session_id).
	    - current_patient (str) : Nom du patient actif.
	    - serialized_figs (list) : Graphiques des constantes sérialisés.
	  - Returns:
	    - str : Message de confirmation ou d’erreur selon le succès de l’export.

	- check_index_status (src/pages/chatbot_ui.py)
	  - Callback périodique pour vérifier la disponibilité de l'index ChromaDB.
	  - Ce callback est déclenché toutes les 2 secondes via `dcc.Interval`.
	  - Il vérifie si le fichier `index_ready.flag` est présent.
	  - Lorsque l'index est prêt, il :
	    - Cache la bannière d'attente
	    - Active les composants d’entrée utilisateur
	  - Args:
	    - n (int) : Nombre d’intervalles écoulés.
	  - Returns:
	    - tuple : Styles de la bannière, état des composants d’entrée.

	- logout_user (src/pages/chatbot_ui.py)
	  - Met fin à la session utilisateur en cours.
	  - Supprime la session active à partir des informations enregistrées, et réinitialise les données côté client.
	  - Args:
	    - n_clicks (int) : Nombre de clics sur le bouton "Déconnexion".
	    - session_data (dict) : Données de session utilisateur en cours.
	  - Returns:
	    - tuple :
	      - Message de confirmation (str),
	      - None pour réinitialiser `session_data`.

## **Nom: generate_ppa_from_poa.py (src/func/generate_ppa_from_poa.py)**
### Rôle: pipeline de génération de PPA.
### Docstring:
  - Module de génération de PPA (Plan Personnalisé d'Accompagnement) à partir d'un document POA.
  - Ce module extrait le nom du patient depuis la requête utilisateur, charge et nettoie le document POA correspondant, anonymise les données, formate le contenu pour le modèle LLM, puis génère un PPA structuré.
  - Fonctions:
	  - **Fonction principale:**
      - process_ppa_request
	      - Traite une requête utilisateur pour générer un Plan Personnalisé d'Accompagnement (PPA) à partir d'un fichier POA.
	      - Étapes :
	        - Extraction du nom du patient depuis la requête.
	        - Chargement et nettoyage du fichier POA associé.
	        - Anonymisation des champs sensibles.
	        - Conversion du document nettoyé en texte pour le LLM.
	        - Construction du prompt et génération de la réponse par le modèle.
	        - Désanonymisation du résultat final.
	      - Args:
	        - user_input (str): La requête formulée par l'utilisateur.
	        - system_prompt (str): Le prompt système servant de base au modèle.
	      - Returns:
	        - tuple:
	          - str: La réponse du modèle désanonymisée, formatée comme un PPA.
	          - dict: Le dictionnaire de mapping d’anonymisation utilisé.

	  - **Fonctions et modules appelés par process_ppa_request:**
	    - extract_patient_name_llm (src/func/extract_patient_name.py)
	      - Module pour l'extraction du nom du patient à partir d'une requête utilisateur.
	      - Ce module utilise un LLM pour analyser une phrase en langage naturel et en extraire uniquement le nom de famille du patient mentionné.

	    - extract_relevant_info (src/func/detect_poa_file_path.py)
	      - Module de détection du chemin du fichier patient.
	      - Ce module fournit une fonction pour localiser automatiquement un fichier contenant les données d'un patient, à partir de son nom, dans le dossier `src/data/poa_patients`.

	    - load_patient_file (src/func/poa_loader.py)
	      - Module de chargement des fichiers POA (Plan d'Objectifs et d'Actions) au format JSON.
	      - Ce module permet de localiser et lire un fichier patient stocké dans le dossier `data/poa_patients/`.

	    - Module appelé:
	      - **Nom: poa_cleaning.py (src/func/poa_cleaning.py)**
	      - Rôle: Module de nettoyage des documents POA (Plan d’Objectifs et d'Actions).
	      - Docstring:
	        - clean_patient_document(data: dict, trace: bool = False) -> dict | (dict, list[str])
	        - Comportement :
	          - supprime les champs vides / non informatifs ("", "non renseigné", "null")
	          - supprime les champs sensibles explicitement demandés (usager + contacts)
	          - émonde les conteneurs (dict/list) devenus vides
              - (optionnel) trace chaque suppression si trace=True
	        - Args : dict (JSON patient)
	        - Returns :
	          - si trace=False : dict nettoyé
	          - si trace=True  : (dict nettoyé, liste des suppressions)

          - Fonctions:
	        - **Fonction principale:**
	          - clean_patient_document
	            - Nettoie récursivement un document JSON de patient :
	              - supprime les champs vides / non informatifs
	              - supprime les champs sensibles explicitement listés (usager + contacts)
	              - émonde les conteneurs vides
	              - (optionnel) trace chaque suppression
	            - Args:
	              - data: Dictionnaire représentant le contenu brut du document POA.
	              - trace: Si True, retourne aussi la liste des suppressions (changes).
	            - Returns:
	              - dict nettoyé, ou (dict nettoyé, changes) si trace=True.
	              - Attention ! si trace == True, on sort avec un tuple.

	        - **Fonctions appelées par le module src/func/poa_cleaning.py:**
              - _is_empty_scalar
	            - Vérifie si une valeur est considérée comme un scalaire vide.
	            - Sont considérés comme vides : None, les chaînes vides et les collections vides. Cette fonction est utilisée pour simplifier le nettoyage récursif des documents patients.
	          - Args:
	            - v (Any): La valeur à vérifier.
	          - Returns:
	            - bool: True si la valeur est vide, False sinon.

            - _pop_in
              - Supprime une clé dans un dictionnaire imbriqué et enregistre le changement.
              - Si la clé existe, elle est supprimée. L’opération peut être tracée en ajoutant le chemin de suppression à la liste des changements.
              - Args:
                - d (Dict[str, Any]): Le dictionnaire à modifier.
                - key (str): La clé à supprimer.
                - changes (List[str] | None, optionnel): Liste des chemins supprimés pour traçabilité.
                - path (str, optionnel): Chemin courant dans la structure. Par défaut "".
                - Returns:
                  - None

            - _get
              - Récupère une valeur dans un dictionnaire imbriqué en suivant un chemin de clés.
              - La fonction parcourt le dictionnaire étape par étape avec les clés données.
              - Retourne None si une clé intermédiaire n'existe pas.
              - Args:
                - d (Dict[str, Any]): Le dictionnaire à parcourir.
                - *path: Séquence de clés représentant le chemin d'accès.
                - Returns:
                  - Any: La valeur trouvée, ou None si inexistante.

            - _ensure_dict
              - Garantit qu'un chemin imbriqué existe dans un dictionnaire sous forme de dictionnaire.
              - Si le chemin n'existe pas, les dictionnaires intermédiaires nécessaires sont créés. Retourne le dictionnaire final au bout du chemin.
              - Args:
                - d (Dict[str, Any]): Le dictionnaire à compléter.
                - *path: Séquence de clés représentant le chemin à garantir.
              - Returns:
                - Dict[str, Any]: Le dictionnaire correspondant au chemin demandé.

            - _clean_rec
                - Nettoie récursivement les valeurs vides dans une structure.
                - Supprime les None, chaînes vides et conteneurs vides (listes, dictionnaires) dans une structure imbriquée.
            - Les suppressions peuvent être enregistrées pour audit.
            - Args:
                - value (Any): La valeur à nettoyer (dict, list ou scalaire).
                - changes (List[str] | None, optionnel): Liste des chemins supprimés.
            - path (str, optionnel): Chemin courant utilisé pour la traçabilité.
            - Returns:
                - Any: La valeur nettoyée, ou None si vide.

            - _remove_usager_sensitive_fields
                - Supprime les champs sensibles dans la section 'usager' d'un document patient.
                - Les champs supprimés concernent les informations identifiantes (adresse, téléphone, identifiants, etc.). Les suppressions peuvent être enregistrées pour traçabilité.
                - Args:
                    - data (Dict[str, Any]): Le document patient sous forme de dictionnaire.
                    - changes (List[str] | None, optionnel): Liste des champs supprimés.
                - Returns:
                - None

            - _remove_contacts_sensitive_fields
                - Supprime les champs sensibles dans la section 'contacts' d'un document patient.
                - L'anonymisation ne s'applique qu'aux contacts de type 'Cercle d'aide et de soin' ou 'Entourage'. Certains champs exclus restent conservés selon les règles définies.
                - Args:
                    - data (Dict[str, Any]): Le document patient sous forme de dictionnaire.
                    - changes (List[str] | None, optionnel): Liste des champs supprimés.
                - Returns:
                    - None

            - _prune_empty_containers
                - Supprime récursivement les conteneurs vides (dictionnaires ou listes).
                - Parcourt la structure et supprime les conteneurs devenus vides après nettoyage. Les suppressions peuvent être enregistrées pour traçabilité.
                - Args:
                    - d (Any): La structure à nettoyer (dict, list, scalaire).
                    - changes (List[str] | None, optionnel): Liste des chemins supprimés.
                    - path (str, optionnel): Chemin courant utilisé pour la traçabilité.
                - Returns:
                    - Any: La structure nettoyée, ou None si elle est vide.

        - Module appelé:
            - **Nom: anonymizer.py (src/func/anonymizer.py)**
            - Rôle: Anonymisation de l'usager via persona française (session-aléatoire).
            - Docstring:
              - Ce module fournit :
                - Des pools de valeurs françaises (prénoms, noms, voies, codes postaux/communes).
                - La création d'une persona cohérente pour l'usager (prénom selon le genre, nom, adresse, CP/commune).
                - Des utilitaires pour lire/écrire dans un dictionnaire JSON par chemins imbriqués.
                - Une anonymisation ciblée des champs usager listés.
                - La construction d'un mapping {valeur_anonymisée: valeur_originale} pour la désanonymisation.
                - Entrée : dict JSON (document patient).
                - Sortie : Tuple[Any, Dict[str, str]] -> (document anonymisé, mapping).

            - Fonctions:
              - **Fonction principale:**
                - anonymize_patient_document
                - Docstring: Anonymise l'usager puis (le cas échéant) les contacts et retourne (doc, mapping).

              - **Fonctions appelées:**
                - _normalize_token
                  - minuscule, accents retirés, espaces/ponctuation enlevés aux extrémités
                  - Args:
                    - value (str): La chaîne de caractères à normaliser.
                  - Returns:
                    - str: La chaîne transformée.

                - _detect_from_fields
                  - Détermine 'M'/'F' en priorisant le champ 'sexe' s'il est exploitable, sinon en se rabattant sur 'civilite'. Retourne None si indéterminé.

                - _is_non_informatif
                    - Vérifie si une valeur est considérée comme non informative.
                    - Une valeur est jugée non informative si elle correspond à l'un des mots-clés prédéfinis (par exemple : "non renseigné", "inconnu", "null").
                    - La comparaison est insensible à la casse.
                    - Args:
                      - value (str): La chaîne de caractères à vérifier.
                    - Returns:
                      - bool: True si la valeur est non informative, False sinon.

                - pick
                  - Sélectionne un élément aléatoire dans une séquence donnée.
                  - Cette fonction choisit un élément au hasard parmi ceux de la séquence passée en argument, en utilisant un générateur aléatoire cryptographiquement sûr (`secrets.choice`).
                  - Args:
                    - options (Sequence[T]): La séquence d'éléments parmi lesquels choisir.
                    - debug (bool, optionnel): Si True, affiche en console la valeur choisie pour faciliter le débogage. Par défaut False.
                  - Returns:
                    - T: L'élément choisi aléatoirement dans la séquence.

                - _gaussian_age_weights
                  - Calcule les poids d'une loi normale tronquée pour des âges entiers.
                  - Génère une distribution discrète d'âges (entiers) comprise entre `lo` et `hi`, centrée sur `mu` avec un écart-type `sigma`. Retourne également la CDF (somme cumulée) pour faire un échantillonnage inverse.
                  - Args:
                    - mu (int): Moyenne ciblée de l'âge (par défaut 83).
                    - sigma (float): Écart-type (par défaut 6.5).
                    - lo (int): Âge minimum (inclus).
                    - hi (int): Âge maximum (inclus).
                    - Returns:
                      - tuple[list[int], list[float]]: (liste des âges, CDF correspondante).

                - _sample_age
                  - Retourne une valeur d'âge aléatoire.
                  - L'âge est tiré dans une plage réaliste pour les patients du jeu de données.
                  - Cette fonction est principalement utilisée lors de l'anonymisation ou du remplacement d'informations sensibles de date de naissance par un âge approximatif.
                  - Returns:
                    - int: Un entier pseudo-aléatoire représentant un âge.

                - _sample_dob_from_age
                  - Génère une date de naissance pseudo-aléatoire à partir d'un âge donné.
                  - La fonction calcule une année de naissance approximative à partir de l'âge fourni puis attribue aléatoirement un mois et un jour. Elle est utilisée pour l'anonymisation lorsqu'on ne conserve que l'âge et qu'une date de naissance synthétique mais réaliste est nécessaire.
                  - Args:
                    - age (int): L'âge de la personne.
                  - Returns:
                    - str: Une date de naissance synthétique au format ISO (YYYY-MM-DD).

                - _anonymize_usager_dob_full
                  - Anonymise la date de naissance complète de la section 'usager' dans un document patient.
                  - Cette fonction remplace la date de naissance originale par une date synthétique générée à partir d'un âge pseudo-aléatoire. Le dictionnaire de correspondance entre valeurs originales et anonymisées est mis à jour pour permettre une désanonymisation ultérieure.
                  - Args:
                    - usager (Dict[str, Any]): Le dictionnaire contenant les informations du patient.
                    - mapping (Dict[str, str]): Le dictionnaire stockant les correspondances d’anonymisation.
                    - debug (bool, optionnel): Si True, affiche des messages de débogage. Par défaut False.
                  - Returns:
                    - Dict[str, Any]: Le dictionnaire 'usager' mis à jour avec la date de naissance anonymisée.

                - _anonymize_contact_dob_full
                  - Remplace la date de naissance du contact par une date fictive.
                  - Utilise la distribution d'âges (gaussienne tronquée 60-100, μ≈83, σ≈6.5), puis construit une date ISO (YYYY-MM-DD) avec jour 1-28 et mois 1-12.
                  - Args:
                    - doc (Dict[str, Any]): Document JSON complet (modifié sur place).
                    - path (List[str]): Chemin du champ date de naissance du contact.
                    - mapping (Dict[str, str]): Mapping {valeur_anon: valeur_originale}.
                    - debug (bool, optionnel): Active les traces de débogage.

                - build_usager_persona
                  - Construit une identité fictive (« persona ») pour l'usager.
                  - Génère des informations cohérentes pour les champs à anonymiser, (nom, prénom, adresse, code postal, commune). Le choix des prénoms, tient compte du sexe si celui-ci est précisé.
                  - Args:
                    - gender (str | None, optionnel): Sexe détecté de l'usager, ("Masculin" ou "Féminin"). Si None, le sexe est choisi au hasard.
                    - debug (bool, optionnel): Si True, affiche les valeurs choisies.
                    - Par défaut False.
                  - Returns:
                    - Dict[str, Any]: Dictionnaire contenant les champs anonymisés, (nom, prénom, adresse, etc.).

                - detect_genre_contact
                  - Détecte le genre d'un contact à partir de sa civilité.
                  - Args:
                    - contact (Dict[str, Any]): Dictionnaire du contact.
                  - Returns:
                    - Optional[str]: « M », « F » ou None.

                - build_contact_persona
                  - Construit une persona française pour un contact.
                  - Génère un prénom (selon le genre si connu), un nom, et une date de naissance fictive cohérente avec la distribution d'âges (gaussienne tronquée 60-100, moyenne ~83).
                  - Args:
                    - gender (Optional[str]): « Masculin », « Féminin » ou None.
                    - debug (bool, optionnel): Si True, affiche les valeurs choisies.
                  - Returns:
                    - Dict[str, Any]: Dictionnaire de persona pour le contact.

                - _contact_paths
                  - Construit les chemins (paths) à anonymiser pour un contact donné.
                  - Les listes étant indexées, on génère les chemins pour l'index `index`.
                  - Args:
                    - index (int): Index du contact dans `doc['contacts']`.
                  - Returns:
                    - Dict[str, List[str]]: Dictionnaire {clé_logique: path_list}.

                - _ensure_path_dict
                  - Crée récursivement les clés manquantes dans un dictionnaire pour un chemin donné.
                  - Si certaines clés du chemin n'existent pas, elles sont initialisées avec des dictionnaires vides jusqu'à atteindre la profondeur souhaitée.
                  - Args:
                    - d (Dict[str, Any]): Le dictionnaire racine.
                    - path (List[str]): Liste des clés représentant le chemin à créer.
                  - Returns:
                    - Dict[str, Any]: Le dictionnaire correspondant à la dernière clé du chemin.

                - _get_at_path
                  - Récupère la valeur d'un dictionnaire en suivant un chemin de clés.
                  - Args:
                    - d (Dict[str, Any]): Le dictionnaire dans lequel chercher.
                    - path (List[str]): Liste des clés successives menant à la valeur.
                  - Returns:
                    - Any: La valeur trouvée ou None si une clé du chemin n'existe pas.

                - _set_at_path
                  - Définit une valeur dans un dictionnaire en suivant un chemin de clés.
                  - Si certaines clés du chemin n'existent pas, elles sont créées.
                  - Args:
                    - d (Dict[str, Any]): Le dictionnaire dans lequel écrire.
                    - path (List[str]): Liste des clés successives menant à la valeur.
                    - value (Any): La valeur à affecter.

                - _replace_and_map
                  - Remplace la valeur à `path` par la version anonymisée et met à jour le mapping {anon -> orig}.
                  - Garde la bijectivité : jamais deux originaux pour le même anonymisé (ajoute un suffixe si collision).
                  - Args:
                    - d (Dict[str, Any]): Le dictionnaire à modifier.
                    - path (List[str]): Liste des clés menant à la valeur à remplacer.
                    - new_value (Any): La valeur anonymisée qui remplace l'ancienne.
                    - mapping (Dict[str, str]): Dictionnaire de correspondance {valeur_anonymisée: valeur_originale}.
                    - debug (bool, optionnel): Si True, affiche les valeurs remplacées.
                    - Par défaut False.

                - detect_genre_usager
                    - Retourne 'M', 'F' ou None si indéterminé.
                    - Cherche d'abord dans usager['Informations d'état civil']['personnePhysique'].
                    - Si la valeur est absente ou non conforme, la fonction renvoie None.
                    - Args:
                      - usager_dict (Dict[str, Any]): Le sous-dictionnaire représentant la section « usager » du document JSON.
                    - Returns:
                      - str | None: « M », « F » ou None si indéterminé.

                - _replace_with_original
                  - appelle _get_at_path
                  - appelle _replace_and_map

                - anonymize_usager_fields
                  - Anonymise les champs sensibles de la section « usager » dans les données JSON.
                  - Construit un persona fictif pour l’usager (nom, prénom, adresse, etc.), puis remplace les valeurs originales par celles générées.
                  - Retourne également le mapping entre les valeurs anonymisées et les valeurs originales.
                  - Args:
                    - data (Dict[str, Any]): Données JSON de l’usager.
                    - debug (bool, optionnel): Si True, affiche les remplacements effectués.
                    - Par défaut False.
                  - Returns:
                    - Tuple[Dict[str, Any], Dict[str, str]]:
                      - Les données avec les champs anonymisés.
                      - Le mapping {valeur_anonymisée: valeur_originale}.

                - anonymize_contacts_fields
                  - Anonymise les champs des contacts (0..N) et alimente le mapping.
                  - Pour chaque contact, la fonction :
                    - Détecte le genre via la civilité (si possible).
                    - Construit une persona (civilité, prénom, nom, DOB fictive).
                  - Args:
                    - doc (Dict[str, Any]): Document JSON du patient (modifié sur place).
                    - mapping (Dict[str, str]): Mapping global {valeur_anon: valeur_originale}.
                    - debug (bool, optionnel): Active les messages de débogage.
                    - Returns:
                    - Dict[str, Any]: Le document JSON modifié (pour chaînage éventuel).

        - Module appelé:
          - **Nom: free_text_name_anonymizer.py (src/func/free_text_name_anonymizer.py)**
          - Rôle: Anonymisation de l'usager via persona française (session-aléatoire).
          - Docstring:
            - Ce module fournit :
              - Ce module gère l'anonymisation et la désanonymisation des mentions libres du nom et prénom du patient dans un POA (Plan d'Objectifs et d'Actions).
              - Contrairement à l'anonymisation structurée (sections « usager » et « contacts »), les informations saisies manuellement par les évaluateurs peuvent contenir le nom ou le prénom du patient dans des champs texte libres (ex. « Mme Anne Dupont, son épouse est présente »).
              - Fonctionnalités principales :
              - Normalisation des chaînes (suppression des accents, casse insensible, gestion des espaces Unicode).
              - Construction de variantes (nom, prénom, « Prénom Nom », « Nom Prénom », civilités + nom, civilités + prénom + nom).
              - Parcours récursif des structures de type dict/list pour détecter les chaînes contenant le nom/prénom du patient.
              - Remplacement par l'alias choisi lors de l'anonymisation structurée.
              - Mise à jour du mapping {alias -> original} pour permettre la désanonymisation correcte de la réponse du LLM.

            - Fonctions:
              - **Fonction principale:**
                - anonymize_name_mentions_in_free_text
                  - docstring:
                    - Remplace, hors sections 'usager' et 'contacts', les mentions libres du nom/prénom du patient par l'alias (persona) et renvoie (document_modifié, mapping_enrichi).
                    - Récupère le couple (prénom/nom) alias dans le document anonymisé, et les originaux en inversant le mapping {anonymisé -> original}.
                    - Construit des variantes texte (Nom, Prénom, "Prénom Nom", "Nom Prénom", civilités + Nom) pour maximiser la détection.
                    - Parcourt récursivement toutes les chaînes du document (dict/list), en **ignorant** explicitement les sections 'usager' et 'contacts'.
                    - Remplace les occurrences par l'alias approprié et **enrichit** le mapping avec des paires {anonymisé -> original} utiles à la désanonymisation LLM.
                    - Remarques :
                      - L'entrée peut être un dict ou un tuple (dict, changes) retourné par `clean_patient_document(trace=True)` ; dans ce cas seul le dict est modifié.
                      - La comparaison est insensible à la casse et aux accents.
                      - Le mapping est mis à jour **in-place** et aussi renvoyé pour chaînage.
                      - Args:
                        - data_or_tuple: Document patient (dict) ou (dict, changes).
                        - mapping_anon_to_orig: Mapping existant {anonymisé -> original} à enrichir.
                        - debug: Active les messages de débogage.
                      - Returns:
                        - Tuple[Dict[str, Any], Dict[str, str]]:
                          - Le document modifié (dict anonymisé côté texte libre).
                          - Le mapping {anonymisé -> original} enrichi.
              - **Fonctions appelées:**
                - _strip_accents_casefold
                  - Normalise une chaîne en supprimant les accents et en ignorant la casse.
                  - La chaîne est décomposée (NFD), les diacritiques sont retirés, tous les types d'espaces Unicode sont comprimés en un seul espace, puis `casefold()` est appliqué pour des comparaisons robustes (mieux que `lower()`).
                  - Args:
                    - s (str): La chaîne d'entrée.
                  - Returns:
                    - str: La chaîne normalisée (sans accents, casse normalisée, espaces compressés).

                - _debug_dump
                  - Retourne une représentation des points de code Unicode d'une chaîne.
                  - Utile pour diagnostiquer des problèmes d'encodage ou d'espaces invisibles (ex. espaces insécables). Chaque caractère est affiché avec sa valeur hexadécimale (ex. ' '(0x00a0) pour NBSP).
                  - Args:
                    - s (str): La chaîne à inspecter.
                  - Returns:
                    - str: Une chaîne listant les caractères et leurs points de code.

                - _iter_string_fields
                  - Itère récursivement sur tous les champs texte d’une structure Python.
                  - Parcourt dictionnaires et listes imbriqués, et produit des couples (chemin, valeur) pour chaque champ de type `str`. Le chemin est une liste de clés/indices (ex. ["social", "blocs", "[0]", "reponse"]).
                  - Args:
                    - obj (Any): Structure Python (dict, list, scalaires).
                    - path (List[str] | None, optionnel): Chemin courant lors de la récursion.
                  - Returns:
                    - Iterable[Tuple[List[str], str]]: Couples (path, value) pour chaque chaîne trouvée.

                - _get_parent_and_key
                  - Retourne le conteneur parent et la clé/position finale pour un chemin donné.
                  - Permet de réassigner une nouvelle valeur à l'emplacement ciblé. Gère les dictionnaires et les listes (indices représentés sous la forme "[i]").
                  - Args:
                    - root (Any): Racine de la structure.
                    - path (List[str]): Chemin vers la valeur cible.
                  - Returns:
                    - Tuple[Any, Optional[str]]: (parent, clé_ou_indice_token) ou (None, None) si introuvable.

                - _should_skip_path
                  - Indique si un chemin doit être ignoré (sections déjà traitées).
                  - Retourne True pour les chemins appartenant aux sections 'usager' ou 'contacts', afin d'éviter un retraitement des champs déjà anonymisés de manière structurée.
                  - Args:
                    - path (List[str]): Chemin du champ courant.
                  - Returns:
                    - bool: True si le chemin doit être ignoré, False sinon.

                - _build_variants
                  - Construit des variantes textuelles du nom de l'usager à détecter.
                  - Génère les formes usuelles pour maximiser la détection en texte libre :
                    - nom seul (ex. "Dupont"),
                    - prénom seul (ex. "Anne"),
                    - "Prénom Nom" et "Nom Prénom",
                    - civilités + nom (ex. "M. Dupont", "Madame Dupont"),
                    - civilités + prénom + nom (ex. "Mme Anne Dupont").
                  - Args:
                    - first_name (str): Prénom original de l'usager.
                    - last_name (str): Nom original de l'usager.
                  - Returns:
                    - List[str]: Liste dédupliquée de variantes à rechercher/remplacer.

                - _compile_variants_regex
                  - Compile un motif regex robuste couvrant toutes les variantes.
                  - Les variantes sont d'abord normalisées (sans accents, casse insensible, espaces Unicode compressés). Le motif résultant tolère des espaces multiples (`\\s+`) entre les tokens et utilise des bords de mots (`\\b`).
                  - Args:
                    - variants (List[str]): Variantes brutes (non normalisées).
                  - Returns:
                    - Tuple[re.Pattern, Dict[str, str]]:
                      - Motif regex compilé pour rechercher les variantes dans du texte normalisé.
                      - Dictionnaire {forme_normalisée: forme_originale} pour retrouver la variante source.

                - _replacement_for_variant
                  - Détermine la chaîne de remplacement (alias) adaptée à une variante rencontrée.
                  - Respecte la structure de la variante originale :
                    - "Prénom Nom" "ias_first alias_last"
                    - "Nom Prénom"  -> "alias_last alias_first"
                    - civilité + Nom -> même civilité + alias_last
                    - nom seul       -> alias_last
                    - prénom seul    -> alias_first
                    - par défaut     -> "alias_first alias_last"
                  - Args:
                    - original_variant (str): Variante détectée dans le texte.
                    - orig_first (str): Prénom original.
                    - orig_last (str): Nom original.
                    - alias_first (str): Prénom alias.
                    - alias_last (str): Nom alias.
                  - Returns:
                    - str: La chaîne de remplacement correspondante.
							
                - _extract_names_from_doc_and_mapping
                  - Extrait (orig_first, orig_last, alias_first, alias_last) depuis le doc et le mapping.
                  - Récupère l’alias (prenomUtilise, nomUtilise) dans le document anonymisé et retrouve les valeurs originales en inversant le mapping {anonymisé -> original}.
                  - Retourne None si une information nécessaire est manquante.
                  - Args:
                    - doc_anon (Dict[str, Any]): Document anonymisé (section usager incluse).
                    - mapping_anon_to_orig (Dict[str, str]): Mapping {anonymisé -> original}.
                  - Returns:
                    - Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
                    - (orig_first, orig_last, alias_first, alias_last).
								
      - convert_json_to_text.py (src/utils/convert_json_text.py)
        - Convertit un dossier patient au format JSON en texte libre lisible par un LLM.
        - Parcourt dynamiquement chaque bloc (usager, contacts, aggir, social, sante, dispositifs, poa*) et toutes leurs sous-branches, avec un repli récursif générique pour ne rien perdre si le schéma évolue.
        - Normalise le texte (Unicode NFKC, “smart title” français pour MAJUSCULES), ainsi que dates, booléens et nombres.
        - Gère AGGIR en ne lisant que la clé 'Resultat' (sans espace) et en aplatissant variables/sous-variables/adverbes.
        - Supporte 0..n contacts et variabilité des champs (synonymes, listes/chaînes).
        - Retourne une chaîne structurée par sections.

        - **Fonction principale:**
          - convert_json_to_text
            - Formate la section « poaAutonomie » en lignes de texte.
            - Parcourt dynamiquement `actions[]` et restitue les champs connus (type d’action, personnes en charge, jours, date de début, durée, moments, types d’aide, actions, détails), avec normalisation souple.
            - Args:
              - data (Json): Dossier patient complet sous forme de dict JSON.
            - Returns:
              - List[str]: Lignes de texte prêtes à être concaténées pour la sortie.

        - **Fonctions appelées:**
          - _strip_diacritics
            - Enlève les diacritiques (pour comparaisons éventuelles).

          - _smart_title_fr
            - Met en 'Title Case' à la française :
              - Si le mot est un ACRONYME (IPA/CHU/HAS/ADMR…), on le garde en MAJ.
              - Petits mots (de/du/des/d'/la/le/les/aux/au/et/ou) en minuscules sauf s'ils sont en début de chaîne.
              - Gère d', l' → d’Alzon, l’Hôpital (guillemets typographiques ’).

          - _looks_shouting
            - ALL CAPS: au moins 80% des lettres alpha sont majuscules.

          - _as_list

          - _norm_text
            - Normalise un texte :
              - Unicode NFKC (cohérence accents/ligatures)
              - trim + collapse des espaces
              - Casse :
                - case_mode='keep'  → ne touche pas à la casse
                - case_mode='lower' → minuscules
                - case_mode='upper' → MAJ
                - case_mode='title' → Smart title FR
                - case_mode='auto'  → si ALL CAPS → smart title, sinon conserve

          - _norm_bool

          - _norm_date

          - _norm_number

          - _join

          - _pick
            - Retourne la première clé présente dans d parmi keys (utile pour synonymes).

          - _addr_line

          - _flatten_unknown
            - Dump récursif générique pour ne rien perdre si le schéma évolue :
            - dict → descend dans les clés
            - list → énumère les éléments
            - atomique → affiche la valeur

          - _section_usager
            - Formate la section « usager » du dossier patient en lignes de texte.
            - Extrait l’état civil, l’adresse et les coordonnées personnelles depuis `usager`, en gérant les variantes de schéma (ex. adresse.ligne en liste ou en chaîne) et en normalisant la casse/diacritiques.
            - Args:
              - data (Json): Dossier patient complet sous forme de dict JSON.
            - Returns:
              - List[str]: Lignes de texte prêtes à être concaténées pour la sortie.

            - _section_contacts
              - Formate la section « contacts » (0..n) en lignes de texte.
              - Lit dynamiquement les contacts au niveau racine, gère l’absence éventuelle de contacts, normalise les champs (noms, téléphones, emails) et affiche un repli générique récursif pour toute sous-branche non standard.
              - Args:
                - data (Json): Dossier patient complet sous forme de dict JSON.
              - Returns:
                - List[str]: Lignes de texte prêtes à être concaténées pour la sortie.

          - _section_aggir
            - Formate la section « AGGIR » en lignes de texte prêtes à l’affichage.
            - Extrait GIR, date de modification et Temps d’aide/24h, puis aplatit AggirVariable/SousVariable en ne lisant que la clé « Resultat » (sans espace) et en restituant les adverbes S/T/C/H, avec normalisation des champs.
            - Args:
              - data (Json): Dossier patient complet sous forme de dict JSON.
            - Returns:
              - List[str]: Lignes de texte pour la section AGGIR.

          - _section_blocs
            - Formate une section à blocs (ex. « social », « sante ») en lignes de texte.
            - Parcourt dynamiquement `blocs[]`, restitue les paires question/réponse, les tests (nom, résultat, date) et les mesures éventuelles, puis applique un repli récursif générique pour toute sous-branche non prévue.
            - Args:
              - data (Json): Dossier patient complet sous forme de dict JSON.
              - section_key (str): Clé top-level de la section à traiter (p. ex. "social", "sante").
              - title (str): Titre d’affichage pour la section.
              - Returns:
                - List[str]: Lignes de texte prêtes à être concaténées pour la sortie.

          - _section_dispositifs_materiels
            - Formate les sections « dispositifs » et « matériels » en lignes de texte.
            - Parcourt dynamiquement les listes hétérogènes (schémas variables selon les dossiers), extrait toutes les paires clé:valeur non vides et normalise le rendu pour une lecture cohérente par un LLM.
            - Args:
              - data (Json): Dossier patient complet sous forme de dict JSON.
            - Returns:
              - List[str]: Lignes de texte pour les sections Dispositifs et Matériels.

          - _section_poa_problemes
            - Formate une section POA à « problèmes » (poaSocial/poaSante) en texte.
            - Parcourt dynamiquement `problemes[]`, restitue nom de bloc, statut, problème posé, objectifs et préoccupations, puis détaille chaque action de `planActions[]` en listant toutes les paires clé=valeur pertinentes.
            - Args:
              - data (Json): Dossier patient complet sous forme de dict JSON.
              - key (str): Clé top-level de la section à traiter (ex. "poaSocial", "poaSante").
              - title (str): Titre d’affichage pour la section.
            - Returns:
              - List[str]: Lignes de texte prêtes à être concaténées pour la sortie.

          - _section_poa_autonomie
            - Formate la section « poaAutonomie » en lignes de texte.
            - Parcourt dynamiquement `actions[]` et restitue les champs connus (type d’action, personnes en charge, jours, date de début, durée, moments, types d’aide, actions, détails), avec normalisation souple.
            - Args:
              - data (Json): Dossier patient complet sous forme de dict JSON.
            - Returns:
              - List[str]: Lignes de texte prêtes à être concaténées pour la sortie.

        - llm_prompt_template_medical_plan 
          - Construit un prompt structuré destiné à un LLM pour générer un plan médical personnalisé. 
          - Utilise un prompt système spécialisé dans l’analyse du POA et la production de recommandations médicales synthétiques. 
          - Returns:
            - ChatPromptTemplate: Template de prompt prêt à être utilisé avec un LLM.

        - medical_prompt_template 
          - Création du template de prompt

        - medical_response_from_llm 
          - Exécute un prompt de type médical via un LLM à partir du POA du patient et de la requête utilisateur.
          - Args:
            - prompt_template (ChatPromptTemplate): Prompt à utiliser pour interroger le LLM. 
            - user_input (str): Requête de l'utilisateur. 
            - poa_content (str): Contenu du document POA du patient. 
          - Returns:
            - str: Réponse du modèle, structurée sous forme de texte exploitable. 

        - deanonymize_fields 
          - Remplace dans 'text' toutes les valeurs anonymisées par leurs valeurs originales en utilisant le mapping {anonymisé -> original}. 
          - Args:
            - text (str): Le texte potentiellement contenant des valeurs anonymisées. 
            - mapping_anon_to_orig (Dict[str, str]): Dictionnaire des correspondances. 
            - debug (bool, optionnel): Affiche les substitutions effectuées si True. 
          - Returns:
            - Tuple[str, Dict[str, str]]:
              - Texte désanonymisé (chaîne de caractères). 
              - Reverse mapping {original -> anonymisé} pour usage ultérieur.

## **Nom: generate_structured_medical_plan.py (src/func/generate_structured_medical_plan.py)**
### Rôle: pipeline de génération de recommandations de soins dans le contexte du patient.
### Docstring:
  - Module de génération d’un plan d’action structuré à partir du POA d’un patient.
  - Ce module est déclenché lorsque l’intention « generate_recommendations » est détectée.
  - Il extrait le nom du patient, charge et nettoie le document POA, anonymise les données, puis interroge un modèle LLM avec un prompt enrichi pour générer des recommandations classées (par type d'action : prévention, soins, traitements, etc.).

    - Fonctions:
      - **Fonction principale:**
        - generate_structured_medical_plan
          - Génère un plan d’action structuré à partir du POA du patient mentionné dans la requête utilisateur.
          - Étapes :
            - Extraction du nom du patient.
            - Chargement et nettoyage du fichier POA.
            - Anonymisation des données.
            - Conversion en texte structuré.
            - Génération de recommandations via un modèle LLM.
            - Désanonymisation de la réponse.
          - Args:
            - user_input (str): Requête utilisateur contenant le nom du patient.
            - system_prompt (str): Prompt système de base transmis au modèle.
          - Returns:
            - tuple:
              - str : Recommandations structurées par type d’action médicale.
              - dict : Dictionnaire de mapping d’anonymisation utilisé.

      - **Fonctions appelées:**
	    - extract_patient_name_llm (src/func/extract_patient_name.py)
	      - Module pour l'extraction du nom du patient à partir d'une requête utilisateur.
	      - Ce module utilise un LLM pour analyser une phrase en langage naturel et en extraire uniquement le nom de famille du patient mentionné.

	    - extract_relevant_info (src/func/detect_poa_file_path.py)
	      - Module de détection du chemin du fichier patient.
	      - Ce module fournit une fonction pour localiser automatiquement un fichier contenant les données d'un patient, à partir de son nom, dans le dossier `src/data/poa_patients`.

	    - load_patient_file (src/func/poa_loader.py)
	      - Module de chargement des fichiers POA (Plan d'Objectifs et d'Actions) au format JSON.
	      - Ce module permet de localiser et lire un fichier patient stocké dans le dossier `data/poa_patients/`.

	    - Module appelé:
	      - **Nom: poa_cleaning.py (src/func/poa_cleaning.py)**
	      - Rôle: Module de nettoyage des documents POA (Plan d’Objectifs et d'Actions).
	      - Docstring:
	        - clean_patient_document(data: dict, trace: bool = False) -> dict | (dict, list[str])
	        - Comportement :
	          - supprime les champs vides / non informatifs ("", "non renseigné", "null")
	          - supprime les champs sensibles explicitement demandés (usager + contacts)
	          - émonde les conteneurs (dict/list) devenus vides
              - (optionnel) trace chaque suppression si trace=True
	        - Args : dict (JSON patient)
	        - Returns :
	          - si trace=False : dict nettoyé
	          - si trace=True  : (dict nettoyé, liste des suppressions)

	      - Fonctions:
	        - **Fonction principale:**
	          - clean_patient_document
	            - Nettoie récursivement un document JSON de patient :
	              - supprime les champs vides / non informatifs
	              - supprime les champs sensibles explicitement listés (usager + contacts)
	              - émonde les conteneurs vides
	              - (optionnel) trace chaque suppression
	            - Args:
	              - data: Dictionnaire représentant le contenu brut du document POA.
	              - trace: Si True, retourne aussi la liste des suppressions (changes).
	            - Returns:
	              - dict nettoyé, ou (dict nettoyé, changes) si trace=True.
	              - Attention ! si trace == True, on sort avec un tuple.

	        - **Fonctions appelées par le module src/func/poa_cleaning.py:**
              - _is_empty_scalar
	            - Vérifie si une valeur est considérée comme un scalaire vide.
	            - Sont considérés comme vides : None, les chaînes vides et les collections vides. Cette fonction est utilisée pour simplifier le nettoyage récursif des documents patients.
	          - Args:
	            - v (Any): La valeur à vérifier.
	          - Returns:
	            - bool: True si la valeur est vide, False sinon.

            - _pop_in
              - Supprime une clé dans un dictionnaire imbriqué et enregistre le changement.
              - Si la clé existe, elle est supprimée. L’opération peut être tracée en ajoutant le chemin de suppression à la liste des changements.
              - Args:
                - d (Dict[str, Any]): Le dictionnaire à modifier.
                - key (str): La clé à supprimer.
                - changes (List[str] | None, optionnel): Liste des chemins supprimés pour traçabilité.
                - path (str, optionnel): Chemin courant dans la structure. Par défaut "".
                - Returns:
                  - None

            - _get
              - Récupère une valeur dans un dictionnaire imbriqué en suivant un chemin de clés.
              - La fonction parcourt le dictionnaire étape par étape avec les clés données.
              - Retourne None si une clé intermédiaire n'existe pas.
              - Args:
                - d (Dict[str, Any]): Le dictionnaire à parcourir.
                - *path: Séquence de clés représentant le chemin d'accès.
                - Returns:
                  - Any: La valeur trouvée, ou None si inexistante.

            - _ensure_dict
              - Garantit qu'un chemin imbriqué existe dans un dictionnaire sous forme de dictionnaire.
              - Si le chemin n'existe pas, les dictionnaires intermédiaires nécessaires sont créés. Retourne le dictionnaire final au bout du chemin.
              - Args:
                - d (Dict[str, Any]): Le dictionnaire à compléter.
                - *path: Séquence de clés représentant le chemin à garantir.
              - Returns:
                - Dict[str, Any]: Le dictionnaire correspondant au chemin demandé.

            - _clean_rec
                - Nettoie récursivement les valeurs vides dans une structure.
                - Supprime les None, chaînes vides et conteneurs vides (listes, dictionnaires) dans une structure imbriquée.
            - Les suppressions peuvent être enregistrées pour audit.
            - Args:
              - value (Any): La valeur à nettoyer (dict, list ou scalaire).
              - changes (List[str] | None, optionnel): Liste des chemins supprimés.
              - path (str, optionnel): Chemin courant utilisé pour la traçabilité.
            - Returns:
              - Any: La valeur nettoyée, ou None si vide.

            - _remove_usager_sensitive_fields
                - Supprime les champs sensibles dans la section 'usager' d'un document patient.
                - Les champs supprimés concernent les informations identifiantes (adresse, téléphone, identifiants, etc.). Les suppressions peuvent être enregistrées pour traçabilité.
                - Args:
                    - data (Dict[str, Any]): Le document patient sous forme de dictionnaire.
                    - changes (List[str] | None, optionnel): Liste des champs supprimés.
                - Returns:
                  - None

            - _remove_contacts_sensitive_fields
                - Supprime les champs sensibles dans la section 'contacts' d'un document patient.
                - L'anonymisation ne s'applique qu'aux contacts de type 'Cercle d'aide et de soin' ou 'Entourage'. Certains champs exclus restent conservés selon les règles définies.
                - Args:
                    - data (Dict[str, Any]): Le document patient sous forme de dictionnaire.
                    - changes (List[str] | None, optionnel): Liste des champs supprimés.
                - Returns:
                    - None

            - _prune_empty_containers
                - Supprime récursivement les conteneurs vides (dictionnaires ou listes).
                - Parcourt la structure et supprime les conteneurs devenus vides après nettoyage. Les suppressions peuvent être enregistrées pour traçabilité.
                - Args:
                    - d (Any): La structure à nettoyer (dict, list, scalaire).
                    - changes (List[str] | None, optionnel): Liste des chemins supprimés.
                    - path (str, optionnel): Chemin courant utilisé pour la traçabilité.
                - Returns:
                    - Any: La structure nettoyée, ou None si elle est vide.

        - Module appelé:
            - **Nom: anonymizer.py (src/func/anonymizer.py)**
            - Rôle: Anonymisation de l'usager via persona française (session-aléatoire).
            - Docstring:
              - Ce module fournit :
                - Des pools de valeurs françaises (prénoms, noms, voies, codes postaux/communes).
                - La création d'une persona cohérente pour l'usager (prénom selon le genre, nom, adresse, CP/commune).
                - Des utilitaires pour lire/écrire dans un dictionnaire JSON par chemins imbriqués.
                - Une anonymisation ciblée des champs usager listés.
                - La construction d'un mapping {valeur_anonymisée: valeur_originale} pour la désanonymisation.
                - Entrée : dict JSON (document patient).
                - Sortie : Tuple[Any, Dict[str, str]] -> (document anonymisé, mapping).

            - Fonctions:
              - **Fonction principale:**
                - anonymize_patient_document
                - Docstring: Anonymise l'usager puis (le cas échéant) les contacts et retourne (doc, mapping).

              - **Fonctions appelées:**
                - _normalize_token
                  - minuscule, accents retirés, espaces/ponctuation enlevés aux extrémités
                  - Args:
                    - value (str): La chaîne de caractères à normaliser.
                  - Returns:
                    - str: La chaîne transformée.

                - _detect_from_fields
                  - Détermine 'M'/'F' en priorisant le champ 'sexe' s'il est exploitable, sinon en se rabattant sur 'civilite'. Retourne None si indéterminé.

                - _is_non_informatif
                    - Vérifie si une valeur est considérée comme non informative.
                    - Une valeur est jugée non informative si elle correspond à l'un des mots-clés prédéfinis (par exemple : "non renseigné", "inconnu", "null").
                    - La comparaison est insensible à la casse.
                    - Args:
                      - value (str): La chaîne de caractères à vérifier.
                    - Returns:
                      - bool: True si la valeur est non informative, False sinon.

                - pick
                  - Sélectionne un élément aléatoire dans une séquence donnée.
                  - Cette fonction choisit un élément au hasard parmi ceux de la séquence passée en argument, en utilisant un générateur aléatoire cryptographiquement sûr (`secrets.choice`).
                  - Args:
                    - options (Sequence[T]): La séquence d'éléments parmi lesquels choisir.
                    - debug (bool, optionnel): Si True, affiche en console la valeur choisie pour faciliter le débogage. Par défaut False.
                  - Returns:
                    - T: L'élément choisi aléatoirement dans la séquence.

                - _gaussian_age_weights
                  - Calcule les poids d'une loi normale tronquée pour des âges entiers.
                  - Génère une distribution discrète d'âges (entiers) comprise entre `lo` et `hi`, centrée sur `mu` avec un écart-type `sigma`. Retourne également la CDF (somme cumulée) pour faire un échantillonnage inverse.
                  - Args:
                    - mu (int): Moyenne ciblée de l'âge (par défaut 83).
                    - sigma (float): Écart-type (par défaut 6.5).
                    - lo (int): Âge minimum (inclus).
                    - hi (int): Âge maximum (inclus).
                    - Returns:
                      - tuple[list[int], list[float]]: (liste des âges, CDF correspondante).

                - _sample_age
                  - Retourne une valeur d'âge aléatoire.
                  - L'âge est tiré dans une plage réaliste pour les patients du jeu de données.
                  - Cette fonction est principalement utilisée lors de l'anonymisation ou du remplacement d'informations sensibles de date de naissance par un âge approximatif.
                  - Returns:
                    - int: Un entier pseudo-aléatoire représentant un âge.

                - _sample_dob_from_age
                  - Génère une date de naissance pseudo-aléatoire à partir d'un âge donné.
                  - La fonction calcule une année de naissance approximative à partir de l'âge fourni puis attribue aléatoirement un mois et un jour. Elle est utilisée pour l'anonymisation lorsqu'on ne conserve que l'âge et qu'une date de naissance synthétique mais réaliste est nécessaire.
                  - Args:
                    - age (int): L'âge de la personne.
                  - Returns:
                    - str: Une date de naissance synthétique au format ISO (YYYY-MM-DD).

                - _anonymize_usager_dob_full
                  - Anonymise la date de naissance complète de la section 'usager' dans un document patient.
                  - Cette fonction remplace la date de naissance originale par une date synthétique générée à partir d'un âge pseudo-aléatoire. Le dictionnaire de correspondance entre valeurs originales et anonymisées est mis à jour pour permettre une désanonymisation ultérieure.
                  - Args:
                    - usager (Dict[str, Any]): Le dictionnaire contenant les informations du patient.
                    - mapping (Dict[str, str]): Le dictionnaire stockant les correspondances d’anonymisation.
                    - debug (bool, optionnel): Si True, affiche des messages de débogage. Par défaut False.
                  - Returns:
                    - Dict[str, Any]: Le dictionnaire 'usager' mis à jour avec la date de naissance anonymisée.

                - _anonymize_contact_dob_full
                  - Remplace la date de naissance du contact par une date fictive.
                  - Utilise la distribution d'âges (gaussienne tronquée 60-100, μ≈83, σ≈6.5), puis construit une date ISO (YYYY-MM-DD) avec jour 1-28 et mois 1-12.
                  - Args:
                    - doc (Dict[str, Any]): Document JSON complet (modifié sur place).
                    - path (List[str]): Chemin du champ date de naissance du contact.
                    - mapping (Dict[str, str]): Mapping {valeur_anon: valeur_originale}.
                    - debug (bool, optionnel): Active les traces de débogage.

                - build_usager_persona
                  - Construit une identité fictive (« persona ») pour l'usager.
                  - Génère des informations cohérentes pour les champs à anonymiser, (nom, prénom, adresse, code postal, commune). Le choix des prénoms, tient compte du sexe si celui-ci est précisé.
                  - Args:
                    - gender (str | None, optionnel): Sexe détecté de l'usager, ("Masculin" ou "Féminin"). Si None, le sexe est choisi au hasard.
                    - debug (bool, optionnel): Si True, affiche les valeurs choisies.
                    - Par défaut False.
                  - Returns:
                    - Dict[str, Any]: Dictionnaire contenant les champs anonymisés, (nom, prénom, adresse, etc.).

                - detect_genre_contact
                  - Détecte le genre d'un contact à partir de sa civilité.
                  - Args:
                    - contact (Dict[str, Any]): Dictionnaire du contact.
                  - Returns:
                    - Optional[str]: « M », « F » ou None.

                - build_contact_persona
                  - Construit une persona française pour un contact.
                  - Génère un prénom (selon le genre si connu), un nom, et une date de naissance fictive cohérente avec la distribution d'âges (gaussienne tronquée 60-100, moyenne ~83).
                  - Args:
                    - gender (Optional[str]): « Masculin », « Féminin » ou None.
                    - debug (bool, optionnel): Si True, affiche les valeurs choisies.
                  - Returns:
                    - Dict[str, Any]: Dictionnaire de persona pour le contact.

                - _contact_paths
                  - Construit les chemins (paths) à anonymiser pour un contact donné.
                  - Les listes étant indexées, on génère les chemins pour l'index `index`.
                  - Args:
                    - index (int): Index du contact dans `doc['contacts']`.
                  - Returns:
                    - Dict[str, List[str]]: Dictionnaire {clé_logique: path_list}.

                - _ensure_path_dict
                  - Crée récursivement les clés manquantes dans un dictionnaire pour un chemin donné.
                  - Si certaines clés du chemin n'existent pas, elles sont initialisées avec des dictionnaires vides jusqu'à atteindre la profondeur souhaitée.
                  - Args:
                    - d (Dict[str, Any]): Le dictionnaire racine.
                    - path (List[str]): Liste des clés représentant le chemin à créer.
                  - Returns:
                    - Dict[str, Any]: Le dictionnaire correspondant à la dernière clé du chemin.

                - _get_at_path
                  - Récupère la valeur d'un dictionnaire en suivant un chemin de clés.
                  - Args:
                    - d (Dict[str, Any]): Le dictionnaire dans lequel chercher.
                    - path (List[str]): Liste des clés successives menant à la valeur.
                  - Returns:
                    - Any: La valeur trouvée ou None si une clé du chemin n'existe pas.

                - _set_at_path
                  - Définit une valeur dans un dictionnaire en suivant un chemin de clés.
                  - Si certaines clés du chemin n'existent pas, elles sont créées.
                  - Args:
                    - d (Dict[str, Any]): Le dictionnaire dans lequel écrire.
                    - path (List[str]): Liste des clés successives menant à la valeur.
                    - value (Any): La valeur à affecter.

                - _replace_and_map
                  - Remplace la valeur à `path` par la version anonymisée et met à jour le mapping {anon -> orig}.
                  - Garde la bijectivité : jamais deux originaux pour le même anonymisé (ajoute un suffixe si collision).
                  - Args:
                    - d (Dict[str, Any]): Le dictionnaire à modifier.
                    - path (List[str]): Liste des clés menant à la valeur à remplacer.
                    - new_value (Any): La valeur anonymisée qui remplace l'ancienne.
                    - mapping (Dict[str, str]): Dictionnaire de correspondance {valeur_anonymisée: valeur_originale}.
                    - debug (bool, optionnel): Si True, affiche les valeurs remplacées.
                    - Par défaut False.

                - detect_genre_usager
                    - Retourne 'M', 'F' ou None si indéterminé.
                    - Cherche d'abord dans usager['Informations d'état civil']['personnePhysique'].
                    - Si la valeur est absente ou non conforme, la fonction renvoie None.
                    - Args:
                      - usager_dict (Dict[str, Any]): Le sous-dictionnaire représentant la section « usager » du document JSON.
                    - Returns:
                      - str | None: « M », « F » ou None si indéterminé.

                - _replace_with_original
                  - appelle _get_at_path
                  - appelle _replace_and_map

                - anonymize_usager_fields
                  - Anonymise les champs sensibles de la section « usager » dans les données JSON.
                  - Construit un persona fictif pour l’usager (nom, prénom, adresse, etc.), puis remplace les valeurs originales par celles générées.
                  - Retourne également le mapping entre les valeurs anonymisées et les valeurs originales.
                  - Args:
                    - data (Dict[str, Any]): Données JSON de l’usager.
                    - debug (bool, optionnel): Si True, affiche les remplacements effectués.
                    - Par défaut False.
                  - Returns:
                    - Tuple[Dict[str, Any], Dict[str, str]]:
                      - Les données avec les champs anonymisés.
                      - Le mapping {valeur_anonymisée: valeur_originale}.

                - anonymize_contacts_fields
                  - Anonymise les champs des contacts (0..N) et alimente le mapping.
                  - Pour chaque contact, la fonction :
                    - Détecte le genre via la civilité (si possible).
                    - Construit une persona (civilité, prénom, nom, DOB fictive).
                  - Args:
                    - doc (Dict[str, Any]): Document JSON du patient (modifié sur place).
                    - mapping (Dict[str, str]): Mapping global {valeur_anon: valeur_originale}.
                    - debug (bool, optionnel): Active les messages de débogage.
                    - Returns:
                    - Dict[str, Any]: Le document JSON modifié (pour chaînage éventuel).

        - Module appelé:
          - **Nom: free_text_name_anonymizer.py (src/func/free_text_name_anonymizer.py)**
          - Rôle: Anonymisation de l'usager via persona française (session-aléatoire).
          - Docstring:
            - Ce module fournit :
              - Ce module gère l'anonymisation et la désanonymisation des mentions libres du nom et prénom du patient dans un POA (Plan d'Objectifs et d'Actions).
              - Contrairement à l'anonymisation structurée (sections « usager » et « contacts »), les informations saisies manuellement par les évaluateurs peuvent contenir le nom ou le prénom du patient dans des champs texte libres (ex. « Mme Anne Dupont, son épouse est présente »).
              - Fonctionnalités principales :
              - Normalisation des chaînes (suppression des accents, casse insensible, gestion des espaces Unicode).
              - Construction de variantes (nom, prénom, « Prénom Nom », « Nom Prénom », civilités + nom, civilités + prénom + nom).
              - Parcours récursif des structures de type dict/list pour détecter les chaînes contenant le nom/prénom du patient.
              - Remplacement par l'alias choisi lors de l'anonymisation structurée.
              - Mise à jour du mapping {alias -> original} pour permettre la désanonymisation correcte de la réponse du LLM.

            - Fonctions:
              - **Fonction principale:**
                - anonymize_name_mentions_in_free_text
                  - docstring:
                    - Remplace, hors sections 'usager' et 'contacts', les mentions libres du nom/prénom du patient par l'alias (persona) et renvoie (document_modifié, mapping_enrichi).
                    - Récupère le couple (prénom/nom) alias dans le document anonymisé, et les originaux en inversant le mapping {anonymisé -> original}.
                    - Construit des variantes texte (Nom, Prénom, "Prénom Nom", "Nom Prénom", civilités + Nom) pour maximiser la détection.
                    - Parcourt récursivement toutes les chaînes du document (dict/list), en **ignorant** explicitement les sections 'usager' et 'contacts'.
                    - Remplace les occurrences par l'alias approprié et **enrichit** le mapping avec des paires {anonymisé -> original} utiles à la désanonymisation LLM.
                    - Remarques :
                      - L'entrée peut être un dict ou un tuple (dict, changes) retourné par `clean_patient_document(trace=True)` ; dans ce cas seul le dict est modifié.
                      - La comparaison est insensible à la casse et aux accents.
                      - Le mapping est mis à jour **in-place** et aussi renvoyé pour chaînage.
                      - Args:
                        - data_or_tuple: Document patient (dict) ou (dict, changes).
                        - mapping_anon_to_orig: Mapping existant {anonymisé -> original} à enrichir.
                        - debug: Active les messages de débogage.
                      - Returns:
                        - Tuple[Dict[str, Any], Dict[str, str]]:
                          - Le document modifié (dict anonymisé côté texte libre).
                          - Le mapping {anonymisé -> original} enrichi.

              - **Fonctions appelées:**
                - _strip_accents_casefold
                  - Normalise une chaîne en supprimant les accents et en ignorant la casse.
                  - La chaîne est décomposée (NFD), les diacritiques sont retirés, tous les types d'espaces Unicode sont comprimés en un seul espace, puis `casefold()` est appliqué pour des comparaisons robustes (mieux que `lower()`).
                  - Args:
                    - s (str): La chaîne d'entrée.
                  - Returns:
                    - str: La chaîne normalisée (sans accents, casse normalisée, espaces compressés).

                - _debug_dump
                  - Retourne une représentation des points de code Unicode d'une chaîne.
                  - Utile pour diagnostiquer des problèmes d'encodage ou d'espaces invisibles (ex. espaces insécables). Chaque caractère est affiché avec sa valeur hexadécimale (ex. ' '(0x00a0) pour NBSP).
                  - Args:
                    - s (str): La chaîne à inspecter.
                  - Returns:
                    - str: Une chaîne listant les caractères et leurs points de code.

                - _iter_string_fields
                  - Itère récursivement sur tous les champs texte d’une structure Python.
                  - Parcourt dictionnaires et listes imbriqués, et produit des couples (chemin, valeur) pour chaque champ de type `str`. Le chemin est une liste de clés/indices (ex. ["social", "blocs", "[0]", "reponse"]).
                  - Args:
                    - obj (Any): Structure Python (dict, list, scalaires).
                    - path (List[str] | None, optionnel): Chemin courant lors de la récursion.
                  - Returns:
                    - Iterable[Tuple[List[str], str]]: Couples (path, value) pour chaque chaîne trouvée.

                - _get_parent_and_key
                  - Retourne le conteneur parent et la clé/position finale pour un chemin donné.
                  - Permet de réassigner une nouvelle valeur à l'emplacement ciblé. Gère les dictionnaires et les listes (indices représentés sous la forme "[i]").
                  - Args:
                    - root (Any): Racine de la structure.
                    - path (List[str]): Chemin vers la valeur cible.
                  - Returns:
                    - Tuple[Any, Optional[str]]: (parent, clé_ou_indice_token) ou (None, None) si introuvable.

                - _should_skip_path
                  - Indique si un chemin doit être ignoré (sections déjà traitées).
                  - Retourne True pour les chemins appartenant aux sections 'usager' ou 'contacts', afin d'éviter un retraitement des champs déjà anonymisés de manière structurée.
                  - Args:
                    - path (List[str]): Chemin du champ courant.
                  - Returns:
                    - bool: True si le chemin doit être ignoré, False sinon.

                - _build_variants
                  - Construit des variantes textuelles du nom de l'usager à détecter.
                  - Génère les formes usuelles pour maximiser la détection en texte libre :
                    - nom seul (ex. "Dupont"),
                    - prénom seul (ex. "Anne"),
                    - "Prénom Nom" et "Nom Prénom",
                    - civilités + nom (ex. "M. Dupont", "Madame Dupont"),
                    - civilités + prénom + nom (ex. "Mme Anne Dupont").
                  - Args:
                    - first_name (str): Prénom original de l'usager.
                    - last_name (str): Nom original de l'usager.
                  - Returns:
                    - List[str]: Liste dédupliquée de variantes à rechercher/remplacer.

                - _compile_variants_regex
                  - Compile un motif regex robuste couvrant toutes les variantes.
                  - Les variantes sont d'abord normalisées (sans accents, casse insensible, espaces Unicode compressés). Le motif résultant tolère des espaces multiples (`\\s+`) entre les tokens et utilise des bords de mots (`\\b`).
                  - Args:
                    - variants (List[str]): Variantes brutes (non normalisées).
                  - Returns:
                    - Tuple[re.Pattern, Dict[str, str]]:
                      - Motif regex compilé pour rechercher les variantes dans du texte normalisé.
                      - Dictionnaire {forme_normalisée: forme_originale} pour retrouver la variante source.

                - _replacement_for_variant
                  - Détermine la chaîne de remplacement (alias) adaptée à une variante rencontrée.
                  - Respecte la structure de la variante originale :
                    - "Prénom Nom" "ias_first alias_last"
                    - "Nom Prénom"  -> "alias_last alias_first"
                    - civilité + Nom -> même civilité + alias_last
                    - nom seul       -> alias_last
                    - prénom seul    -> alias_first
                    - par défaut     -> "alias_first alias_last"
                  - Args:
                    - original_variant (str): Variante détectée dans le texte.
                    - orig_first (str): Prénom original.
                    - orig_last (str): Nom original.
                    - alias_first (str): Prénom alias.
                    - alias_last (str): Nom alias.
                  - Returns:
                    - str: La chaîne de remplacement correspondante.
							
                - _extract_names_from_doc_and_mapping
                  - Extrait (orig_first, orig_last, alias_first, alias_last) depuis le doc et le mapping.
                  - Récupère l’alias (prenomUtilise, nomUtilise) dans le document anonymisé et retrouve les valeurs originales en inversant le mapping {anonymisé -> original}.
                  - Retourne None si une information nécessaire est manquante.
                  - Args:
                    - doc_anon (Dict[str, Any]): Document anonymisé (section usager incluse).
                    - mapping_anon_to_orig (Dict[str, str]): Mapping {anonymisé -> original}.
                  - Returns:
                    - Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
                    - (orig_first, orig_last, alias_first, alias_last).
								
      - ## Nom: convert_json_to_text.py (src/utils/convert_json_text.py)
      - ### Docstring:
        - Convertit un dossier patient au format JSON en texte libre lisible par un LLM.
        - Parcourt dynamiquement chaque bloc (usager, contacts, aggir, social, sante, dispositifs, poa*) et toutes leurs sous-branches, avec un repli récursif générique pour ne rien perdre si le schéma évolue.
        - Normalise le texte (Unicode NFKC, “smart title” français pour MAJUSCULES), ainsi que dates, booléens et nombres.
        - Gère AGGIR en ne lisant que la clé 'Resultat' (sans espace) et en aplatissant variables/sous-variables/adverbes.
        - Supporte 0..n contacts et variabilité des champs (synonymes, listes/chaînes).
        - Retourne une chaîne structurée par sections.

        - **Fonction principale:**
          - convert_json_to_text
            - Formate la section « poaAutonomie » en lignes de texte.
            - Parcourt dynamiquement `actions[]` et restitue les champs connus (type d’action, personnes en charge, jours, date de début, durée, moments, types d’aide, actions, détails), avec normalisation souple.
            - Args:
              - data (Json): Dossier patient complet sous forme de dict JSON.
            - Returns:
              - List[str]: Lignes de texte prêtes à être concaténées pour la sortie.
              - 
        - **Fonctions appelées:**
          - _strip_diacritics
            - Enlève les diacritiques (pour comparaisons éventuelles).

          - _smart_title_fr
            - Met en 'Title Case' à la française :
              - Si le mot est un ACRONYME (IPA/CHU/HAS/ADMR…), on le garde en MAJ.
              - Petits mots (de/du/des/d'/la/le/les/aux/au/et/ou) en minuscules sauf s'ils sont en début de chaîne.
              - Gère d', l' → d’Alzon, l’Hôpital (guillemets typographiques ’).

          - _looks_shouting
            - ALL CAPS: au moins 80% des lettres alpha sont majuscules.

          - _as_list

          - _norm_text
            - Normalise un texte :
              - Unicode NFKC (cohérence accents/ligatures)
              - trim + collapse des espaces
              - Casse :
                - case_mode='keep'  → ne touche pas à la casse
                - case_mode='lower' → minuscules
                - case_mode='upper' → MAJ
                - case_mode='title' → Smart title FR
                - case_mode='auto'  → si ALL CAPS → smart title, sinon conserve

          - _norm_bool

          - _norm_date

          - _norm_number

          - _join

          - _pick
            - Retourne la première clé présente dans d parmi keys (utile pour synonymes).

          - _addr_line

          - _flatten_unknown
            - Dump récursif générique pour ne rien perdre si le schéma évolue :
            - dict → descend dans les clés
            - list → énumère les éléments
            - atomique → affiche la valeur

          - _section_usager
            - Formate la section « usager » du dossier patient en lignes de texte.
            - Extrait l’état civil, l’adresse et les coordonnées personnelles depuis `usager`, en gérant les variantes de schéma (ex. adresse.ligne en liste ou en chaîne) et en normalisant la casse/diacritiques.
            - Args:
              - data (Json): Dossier patient complet sous forme de dict JSON.
            - Returns:
              - List[str]: Lignes de texte prêtes à être concaténées pour la sortie.

            - _section_contacts
              - Formate la section « contacts » (0..n) en lignes de texte.
              - Lit dynamiquement les contacts au niveau racine, gère l’absence éventuelle de contacts, normalise les champs (noms, téléphones, emails) et affiche un repli générique récursif pour toute sous-branche non standard.
              - Args:
                - data (Json): Dossier patient complet sous forme de dict JSON.
              - Returns:
                - List[str]: Lignes de texte prêtes à être concaténées pour la sortie.

          - _section_aggir
            - Formate la section « AGGIR » en lignes de texte prêtes à l’affichage.
            - Extrait GIR, date de modification et Temps d’aide/24h, puis aplatit AggirVariable/SousVariable en ne lisant que la clé « Resultat » (sans espace) et en restituant les adverbes S/T/C/H, avec normalisation des champs.
            - Args:
              - data (Json): Dossier patient complet sous forme de dict JSON.
            - Returns:
              - List[str]: Lignes de texte pour la section AGGIR.

          - _section_blocs
            - Formate une section à blocs (ex. « social », « sante ») en lignes de texte.
            - Parcourt dynamiquement `blocs[]`, restitue les paires question/réponse, les tests (nom, résultat, date) et les mesures éventuelles, puis applique un repli récursif générique pour toute sous-branche non prévue.
            - Args:
              - data (Json): Dossier patient complet sous forme de dict JSON.
              - section_key (str): Clé top-level de la section à traiter (p. ex. "social", "sante").
              - title (str): Titre d’affichage pour la section.
              - Returns:
                - List[str]: Lignes de texte prêtes à être concaténées pour la sortie.

          - _section_dispositifs_materiels
            - Formate les sections « dispositifs » et « matériels » en lignes de texte.
            - Parcourt dynamiquement les listes hétérogènes (schémas variables selon les dossiers), extrait toutes les paires clé:valeur non vides et normalise le rendu pour une lecture cohérente par un LLM.
            - Args:
              - data (Json): Dossier patient complet sous forme de dict JSON.
            - Returns:
              - List[str]: Lignes de texte pour les sections Dispositifs et Matériels.

          - _section_poa_problemes
            - Formate une section POA à « problèmes » (poaSocial/poaSante) en texte.
            - Parcourt dynamiquement `problemes[]`, restitue nom de bloc, statut, problème posé, objectifs et préoccupations, puis détaille chaque action de `planActions[]` en listant toutes les paires clé=valeur pertinentes.
            - Args:
              - data (Json): Dossier patient complet sous forme de dict JSON.
              - key (str): Clé top-level de la section à traiter (ex. "poaSocial", "poaSante").
              - title (str): Titre d’affichage pour la section.
            - Returns:
              - List[str]: Lignes de texte prêtes à être concaténées pour la sortie.

          - _section_poa_autonomie
            - Formate la section « poaAutonomie » en lignes de texte.
            - Parcourt dynamiquement `actions[]` et restitue les champs connus (type d’action, personnes en charge, jours, date de début, durée, moments, types d’aide, actions, détails), avec normalisation souple.
            - Args:
              - data (Json): Dossier patient complet sous forme de dict JSON.
            - Returns:
              - List[str]: Lignes de texte prêtes à être concaténées pour la sortie.

      - **Module appelé: llm_prompts.py (src/func/llm_prompts.py)**
        - rag_llm_prompt_template_medical_plan 
          - Construit un prompt structuré intégrant des extraits documentaires (RAG) pour générer un plan médical enrichi.
          - Inclut :
            - la requête utilisateur, 
            - le contenu du POA, 
            - les extraits pertinents issus de ChromaDB. 
            - Returns:
              - ChatPromptTemplate: Prompt structuré avec enrichissement documentaire.

        - rag_medical_response_from_llm 
          - Génère une réponse médicale enrichie à partir d'un prompt et de données issues de ChromaDB.
          - Étapes :
            - Récupération des extraits pertinents via RAG. 
            - Formatage des messages pour le LLM. 
            - Génération de la réponse. 
            - Args:
              - prompt_template (ChatPromptTemplate): Template de prompt RAG structuré. 
              - user_input (str): Demande utilisateur. 
              - poa_content (str): Contenu complet du POA du patient. 
            - Returns:
              - str: Réponse du modèle LLM enrichie par les documents référencés.

          - **Module appelé: retrieve_relevant_chunks.py (src/func/retrieve_relevant_chunks.py)**
            - **Fonction principale:**
              - retrieve_relevant_chunks
                - Récupère et formatte les passages les plus pertinents à partir d'une requête utilisateur.
                - Cette fonction interroge deux collections ChromaDB :
                  - d'abord la collection "base_docx" (prioritaire),
                  - puis la collection "base_web" (secondaire).
                - Les extraits les plus proches de la requête sont sélectionnés par similarité vectorielle, puis concaténés et formatés pour être injectés dans le prompt du modèle LLM. 
                - Args:
                  - query: Requête utilisateur ou texte à rechercher.
                  - top_k_docx: Nombre d'extraits à récupérer depuis la base documentaire "docx".
                  - top_k_web: Nombre d'extraits à récupérer depuis la base documentaire "web".
                  - separator: Chaîne utilisée pour séparer les extraits dans le résultat final.
                - Returns:
                  - Une chaîne de texte formatée contenant les extraits les plus pertinents, chacun précédé de son titre et de sa source.

            - **Fonctions appelées:**
              - _url_norm

              - _slug_from_url

              - _display_domain

              - _shorten

              - _pick_title

              - _strip_accents

              - _tfidf_novelty_scores
                - Retourne un array de 'nouveauté' = 1 - cosine_sim(docx_agg, web_i).
                - Plus c'est proche de 1, plus le web est 'différent' des DOCX -> donc complémentaire.

              - _format_results_with_ids
                - DOCX en premier, bornés à docx_limit.
                - WEB complémentaires uniquement (score de nouveauté >= seuil), bornés à web_limit.
                - Si aucun web pertinent retenu: insère un message explicite.

      - deanonymize_fields 
        - Remplace dans 'text' toutes les valeurs anonymisées par leurs valeurs originales en utilisant le mapping {anonymisé -> original}. 
        - Args:
          - text (str): Le texte potentiellement contenant des valeurs anonymisées. 
          - mapping_anon_to_orig (Dict[str, str]): Dictionnaire des correspondances. 
          - debug (bool, optionnel): Affiche les substitutions effectuées si True. 
        - Returns:
          - Tuple[str, Dict[str, str]]:
            - Texte désanonymisé (chaîne de caractères). 
            - Reverse mapping {original -> anonymisé} pour usage ultérieur.

## **Nom: get_patient_constants_graphs.py (src/func/get_patient_constants_graphs.py)**
### Rôle: extraction valeurs de constantes du patient et construction de graphes, tables et détection de valeurs anormales.
### Docstring:
  - Module d'analyse et de visualisation des constantes médicales des patients.
  - Ce module permet :
    - de convertir les constantes brutes issues de la base de données en DataFrame,
    - de détecter des anomalies selon des seuils définis,
    - de générer des graphiques Plotly (poids, tension, température...),
    - de produire des tableaux HTML interactifs pour Dash,
    - de centraliser le traitement dans une fonction complète pour l’interface.
    - Utilisé notamment dans la page chatbot_ui de l’application OBY-IA.

  - Fonctions:
    - **Fonction principale:**
      - process_patient_request_with_constants
        - Pipeline complet de traitement des constantes d’un patient pour l’interface Dash.
        - Charge les données depuis la base, construit les visualisations, détecte les anomalies et génère les blocs HTML à afficher dans l’application.
        - Args:
          - nom (str): Nom du patient. 
        - Returns:
          - Tuple[str, list, html.Div, html.Div]:
            - Message texte pour le chatbot
            - Liste de graphiques Plotly
            - Tableau HTML des constantes
            - Bloc Markdown avec l’analyse des tendances

    - **Fonctions appelées:**
      - get_available_constantes
        - Retourne la liste des tables (constantes disponibles) dans la base SQLite.

        - get_constantes_patient
          - Retourne un dictionnaire de DataFrames pour toutes les constantes disponibles du patient.

        - convert_constants_to_dataframe
          - Convertit un dictionnaire brut de constantes médicales en un DataFrame fusionné.
          - Pour la tension, sépare les valeurs systolique/diastolique.
          - Pour les autres constantes, convertit les valeurs en numérique.
          - Args:
            - constants_dict (dict): Dictionnaire {constante: DataFrame} pour un patient.
          - Returns:
            - pd.DataFrame: DataFrame fusionné avec toutes les constantes disponibles.

        - analyze_constants
          - Analyse les constantes pour détecter des valeurs anormales.
          - Compare les valeurs observées à des seuils définis (poids, température, tension).
          - Marque les anomalies dans le DataFrame et produit un résumé textuel.
          - Args:
            - df (pd.DataFrame): Données des constantes fusionnées.
          - Returns:
            - Tuple[str, str]: (Tableau markdown des données + colonnes _anormal, résumé des anomalies)

        - generate_graphs
          - Génère des graphiques interactifs Plotly pour les constantes médicales.
          - Args:
            - df (pd.DataFrame): Données des constantes.
          - Returns:
            - list: Liste de composants Dash contenant les graphiques.

        - generate_constants_table
          - Crée une table interactive Dash à partir d'un DataFrame de constantes.
          - Args:
            - df (pd.DataFrame): Données des constantes.
          - Returns:
            - dash_table.DataTable: Table interactive à afficher dans l'interface.

## **Nom: run_full_indexing_pipeline.py (src/func/run_full_indexing_pipeline.py)**
### Rôle: Exécuter le pipeline complet d’indexation documentaire utilisant une base chromadb et approche « RAG ».
### Docstring:
  - Module `run_full_indexing_pipeline.py` – Pipeline principal d’indexation documentaire pour OBY-IA.
  - Ce module orchestre la maintenance de l’index vectoriel à partir de deux sources :
    - des fiches au format DOCX (converties en JSON),
    - des pages web de confiance (scrapées en JSON). 
    - Il a pour objectif d'être appelé au démarrage et à chaque événement Watchdog. 
    - Fonctionnement, synthèse :
      - Détection des changements via `detect_changes_and_get_modified_files()` :
        ajouts, modifications, suppressions de fichiers DOCX/WEB, changement de `trusted_web_sites_list.py`.
      - Nettoyage :
        - suppression des JSON dérivés de DOCX supprimés,
        - purge défensive des JSON web si la configuration des sites change.
      - Production des données :
        - conversion DOCX → JSON si des DOCX ont changé,
        - scraping complet/partiel des sites web si nécessaire.
      - Reconstruction des index ChromaDB :
        - réindexation des collections à partir des dossiers JSON présents sur disque.
      - Mise à jour du journal et pose d’un « ready flag ». 
      - Dépendances (importées ailleurs dans le projet) :
        - `detect_changes_and_get_modified_files`, `update_index_journal`
        - `convert_and_save_fiches`
        - `scrape_all_trusted_sites`
        - `get_chroma_client`, `index_documents` (ou `rebuild_collection_from_disk`)
        - constantes de chemins : `INPUT_DOCX`, `JSON_HEALTH_DOC_BASE`,
          `WEB_SITES_JSON_HEALTH_DOC_BASE`, `WEB_SITES_MODULE_PATH`, `BASE_DIR`
      - Notes :
        - Les purges de répertoires sont précédées de vérifications de chemin (résolution absolue, inclusion sous `BASE_DIR`).
        - Les erreurs critiques d’E/S sont loguées sur STDERR.

  - Fonctions:
    - **Fonction principale:**
      - run_full_indexing_pipeline
        - Exécute le pipeline complet de supervision et (ré)indexation.
        - Objectifs :
          - Détecte l’état courant et les diffs (ajouts/modifs/suppressions).
          - Supprime les JSON orphelins issus de DOCX supprimés.
          - Si la configuration des sites change, purge les JSON web puis lance un scraping complet ; sinon, scraping conditionnel si nécessaire.
          - Reconstruit l’index ChromaDB à partir des JSON présents sur disque (DOCX et WEB), si des changements ont été détectés.
          - Recalcule les hachages et met à jour le journal d’indexation.
          - Pose le « ready flag » marquant la fin réussie du processus.
      - Notes :
        - Écrit/écrase des fichiers JSON (conversion DOCX, scraping web). 
        - Purge de dossiers JSON (web) en cas de changement de configuration.
        - (Ré)initialise des collections ChromaDB. 
        - Met à jour le journal d’indexation et le drapeau « ready ». 
      - Raises:
        - RuntimeError: si une incohérence de chemin est détectée lors d’une purge.
        - OSError: en cas d’erreurs E/S non gérées par les « ignore_errors ».
        - Exception: toutes exceptions non interceptées par les appels sous-jacents.
      - Returns:
        - None 
    
    - **Fonctions appelées:**
      - detect_changes_and_get_modified_files (src/func/indexed_health_related_files.py)
        - Détecte les fichiers de santé modifiés depuis la dernière indexation.
        - Vérifie les fichiers :
        - DOCX dans `INPUT_DOCX`
        - JSON web dans `WEB_SITES_JSON_HEALTH_DOC_BASE`
        - Le fichier `trusted_web_sites_list.py`
        - Returns:
          - dict: Dictionnaire contenant :
          - `docx_files_to_index`: fichiers DOCX modifiés
          - `web_files_to_index`: fichiers JSON web modifiés
          - `trusted_sites_py_changed`: booléen indiquant une modification du fichier Python
          - `current_docx_hashes`: nouveaux hash DOCX
          - `current_web_hashes`: nouveaux hash JSON
          - `current_py_hash`: nouveau hash du fichier `.py`
          - `docx_deleted_files`: liste des DOCX supprimés depuis le dernier journal
          - `web_deleted_files`: liste des JSON web supprimés depuis le dernier journal

      - rebuild_collection_from_disk (src/func/index_documents_chromadb.py)
        - Reconstruit entièrement la collection ChromaDB d’un type donné.
        - Objectif: 
          - garantir la cohérence parfaite entre l’état disque (répertoire JSON) et l’index ChromaDB (par ex. après suppressions de fichiers, changements de configuration des sites, migration d’embedding, etc.). 
          - supprime la collection ciblée (si elle existe),
          - (re)crée et réindexe la collection en appelant `index_documents` à partir des JSON présents dans `source_dir`.
        - Args:
          - client: instance ChromaDB (ClientAPI) déjà initialisée.
          - source_type: 'docx' ou 'web' (détermine la collection à reconstruire).
          - source_dir: chemin du répertoire contenant les JSON à indexer.
        - Raises:
          - ValueError: si `source_type` n’est pas 'docx' ni 'web'.
          - Exception: si la suppression ou la réindexation échoue (erreurs du client ChromaDB ou d’E/S remontées telles quelles).
        - Returns:
          - None

      - convert_fiches_docx_to_json (src/utils/convert_fiches_docx_to_json.py)
        - Convertit toutes les fiches DOCX d’un répertoire en dictionnaires JSON.
        - Parcourt les fichiers `.docx` du dossier spécifié, extrait leur contenu sous forme de paragraphes structurés, puis les formate en paires (titre, contenu) dans une liste de dictionnaires.
        - Args:
          - input_dir (str) : Chemin vers le répertoire contenant les fichiers DOCX.
        - Returns:
          - List[Dict[str, str]] : Liste de dictionnaires contenant les textes extraits de chaque fiche, prêts à être sauvegardés ou indexés.

      - save_fiches_to_json (src/utils/convert_fiches_docx_to_json.py)
        - Sauvegarde une liste de fiches au format JSON dans un répertoire donné.
        - Crée un fichier `.json` pour chaque fiche, nommé à partir de son titre, dans le dossier de destination spécifié.
        - Args:
          - fiches (List[Dict[str, str]]) : Liste de dictionnaires représentant les fiches.
          - JSON_HEALTH_DOC_BASE (str) : Répertoire où sauvegarder les fichiers JSON.

      - convert_and_save_fiches (src/utils/convert_fiches_docx_to_json.py)
        - Convertit toutes les fiches DOCX d’un répertoire et les enregistre au format JSON.
        - Enchaîne les étapes de traitement :
        - Lecture et conversion des fichiers `.docx` en dictionnaires.
        - Sauvegarde des résultats dans des fichiers `.json` individuels.
        - Args:
          - INPUT_DOCX (str) : Répertoire contenant les fichiers DOCX source.
          - JSON_HEALTH_DOC_BASE (str) : Répertoire de destination des fichiers JSON générés.

      - scrape_all_trusted_sites (src/func/scrape_trusted_sites.py)
        - Scrape l’ensemble des sites de confiance et sauvegarde chaque page utile en JSON.
        - Args:
          - trusted_sites (list[dict] | None): Liste de sites à scruter (name, base_url, start_pages).
          - Si None, la liste est chargée depuis la configuration.
          - output_dir (str | pathlib.Path | None): Dossier de sortie des JSON; si None, utilise le chemin configuré (WEB_SITES_JSON_HEALTH_DOC_BASE).
        - Returns:
          - list[pathlib.Path]: La liste des chemins des fichiers JSON écrits (vide si rien n’a été produit).
    
        - **Fonctions appelées par scrape_all_trusted_sites:**
          - _is_pdf_url
          - _normalize_host
          - _is_allowed_pdf_domain
          - _head_content_type
          - _download_binary
          - _pdf_to_sections
          - _log_print
          - _normalize_space
          - _text
          - _normalized_netloc
          - _same_site
          - _normalize_url
          - _blocked_by_stop_patterns
          - _pick_root
          - is_irrelevant_text
          - _request_soup
          - _extract_title
          - _table_to_text
          - _collect_same_site_links
          - extract_structured_content
          - _extract_minimal_sections_for_bfs
          - extract_useful_links
          - _safe_filename_from_url
          - _collect_links_per_section_from_dom
          - _norm
          - _pick
          - _safe_get_attr
          - _text_of
          - _try_parse_date
          - _extract_from_jsonld
          - _extract_metadata
          - save_page_as_json
          - load_trusted_sites

      - get_chroma_client (src/utils/chroma_client.py)
        - Point d’accès centralisé au client Chroma avec cache et reset sûrs.
        - Ce module expose `get_chroma_client()` (LRU-caché) pour créer un client unique et cohérent sur tout le projet, ainsi que `reset_chroma_client_cache()`pour invalider ce cache lors des resets/rebuilds. L’objectif est d’éviter les handles orphelins et les états SQLite en lecture seule, en garantissant une seule façon d’instancier le client (p. ex. PersistentClient) et des chemins/flags unifiés via `config.config`.
        - Peut inclure un logging de debug optionnel pour tracer les appels au client pendant l’indexation.

      - index_documents (src/func/index_documents_chromadb.py)
        - Indexe les documents JSON contenus dans un répertoire dans une collection ChromaDB.
        - Chaque document est découpé en sections (ou chunk unique dans le cas d'un fichier DOCX complet), puis inséré dans une base vectorielle avec ses métadonnées.
        - Args:
          - source_dir (str): Chemin du dossier contenant les fichiers JSON à indexer.
          - source_type (str): Type de document à indexer, soit 'docx' soit 'web'.
          - client (Client): Instance du client ChromaDB utilisée pour la persistance des données.
        - Entrées :
          - source_dir (str) : Dossier contenant les fichiers JSON.
          - source_type (str) : 'docx' ou 'web' (détermine la collection cible).
          - Sorties :
            - Indexation des chunks dans une collection nommée selon la source.
        - Raises:
          - ValueError: Si le type de source est invalide (autre que 'docx' ou 'web').

      - is_chroma_index_ready (src/utils/vector_db_utils.py)
        - Vérifie si le fichier 'index_ready.flag' existe dans le dossier vectoriel.
        - Returns:
          - bool: True si les bases ChromaDB ont été indexées, False sinon.

      - mark_index_ready_flag (src/utils/vector_db_utils.py)
        - Crée un fichier flag indiquant que l'indexation ChromaDB est terminée.
        - Si le répertoire n'existe pas, il est créé.

##	**Nom: chat.py (src/api/routes/chat.py)**
### Rôle: Exposer l’endpoint POST /chat/chat qui délègue au tronc commun process_user_input et retourne une réponse sérialisable pour l’intégration OBY.
### Docstring:
  - Routes de conversation (chat) pour OBY-IA.
  - Ce module expose les endpoints nécessaires pour piloter l’agent de conversation depuis une application externe (OBY) via FastAPI.
    - Ils’appuie sur la fonction centrale `process_user_input` qui orchestre la détection d’intention, la demande de confirmation et l’exécution des pipelines, et renvoie un objet JSON-sérialisable (mode "api").
    - Fonction: 
      - handle_chat_api()
        - Gère un tour de conversation OBY-IA via API (mode "api").
        - Reçoit le message utilisateur et l’état de session, délègue au tronc commun `process_user_input` (avec `output_mode="api"`), puis renvoie une réponse normalisée pour l’intégration.
        - Parameters:
          - payload : ChatRequest
          - Entrée structurée : clics, saisie, historique, session, patient.
          - Returns:
            - ChatResponse
            - Statut du tour, historique (partiel ou complet), sorties métiers (table_html, anomalies, figures sérialisées si disponible) et patient courant.
            - Notes
              - Cet endpoint n’expose pas directement les fonctions internes `handle_initial_request` / `handle_confirmation_response` : elles restent derrière l’API `process_user_input`.

## **Nom: export.py (src/api/routes/export.py)**
### Rôle: Exposer POST /chat/export pour déclencher l’export Markdown d’une session (réponses LLM + visuels) et renvoyer une URL statique servie par FastAPI.
### Docstring:
  - Export Markdown des échanges OBY-IA (API).
  - Ce module propose un endpoint d’export qui :
  - désérialise les figures si nécessaire,
  - appelle `export_llm_responses` pour générer le fichier `.md`,
  - renvoie une URL statique `/static/...` pointant vers `outputs/...`.
- Fonction: 
  - export_chat_response_api()
    - Exporte l’historique LLM au format Markdown et renvoie une URL statique.
    - Parameters:
      - payload : ExportRequest
      - Données de session (session_id), patient courant, figures sérialisées.
      - Returns:
        - dict: { "status": "success" | "error", "message": str, "markdown_file_url": str | None }
      - Notes
        - Nécessite une session valide (`session_id`) et un patient.
        - L’URL renvoyée suppose `app.mount("/static", StaticFiles(directory="outputs"))` dans `main_api.py`.


## **Nom: login.py (src/api/routes/login.py)**
### Rôle: Exposer POST /auth/login. Authentifie l’utilisateur, crée un session_id (UUID), initialise la session, renvoie session_data.
### Docstring:
  - Authentification (login) pour OBY-IA via API.
  - module offre un endpoint de connexion qui valide l’utilisateur contre `USER_DATABASE`, crée un `session_id` unique, initialise la session LLM et renvoie `session_data` à utiliser sur les autres endpoints.
- Fonction: 
  - authenticate_user_api()
    - Authentifie l’utilisateur et crée une session.
    - Parameters:
      - request : LoginRequest
      - Identifiants : user_id, password.
    - Returns:
      - LoginResponse
      - Message et `session_data = {"user_id": ..., "session_id": ...}`.
      - Raises:
        - HTTPException
        - 400 si champs manquants, 401 si identifiants invalides.
    - Notes:
      - Le `session_id` est un UUID par session (pas égal à `user_id`).
      - La base d’utilisateurs est simulée (usage démo), non sécurisée pour la prod.


## **Nom: logout.py (src/api/routes/logout.py)**
### Rôle: Exposer POST /auth/logout. Termine proprement la session si elle existe. Comporte un mode idempotent.
### Docstring:
  - Déconnexion (logout) d’une session OBY-IA via API.
  - Ce module termine la session courante si elle existe, et renvoie un message et un indicateur `already_logged_out` pour permettre un traitement idempotent.
  - Fonction:
    - logout_user_api
      - Met fin à une session et reset les stores côté client.
      - Parameters:
        - request : LogoutRequest 
        - Données de session : user_id, session_id. 
      - Returns:
        - LogoutResponse 
        - Message de succès, payload vidé (session_data=None, chat_history=[], current_patient=None, constants_graphs_store=None), indicateur `already_logged_out`.
      - Notes
        - Idempotent : renvoie 200 même si la session est déjà absente.


## **Nom: poa_patients.py (src/api/routes/poa_patients.py)**
### Rôle: CRUD léger sur les fichiers patients (POA) : lister, lire, créer/mettre à jour. Utilise PATIENT_FILES_DIR.
### Docstring:
  - Moule API pour la gestion des dossiers patients POA dans OBY-IA.
  - Ce module expose plusieurs endpoints sécurisés pour :
  - Lister les fichiers patients disponibles.
  - Lire un dossier patient au format JSON.
  - Créer un nouveau dossier patient.
  - Mettre à jour un dossier patient existant.
  - Supprimer un dossier patient.
  - Seuls les utilisateurs authentifiés disposant des droits d'édition (actuellement : `admin`) peuvent effectuer ces opérations.
  - Endpoints :
    - GET    /patients           → Liste les fichiers patients.
    - GET    /patients/{file}    → Retourne le contenu JSON d’un patient.
    - POST   /patients           → Crée un nouveau dossier patient.
    - PUT    /patients/{file}    → Met à jour un dossier patient existant.
    - DELETE /patients/{file}    → Supprime un dossier patient.
  - Sécurité :
    - Les appels nécessitent les en-têtes HTTP :
    - X-User-Id    : identifiant utilisateur
    - X-Session-Id : identifiant de session obtenu via /auth/login

- **Fonctions du module:**
  - ensure_data_dir()
    - Docstring:
      - Crée le répertoire de stockage des patients s’il n’existe pas

  - fs_path_for()
    - Docstring:
      - Retourne le chemin absolu pour un fichier patient donné.
      - Args:
        - filename (str): Nom de fichier patient.
      - Returns:
        - str: Chemin absolu vers le fichier.

  - require_editor_session()
    - Docstring:
      - Retourne le chemin absolu pour un fichier patient donné.
      - Args:
        - filename (str): Nom de fichier patient.
      - Returns:
        - str: Chemin absolu vers le fichier.

  - list_patients()
    - Docstring:
      - Retourne la liste des fichiers patients (.json) disponibles.
      - Returns:
        - List[str]: Liste triée des noms de fichiers patients.
      - Raises:
        - HTTPException: Si le répertoire patient est introuvable.

  - get_patient()
    - Docstring:
      - Retourne le contenu JSON d’un dossier patient.
      - Args:
        - filename (str): Nom du fichier patient.
      - Returns:
        - dict: Contenu JSON du dossier patient.
      - Raises:
        - HTTPException: Si le fichier n’existe pas ou si le JSON est invalide.

  - create_patient()
    - Docstring:
      - Crée un nouveau fichier patient.
      - Args:
        - req (CreatePatientRequest): Modèle contenant le nom et le contenu du dossier.
      - Returns:
        - dict: Statut de création.
      - Raises:
        - HTTPException: Si le fichier existe déjà ou en cas d'erreur d'écriture.

  - update_patient()
  - Docstring:
    - Met à jour le contenu d’un dossier patient existant.
    - Args:
      - filename (str): Nom du fichier patient.
      - data (PatientData): Contenu JSON à sauvegarder.
    - Returns:
      - dict: Statut de mise à jour.
    - Raises:
      - HTTPException: Si le fichier n’existe pas ou en cas d'erreur d'écriture.

  - delete_patient()
    - Docstring:
      - Supprime un fichier patient.
      - Args:
        - filename (str): Nom du fichier patient à supprimer.
      - Returns:
        - dict: Statut de suppression.
      - Raises:
        - HTTPException: Si le fichier n’existe pas ou en cas d'erreur de suppression.

## **Nom: status.py (src/api/routes/status.py)**
### Rôle: Informer de la disponibilité de la base chromadb.
### Docstring:
  - Vérifie si les index ChromaDB sont prêts à être interrogés.
  - Renvoie le statut à l’interface OBY pour activer/désactiver les champs.

  - Fonction: Pas de fonction associée.

## **Nom: main_api.py (src/api/main_api.py)**
### Rôle: 
  - point d’entrée du serveur FastAPI. main_api.py a pour rôle de :
  - Créer l’objet FastAPI()
  - Importer et inclure les routes (chat, login, logout…)
  - Définir la configuration de CORS (permet d’autoriser les appels depuis l’interface OBY)
  - Ajouter éventuellement des middlewares (authentification, logs, etc.)
  - Docstring:
    - point d’entrée du serveur FastAPI. main_api.py a pour rôle de :
    - Créer l’objet FastAPI()
    - Importer et inclure les routes (chat, login, logout…)
    - Définir la configuration de CORS (permet d’autoriser les appels depuis l’interface OBY)
    - Ajouter éventuellement des middlewares (authentification, logs, etc.)

  - Fonction: Pas de fonction associée.


## **Nom: models.py (src/api/models.py)**
### Rôle: Ce fichier regroupe toutes les structures de données échangées avec l’API, basées sur pydantic.
### Docstring: Ce fichier regroupe toutes les structures de données échangées avec l’API, basées sur pydantic.

  - Fonction: Pas de fonction associée.





