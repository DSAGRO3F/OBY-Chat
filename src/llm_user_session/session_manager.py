"""
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
"""

class Session:

    """
    Représente une session de chat entre un utilisateur et le modèle LLM.

    Cette classe stocke l'identifiant de l'utilisateur, l'identifiant de la session,
    ainsi que l'historique des échanges sous forme de couples (entrée utilisateur, réponse du modèle).

    Attributs :
        user_id (str) : Identifiant de l'utilisateur.
        session_id (str) : Identifiant unique de la session.
        chat_history (list) : Liste des messages échangés sous forme de tuples (user_input, model_response).

    Méthodes :
        add_message(user_input, model_response) :
            Ajoute un nouvel échange à l'historique de la session.
        get_history() :
            Retourne l'historique complet des échanges de la session.
    """

    def __init__(self, user_id, session_id):

        """
        Initialise une nouvelle session utilisateur.

        Args:
            user_id (str): Identifiant de l'utilisateur associé à la session.
            session_id (str): Identifiant unique de la session.

        Attributs initialisés :
            - user_id : identifiant de l'utilisateur.
            - session_id : identifiant de session.
            - chat_history : liste vide pour stocker l'historique des échanges (tuples : user_input, model_response).
        """

        self.user_id = user_id
        self.session_id = session_id
        self.chat_history = []  # Liste de tuples (user_input, model_response)

    def add_message(self, user_input, model_response):

        """
        Ajoute un échange à l'historique de la session.

        Args:
            user_input (str) : Message envoyé par l'utilisateur.
            model_response (str) : Réponse générée par le modèle LLM.

        Effet :
            L'échange est ajouté à la liste `chat_history` sous forme de tuple
            (user_input, model_response).
        """

        self.chat_history.append((user_input, model_response))

    def get_history(self):
        """
        Retourne l'historique complet des échanges de la session.

        Returns:
            list : Liste de tuples (user_input, model_response) représentant
            les échanges entre l'utilisateur et le modèle LLM.
        """

        return self.chat_history


class SessionManager:

    """
    Gestionnaire centralisé des sessions utilisateurs dans l'application OBY-IA.

    Cette classe permet de créer, suivre et supprimer les sessions utilisateur,
    tout en maintenant des informations spécifiques à chaque session, telles que :
      - l'identifiant de l'utilisateur,
      - le patient actuellement concerné par la session,
      - un dictionnaire d'anonymisation pour masquer les données sensibles,
      - les réponses générées par le modèle LLM (pour archivage ou affichage ultérieur).

    Attributs :
        sessions (dict) : Dictionnaire contenant les sessions actives, indexées par session_id.
                          Chaque entrée stocke les données associées à une session (user_id, patient, mapping, etc.).

    Méthodes principales :
        - create_session(user_id, session_id) :
            Crée une nouvelle session avec un mapping d'anonymisation vide.
        - get_session(session_id) :
            Retourne les données de session associées à un identifiant donné.
        - end_session(user_id, session_id) :
            Supprime proprement une session terminée.
        - set_current_patient(session_id, patient_name) :
            Définit le patient actif dans une session.
        - set_anonymization_mapping(session_id, mapping) :
            Enregistre un dictionnaire de correspondance pour l’anonymisation.
        - get_anonymization_mapping(session_id) :
            Récupère le mapping d’anonymisation de la session.
        - reset_anonymization_mapping(session_id) :
            Réinitialise ce mapping à une structure vide.
        - append_llm_response(session_id, response) :
            Ajoute une réponse du LLM à l’historique des réponses pour la session.
        - get_llm_responses(session_id) :
            Retourne toutes les réponses du LLM stockées dans la session.
    """

    def __init__(self):

        """
        Initialise un nouveau gestionnaire de sessions utilisateur.

        Attributs initialisés :
            sessions (dict) : Dictionnaire vide destiné à contenir les sessions actives.
                              Chaque session est indexée par son identifiant (`session_id`)
                              et contient les données associées (user_id, patient actif, mapping d’anonymisation, etc.).
        """

        self.sessions = {}  # Clé : (user_id, session_id), Valeur : Session


    def create_session(self, user_id, session_id):
        """
            Crée une nouvelle session utilisateur.

            Cette méthode initialise une nouvelle entrée dans le dictionnaire des sessions,
            contenant les informations de base nécessaires au suivi de l’utilisateur et
            à l’anonymisation des données.

            Args:
                user_id (str) : Identifiant de l'utilisateur.
                session_id (str) : Identifiant unique de la session.

            Effet :
                Ajoute une entrée dans `self.sessions` avec les clés :
                    - "user_id" : l'identifiant utilisateur,
                    - "current_patient" : initialisé à None,
                    - "anonymization_mapping" : dictionnaire vide pour les correspondances anonymes.
            """

        self.sessions[session_id] = {
            "user_id": user_id,
            "current_patient": None,
            "anonymization_mapping": {}, # Ajouté pour l'anonymisation
            "session_obj": Session(user_id, session_id),
            "intent_confirmation_pending": False,
            "intent_candidate": {"intent": None, "name": None, "full_user_input": None},
        }


    def get_session(self, session_id):
        """
    Récupère les données associées à une session existante.

    Args:
        session_id (str) : Identifiant unique de la session.

    Returns:
        dict or None : Les données de session (dictionnaire) si la session existe,
        sinon None.
    """
        return self.sessions.get(session_id, None)



    def get_chat_history(self, session_id):
        """
        Retourne l'historique des échanges utilisateur-LLM pour une session donnée.

        Args:
            session_id (str): Identifiant de la session.

        Returns:
            list of tuples: Liste des paires (user_input, model_response).
        """

        session_data = self.get_session(session_id)
        if not session_data:
            return []

        # session_data: dict = session_data or {} Pour typer la variable
        session_obj = session_data.get("session_obj")
        if session_obj:
            return session_obj.get_history()
        return []


    def end_session(self, user_id, session_id):
        """
    Supprime une session utilisateur existante.

    Cette méthode retire du gestionnaire la session correspondant à l'identifiant donné,
    si elle existe.

    Args:
        user_id (str) : Identifiant de l'utilisateur (utilisé à des fins de journalisation).
        session_id (str) : Identifiant unique de la session à supprimer.

    Effet :
        Supprime l'entrée correspondante dans `self.sessions`.
        Affiche un message de confirmation dans la console.
    """
        if session_id in self.sessions:
            del self.sessions[session_id]
            print(f"Session supprimée pour user_id={user_id}, session_id={session_id}")


    def set_current_patient(self, session_id, patient_name):
        """
    Définit le patient actuellement actif dans une session donnée.

    Cette méthode met à jour le champ `current_patient` pour la session identifiée,
    afin de suivre le patient en cours d’analyse ou de génération de documents.

    Args:
        session_id (str) : Identifiant unique de la session.
        patient_name (str) : Nom du patient à associer à la session.

    Effet :
        Met à jour la clé `"current_patient"` dans le dictionnaire de session.
    """
        if session_id in self.sessions:
            self.sessions[session_id]["current_patient"] = patient_name


    def set_anonymization_mapping(self, session_id, mapping):
        """
    Définit le dictionnaire d'anonymisation pour une session donnée.

    Ce dictionnaire permet d'associer des identifiants anonymes à leurs valeurs réelles,
    afin de préserver la confidentialité tout en conservant un historique exploitable.

    Args:
        session_id (str) : Identifiant unique de la session.
        mapping (dict) : Dictionnaire de correspondances {clé_anonyme: valeur réelle}.

    Effet :
        Met à jour la clé "anonymization_mapping" dans la session spécifiée.
    """

        if session_id in self.sessions:
            existing = self.sessions[session_id].get("anonymization_mapping", {})
            # Préserver les réponses déjà enregistrées
            llm_responses = existing.get("llm_responses", [])
            mapping["llm_responses"] = llm_responses
            self.sessions[session_id]["anonymization_mapping"] = mapping


    def get_anonymization_mapping(self, session_id):
        """
    Récupère le dictionnaire d'anonymisation associé à une session.

    Ce dictionnaire contient les correspondances entre les clés anonymes utilisées
    temporairement et les vraies valeurs, dans le cadre de la protection des données personnelles.

    Args:
        session_id (str) : Identifiant unique de la session.

    Returns:
        dict : Dictionnaire des correspondances {clé_anonyme: valeur réelle}.
               Retourne un dictionnaire vide si la session n'existe pas
               ou si aucun mapping n’a été défini.
    """
        if session_id in self.sessions:
            return self.sessions[session_id].get("anonymization_mapping", {})
        return {}


    def reset_anonymization_mapping(self, session_id):
        """
    Réinitialise le dictionnaire d'anonymisation d'une session.

    Cette méthode vide le mapping d'anonymisation associé à la session spécifiée,
    supprimant toutes les correspondances précédemment enregistrées.

    Args:
        session_id (str) : Identifiant unique de la session.

    Effet :
        Réinitialise la clé "anonymization_mapping" avec un dictionnaire vide.
    """
        if session_id in self.sessions:
            self.sessions[session_id]["anonymization_mapping"] = {}


    def append_llm_response(self, session_id, response):
        """
    Ajoute une réponse générée par le LLM à la session spécifiée.

    La réponse est stockée dans la structure d’anonymisation de la session,
    sous la clé "llm_responses", permettant un suivi des productions du modèle
    pour cette session (ex. : en vue d’une génération de document ou d’audit).

    Args:
        session_id (str) : Identifiant unique de la session.
        response (str) : Réponse produite par le modèle LLM à enregistrer.

    Effet :
        Ajoute la réponse dans la liste `llm_responses` du mapping d’anonymisation.
        Si cette liste n’existe pas, elle est créée.
        Affiche un message de confirmation ou d’erreur dans la console.
    """
        if session_id in self.sessions:
            mapping = self.sessions[session_id].get("anonymization_mapping", {})
            if "llm_responses" not in mapping:
                mapping["llm_responses"] = []
            mapping["llm_responses"].append(response)
            self.sessions[session_id]["anonymization_mapping"] = mapping  # Mise à jour explicite
            print(f"✅ Réponse ajoutée. Total actuel : {len(mapping['llm_responses'])}")
        else:
            print(f"❌ [SessionManager] Session inconnue : {session_id}")


    def get_llm_responses(self, session_id):
        """
    Récupère toutes les réponses générées par le LLM pour une session donnée.

    Ces réponses sont stockées dans le mapping d'anonymisation de la session,
    et peuvent être utilisées pour l'affichage ou l'intégration dans un document
    généré (ex. : PDF de synthèse).

    Args:
        session_id (str) : Identifiant unique de la session.

    Returns:
        list : Liste des réponses du LLM associées à la session.
               Retourne une liste vide si aucune réponse n'est enregistrée.
    """

        mapping = self.get_anonymization_mapping(session_id)
        return mapping.get("llm_responses", [])





# -> Instanciation unique du SessionManager (à importer dans chatbot_ui.py)
session_manager_instance = SessionManager()
# Explications :
# Session : Gère l’historique des échanges pour un utilisateur et une session donnés.
# SessionManager :
# create_session → Crée une session unique basée sur user_id et session_id.
# add_message → Ajoute les échanges au fil de la conversation.
# get_history → Permet d’afficher ou d’analyser l’historique pour un export éventuel.
# end_session → Permet de purger les sessions obsolètes.
