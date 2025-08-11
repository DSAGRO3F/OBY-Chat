# 🧭 Vue d'ensemble des modules du projet OBY-Chat

_Cette page fournit une description concise des principaux modules Python du projet._

---


## 📄 Module : `api.routes.chat`

> **Rôle :**
> src/api/routes/chat.py
> 
> chat.py — Routes API pour la gestion des échanges entre l'utilisateur et OBY-IA.
> 
> 📁 Chemin : src/api/routes/chat.py
> 
> Ce module définit les endpoints FastAPI permettant d'interagir avec l'agent
> conversationnel OBY-IA via API.  
> Il gère la réception des requêtes utilisateur, la transmission au moteur
> de traitement (`process_user_input`) et le renvoi des réponses formatées.
> 
> Fonctionnalités principales :
> - Point d'entrée `/chat` (méthode POST) pour envoyer un message et recevoir une réponse.
> - Conversion automatique de la requête JSON en modèle `ChatRequest`.
> - Utilisation du modèle `ChatResponse` pour structurer la réponse API.
> - Passage des données de session, historique de chat et contexte patient
>   au moteur de traitement.
> 
> Imports :
> - `APIRouter` : gestion des routes FastAPI.
> - `ChatResponse`, `ChatRequest` : modèles Pydantic pour la validation des données.
> - `process_user_input` : fonction cœur de traitement des requêtes.
> 
> Usage :
>     POST /chat
>     Body : ChatRequest (JSON)
>     Retour : ChatResponse (JSON)

---


## 📄 Module : `api.routes.export`

> **Rôle :**
> src/api/routes/export.py
> Exporte l’historique de conversation OBY-IA au format Markdown et renvoie l’URL du fichier.
> 
> Cette route :
> 1) vérifie la présence d’une session valide (session_id),
> 2) désérialise les éventuels graphiques des constantes (Plotly) fournis,
> 3) appelle `export_llm_responses(...)` pour générer le fichier `.md` dans `outputs/...`,
> 4) retourne une réponse JSON avec un lien web pointant vers la ressource statique
>    (mappée par l’application vers `/static/...`).
> 
> Paramètres
> ----------
> payload : ExportRequest
>     Corps de requête contenant :
>     - `session_data` : dict avec au minimum `session_id`,
>     - `current_patient` : nom du patient (utilisé pour le nommage/chemin),
>     - `serialized_figs` : liste des figures Plotly sérialisées (peut être vide).
> 
> Returns
> -------
> dict
>     Objet JSON avec :
>     - `status` : "success" ou "error",
>     - `message` : détail du résultat,
>     - `markdown_file_url` : URL relative `/static/...` vers le fichier exporté, ou `None` en cas d’erreur.
> 
> Notes
> -----
> - Cette route suppose que l’application FastAPI a monté un répertoire statique
>   exposant `outputs/` sous le préfixe `/static/`.
> - Si aucun graphique n’est fourni, l’export Markdown se base uniquement sur l’historique
>   de session (messages utilisateur / réponses OBY-IA) maintenu par `session_manager_instance`.

---


## 📄 Module : `api.routes.login`

> **Rôle :**
> src/api/routes/login.py
> 
> Authentifier un utilisateur et créer une nouvelle session.
> 
> Vérifie si les identifiants fournis correspondent à un utilisateur
> valide dans la base locale. Si oui, génère un identifiant de session
> unique, initialise la session dans le gestionnaire centralisé, et
> retourne les données de session.
> 
> Args:
>     request (LoginRequest): Objet contenant `user_id` et `password`.
> 
> Returns:
>     LoginResponse: Message de confirmation et données de session.
> 
> Raises:
>     HTTPException: Si les champs sont manquants (400) ou si les
>     identifiants sont invalides (401).

---


## 📄 Module : `api.routes.logout`

> **Rôle :**
> src/api/routes/logout.py
> 
> Déconnecter un utilisateur et réinitialiser sa session.
> 
> Supprime la session identifiée par `user_id` et `session_id` du
> gestionnaire centralisé. Retourne un indicateur `already_logged_out`
> pour signaler si la session était déjà inexistante.
> 
> Args:
>     request (LogoutRequest): Objet contenant `user_id` et `session_id`.
> 
> Returns:
>     LogoutResponse: Message de confirmation, état des données de
>     session, et indicateur `already_logged_out`.
> 
> Raises:
>     HTTPException: Si la requête est invalide (400) ou si les champs
>     obligatoires sont absents.

---


## 📄 Module : `api.routes.poa_patients`

> **Rôle :**
> src/api/routes/poa_patients.py
> Module API pour la gestion des dossiers patients POA dans OBY-IA.
> 
> Ce module expose plusieurs endpoints sécurisés pour :
>     - Lister les fichiers patients disponibles.
>     - Lire un dossier patient au format JSON.
>     - Créer un nouveau dossier patient.
>     - Mettre à jour un dossier patient existant.
>     - Supprimer un dossier patient.
> 
> Seuls les utilisateurs authentifiés disposant des droits d'édition
> (actuellement : `admin`) peuvent effectuer ces opérations.
> 
> Endpoints :
>     GET    /patients           → Liste les fichiers patients.
>     GET    /patients/{file}    → Retourne le contenu JSON d’un patient.
>     POST   /patients           → Crée un nouveau dossier patient.
>     PUT    /patients/{file}    → Met à jour un dossier patient existant.
>     DELETE /patients/{file}    → Supprime un dossier patient.
> 
> Sécurité :
>     Les appels nécessitent les en-têtes HTTP :
>         X-User-Id    : identifiant utilisateur
>         X-Session-Id : identifiant de session obtenu via /auth/login

---


## 📄 Module : `api.routes.status`

> **Rôle :**
> src/api/routes/status.py
> Vérifie si les index ChromaDB sont prêts à être interrogés.
> Renvoie le statut à l’interface OBY pour activer/désactiver les champs.

---


## 📄 Module : `api.main_api`

> **Rôle :**
> src/api/main_api.py
> 
> point d’entrée du serveur FastAPI. main_api.py a pour rôle de :
> Créer l’objet FastAPI()
> Importer et inclure les routes (chat, login, logout…)
> Définir la configuration de CORS (permet d’autoriser les appels depuis l’interface OBY)
> Ajouter éventuellement des middlewares (authentification, logs, etc.)

---


## 📄 Module : `api.models`

> **Rôle :**
> src/api/models.py
> 
> Ce fichier regroupe toutes les structures de données échangées avec l’API, basées sur pydantic.

---


## 📄 Module : `data.constant_generator`

> **Rôle :**
> Module de génération de données fictives pour les constantes médicales.
> Ce module permet de créer une base SQLite contenant des données simulées pour plusieurs types
> de constantes de santé : poids, tension artérielle, fréquence cardiaque et température.
> Les données sont générées automatiquement pour un ensemble de patients fictifs,
> sur une période de 16 semaines, afin de servir de base de tests dans l'application OBY-IA.

---


## 📄 Module : `data.get_constants`

> **Rôle :**
> Module d'accès aux constantes médicales des patients depuis la base SQLite.
> Ce module permet :
> - d’identifier les constantes disponibles en base (poids, tension, etc.),
> - de récupérer l’historique des valeurs d’un patient pour chaque constante.
> Les données extraites sont retournées sous forme de DataFrames Pandas,
> prêtes à être analysées ou visualisées dans l'application OBY-IA.

---


## 📄 Module : `func.anonymizer`

> **Rôle :**
> Ce module permet :
> - d'anonymiser des champs sensibles dans une structure JSON (ex. : prénoms, adresses, contacts),
> - de générer un dictionnaire de correspondance entre valeurs originales et anonymisées,
> - de désanonymiser un texte produit à partir des données en réinjectant les valeurs originales.
> 
> L’anonymisation repose à la fois sur des règles dynamiques (ex. : prénom selon le sexe)
> et sur des valeurs codées en dur (HARDCODED_VALUES).

---


## 📄 Module : `func.api_core`

> **Rôle :**
> Fonction centrale appelée par l'API ou l'interface pour traiter la requête utilisateur.
> 
>     Args:
>         send_clicks (int): Nombre de clics sur le bouton envoyer.
>         user_input (str): Message saisi par l'utilisateur.
>         chat_history (list): Historique des échanges.
>         session_data (dict): Données de session utilisateur.
>         current_patient (Optional[str]): Nom du patient actuellement sélectionné.
> 
>     Returns:
>         dict: Dictionnaire contenant les résultats du traitement.

---


## 📄 Module : `func.auto_index_documents`

> **Rôle :**
> Module de déclenchement automatique de l'indexation documentaire.
> 
> Vérifie les modifications dans les fichiers DOCX et les pages web médicales,
> et lance l'indexation via ChromaDB uniquement si des changements sont détectés.

---


## 📄 Module : `func.detect_genre`

> **Rôle :**
> Module de génération de prénoms anonymisés à partir du sexe renseigné.
> 
> Ce module permet de produire des prénoms fictifs cohérents avec le sexe (masculin, féminin ou inconnu)
> dans le cadre d’un processus d’anonymisation de données personnelles.
> Il inclut également des valeurs codées en dur pour compléter des structures anonymisées.

---


## 📄 Module : `func.detect_poa_file_path`

> **Rôle :**
> Module de détection du chemin du fichier patient.
> 
> Ce module fournit une fonction pour localiser automatiquement un fichier contenant les données
> d’un patient, à partir de son nom, dans le dossier `src/data/poa_patients`.

---


## 📄 Module : `func.extract_patient_name`

> **Rôle :**
> Module pour l'extraction du nom du patient à partir d'une requête utilisateur.
> 
> Ce module utilise un LLM pour analyser une phrase en langage naturel
> et en extraire uniquement le nom de famille du patient mentionné.

---


## 📄 Module : `func.extract_user_intent`

> **Rôle :**
> Module extract_user_intent
> 
> Ce module permet de détecter l’intention principale d’un utilisateur à partir de sa requête textuelle.
> La détection repose d’abord sur des correspondances par mots-clés, puis bascule sur un modèle de langage
> (LLM) si aucune correspondance directe n’est trouvée.
> 
> Modifications apportées :
> - Ajout d’une hiérarchie de priorité dans la détection par mots-clés pour résoudre les ambiguïtés.
> - Ajout de docstrings conformes à la PEP 257.
> - Refactorisation avec étapes explicites et commentaires clairs.

---


## 📄 Module : `func.generate_ppa_from_poa`

> **Rôle :**
> Module de génération de PPA (Plan Personnalisé d’Accompagnement) à partir d’un document POA.
> 
> Ce module extrait le nom du patient depuis la requête utilisateur, charge et nettoie le document POA
> correspondant, anonymise les données, formate le contenu pour le modèle LLM, puis génère un PPA structuré.

---


## 📄 Module : `func.generate_structured_medical_plan`

> **Rôle :**
> Module de génération d’un plan d’action structuré à partir du POA d’un patient.
> 
> Ce module est déclenché lorsque l’intention « generate_recommendations » est détectée.
> Il extrait le nom du patient, charge et nettoie le document POA, anonymise les données,
> puis interroge un modèle LLM avec un prompt enrichi pour générer des recommandations classées
> (par type d'action : prévention, soins, traitements, etc.).

---


## 📄 Module : `func.get_chroma_stats`

> **Rôle :**
> Statistiques sur les données indexées dans ChromaDB et les fichiers JSON préparés.
> 
>     Returns:
>         dict: {
>             "docx_files": int,        # Fichiers uniques indexés depuis docx
>             "web_files": int,         # Fichiers uniques indexés depuis web
>             "docx_chunks": int,
>             "web_chunks": int,
>             "docx_json_files": int,   # Fichiers JSON générés depuis les DOCX
>             "web_json_files": int     # Fichiers JSON générés depuis le web
>         }

---


## 📄 Module : `func.get_patient_constants_graphs`

> **Rôle :**
> Module d'analyse et de visualisation des constantes médicales des patients.
> 
> Ce module permet :
> - de convertir les constantes brutes issues de la base de données en DataFrame,
> - de détecter des anomalies selon des seuils définis,
> - de générer des graphiques Plotly (poids, tension, température...),
> - de produire des tableaux HTML interactifs pour Dash,
> - de centraliser le traitement dans une fonction complète pour l’interface.
> 
> Utilisé notamment dans la page chatbot_ui de l’application OBY-IA.

---


## 📄 Module : `func.handle_user_requests`

> **Rôle :**
> Gestion des requêtes utilisateur pour OBY-IA (détection d’intention, confirmation et exécution).
> 
> Ce module centralise la logique conversationnelle « back-end » entre l’interface
> et les pipelines métier d’OBY-IA. Il orchestre deux étapes clés :
> 
> 1) handle_initial_request(...) :
>    - Analyse l’input utilisateur (détection d’intention et extraction éventuelle
>      du nom de patient).
>    - Met en place un état de confirmation (session["intent_confirmation_pending"] = True)
>      et prépare un message de confirmation.
>    - Retourne les éléments nécessaires pour l’affichage / la réponse (historique,
>      tableaux, graphiques, etc.), généralement vides à ce stade.
> 
> 2) handle_confirmation_response(...) :
>    - Interprète la confirmation (ex.: « oui / non ») lorsque l’intention est en attente.
>    - Déclenche le pipeline adapté :
>        • PPA (generate_ppa_from_poa.process_ppa_request),
>        • Recommandations (generate_structured_medical_plan),
>        • Constantes patient (process_patient_request_with_constants).
>    - Met à jour l’état de session (réinitialisation du flag de confirmation,
>      mémorisation du patient courant, etc.) et assemble la réponse finale.
> 
> Modes de sortie :
>     Le paramètre `output_mode` permet d’adapter le format des objets retournés :
>       - "dash" : le module peut retourner des composants Dash (html.Div, dcc.Markdown,
>                  figures Plotly « go.Figure », etc.) pour l’UI interne.
>       - "api"  : le module retourne des structures sérialisables (listes/dicts/strings),
>                  adaptées à FastAPI / JSON (pas d’objets Dash).
> 
> Effets de bord :
>     - Mise à jour de la session (ex. intent_confirmation_pending, intent_candidate).
>     - Enrichissement de l’historique de conversation (chat_history / new_chat_history).
> 
> Dépendances principales :
>     - src.llm_user_session.session_manager_instance
>     - src.func.extract_user_intent, src.func.extract_patient_name
>     - src.func.generate_ppa_from_poa, src.func.generate_structured_medical_plan
>     - src.func.get_patient_constants_graphs
>     - src.func.serialize_figs (sérialisation des figures)
>     - (optionnel côté UI) dash.html / dash.dcc pour le mode "dash"
> 
> Convention de retour :
>     Les fonctions retournent un 7-uplet :
>         (chat_history_ou_new_chat_history,
>          figures_out,
>          table_html,
>          anomaly_block,
>          current_patient,
>          serialized_figs,
>          chat_history_display)
> 
>     * En mode "initial", chat_history est renvoyé (nouvel historique cumulé).
>     * En mode "confirmation", new_chat_history est renvoyé (ajouts du tour courant).
>     * Le « full_chat_history » est assemblé par l’appelant si nécessaire.
> 
> Ce module est conçu pour être appelé à la fois par l’interface Dash (UI)
> et par la couche API (FastAPI) via une fonction « tronc commun ».

---


## 📄 Module : `func.index_documents_chromadb`

> **Rôle :**
> Module d'indexation des documents de santé dans une base vectorielle ChromaDB.
> 
> Ce module prend en entrée des fichiers JSON représentant soit des documents issus de fichiers DOCX,
> soit des pages web structurées, puis les segmente et les insère dans une collection ChromaDB.
>     Indexe les documents JSON contenus dans un répertoire dans une collection ChromaDB.
> 
>     Chaque document est découpé en sections (ou chunk unique dans le cas d'un fichier DOCX complet),
>     puis inséré dans une base vectorielle avec ses métadonnées.
> 
>     Args:
>         source_dir (str): Chemin du dossier contenant les fichiers JSON à indexer.
>         source_type (str): Type de document à indexer, soit 'docx' soit 'web'.
>         client (Client): Instance du client ChromaDB utilisée pour la persistance des données.
> 
>     Entrées :
>         - source_dir (str) : Dossier contenant les fichiers JSON.
>         - source_type (str) : 'docx' ou 'web' (détermine la collection cible).
> 
>     Sorties :
>         - Indexation des chunks dans une collection nommée selon la source.
> 
> 
>     Raises:
>         ValueError: Si le type de source est invalide (autre que 'docx' ou 'web').

---


## 📄 Module : `func.indexed_health_related_files`

> **Rôle :**
> Module de suivi et de détection des changements dans les fichiers de santé.
> 
> Il permet de :
> - Calculer le hash des fichiers (DOCX, JSON, Python) pour en détecter les modifications.
> - Comparer l’état actuel à un journal enregistré.
> - Déterminer quels fichiers nécessitent une réindexation.

---


## 📄 Module : `func.llm_prompts`

> **Rôle :**
> Module de génération de prompts pour produire des Plans Personnalisés d’Accompagnement (PPA) ou des recommandations médicales,
> à partir du POA d’un patient et d’une requête utilisateur. Intègre également la version RAG avec enrichissement par des documents issus de ChromaDB.

---


## 📄 Module : `func.poa_cleaning`

> **Rôle :**
> Module de nettoyage des documents POA (Plan d’Objectifs et d’Actions).
> 
> Ce module filtre les champs non informatifs ou vides dans les fichiers JSON représentant
> les données patients, afin de faciliter leur traitement en aval.

---


## 📄 Module : `func.poa_loader`

> **Rôle :**
> Module de chargement des fichiers POA (Plan d’Objectifs et d’Actions) au format JSON.
> Ce module permet de localiser et lire un fichier patient stocké dans le dossier `data/poa_patients/`.

---


## 📄 Module : `func.retrieve_relevant_chunks`

> **Rôle :**
> Module de récupération des extraits pertinents depuis une base ChromaDB.
> Ce module interroge une collection vectorielle Chroma (via LangChain)
> et retourne les passages les plus similaires à une requête, pour enrichir un prompt.

---


## 📄 Module : `func.run_full_indexing_pipeline`

> **Rôle :**
> Module `run_full_indexing_pipeline.py` – Pipeline principal d’indexation documentaire pour OBY-IA.
> 
> Ce module exécute l’ensemble du processus de préparation de la base documentaire utilisée
> par les agents RAG de OBY-IA, en assurant une indexation vectorielle actualisée dans ChromaDB.
> 
> Fonctionnalités couvertes :
> 1. **Détection de modifications** :
>    - Identification des fichiers DOCX ou pages web récemment modifiés via calcul de hashs.
>    - Détection des changements dans la définition des sites de confiance (`trusted_sites.py`).
> 
> 2. **Conversion en JSON structuré** :
>    - Transformation des fichiers DOCX en fichiers JSON exploitables.
>    - Scraping et structuration des nouvelles pages web selon les règles définies.
> 
> 3. **Indexation vectorielle dans ChromaDB** :
>    - Indexation incrémentale ou complète des données selon les changements détectés.
>    - Séparation des sources DOCX et web (`source_type`).
> 
> 4. **Journalisation des indexations** :
>    - Mise à jour du fichier de suivi (`indexed_files.json`) pour éviter les réindexations inutiles.
> 
> 5. **Signalement de disponibilité** :
>    - Écriture d’un fichier `index_ready.flag` permettant aux autres modules de savoir si l’index est prêt.
> 
> Ce pipeline peut être lancé :
> - automatiquement (via un scheduler ou watchdog),
> - ou manuellement (en exécutant ce fichier en tant que script).
> 
> Il constitue un composant critique du système OBY-IA pour garantir la fraîcheur et la cohérence
> des bases documentaires utilisées dans les interactions LLM + RAG.

---


## 📄 Module : `func.scrape_trusted_sites`

> **Rôle :**
> Module de scraping des sites web de confiance en santé.
> 
> Ce module permet :
> - de charger dynamiquement la liste des sites référencés,
> - d’extraire les liens utiles à partir de pages de départ,
> - de structurer le contenu HTML pertinent (titres, paragraphes, listes),
> - et de sauvegarder les pages web sous forme de fichiers JSON pour indexation.
> Utilisé pour alimenter une base documentaire de recommandations en santé.

---


## 📄 Module : `func.serialize_figs`

> **Rôle :**
> Module de sérialisation et désérialisation de graphiques Plotly.
> Permet d’encoder les objets graphiques en base64 pour stockage ou transmission,
> et de les décoder pour affichage ultérieur dans l'application.

---


## 📄 Module : `utils.chroma_client`

> **Rôle :**
> Module d’accès centralisé au client ChromaDB pour l'application OBY-IA.
> Ce module fournit une fonction utilitaire permettant d’instancier un client ChromaDB
> persistant, configuré pour enregistrer les données dans le répertoire défini par
> `CHROMA_GLOBAL_DIR`. Il garantit qu’une seule instance client est utilisée
> grâce au décorateur `lru_cache`.
> Utilisé dans l'ensemble du projet pour interagir avec la base Chroma.

---


## 📄 Module : `utils.convert_fiches_docx_to_json`

> **Rôle :**
> Module de conversion de fiches documentaires DOCX en fichiers JSON exploitables.
> 
> Ce module permet d’extraire le contenu textuel structuré de fichiers Word (.docx)
> présents dans un répertoire donné, et de les convertir en dictionnaires JSON.
> Ces JSON sont ensuite utilisés dans l’application OBY-IA pour l’indexation
> et la recherche sémantique de recommandations.
> 
> Fonctionnalités :
> - Lecture et traitement de fichiers `.docx`.
> - Nettoyage et normalisation du contenu.
> - Export en fichiers `.json` avec le même nom de base.

---


## 📄 Module : `utils.convert_json_text`

> **Rôle :**
> Module de conversion des données JSON d'un POA en texte structuré pour LLM.
> 
> Ce module extrait les informations pertinentes du dictionnaire JSON d’un plan
> d’objectifs et d’actions (POA), notamment les données de la personne accompagnée,
> ses contacts et les différentes sections thématiques (social, santé, autonomie).
> Il génère un texte lisible destiné à être injecté dans un prompt pour un modèle LLM.
> 
> Utilisé pour formater proprement les données en amont d’une génération automatique
> de synthèse ou de recommandations.

---


## 📄 Module : `utils.export_chat_response`

> **Rôle :**
> Module d'export des réponses générées par le modèle LLM pour un patient donné.
> 
> Ce module permet de récupérer toutes les réponses associées à une session (requête utilisateur + réponse LLM),
> de les concaténer proprement, et de les exporter dans un fichier Markdown.
> Il peut également intégrer des graphiques de constantes si fournis.
> 
> Utilisé notamment pour générer des synthèses textuelles enrichies à partir
> des sessions de chat dans l'application OBY-IA.

---


## 📄 Module : `utils.reset_data`

> **Rôle :**
> Module de réinitialisation des données indexées de l'application OBY-IA.
> Ce module fournit une fonction utilitaire permettant de nettoyer l’environnement
> de travail en supprimant :
> - les collections ChromaDB (ex. : `base_docx`, `base_web`),
> - les fichiers JSON issus de l’extraction documentaire locale et web,
> - le fichier journal qui suit les fichiers déjà indexés.
> Utile pour remettre à zéro l’état de l’index avant un nouveau traitement complet.

---


## 📄 Module : `utils.scheduler`

> **Rôle :**
> Module de surveillance des fichiers pour l'indexation automatique.
> 
> Ce module utilise Watchdog pour observer les répertoires contenant des documents à indexer
> (docx, données web, versions de plans). Lorsqu’un changement est détecté, le pipeline
> d’indexation complet est automatiquement relancé pour mettre à jour les bases vectorielles.
> 
> Fonctions :
> - start_scheduler : Démarre la surveillance continue via Watchdog.
> 
> Classes :
> - IndexingEventHandler : Handler personnalisé déclenchant l’indexation à chaque événement.

---


## 📄 Module : `utils.vector_db_utils`

> **Rôle :**
> Module utilitaire pour la gestion de l'état de l'indexation ChromaDB.
> Ce module contient des fonctions permettant de :
> - Vérifier si l'indexation ChromaDB est terminée (via un fichier flag).
> - Créer ou supprimer ce flag selon les besoins.
> Ce mécanisme permet à l'application (ex. interface Dash) de savoir si les bases
> vectorielles sont prêtes à être interrogées par les utilisateurs.

---


## 📄 Module : `llm_user_session.model`

> **Rôle :**
> Initialisation des modèles de langage utilisés dans l'application OBY-IA.
> Ce module charge les clés API depuis le fichier `.env` et instancie un modèle
> de langage compatible avec LangChain, en fonction de la configuration disponible.
> Actuellement :
> - Le modèle `ChatOpenAI` (GPT-4.1) est utilisé par défaut, en raison de la limitation
>   de tokens rencontrée avec Mistral lors du traitement de documents volumineux.
> - Le modèle `ChatMistralAI` reste présent en commentaire à des fins de test ou migration future.
> Variables :
>     llm_model : Instance unique du modèle LLM utilisé pour répondre aux requêtes utilisateur.

---


## 📄 Module : `llm_user_session.session_manager`

> **Rôle :**
> Gestion centralisée des sessions utilisateurs pour l'application OBY-IA.
> Ce module définit deux classes principales :
> - `Session` : Représente une session utilisateur, incluant l’historique des échanges entre
>   l’utilisateur et le modèle LLM (chat_history).
> - `SessionManager` : Gère les sessions actives à l’aide d’un dictionnaire indexé par `session_id`.
>   Il permet de :
>     - créer, récupérer et supprimer des sessions,
>     - suivre le patient actuellement traité dans une session,
>     - stocker et réinitialiser un dictionnaire de correspondance pour l’anonymisation des données,
>     - enregistrer et restituer les réponses générées par le LLM pour les réutiliser (ex. : génération de documents PDF).
> Ce gestionnaire est conçu pour un usage multi-utilisateur avec une mémoire indépendante par session.

---


## 📄 Module : `llm_user_session.session_manager_instance`

> **Rôle :**
> Initialisation de l'instance unique du gestionnaire de sessions utilisateur.
> 
> Ce module importe la classe `SessionManager` et instancie un objet unique
> `session_manager_instance` utilisé pour gérer les sessions utilisateur
> dans l'application OBY-IA.
> 
> Cette instance centralisée permet de partager la gestion des sessions entre
> différents modules sans créer plusieurs objets SessionManager.

---


## 📄 Module : `pages.chatbot_ui`

> **Rôle :**
> Module `chatbot_ui.py` – Interface conversationnelle de l'application OBY-IA (page `/chatbot`)
> 
> Ce module Dash définit la page chatbot de OBY-IA, qui permet aux professionnels de santé
> d’interagir avec un agent intelligent pour obtenir :
> 
> 1. **Analyse des constantes médicales du patient** :
>    - Extraction et affichage des constantes sous forme de graphiques et tableaux.
>    - Détection automatique des anomalies.
>    - Sérialisation et désérialisation des graphiques pour l’exportation.
> 
> 2. **Interaction en langage naturel avec le LLM** :
>    - Détection de l’intention utilisateur (consultation, génération de PPA, recommandations).
>    - Extraction du nom du patient à partir de la requête.
>    - Génération de contenu médical structuré via des prompts spécialisés.
>    - Historisation des messages utilisateur/LLM et affichage dynamique.
> 
> 3. **Export des résultats** :
>    - Génération d’un fichier Markdown résumant la session (réponses LLM + graphiques).
> 
> 4. **Contrôle de disponibilité de l’index ChromaDB** :
>    - Affichage d’une bannière d’attente tant que l’index n’est pas prêt.
>    - Activation différée des composants de saisie utilisateur.
> 
> 5. **Gestion de la deconnexion de l'utilisateur** :
>    - Le click du bouton deconnexion dans la page de chat déclenche la supression de la session.
>    - La suppression de la session entraîne celle de l'historique du chat de la fenêtre de chat.
> 
> 
> Composants techniques :
> - Utilise `session_manager_instance` pour la gestion d’état (session, mapping, historique).
> - Repose sur les modules fonctionnels : `extract_user_intent`, `generate_ppa_from_poa`,
>   `generate_structured_medical_plan`, `get_patient_constants_graphs`, `export_chat_response`, etc.
> 
> Cette page est au cœur de l’expérience utilisateur de OBY-IA, combinant interface conviviale
> et logique métier intelligente.

---


## 📄 Module : `pages.home`

> **Rôle :**
> Module `home.py` – Page d'accueil, authentification et interface d'administration de OBY-IA.
> 
> Ce module Dash gère les fonctionnalités suivantes :
> 1. **Authentification utilisateur** :
>    - Vérification des identifiants via une base interne (`USER_DATABASE`).
>    - Création et stockage de la session via `dcc.Store` et `session_manager_instance`.
>    - Affichage conditionnel de l'interface selon le rôle (utilisateur ou admin).
> 
> 2. **Contrôles d'administration (admin uniquement)** :
>    - Réinitialisation des bases : ChromaDB, fichiers JSON extraits du web, index de suivi.
>    - Interface de déclenchement réservée aux administrateurs.
> 
> 3. **Accès à la documentation du projet** :
>    - Vérification en temps réel de la disponibilité du serveur MkDocs (`http://127.0.0.1:8000`).
>    - Redirection automatique vers la documentation si disponible.
>    - Cette documentation projet n'est pas mise à jour régulièrement. Elle sera définitivement remplacée par une documentation dynamique.
>    - Cette documentation dynamique pourra être consultée par le paramétrage de "start.sh".
> 
> 4. **Visualisation des statistiques d’indexation ChromaDB** :
>    - Affichage du nombre de fichiers indexés (DOCX, web), de chunks, et de fichiers JSON associés.
>    - Rafraîchissement manuel ou automatique de ces statistiques à l’ouverture.
> 
> Ce module constitue la page d’accueil et d’entrée principale de l’application OBY-IA.

---


## 📄 Module : `app`

> **Rôle :**
> Module principal de l'application OBY-IA.
> Ce module initialise l'application Dash, configure la navigation entre les pages,
> et vérifie la disponibilité de la base de données des constantes médicales.
> Fonctionnalités principales :
> - Chargement des variables d'environnement depuis un fichier `.env` à la racine.
> - Vérification et génération automatique de la base SQLite (`constantes_sante.db`).
> - Initialisation de l'application Dash avec gestion des pages (`use_pages=True`).
> - Mise en place d'une barre de navigation et d'un conteneur de pages dynamiques.
> - Démarrage d'un planificateur de tâches (scheduler) dans un thread dédié au lancement.
> Ce fichier doit être exécuté pour lancer le serveur Dash : `python -m src.app`

---

