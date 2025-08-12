
# 🚀 Déploiement Docker – OBY-Chat (nouvelle version du le 26-07-2025)

## 🗂️ Projet : OBY-Chat

OBY-Chat est une application conversationnelle (Dash + IA) pour le traitement des documents de santé, la génération de plans personnalisés d'accompagnement (PPA), et l'analyse des constantes médicales des patients.  
Elle inclut également un site de documentation technique complet basé sur MkDocs.

---

## 🎯 Objectif du déploiement

- Déployer rapidement OBY-Chat via un **package Docker complet** (image + container)
- Offrir deux modes de fonctionnement :
  - `APP_MODE=app` → Interface Dash (application par défaut)
  - `APP_MODE=doc` → Site de documentation MkDocs

---

## 🧾 Arborescence essentielle

```
📦 OBY-Chat
├── Dockerfile
├── docker-compose.yml
├── docker-compose.override.yml
├── scripts/
│   └── start.sh
├── src/
├── docs/
├── assets/
├── outputs/
├── config/
└── requirements.txt / pyproject.toml
```

---

## ⚙️ Fonctionnement général

Le comportement de l'application dépend de la variable d'environnement `APP_MODE` :

- `APP_MODE=app` ou vide → Lance l’interface utilisateur OBY-Chat (Dash)
- `APP_MODE=doc` → Lance le site de documentation technique (MkDocs)

Le fichier `scripts/start.sh` s’occupe de détecter ce mode et d’exécuter la bonne commande.

---

## 🐳 Déploiement avec Docker

### 1. 🏗️ Construction de l’image (⚠️ déjà faite)

L’image Docker est **déjà construite** avant livraison du package.

> ✅ Vous **n’avez pas besoin d’exécuter** `docker build`.

---

### 2. ✅ Lancement de l’application (mode app)

```bash
docker compose up -d
```

Accéder à l’interface :

```
http://localhost:8050
```

---

### 3. ✅ Rebuild après modifications (réservé au développeur)

Si vous modifiez le code source :

```bash
docker compose down
docker compose build
docker compose up -d
```

---

### 4. ✅ Volumes montés (override)

Le fichier `docker-compose.override.yml` permet de monter des volumes en local pour un usage en développement.

---

### 5. ✅ Lancement du site de documentation (mode doc)

Vous pouvez aussi démarrer **uniquement le site de documentation MkDocs** :

```bash
docker run -p 8080:8080 -e APP_MODE=doc oby-chat
```

Puis ouvrir :

```
http://localhost:8080
```

> 📚 Ce mode utilise `mkdocs serve` à l’intérieur du container.

---

### 6. ✅ Revenir au mode application

1. Arrêter le container documentation :

```bash
docker ps    # identifier l’ID du container actif
docker stop <container_id>
```

2. Redémarrer OBY-Chat en mode application :

```bash
docker compose up -d
```

---

### 7. ✅ Fichiers à ignorer (extrait de `.gitignore`)

```
# Fichiers sensibles
.env
__pycache__/
*.pyc

# OS
.DS_Store

# IDE
.idea/

# Export
# outputs/
site/

# Base chroma
src/vector_db/chromadb/

# Fichiers générés par ChromaDB
src/vector_db/chromadb/
*.bin
*.pickle
*.sqlite3
```

---

### 8. ✅ Nettoyage

Supprimer tous les containers, images, volumes (⚠️ avec précaution) :

```bash
docker system prune -a
```

---

## ✅ Résumé des commandes

| Objectif                          | Commande                                                                 |
|----------------------------------|--------------------------------------------------------------------------|
| Démarrer OBY-Chat (interface)    | `docker compose up -d`                                                  |
| Arrêter OBY-Chat                 | `docker compose down`                                                   |
| Lancer la documentation MkDocs   | `docker run -p 8080:8080 -e APP_MODE=doc oby-chat`                      |
| Accéder à OBY-Chat               | http://localhost:8050                                                   |
| Accéder à la documentation       | http://localhost:8080                                                   |


### 🆘 Support
- Pour tout problème de clé API, vérifier le fichier .env
- Pour le debug des logs : consulter la sortie du terminal (docker compose logs)
- En cas de besoin : reconstruire l’image docker compose build --no-cache

---

## ✅Test de OBY-IA en mode API
En plus du mode application web, OBY-IA peut être sollicité directement via une API REST.
Ce mode permet à l’agence d’intégrer ou de tester les fonctionnalités de l’agent conversationnel depuis n’importe quel outil compatible HTTP (Swagger UI, Postman, cURL…).
### 1. Lancement du mode API

Le mode API est activé automatiquement lorsque la variable d’environnement APP_MODE est positionnée sur api.
En exécution Docker, cela est géré par le script start.sh :
```
elif [ "$APP_MODE" = "api" ]; then
    echo "🌐 Lancement du service OBY-IA en mode API..."
    uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```
Le conteneur expose le port 8000, qui correspond à l’API FastAPI.

### 2. Accès à la documentation interactive
Une fois l’application démarrée en mode API, la documentation Swagger UI est accessible à l’adresse :
```
https://<nom-domaine-ou-ip>:8000/docs
```
Elle permet de :
Visualiser les endpoints disponibles.
Consulter le format attendu des requêtes et des réponses.
Tester les appels directement depuis le navigateur.

### 3. Endpoints principaux

| Endpoint              | Méthode | Description |
|-----------------------|:-------:|-------------|
| `/auth/login`         | `POST`  | Authentifie un utilisateur et retourne un `session_id`. |
| `/auth/logout`        | `POST`  | Ferme la session utilisateur. |
| `/chat/chat`          | `POST`  | Envoie un message à l’agent et reçoit la réponse. |
| `/chat/export`        | `POST`  | Exporte l’historique de la session au format Markdown. |
| `/status/indexing`    | `GET`   | Vérifie si l’indexation documentaire est prête. |
| `/patients`           | `GET`   | Liste les fichiers patients disponibles (POA). |
| `/patients/{file}`    | `GET`   | Retourne le contenu JSON d’un dossier patient. |
| `/patients`           | `POST`  | Crée un nouveau dossier patient. |
| `/patients/{file}`    | `PUT`   | Met à jour un dossier patient existant. |
| `/patients/{file}`    | `DELETE`| Supprime un dossier patient. |


### 4. Séquence type de test
   1. Authentification
   - Endpoint : /auth/login
   - Fournir user_id et password.
   - Récupérer le session_id de la réponse.
   2. Interaction avec l’agent
   - Endpoint : /chat/chat
   - Fournir un corps JSON :
   {
     "user_input": "Prépare le plan pour le patient Dupont",
     "session_data": {
       "user_id": "demo",
       "session_id": "<valeur_retournee_par_login>"
     }
   }

   3. Export de session (optionnel)
      - Endpoint : /chat/export
      - Fournir le même session_data pour obtenir le résumé de la session au format Markdown.
   4. Déconnexion
      - Endpoint : /auth/logout
      - Met fin à la session côté serveur.

## **Remarque importante**
- Les appels API sont stateless côté HTTP : c’est le session_id qui permet de retrouver le contexte.
- Un utilisateur doit obligatoirement s’authentifier avant tout échange avec /chat/chat.
- Le nom du patient doit être dans la requête utilisateur: Cela permet de détecter le changement de patient et d'enclencher la suppression de l'historique dans la fenêtre de chat.







