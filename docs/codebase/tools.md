# Outils IA & Traitement

Ce chapitre regroupe la documentation technique des modules qui assurent le traitement des données, les fonctions d'IA, la gestion des sessions, les pages Dash, ainsi que le point d'entrée de l’application.

---

## 📁 Module : `api`
<!---
src/api/routes/chat.py

chat.py — Routes API pour la gestion des échanges entre l'utilisateur et OBY-IA.

📁 Chemin : src/api/routes/chat.py

Ce module définit les endpoints FastAPI permettant d'interagir avec l'agent
conversationnel OBY-IA via API.  
Il gère la réception des requêtes utilisateur, la transmission au moteur
de traitement (`process_user_input`) et le renvoi des réponses formatées.

Fonctionnalités principales :
- Point d'entrée `/chat` (méthode POST) pour envoyer un message et recevoir une réponse.
- Conversion automatique de la requête JSON en modèle `ChatRequest`.
- Utilisation du modèle `ChatResponse` pour structurer la réponse API.
- Passage des données de session, historique de chat et contexte patient
  au moteur de traitement.

Imports :
- `APIRouter` : gestion des routes FastAPI.
- `ChatResponse`, `ChatRequest` : modèles Pydantic pour la validation des données.
- `process_user_input` : fonction cœur de traitement des requêtes.

Usage :
    POST /chat
    Body : ChatRequest (JSON)
    Retour : ChatResponse (JSON)
--->

::: api.routes.chat
    options:
      show_source: true
      heading_level: 2

---

<!---
src/api/routes/export.py
Exporte l’historique de conversation OBY-IA au format Markdown et renvoie l’URL du fichier.

Cette route :
1) vérifie la présence d’une session valide (session_id),
2) désérialise les éventuels graphiques des constantes (Plotly) fournis,
3) appelle `export_llm_responses(...)` pour générer le fichier `.md` dans `outputs/...`,
4) retourne une réponse JSON avec un lien web pointant vers la ressource statique
   (mappée par l’application vers `/static/...`).

Paramètres
----------
payload : ExportRequest
    Corps de requête contenant :
    - `session_data` : dict avec au minimum `session_id`,
    - `current_patient` : nom du patient (utilisé pour le nommage/chemin),
    - `serialized_figs` : liste des figures Plotly sérialisées (peut être vide).

Returns
-------
dict
    Objet JSON avec :
    - `status` : "success" ou "error",
    - `message` : détail du résultat,
    - `markdown_file_url` : URL relative `/static/...` vers le fichier exporté, ou `None` en cas d’erreur.

Notes
-----
- Cette route suppose que l’application FastAPI a monté un répertoire statique
  exposant `outputs/` sous le préfixe `/static/`.
- Si aucun graphique n’est fourni, l’export Markdown se base uniquement sur l’historique
  de session (messages utilisateur / réponses OBY-IA) maintenu par `session_manager_instance`.

--->

::: api.routes.export
    options:
      show_source: true
      heading_level: 2

---

<!---
src/api/routes/login.py

Authentifier un utilisateur et créer une nouvelle session.

Vérifie si les identifiants fournis correspondent à un utilisateur
valide dans la base locale. Si oui, génère un identifiant de session
unique, initialise la session dans le gestionnaire centralisé, et
retourne les données de session.

Args:
    request (LoginRequest): Objet contenant `user_id` et `password`.

Returns:
    LoginResponse: Message de confirmation et données de session.

Raises:
    HTTPException: Si les champs sont manquants (400) ou si les
    identifiants sont invalides (401).
--->

::: api.routes.login
    options:
      show_source: true
      heading_level: 2

---

<!---
src/api/routes/logout.py

Déconnecter un utilisateur et réinitialiser sa session.

Supprime la session identifiée par `user_id` et `session_id` du
gestionnaire centralisé. Retourne un indicateur `already_logged_out`
pour signaler si la session était déjà inexistante.

Args:
    request (LogoutRequest): Objet contenant `user_id` et `session_id`.

Returns:
    LogoutResponse: Message de confirmation, état des données de
    session, et indicateur `already_logged_out`.

Raises:
    HTTPException: Si la requête est invalide (400) ou si les champs
    obligatoires sont absents.

--->

::: api.routes.logout
    options:
      show_source: true
      heading_level: 2

---

<!---
src/api/routes/poa_patients.py
Module API pour la gestion des dossiers patients POA dans OBY-IA.

Ce module expose plusieurs endpoints sécurisés pour :
    - Lister les fichiers patients disponibles.
    - Lire un dossier patient au format JSON.
    - Créer un nouveau dossier patient.
    - Mettre à jour un dossier patient existant.
    - Supprimer un dossier patient.

Seuls les utilisateurs authentifiés disposant des droits d'édition
(actuellement : `admin`) peuvent effectuer ces opérations.

Endpoints :
    GET    /patients           → Liste les fichiers patients.
    GET    /patients/{file}    → Retourne le contenu JSON d’un patient.
    POST   /patients           → Crée un nouveau dossier patient.
    PUT    /patients/{file}    → Met à jour un dossier patient existant.
    DELETE /patients/{file}    → Supprime un dossier patient.

Sécurité :
    Les appels nécessitent les en-têtes HTTP :
        X-User-Id    : identifiant utilisateur
        X-Session-Id : identifiant de session obtenu via /auth/login
--->

::: api.routes.poa_patients
    options:
      show_source: true
      heading_level: 2

---

<!---
src/api/routes/status.py
Vérifie si les index ChromaDB sont prêts à être interrogés.
Renvoie le statut à l’interface OBY pour activer/désactiver les champs.
--->

::: api.routes.status
    options:
      show_source: true
      heading_level: 2

---

<!---
src/api/main_api.py

point d’entrée du serveur FastAPI. main_api.py a pour rôle de :
Créer l’objet FastAPI()
Importer et inclure les routes (chat, login, logout…)
Définir la configuration de CORS (permet d’autoriser les appels depuis l’interface OBY)
Ajouter éventuellement des middlewares (authentification, logs, etc.)
--->

::: api.main_api
    options:
      show_source: true
      heading_level: 2

---

<!---
src/api/models.py

Ce fichier regroupe toutes les structures de données échangées avec l’API, basées sur pydantic.
--->

::: api.models
    options:
      show_source: true
      heading_level: 2

---


## 📁 Module : `data`
<!---
Module de génération de données fictives pour les constantes médicales.
Ce module permet de créer une base SQLite contenant des données simulées pour plusieurs types
de constantes de santé : poids, tension artérielle, fréquence cardiaque et température.
Les données sont générées automatiquement pour un ensemble de patients fictifs,
sur une période de 16 semaines, afin de servir de base de tests dans l'application OBY-IA.
--->

::: data.constant_generator
    options:
      show_source: true
      heading_level: 2

---

<!---
Module d'accès aux constantes médicales des patients depuis la base SQLite.
Ce module permet :
- d’identifier les constantes disponibles en base (poids, tension, etc.),
- de récupérer l’historique des valeurs d’un patient pour chaque constante.
Les données extraites sont retournées sous forme de DataFrames Pandas,
prêtes à être analysées ou visualisées dans l'application OBY-IA.
--->

::: data.get_constants
    options:
      show_source: true
      heading_level: 2

---


## 📁 Module : `func`
<!---
Anonymisation de l'usager via persona française (session-aléatoire).

Ce module fournit :
- Des pools de valeurs françaises (prénoms, noms, voies, codes postaux/communes).
- La création d'une persona cohérente pour l'usager (prénom selon le genre, nom, adresse, CP/commune).
- Des utilitaires pour lire/écrire dans un dictionnaire JSON par chemins imbriqués.
- Une anonymisation ciblée des champs usager que vous avez listés.
- La construction d'un mapping {valeur_anonymisée: valeur_originale} pour la désanonymisation.

Entrée : dict JSON (document patient).
Sortie : Tuple[Any, Dict[str, str]] -> (document anonymisé, mapping).
--->

::: func.anonymizer
    options:
      show_source: true
      heading_level: 2

---

<!---
    Fonction centrale appelée par l'API ou l'interface pour traiter la requête utilisateur.

    Args:
        send_clicks (int): Nombre de clics sur le bouton envoyer.
        user_input (str): Message saisi par l'utilisateur.
        chat_history (list): Historique des échanges.
        session_data (dict): Données de session utilisateur.
        current_patient (Optional[str]): Nom du patient actuellement sélectionné.

    Returns:
        dict: Dictionnaire contenant les résultats du traitement.
--->

::: func.api_core
    options:
      show_source: true
      heading_level: 2

---

<!---
Module de déclenchement automatique de l'indexation documentaire.

Vérifie les modifications dans les fichiers DOCX et les pages web médicales,
et lance l'indexation via ChromaDB uniquement si des changements sont détectés.
--->

::: func.auto_index_documents
    options:
      show_source: true
      heading_level: 2

---

<!---
Module de génération de prénoms anonymisés à partir du sexe renseigné.

Ce module permet de produire des prénoms fictifs cohérents avec le sexe (masculin, féminin ou inconnu)
dans le cadre d’un processus d’anonymisation de données personnelles.
Il inclut également des valeurs codées en dur pour compléter des structures anonymisées.
--->

::: func.detect_genre
    options:
      show_source: true
      heading_level: 2

---

<!---
Module de détection du chemin du fichier patient.

Ce module fournit une fonction pour localiser automatiquement un fichier contenant les données
d’un patient, à partir de son nom, dans le dossier `src/data/poa_patients`.
--->

::: func.detect_poa_file_path
    options:
      show_source: true
      heading_level: 2

---

<!---
Module pour l'extraction du nom du patient à partir d'une requête utilisateur.

Ce module utilise un LLM pour analyser une phrase en langage naturel
et en extraire uniquement le nom de famille du patient mentionné.
--->

::: func.extract_patient_name
    options:
      show_source: true
      heading_level: 2

---

<!---
Module extract_user_intent

Ce module permet de détecter l’intention principale d’un utilisateur à partir de sa requête textuelle.
La détection repose d’abord sur des correspondances par mots-clés, puis bascule sur un modèle de langage
(LLM) si aucune correspondance directe n’est trouvée.

Modifications apportées :
- Ajout d’une hiérarchie de priorité dans la détection par mots-clés pour résoudre les ambiguïtés.
- Ajout de docstrings conformes à la PEP 257.
- Refactorisation avec étapes explicites et commentaires clairs.
--->

::: func.extract_user_intent
    options:
      show_source: true
      heading_level: 2

---

<!---
Module free_text_name_anonymizer

Ce module gère l’anonymisation et la désanonymisation des mentions libres
du nom et prénom du patient dans un POA (Plan d’Objectifs et d’Actions).

Contrairement à l’anonymisation structurée (sections « usager » et « contacts »),
les informations saisies manuellement par les évaluateurs peuvent contenir
le nom ou le prénom du patient dans des champs texte libres
(ex. « Mme Anne Dupont, son épouse est présente »).

Fonctionnalités principales :
    - Normalisation des chaînes (suppression des accents, casse insensible,
      gestion des espaces Unicode).
    - Construction de variantes (nom, prénom, « Prénom Nom », « Nom Prénom »,
      civilités + nom, civilités + prénom + nom).
    - Parcours récursif des structures de type dict/list pour détecter
      les chaînes contenant le nom/prénom du patient.
    - Remplacement par l’alias choisi lors de l’anonymisation structurée.
    - Mise à jour du mapping {alias -> original} pour permettre la
      désanonymisation correcte de la réponse du LLM.
--->

::: func.free_text_name_anonymizer
    options:
      show_source: true
      heading_level: 2

---


<!---
Module de génération de PPA (Plan Personnalisé d’Accompagnement) à partir d’un document POA.

Ce module extrait le nom du patient depuis la requête utilisateur, charge et nettoie le document POA
correspondant, anonymise les données, formate le contenu pour le modèle LLM, puis génère un PPA structuré.
--->

::: func.generate_ppa_from_poa
    options:
      show_source: true
      heading_level: 2

---

<!---
Module de génération d’un plan d’action structuré à partir du POA d’un patient.

Ce module est déclenché lorsque l’intention « generate_recommendations » est détectée.
Il extrait le nom du patient, charge et nettoie le document POA, anonymise les données,
puis interroge un modèle LLM avec un prompt enrichi pour générer des recommandations classées
(par type d'action : prévention, soins, traitements, etc.).
--->

::: func.generate_structured_medical_plan
    options:
      show_source: true
      heading_level: 2

---

<!---
    Statistiques sur les données indexées dans ChromaDB et les fichiers JSON préparés.

    Returns:
        dict: {
            "docx_files": int,        # Fichiers uniques indexés depuis docx
            "web_files": int,         # Fichiers uniques indexés depuis web
            "docx_chunks": int,
            "web_chunks": int,
            "docx_json_files": int,   # Fichiers JSON générés depuis les DOCX
            "web_json_files": int     # Fichiers JSON générés depuis le web
        }
--->

::: func.get_chroma_stats
    options:
        show_source: true
        heading_level: 2
---

<!---
Module d'analyse et de visualisation des constantes médicales des patients.

Ce module permet :
- de convertir les constantes brutes issues de la base de données en DataFrame,
- de détecter des anomalies selon des seuils définis,
- de générer des graphiques Plotly (poids, tension, température...),
- de produire des tableaux HTML interactifs pour Dash,
- de centraliser le traitement dans une fonction complète pour l’interface.

Utilisé notamment dans la page chatbot_ui de l’application OBY-IA.
--->

::: func.get_patient_constants_graphs
    options:
      show_source: true
      heading_level: 2

---

<!---
Gestion des requêtes utilisateur pour OBY-IA (détection d’intention, confirmation et exécution).

Ce module centralise la logique conversationnelle « back-end » entre l’interface
et les pipelines métier d’OBY-IA. Il orchestre deux étapes clés :

1) handle_initial_request(...) :
   - Analyse l’input utilisateur (détection d’intention et extraction éventuelle
     du nom de patient).
   - Met en place un état de confirmation (session["intent_confirmation_pending"] = True)
     et prépare un message de confirmation.
   - Retourne les éléments nécessaires pour l’affichage / la réponse (historique,
     tableaux, graphiques, etc.), généralement vides à ce stade.

2) handle_confirmation_response(...) :
   - Interprète la confirmation (ex.: « oui / non ») lorsque l’intention est en attente.
   - Déclenche le pipeline adapté :
       • PPA (generate_ppa_from_poa.process_ppa_request),
       • Recommandations (generate_structured_medical_plan),
       • Constantes patient (process_patient_request_with_constants).
   - Met à jour l’état de session (réinitialisation du flag de confirmation,
     mémorisation du patient courant, etc.) et assemble la réponse finale.

Modes de sortie :
    Le paramètre `output_mode` permet d’adapter le format des objets retournés :
      - "dash" : le module peut retourner des composants Dash (html.Div, dcc.Markdown,
                 figures Plotly « go.Figure », etc.) pour l’UI interne.
      - "api"  : le module retourne des structures sérialisables (listes/dicts/strings),
                 adaptées à FastAPI / JSON (pas d’objets Dash).

Effets de bord :
    - Mise à jour de la session (ex. intent_confirmation_pending, intent_candidate).
    - Enrichissement de l’historique de conversation (chat_history / new_chat_history).

Dépendances principales :
    - src.llm_user_session.session_manager_instance
    - src.func.extract_user_intent, src.func.extract_patient_name
    - src.func.generate_ppa_from_poa, src.func.generate_structured_medical_plan
    - src.func.get_patient_constants_graphs
    - src.func.serialize_figs (sérialisation des figures)
    - (optionnel côté UI) dash.html / dash.dcc pour le mode "dash"

Convention de retour :
    Les fonctions retournent un 7-uplet :
        (chat_history_ou_new_chat_history,
         figures_out,
         table_html,
         anomaly_block,
         current_patient,
         serialized_figs,
         chat_history_display)

    * En mode "initial", chat_history est renvoyé (nouvel historique cumulé).
    * En mode "confirmation", new_chat_history est renvoyé (ajouts du tour courant).
    * Le « full_chat_history » est assemblé par l’appelant si nécessaire.

Ce module est conçu pour être appelé à la fois par l’interface Dash (UI)
et par la couche API (FastAPI) via une fonction « tronc commun ».
--->

::: func.handle_user_requests
    options:
      show_source: true
      heading_level: 2

---

<!---
    Outils d’indexation ChromaDB pour OBY-IA.

    Ce module expose des utilitaires pour (ré)indexer des collections ChromaDB
    à partir de répertoires de JSON structurés :
    - `base_docx` : documents dérivés de fiches DOCX,
    - `base_web`  : documents dérivés du scraping de sites de confiance.

    Fournit notamment une fonction de reconstruction qui
    supprime la collection ciblée puis la reconstruit à partir des fichiers
    présents sur disque, garantissant l’absence de documents « fantômes »
    lorsqu’il y a des suppressions ou des changements de configuration.

    Fonctions attendues dans ce module (ou importées) :
    - `index_documents(source_dir, source_type, client)`: effectue l’indexation
      à partir d’un répertoire JSON (crée la collection si nécessaire).
    - `collection_name_for(source_type)`: mappe 'docx'/'web' vers le nom
      de collection ChromaDB (p. ex. 'base_docx' / 'base_web').
    - `rebuild_collection_from_disk(client, source_type, source_dir)`: supprime
      la collection puis réindexe depuis le disque (cf. docstring ci-dessous).
--->

::: func.index_documents_chromadb
    options:
      show_source: true
      heading_level: 2

---

<!---
Module de suivi et de détection des changements dans les fichiers de santé.

Il permet de :
- Calculer le hash des fichiers (DOCX, JSON, Python) pour en détecter les modifications.
- Comparer l’état actuel à un journal enregistré.
- Déterminer quels fichiers nécessitent une réindexation.
--->

::: func.indexed_health_related_files
    options:
      show_source: true
      heading_level: 2

---

<!---
Module de génération de prompts pour produire des Plans Personnalisés d’Accompagnement (PPA) ou des recommandations médicales,
à partir du POA d’un patient et d’une requête utilisateur. Intègre également la version RAG avec enrichissement par des documents issus de ChromaDB.
--->

::: func.llm_prompts
    options:
      show_source: true
      heading_level: 2

---

<!---
Module de nettoyage des documents POA (Plan d’Objectifs et d’Actions).

Fonctions :
- clean_patient_document(data: dict, trace: bool = False) -> dict | (dict, list[str])

Comportement :
1) supprime les champs vides / non informatifs ("", "non renseigné", "null")
2) supprime les champs sensibles explicitement demandés (usager + contacts)
3) émonde les conteneurs (dict/list) devenus vides
4) (optionnel) trace chaque suppression si trace=True

Entrée : dict (JSON patient)
Sortie :
- si trace=False : dict nettoyé
- si trace=True  : (dict nettoyé, liste des suppressions)
--->

::: func.poa_cleaning
    options:
      show_source: true
      heading_level: 2

---

<!---
Module de chargement des fichiers POA (Plan d’Objectifs et d’Actions) au format JSON.
Ce module permet de localiser et lire un fichier patient stocké dans le dossier `data/poa_patients/`.
--->

::: func.poa_loader
    options:
      show_source: true
      heading_level: 2

---

<!---
Module de récupération des extraits pertinents depuis une base ChromaDB.
Ce module interroge une collection vectorielle Chroma (via LangChain)
et retourne les passages les plus similaires à une requête, pour enrichir un prompt.
--->

::: func.retrieve_relevant_chunks
    options:
      show_source: true
      heading_level: 2

---

<!---
Module `run_full_indexing_pipeline.py` – Pipeline principal d’indexation documentaire pour OBY-IA.

Pipeline d'indexation ChromaDB pour OBY-IA.

Ce module orchestre la maintenance de l’index vectoriel à partir de deux sources :
1) des fiches au format DOCX (converties en JSON),
2) des pages web de confiance (scrapées en JSON).

Il a pour objectif d'être appelé au démarrage et à chaque événement Watchdog.

Fonctionnement, synthèse :
- Détection des changements via `detect_changes_and_get_modified_files()` :
  ajouts, modifications, suppressions de fichiers DOCX/WEB, changement de
  `trusted_web_sites_list.py`.
- Nettoyage :
  - suppression des JSON dérivés de DOCX supprimés,
  - purge défensive des JSON web si la configuration des sites change.
- Production des données :
  - conversion DOCX → JSON si des DOCX ont changé,
  - scraping complet/partiel des sites web si nécessaire.
- Reconstruction des index ChromaDB :
  - réindexation des collections à partir des dossiers JSON présents sur disque.
- Mise à jour du journal et pose d’un « ready flag ».

Dépendances (importées ailleurs dans le projet) :
- `detect_changes_and_get_modified_files`, `update_index_journal`
- `convert_and_save_fiches`
- `scrape_all_trusted_sites`
- `get_chroma_client`, `index_documents` (ou `rebuild_collection_from_disk`)
- constantes de chemins : `INPUT_DOCX`, `JSON_HEALTH_DOC_BASE`,
  `WEB_SITES_JSON_HEALTH_DOC_BASE`, `WEB_SITES_MODULE_PATH`, `BASE_DIR`

Notes :
- Les purges de répertoires sont précédées de vérifications de chemin
  (résolution absolue, inclusion sous `BASE_DIR`).
- Les erreurs critiques d’E/S sont loguées sur STDERR.
- Pour éviter des relances concurrentes, préférer un déclencheur
  « debounced + lock » côté Watchdog.
--->

::: func.run_full_indexing_pipeline
    options:
      show_source: true
      heading_level: 2

---

<!---
Module de scraping des sites web de confiance en santé.

Ce module permet :
- de charger dynamiquement la liste des sites référencés,
- d’extraire les liens utiles à partir de pages de départ,
- de structurer le contenu HTML pertinent (titres, paragraphes, listes),
- et de sauvegarder les pages web sous forme de fichiers JSON pour indexation.
Utilisé pour alimenter une base documentaire de recommandations en santé.
--->

::: func.scrape_trusted_sites
    options:
      show_source: true
      heading_level: 2

---

<!---
Module de sérialisation et désérialisation de graphiques Plotly.
Permet d’encoder les objets graphiques en base64 pour stockage ou transmission,
et de les décoder pour affichage ultérieur dans l'application.
--->

::: func.serialize_figs
    options:
      show_source: true
      heading_level: 2

---


## 📁 Module : `utils`

<!---
Module d’accès centralisé au client ChromaDB pour l'application OBY-IA.
Ce module fournit une fonction utilitaire permettant d’instancier un client ChromaDB
persistant, configuré pour enregistrer les données dans le répertoire défini par
`CHROMA_GLOBAL_DIR`. Il garantit qu’une seule instance client est utilisée
grâce au décorateur `lru_cache`.
Utilisé dans l'ensemble du projet pour interagir avec la base Chroma.
--->

::: utils.chroma_client
    options:
      show_source: true
      heading_level: 2

---

<!---
Module de conversion de fiches documentaires DOCX en fichiers JSON exploitables.

Ce module permet d’extraire le contenu textuel structuré de fichiers Word (.docx)
présents dans un répertoire donné, et de les convertir en dictionnaires JSON.
Ces JSON sont ensuite utilisés dans l’application OBY-IA pour l’indexation
et la recherche sémantique de recommandations.

Fonctionnalités :
- Lecture et traitement de fichiers `.docx`.
- Nettoyage et normalisation du contenu.
- Export en fichiers `.json` avec le même nom de base.
--->
::: utils.convert_fiches_docx_to_json
    options:
      show_source: true
      heading_level: 2

---

<!---
Module de conversion des données JSON d'un POA en texte structuré pour LLM.

Ce module extrait les informations pertinentes du dictionnaire JSON d’un plan
d’objectifs et d’actions (POA), notamment les données de la personne accompagnée,
ses contacts et les différentes sections thématiques (social, santé, autonomie).
Il génère un texte lisible destiné à être injecté dans un prompt pour un modèle LLM.

Utilisé pour formater proprement les données en amont d’une génération automatique
de synthèse ou de recommandations.
--->

::: utils.convert_json_text
    options:
      show_source: true
      heading_level: 2

---

<!---
Module d'export des réponses générées par le modèle LLM pour un patient donné.

Ce module permet de récupérer toutes les réponses associées à une session (requête utilisateur + réponse LLM),
de les concaténer proprement, et de les exporter dans un fichier Markdown.
Il peut également intégrer des graphiques de constantes si fournis.

Utilisé notamment pour générer des synthèses textuelles enrichies à partir
des sessions de chat dans l'application OBY-IA.
--->

::: utils.export_chat_response
    options:
      show_source: true
      heading_level: 2

---

<!---
Module de réinitialisation des données indexées de l'application OBY-IA.
Ce module fournit une fonction utilitaire permettant de nettoyer l’environnement
de travail en supprimant :
- les collections ChromaDB (ex. : `base_docx`, `base_web`),
- les fichiers JSON issus de l’extraction documentaire locale et web,
- le fichier journal qui suit les fichiers déjà indexés.
Utile pour remettre à zéro l’état de l’index avant un nouveau traitement complet.
--->

::: utils.reset_data
    options:
      show_source: true
      heading_level: 2

---

<!---
Surveillance des répertoires et (ré)indexation ChromaDB.

- Au démarrage :
  * Si CHROMA_GLOBAL_DIR est absent ou vide → pipeline d'indexation initiale.
  * Sinon, si le flag 'index_ready' est absent :
      - Vérifie la présence des collections 'base_docx' et 'base_web'.
      - Si elles manquent → relance le pipeline.
      - Sinon → marque le flag 'ready'.
  * Si le flag est présent → simple surveillance.

- En fonctionnement :
  - Watchdog surveille INPUT_DOCX et WEB_SITES_HEALTH_DOC_BASE.
  - Au moindre changement fichier, déclenche une indexation en empêchant les exécutions simultanées.
--->

::: utils.scheduler
    options:
      show_source: true
      heading_level: 2

---

<!---
Module utilitaire pour la gestion de l'état de l'indexation ChromaDB.
Ce module contient des fonctions permettant de :
- Vérifier si l'indexation ChromaDB est terminée (via un fichier flag).
- Créer ou supprimer ce flag selon les besoins.
Ce mécanisme permet à l'application (ex. interface Dash) de savoir si les bases
vectorielles sont prêtes à être interrogées par les utilisateurs.
--->

::: utils.vector_db_utils
    options:
      show_source: true
      heading_level: 2


## 📁 Module : `llm_user_session`

<!---
Initialisation des modèles de langage utilisés dans l'application OBY-IA.
Ce module charge les clés API depuis le fichier `.env` et instancie un modèle
de langage compatible avec LangChain, en fonction de la configuration disponible.
Actuellement :
- Le modèle `ChatOpenAI` (GPT-4.1) est utilisé par défaut, en raison de la limitation
  de tokens rencontrée avec Mistral lors du traitement de documents volumineux.
- Le modèle `ChatMistralAI` reste présent en commentaire à des fins de test ou migration future.
Variables :
    llm_model : Instance unique du modèle LLM utilisé pour répondre aux requêtes utilisateur.
--->

::: llm_user_session.model
    options:
      show_source: true
      heading_level: 2

---

<!---
Gestion centralisée des sessions utilisateurs pour l'application OBY-IA.
Ce module définit deux classes principales :
- `Session` : Représente une session utilisateur, incluant l’historique des échanges entre
  l’utilisateur et le modèle LLM (chat_history).
- `SessionManager` : Gère les sessions actives à l’aide d’un dictionnaire indexé par `session_id`.
  Il permet de :
    - créer, récupérer et supprimer des sessions,
    - suivre le patient actuellement traité dans une session,
    - stocker et réinitialiser un dictionnaire de correspondance pour l’anonymisation des données,
    - enregistrer et restituer les réponses générées par le LLM pour les réutiliser (ex. : génération de documents PDF).
Ce gestionnaire est conçu pour un usage multi-utilisateur avec une mémoire indépendante par session.
--->

::: llm_user_session.session_manager
    options:
      show_source: true
      heading_level: 2

---

<!---
Initialisation de l'instance unique du gestionnaire de sessions utilisateur.

Ce module importe la classe `SessionManager` et instancie un objet unique
`session_manager_instance` utilisé pour gérer les sessions utilisateur
dans l'application OBY-IA.

Cette instance centralisée permet de partager la gestion des sessions entre
différents modules sans créer plusieurs objets SessionManager.
--->

::: llm_user_session.session_manager_instance
    options:
      show_source: true
      heading_level: 2

---


## 📁 Module : `pages`

<!---
Module `chatbot_ui.py` – Interface conversationnelle de l'application OBY-IA (page `/chatbot`)

Ce module Dash définit la page chatbot de OBY-IA, qui permet aux professionnels de santé
d’interagir avec un agent intelligent pour obtenir :

1. **Analyse des constantes médicales du patient** :
   - Extraction et affichage des constantes sous forme de graphiques et tableaux.
   - Détection automatique des anomalies.
   - Sérialisation et désérialisation des graphiques pour l’exportation.

2. **Interaction en langage naturel avec le LLM** :
   - Détection de l’intention utilisateur (consultation, génération de PPA, recommandations).
   - Extraction du nom du patient à partir de la requête.
   - Génération de contenu médical structuré via des prompts spécialisés.
   - Historisation des messages utilisateur/LLM et affichage dynamique.

3. **Export des résultats** :
   - Génération d’un fichier Markdown résumant la session (réponses LLM + graphiques).

4. **Contrôle de disponibilité de l’index ChromaDB** :
   - Affichage d’une bannière d’attente tant que l’index n’est pas prêt.
   - Activation différée des composants de saisie utilisateur.

5. **Gestion de la deconnexion de l'utilisateur** :
   - Le click du bouton deconnexion dans la page de chat déclenche la supression de la session.
   - La suppression de la session entraîne celle de l'historique du chat de la fenêtre de chat.


Composants techniques :
- Utilise `session_manager_instance` pour la gestion d’état (session, mapping, historique).
- Repose sur les modules fonctionnels : `extract_user_intent`, `generate_ppa_from_poa`,
  `generate_structured_medical_plan`, `get_patient_constants_graphs`, `export_chat_response`, etc.

Cette page est au cœur de l’expérience utilisateur de OBY-IA, combinant interface conviviale
et logique métier intelligente.
--->

::: pages.chatbot_ui
    options:
      show_source: true
      heading_level: 2

---

<!---
Module `home.py` – Page d'accueil, authentification et interface d'administration de OBY-IA.

Ce module Dash gère les fonctionnalités suivantes :
1. **Authentification utilisateur** :
   - Vérification des identifiants via une base interne (`USER_DATABASE`).
   - Création et stockage de la session via `dcc.Store` et `session_manager_instance`.
   - Affichage conditionnel de l'interface selon le rôle (utilisateur ou admin).

2. **Contrôles d'administration (admin uniquement)** :
   - Réinitialisation des bases : ChromaDB, fichiers JSON extraits du web, index de suivi.
   - Interface de déclenchement réservée aux administrateurs.

3. **Accès à la documentation du projet** :
   - Vérification en temps réel de la disponibilité du serveur MkDocs (`http://127.0.0.1:8000`).
   - Redirection automatique vers la documentation si disponible.
   - Cette documentation projet n'est pas mise à jour régulièrement. Elle sera définitivement remplacée par une documentation dynamique.
   - Cette documentation dynamique pourra être consultée par le paramétrage de "start.sh".

4. **Visualisation des statistiques d’indexation ChromaDB** :
   - Affichage du nombre de fichiers indexés (DOCX, web), de chunks, et de fichiers JSON associés.
   - Rafraîchissement manuel ou automatique de ces statistiques à l’ouverture.

Ce module constitue la page d’accueil et d’entrée principale de l’application OBY-IA.
--->

::: pages.home
    options:
      show_source: true
      heading_level: 2

---

## 📄 Fichier principal : `app.py`

<!---
Module principal de l'application OBY-IA.
Ce module initialise l'application Dash, configure la navigation entre les pages,
et vérifie la disponibilité de la base de données des constantes médicales.
Fonctionnalités principales :
- Chargement des variables d'environnement depuis un fichier `.env` à la racine.
- Vérification et génération automatique de la base SQLite (`constantes_sante.db`).
- Initialisation de l'application Dash avec gestion des pages (`use_pages=True`).
- Mise en place d'une barre de navigation et d'un conteneur de pages dynamiques.
- Démarrage d'un planificateur de tâches (scheduler) dans un thread dédié au lancement.
Ce fichier doit être exécuté pour lancer le serveur Dash : `python -m src.app`
--->

::: app
    options:
      show_source: true
      heading_level: 2
