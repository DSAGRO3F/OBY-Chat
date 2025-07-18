# TODO: Redirection vers page "home.py" après authentification réussie
#       ➜ Vérifier l'URL de redirection et l'état de la session utilisateur.

# TODO: Vider l'emplacement de texte entrée utilisateur après avoir obtenu la réponse du modèle
#       ➜ Ajout d'une méthode pour réinitialiser le champ de saisie dans Dash.

# TODO: ✅ Création fonction recherche de documents de référence en local sur le disque
#       ➜ Scanner un dossier local, filtrer par type (PDF, DOCX) et renvoyer les liens trouvés.

# TODO: ✅ Adaptation de fonctions pour lire un format "json" au lieu d'un format PDF
#       ➜ Modifier les fonctions de chargement (loader.py) pour intégrer la lecture de JSON.

# TODO: Suite réunions (matin et après midi) du 04/06/2025
#       -> 1. Dans le PPA, "Situation médicale et sociale"
#           ->  Séparer le médical du social
#           ->  Si utilisateur avec droits insuffisants et que section médicale est alors vide, mettre une mention "Droits insufisants" par exemple.
#       -> 2. Le json d'entrée sera vidé de certaines informations en fonction des droits utilisateur
#       ✅-> 3. Anonymisation: Prévoir de remplacer le nom du patient si le nom apparaît aussi dans d'autres sections du PPA
#       ✅-> 4. Bouton "EXPORTER": doit permettre de sauvegarder l'historique des réponses du LLM pour un patient donné dans un fichier markdown
#       -> 5. Lister les sources utilisées par le LLM (metadata)

# TODO: ‼️ ATTENTION!
#   1. Constantes: Affichage des constantes implique aller rechercher les valeurs par patient pour voir l'évolution de celles-ci.
#   2. Est ce toujours un objectif ?
#   3. A quelle fréquence les valeurs sont elles saisies ?
#   - A terme: récupération constantes à partir de devices

# TODO: ‼️ ATTENTION!
#   1. Est ce que l'affichage des extraits des recherches + détails convient ?
#   2. Si non, comment l'adapter ?
#   3. L'IA doit être capable de retouner une information suite à une requête utilisateur (nouvel évènement du jour concernant le patient) en prenant des sources sur
#   - base de référence documentaire avec interprétation à partir dossier patient
#   - web
#   - dossier patient

# TODO: ⚠️ Mise à jour schéma pour y inclure "recherche locale"


