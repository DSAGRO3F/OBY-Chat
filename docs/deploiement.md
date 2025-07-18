# 📦 Déploiement Docker

## Projet : OBY-IA – Agent conversationnel médical pour l'accompagnement des personnes âgées
### Objectif du déploiement
- Ce module décrit la procédure complète pour déployer localement l'application OBY-IA à l’aide de Docker.
- L’objectif est de fournir un environnement reproductible pour lancer l'interface Dash, interagir avec le chatbot, visualiser les constantes de santé, générer des plans d'accompagnement personnalisés, et exporter les échanges.

### 📁 Arborescence essentielle
``` 
.
├── Dockerfile
├── docker-compose.yml
├── docker-compose.override.yml
├── .env
├── .gitignore
├── requirements.txt
├── pyproject.toml
├── src/
├── config/
├── outputs/
│   └── chat_exports/
├── docs/
├── scripts/

```

### Fonctionnement général
#### L'application OBY-IA repose sur :

- Un agent conversationnel basé sur des LLMs (Mistral, OpenAI)
- Une interface web construite avec Dash
- Une gestion de sessions utilisateurs avec historique
- Des exports en Markdown des réponses générées
- Une Dockerisation complète (image légère, config reproductible)

### Configuration : variables d’environnement
#### 🟢 Le fichier .env contient les clés nécessaires à l’accès aux APIs :

- OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
- MISTRAL_API_KEY=hf_xxxxxxxxxxxxxxxxxxxxxxx
- Ce fichier ne doit pas être versionné dans Git : il est protégé par .gitignore.

### Déploiement avec Docker

#### 1. 🏗️ Construction de l’image
docker compose build

#### 2. ✅ Lancement de l’application
docker compose up
L'application sera disponible à l'adresse :
http://localhost:8050

#### 3. ✅ Rebuild après modifications
Si vous changez des fichiers sources (src/, config/, etc.) :
docker compose down
docker compose up --build

#### 4. ✅ Volumes montés (override)
- Le fichier docker-compose.override.yml permet de monter les volumes pour un environnement de développement :

- volumes:
  - ./src:/app/src
  - ./config:/app/config
  - ./scripts:/app/scripts
  - ./docs:/app/docs
  - ./src/data:/app/src/data
  - ./outputs:/app/outputs

- Ces volumes garantissent la persistance des données locales (exports, fichiers patients, graphiques...).

#### 5. ✅ Gestion des sessions
- Chaque utilisateur dispose d’un user_id et session_id spécifiques
- Les échanges avec le LLM sont enregistrés dans la mémoire de session
- Les réponses peuvent être exportées en Markdown dans outputs/chat_exports/<nom_patient>/

#### 6. ✅ Vérification post-déploiement
- Après le lancement :
- Accédez à l’interface sur localhost:8050
- Authentifiez-vous avec un user_id et mot de passe
- Demandez un plan (PPA) ou des recommandations.
  - "Prépare un Plan Personnalisé d'Accompagnement du patient Deloin"
  - "Monsieur Deloin vient de faire une chute, donne moi la conduite à tenir"
- Testez l’export Markdown via le bouton dédié
- Vérifiez l’arborescence : outputs/chat_exports/<patient>/<date>/export_chat_<patient>.md

#### 7. ✅ Fichiers à ignorer (extrait de .gitignore)
- ▶︎ Fichiers sensibles
- .env
- ▶︎ OS
- .DS_Store

#### 8. ✅ Nettoyage
Pour tout réinitialiser :
docker compose down -v --remove-orphans

#### 🆘 Support
- Pour tout problème de clé API, vérifier le fichier .env
- Pour le debug des logs : consulter la sortie du terminal (docker compose logs)
- En cas de besoin : reconstruire l’image docker compose build --no-cache
