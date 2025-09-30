# Déploiement Docker – OBY-Chat

## Objectif de ce document
Ce guide explique comment démarrer OBY-Chat dans ses différents modes (application Dash, API, documentation) à l’aide de Docker.
Il présente des commandes claires et des exemples prêts à l’emploi, pour l’équipe de dev comme pour l’agence qui teste l’API.

## À propos d’OBY-Chat (rappel)
OBY-Chat est une application conversationnelle (Dash + IA) dédiée à l’accompagnement des personnes âgées :
• génération de PPA, • synthèses, • analyse de constantes, • documentation technique (MkDocs).

## 🟢 Modes de lancement (Option A)
But : choisir explicitement le mode au lancement, de façon simple et déterministe.
OBY-Chat se lance en trois modes exclusifs, via un argument passé à start.sh :

app — Application Dash (UI) — port par défaut 8050
api — Service API (Uvicorn) — port par défaut 8000
doc — Documentation MkDocs — port par défaut 8080

### Priorité et compatibilité (“legacy”)
Priorité à l’argument : ./start.sh app|api|doc
Si aucun argument n’est fourni, le script peut encore lire APP_MODE (compatibilité avec les anciens usages).
Si ni argument ni APP_MODE : défaut = app.
En code : MODE="${1:-${APP_MODE:-app}}"

### Ports (défaut ou personnalisés)
Si PORT n’est pas défini, le script prend : app=8050, api=8000, doc=8080.
Vous pouvez forcer un port ponctuellement :
PORT=18050 ./start.sh app

### Debug Dash en local (optionnel)
APP_DEBUG=1 active debug=True + use_reloader=True côté Dash (géré dans app.py).
Ne pas activer en environnement d’intégration.

---
### Version “agence BlueSoft” -> L'image est créée (build non nécessaire) dans fichier ".tar"
- 🟢 Lancer avec une image fournie (.tar)
- Pré-requis
  - Fichiers transmis : 
    - oby-ia_v2025.09.30.tar
    - oby-ia_v2025.09.30.tar.sha256
    - docker-compose.yml
    - deploiement.md
  - Docker / Docker Compose installés

#### Vérifier l’intégrité & charger l’image
```
shasum -a 256 -c oby-ia_v2025.09.30.tar.sha256
docker load -i oby-ia_v2025.09.30.tar
```
```
docker images | grep oby-ia
```
doit afficher v2025.09.30

#### Préparer l’environnement
**1. Remplacer les clés OPENAI_API_KEY, MISTRAL_API_KEY et autres clés par celles de BVIDF (ou BlueSoft) dans .env**
**2. ```mkdir -p outputs assets```**

#### Démarrer (mode APP par défaut)
- **dans un terminal :**
  - si app
  - si API
  - si docs
```
docker compose up -d                  
docker compose --profile api up -d    
docker compose --profile doc up -d

docker compose logs --tail 200
```
- **docker-compose.yml (runtime, sans build)**
```
  services:
  # === Application Dash (UI) ===
  obyia-app:
    image: oby-ia:v2025.09.30
    container_name: obyia-app
    command: ["./start.sh", "app"]
    ports:
      - "8050:8050"
    volumes:
      - ./outputs:/app/outputs
      - ./assets:/app/assets
    env_file:
      - .env

  # === API (Uvicorn) — lancer avec: docker compose --profile api up -d obyia-api
  obyia-api:
    image: oby-ia:v2025.09.30
    container_name: obyia-api
    command: ["./start.sh", "api"]
    ports:
      - "8000:8000"
    profiles: ["api"]
    env_file:
      - .env

  # === DOC (MkDocs) — lancer avec: docker compose --profile doc up -d obyia-doc
  obyia-doc:
    image: oby-ia:v2025.09.30
    container_name: obyia-doc
    command: ["./start.sh", "doc"]
    ports:
      - "8080:8080"
    profiles: ["doc"]
    env_file:
      - .env
  
```

- **Arrêt / redémarrage**
```
docker compose down            # (garde les volumes/données)
docker compose up -d --force-recreate
```

## (Annexe dev) Rebuild local si modification du code
- **Cette partie ne concerne que les équipes qui reconstruisent l’image.**
```
docker compose build --no-cache
docker compose up -d
```

### 🟢 Lancement avec Docker Compose
But : démarrer rapidement le service voulu, sans ambigüité, avec un seul port exposé.
Par défaut, seul le service app (Dash) démarre. Les services api et doc sont disponibles via des profiles.

```
version: "3.9"

services:
  # === Application Dash — démarre par défaut ===
  obyia-app:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: obyia-app
    command: ["./start.sh", "app"]   # <-- argument à start.sh
    ports:
      - "8050:8050"
    volumes:
      - ./outputs:/app/outputs
      - ./assets:/app/assets
    # optionnel pour debug local :
    # environment:
    #   - APP_DEBUG=1

  # === API (Uvicorn) — démarrage à la demande ===
  obyia-api:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: obyia-api
    command: ["./start.sh", "api"]   # <-- argument à start.sh
    ports:
      - "8000:8000"
    profiles: ["api"]

  # === Documentation (MkDocs) — démarrage à la demande ===
  obyia-doc:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: obyia-doc
    command: ["./start.sh", "doc"]   # <-- argument à start.sh
    ports:
      - "8080:8080"
    profiles: ["doc"]
```

## 🟢 Commandes utiles
App (Dash) : → http://localhost:8050
```
docker compose up -d 
```

API : → http://localhost:8000
```
docker compose --profile api up -d obyia-api
```

Doc : → http://localhost:8080
```
docker compose --profile doc up -d obyia-doc
```

Arrêter :
docker compose down (ou cibler un service)
✔️ Bonne pratique : n’exposez qu’un seul port par service (8050 ou 8000 ou 8080).
❌ Évitez de mapper 8050/8000/8080 simultanément sur le même service : collisions assurées.


## 🟢 Lancement direct (sans Compose)
But : lancer un mode ponctuellement avec une commande unique.
```
# Application (Dash)
docker run -p 8050:8050 oby-chat ./start.sh app
# → http://localhost:8050

# API (pour l’agence)
docker run -p 8000:8000 oby-chat ./start.sh api
# → http://localhost:8000

# Documentation (MkDocs)
docker run -p 8080:8080 oby-chat ./start.sh doc
# → http://localhost:8080

```

## 🟢 Compat legacy (encore possible si pas d’utilisation d’argument)
```
docker run -p 8000:8000 -e APP_MODE=api oby-chat ./start.sh
# Ici, pas d’argument ⇒ start.sh lira APP_MODE=api

```

## 🟢 Rebuild après modifications (développeurs)
But : reconstruire l’image et relancer uniquement le service utile.

```
docker compose down
docker compose build
docker compose up -d obyia-app     # ou: obyia-api | obyia-doc

```

## 🟢 Accès aux URLs (important)
But : éviter les confusions entre adresse de bind et URL cliente.
Ouvrez http://localhost:8050 (ou http://127.0.0.1:8050) pour l’app.
N’utilisez pas http://0.0.0.0:8050 dans le navigateur : 0.0.0.0 est une adresse de bind (serveur), pas une URL cliente.



## 🟢 Endpoints principaux

| Endpoint                 |  Méthode | Description                                                                                                    |
| ------------------------ | :------: | -------------------------------------------------------------------------------------------------------------- |
| `/auth/login`            |  `POST`  | Authentifie un utilisateur et retourne un `session_id`.                                                        |
| `/auth/logout`           |  `POST`  | Ferme la session utilisateur.                                                                                  |
| `/chat`                  |  `POST`  | Envoie un message à l’agent et reçoit la réponse (renvoie un **delta** dans `partial_chat_from_user_request`). |
| `/chat/export`           |  `POST`  | Exporte la session courante (ex. PDF/Markdown), selon l’implémentation.                                        |
| `/status/indexing`       |   `GET`  | Vérifie si l’indexation documentaire est prête.                                                                |
| `/admin/patients`        |   `GET`  | Liste les fichiers patients disponibles (POA).                                                                 |
| `/admin/patients/{file}` |   `GET`  | Retourne le contenu JSON d’un dossier patient.                                                                 |
| `/admin/patients`        |  `POST`  | Crée un nouveau dossier patient.                                                                               |
| `/admin/patients/{file}` |   `PUT`  | Met à jour un dossier patient existant.                                                                        |
| `/admin/patients/{file}` | `DELETE` | Supprime un dossier patient.                                                                                   |


### 🟢 Séquence type de test
1. Authentification
   - Endpoint : POST /auth/login
   - Fournir user_id et password.
   - Récupérer le session_id de la réponse.
   
2. Interaction avec l’agent (Tour 1)
   - Endpoint : POST /chat
   - Fournir un corps JSON :
   
```
{
  "send_clicks": 1,
  "user_input": "Prépare le plan pour le patient Dupont",
  "chat_history": [],
  "session_data": {
    "user_id": "demo",
    "session_id": "<valeur_retournee_par_login>"
  },
  "current_patient": null
}

```

    Réponse attendue :
    - status: "awaiting_confirmation"
    - partial_chat_from_user_request: tableau de 2 items (le message utilisateur + la demande de confirmation du bot).
    - Côté client, vous devez ajouter ces 2 items à votre chat_history local.

3. Confirmation (tour 2)
    - Endpoint : POST /chat
    - Corps JSON (avec l’historique cumulé du tour 1) :

```
{
  "send_clicks": 1,
  "user_input": "oui",
  "chat_history": [
    { "role": "user", "format": "markdown", "content": "Prépare le plan pour le patient Dupont" },
    { "role": "assistant", "format": "markdown", "content": "Je comprends que vous souhaitez une demande de recommandations... confirmez oui/non ?" }
  ],
  "session_data": {
    "user_id": "demo",
    "session_id": "<valeur_retournee_par_login>"
  },
  "current_patient": "Dupont"
}

```

    Réponse attendue :
    - status: "response_processed"
    - partial_chat_from_user_request: 2 items (la confirmation "oui" + la réponse finale).
    - Côté client, ajoutez ces 2 nouveaux items à votre chat_history local.





   3. Export de session (optionnel)
      - Endpoint : POST /chat/export
      - Fournir le même session_data pour obtenir le résumé de la session au format Markdown.

```
{
  "session_data": {
    "user_id": "demo",
    "session_id": "<valeur_retournee_par_login>"
  },
  "current_patient": "Dupont"
}

```
    Réponse : selon implémentation (ex. file_url pour télécharger l’export, ou FileResponse directement).

   4. Déconnexion
      - Endpoint : POST /auth/logout
      - Met fin à la session côté serveur.

## **Remarque importante**
- Les appels API sont stateless côté HTTP : c’est le session_id qui permet de retrouver le contexte côté serveur.
- Un utilisateur doit obligatoirement s’authentifier avant tout échange avec /chat.
- L’API renvoie un delta de conversation dans partial_chat_from_user_request. C’est au client d’additionner ce delta à son chat_history local et de le réenvoyer à chaque requête.
- Le nom du patient doit idéalement apparaître dans la requête utilisateur (et/ou être fourni dans current_patient) : cela facilite la détection du patient actif et évite les incohérences d’historique.





