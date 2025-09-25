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
> Anonymisation de l'usager via persona française (session-aléatoire).
> 
> Ce module fournit :
> - Des pools de valeurs françaises (prénoms, noms, voies, codes postaux/communes).
> - La création d'une persona cohérente pour l'usager (prénom selon le genre, nom, adresse, CP/commune).
> - Des utilitaires pour lire/écrire dans un dictionnaire JSON par chemins imbriqués.
> - Une anonymisation ciblée des champs usager et contacts.
> - La construction d'un mapping {valeur_anonymisée: valeur_originale} pour la désanonymisation.
> 
> Entrée : dict JSON (document patient).
> Sortie : Tuple[Any, Dict[str, str]] -> (document anonymisé, mapping).

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


## 📄 Module : `func.free_text_name_anonymizer`

> **Rôle :**
> Module free_text_name_anonymizer
> 
> Ce module gère l’anonymisation et la désanonymisation des mentions libres
> du nom et prénom du patient dans un POA (Plan d’Objectifs et d’Actions).
> 
> Contrairement à l’anonymisation structurée (sections « usager » et « contacts »),
> les informations saisies manuellement par les évaluateurs peuvent contenir
> le nom ou le prénom du patient dans des champs texte libres
> (ex. « Mme Anne Dupont, son épouse est présente »).
> 
> Fonctionnalités principales :
>     - Normalisation des chaînes (suppression des accents, casse insensible,
>       gestion des espaces Unicode).
>     - Construction de variantes (nom, prénom, « Prénom Nom », « Nom Prénom »,
>       civilités + nom, civilités + prénom + nom).
>     - Parcours récursif des structures de type dict/list pour détecter
>       les chaînes contenant le nom/prénom du patient.
>     - Remplacement par l’alias choisi lors de l’anonymisation structurée.
>     - Mise à jour du mapping {alias -> original} pour permettre la
>       désanonymisation correcte de la réponse du LLM.

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
> Collecte et expose des statistiques d’index Chroma pour l’UI.
>     
>     Ce module fournit une fonction principale, :func:`get_chroma_index_stats`, qui
>     retourne des compteurs utiles à l’interface (nb de fichiers/chunks DOCX & Web,
>     nb de JSON locaux, etc.) sans perturber l’indexation en cours.
>     
>     Comportement clé
>     ----------------
>     - **Aucun accès Chroma pendant l’indexation** : si l’un des drapeaux
>       ``FORCE_FULL_INDEX_FLAG`` ou ``INDEXING_FLAG_FILE`` est présent, la fonction
>       n’instancie pas de client Chroma et renvoie simplement les compteurs de fichiers
>       JSON présents sur disque, avec ``indexing=True``.
>     - **Accès Chroma en lecture seule sinon** : une fois l’index prêt
>       (flags absents), le cache client est invalidé puis un client Chroma est créé
>       pour lire les collections (``base_docx`` / ``base_web``) et calculer les
>       compteurs (chunks, fichiers, domaines).
>     - **Aucun effet de bord à l’import** : le module n’ouvre jamais Chroma au
>       chargement. Toute lecture Chroma se fait *uniquement* à l’appel de la fonction.
>     
>     Valeur de retour
>     ----------------
>     La fonction :func:`get_chroma_index_stats` renvoie un ``dict`` du type :
>     
>         {
>             "docx_files": int,
>             "docx_chunks": int,
>             "docx_json_files": int,
>             "web_files": int,
>             "web_chunks": int,
>             "web_json_files": int,
>             "docx_fiches": int,
>             "web_domains": int,
>             "indexing": bool,  # True si un rebuild est demandé/en cours
>         }
>     
>     Dans les cas d’erreur de lecture Chroma, la fonction reste tolérante et
>     renvoie simplement les compteurs JSON avec les autres valeurs à 0.
>     
>     Dépendances & conventions
>     -------------------------
>     - Ce module s’appuie sur les chemins/flags centralisés dans ``config.config`` :
>       ``FORCE_FULL_INDEX_FLAG``, ``INDEXING_FLAG_FILE``, ``JSON_HEALTH_DOC_BASE``,
>       ``WEB_SITES_JSON_HEALTH_DOC_BASE``.
>     - L’accès client est **centralisé** via ``src.utils.chroma_client`` :
>       ``get_chroma_client`` et ``reset_chroma_client_cache``.
>     - Les noms de collections attendues sont ``base_docx`` et ``base_web``.

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
> Gestion des requêtes utilisateur pour OBY-IA (module Dash/API).
> 
> Ce module orchestre les deux temps de la conversation : requête initiale
> (`handle_initial_request`) avec détection d’intention et question de confirmation,
> puis traitement de la réponse de confirmation (`handle_confirmation_response`)
> avec exécution du pipeline et construction de l’affichage final.
> Les messages sont tagués (patient_key, user_id, msg_type) puis filtrés/retagués
> pour éviter tout mélange d’historiques entre patients, et une vue prête à afficher
> (`chat_history_display`) est renvoyée à l’UI lorsqu’un changement de patient survient.
> 
> **1. handle_initial_request(...) :**
>     - Prépare la phase pré-confirmation : détecte l’intention et le patient, met à jour la session et renvoie le delta d’affichage (requête + question de confirmation).
>     - Paramètres:
>         - user_input (str)
>         - session (dict)
>         - session_data (dict avec "user_id","session_id")
>         - chat_history (list)
>         - current_patient (str|None)
>         - output_mode (Literal["dash","api"]).
>     - Retourne un tuple:
>         - (chat_history: list, figures_out: list, table_html: str, anomaly_block: str, current_patient: str|None, serialized_figs: list|None, chat_history_display: Any|None).
>     Ne lance aucun pipeline métier; lève ValueError si session_data est incomplet.
>     Les messages ajoutés sont tagués (patient_key, user_id, msg_type).
> 
> **2. handle_confirmation_response(...) :**
>    - Traite la réponse de confirmation (oui/non), exécute le pipeline demandé et prépare l’affichage.
>    - Paramètres:
>         - user_input (str)
>         - session (dict)
>         - session_data (dict avec "user_id","session_id")
>         - chat_history (list, snapshot UI)
>         - current_patient (str|None)
>         - output_mode (Literal["dash","api"])
>     - Filtre/retague l’historique par (patient_key, user_id), reconstruit la paire [user_request, confirm_prompt], ajoute le delta [confirm_answer, bot_response], gère le changement de patient et réinitialise les flags d’intention.
>     - Retourne un tuple :
>         - (chat_history: list, figures_out: list, table_html: str, anomaly_block: str, current_patient: str|None, serialized_figs: list|None, chat_history_display: Any).
>     - Lève ValueError si session_data est incomplet.

---


## 📄 Module : `func.index_documents_chromadb`

> **Rôle :**
> Outils d’indexation ChromaDB pour OBY-IA.
> 
>     Ce module expose des utilitaires pour (ré)indexer des collections ChromaDB
>     à partir de répertoires de JSON structurés :
>     - `base_docx` : documents dérivés de fiches DOCX,
>     - `base_web`  : documents dérivés du scraping de sites de confiance.
> 
>     Fournit notamment une fonction de reconstruction qui
>     supprime la collection ciblée puis la reconstruit à partir des fichiers
>     présents sur disque, garantissant l’absence de documents « fantômes »
>     lorsqu’il y a des suppressions ou des changements de configuration.
> 
>     Fonctions attendues dans ce module (ou importées) :
>     - `index_documents(source_dir, source_type, client)`: effectue l’indexation
>       à partir d’un répertoire JSON (crée la collection si nécessaire).
>     - `collection_name_for(source_type)`: mappe 'docx'/'web' vers le nom
>       de collection ChromaDB (p. ex. 'base_docx' / 'base_web').
>     - `rebuild_collection_from_disk(client, source_type, source_dir)`: supprime
>       la collection puis réindexe depuis le disque (cf. docstring ci-dessous).

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
> Fonctions :
> - clean_patient_document(data: dict, trace: bool = False) -> dict | (dict, list[str])
> 
> Comportement :
> 1) supprime les champs vides / non informatifs ("", "non renseigné", "null")
> 2) supprime les champs sensibles explicitement demandés (usager + contacts)
> 3) émonde les conteneurs (dict/list) devenus vides
> 4) (optionnel) trace chaque suppression si trace=True
> 
> Entrée : dict (JSON patient)
> Sortie :
> - si trace=False : dict nettoyé
> - si trace=True  : (dict nettoyé, liste des suppressions)

---


## 📄 Module : `func.poa_loader`

> **Rôle :**
> Module de chargement des fichiers POA (Plan d’Objectifs et d’Actions) au format JSON.
> Ce module permet de localiser et lire un fichier patient stocké dans le dossier `data/poa_patients/`.

---


## 📄 Module : `func.retrieve_relevant_chunks`

> **Rôle :**
> Outils de récupération et de formatage des extraits (“chunks”) pour le RAG.
> 
> Ce module interroge deux collections Chroma (DOCX prioritaire, WEB secondaire),
> sélectionne les passages pertinents, puis garde côté WEB uniquement ceux qui
> apportent une information complémentaire (TF-IDF “novelty”) et restent proches
> de la requête (similarité embeddings). Les extraits sont formatés avec des
> identifiants [DOCXn]/[WEBn], titres, sources/URLs et un fallback
> [WEB_PERTINENCE] si aucun lien web pertinent n’est retenu. Seuils et top-K
> sont pilotés par la configuration.

---


## 📄 Module : `func.run_full_indexing_pipeline`

> **Rôle :**
> Module `run_full_indexing_pipeline.py` – Pipeline principal d’indexation documentaire pour OBY-IA.
> 
> Pipeline d'indexation ChromaDB pour OBY-IA.
> 
> Ce module orchestre la maintenance de l’index vectoriel à partir de deux sources :
> 1) des fiches au format DOCX (converties en JSON),
> 2) des pages web de confiance (scrapées en JSON).
> 
> Il a pour objectif d'être appelé au démarrage et à chaque événement Watchdog.
> 
> Fonctionnement, synthèse :
> - Détection des changements via `detect_changes_and_get_modified_files()` :
>   ajouts, modifications, suppressions de fichiers DOCX/WEB, changement de
>   `trusted_web_sites_list.py`.
> - Nettoyage :
>   - suppression des JSON dérivés de DOCX supprimés,
>   - purge défensive des JSON web si la configuration des sites change.
> - Production des données :
>   - conversion DOCX → JSON si des DOCX ont changé,
>   - scraping complet/partiel des sites web si nécessaire.
> - Reconstruction des index ChromaDB :
>   - réindexation des collections à partir des dossiers JSON présents sur disque.
> - Mise à jour du journal et pose d’un « ready flag ».
> 
> Dépendances (importées ailleurs dans le projet) :
> - `detect_changes_and_get_modified_files`, `update_index_journal`
> - `convert_and_save_fiches`
> - `scrape_all_trusted_sites`
> - `get_chroma_client`, `index_documents` (ou `rebuild_collection_from_disk`)
> - constantes de chemins : `INPUT_DOCX`, `JSON_HEALTH_DOC_BASE`,
>   `WEB_SITES_JSON_HEALTH_DOC_BASE`, `WEB_SITES_MODULE_PATH`, `BASE_DIR`
> 
> Notes :
> - Les purges de répertoires sont précédées de vérifications de chemin
>   (résolution absolue, inclusion sous `BASE_DIR`).
> - Les erreurs critiques d’E/S sont loguées sur STDERR.
> - Pour éviter des relances concurrentes, préférer un déclencheur
>   « debounced + lock » côté Watchdog.

---


## 📄 Module : `func.scrape_trusted_sites`

> **Rôle :**
> Module de scraping des sites de confiance.
> 
>     Il extrait un contenu structuré (titres h1–h4, paragraphes, listes, blockquotes, tables),
>     enregistre les hyperliens par section, et explore en BFS (profondeur 2) limité au même
>     domaine et à un nombre de pages par site. Les pages sont enrichies de métadonnées
>     (titre, dates, auteur, URL canonique, source originelle) et sauvegardées en JSON dans
>     le répertoire configuré. L’ingestion de PDF peut être activée pour des domaines autorisés,
>     tout en conservant un format de sortie stable pour le pipeline d’indexation.

---


## 📄 Module : `func.serialize_figs`

> **Rôle :**
> Module de sérialisation et désérialisation de graphiques Plotly.
> Permet d’encoder les objets graphiques en base64 pour stockage ou transmission,
> et de les décoder pour affichage ultérieur dans l'application.

---


## 📄 Module : `utils.chroma_client`

> **Rôle :**
> Point d’accès centralisé au client Chroma avec cache et reset sûrs.
> 
> Ce module expose `get_chroma_client()` (LRU-caché) pour créer un client
> unique et cohérent sur tout le projet, ainsi que `reset_chroma_client_cache()`
> pour invalider ce cache lors des resets/rebuilds. L’objectif est d’éviter
> les handles orphelins et les états SQLite en lecture seule, en garantissant
> une seule façon d’instancier le client (p. ex. PersistentClient) et des
> chemins/flags unifiés via `config.config`. Peut inclure un logging de debug
> optionnel pour tracer les appels au client pendant l’indexation.

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
> Convertit un dossier patient au format JSON en texte libre lisible par un LLM.
> Parcourt dynamiquement chaque bloc (usager, contacts, aggir, social, sante, dispositifs, poa*)
> et toutes leurs sous-branches, avec un repli récursif générique pour ne rien perdre si le schéma évolue.
> Normalise le texte (Unicode NFKC, “smart title” français pour MAJUSCULES), ainsi que dates, booléens et nombres.
> Gère AGGIR en ne lisant que la clé 'Resultat' (sans espace) et en aplatissant variables/sous-variables/adverbes.
> Supporte 0..n contacts et variabilité des champs (synonymes, listes/chaînes).
> Retourne une chaîne structurée par sections.

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
> Réinitialise proprement l’environnement d’indexation Chroma et les artefacts locaux.
> 
> Ce module fournit `reset_all_data()` qui, sous verrou inter-processus,
> efface le dossier Chroma, nettoie les JSON générés et réinitialise le
> journal via une écriture atomique. Il supprime le ready-flag, pose le
> flag `.force_full_index` (écriture atomique) et recrée les répertoires
> avec des permissions minimales sûres. Aucun client Chroma direct n’est
> instancié ici : le cache client global est d’abord invalidé pour éviter
> les handles orphelins et les erreurs SQLite “readonly (1032)”.

---


## 📄 Module : `utils.scheduler`

> **Rôle :**
> Scheduler de réindexation Chroma : surveillance, sérialisation et relance sûres.
> 
> Ce module démarre un watchdog des dossiers d’entrée, scrute le flag
> `.force_full_index` et lance le pipeline via `_run_pipeline_safely()`,
> sous verrou inter-processus. Il effectue une probe d’écriture sans
> embedder, n’exécute le pipeline que si la base est utilisable, et ne
> pose le `index_ready.flag` qu’en cas de succès, en consommant le flag
> de forçage ensuite. Il évite les accès concurrents à Chroma pendant
> les resets/rebuilds et peut appliquer un backoff sur les relances.

---


## 📄 Module : `utils.vector_db_utils`

> **Rôle :**
> Utilitaires pour la base vectorielle (Chroma) : flags et E/S atomiques.
> 
> Ce module regroupe des helpers pour gérer les drapeaux de statut
> (`index_ready.flag`, `.force_full_index`), avec des écritures atomiques
> et une suppression tolérante aux erreurs. Il peut fournir des fonctions
> comme `mark_index_ready_flag()` et `clear_index_ready_flag()` basées
> sur les chemins centralisés de `config.config`. L’objectif est d’éviter
> les états incohérents pendant les resets/rebuilds et d’offrir une API
> simple et sûre aux autres modules (scheduler, UI, pipelines).

---


## 📄 Module : `llm_user_session.model`

> **Rôle :**
> Module de configuration du modèle LLM pour l'application OBY-IA.
> 
> Ce module initialise un modèle de langage basé sur les clés API disponibles dans
> les variables d'environnement. L'ordre de priorité est le suivant :
>     1. Mistral (ChatMistralAI)
>     2. OpenAI (ChatOpenAI) en fallback si Mistral n'est pas disponible
> 
> Il gère la sécurisation via des blocs try/except afin d'éviter un plantage en cas
> d'erreur d'initialisation (clé manquante, modèle indisponible, etc.). Tous les
> événements importants sont journalisés via le module standard `logging`.
> 
> Attributs:
>     llm_model (ChatMistralAI | ChatOpenAI | None): 
>         Instance unique du modèle de langage, ou None si aucune initialisation
>         n'a pu être réalisée.

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

