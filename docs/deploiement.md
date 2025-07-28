
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

