"""
Initialisation de l'instance unique du gestionnaire de sessions utilisateur.

Ce module importe la classe `SessionManager` et instancie un objet unique
`session_manager_instance` utilisé pour gérer les sessions utilisateur
dans l'application OBY-IA.

Cette instance centralisée permet de partager la gestion des sessions entre
différents modules sans créer plusieurs objets SessionManager.
"""

from .session_manager import SessionManager
session_manager_instance = SessionManager()
