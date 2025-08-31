#!/bin/bash

# """Script de démarrage OBY-IA.
#
# Résumé
#     Lance OBY-IA en trois modes exclusifs : "app" (Dash), "api" (Uvicorn) ou "doc" (MkDocs).
#     Le mode est piloté par l’argument positionnel ou, à défaut, par la variable d’environnement APP_MODE.
#     Le port est choisi selon le mode (8050/8000/8080) sauf si PORT est déjà défini.
#
# Comportement
#     - Détermine le mode : MODE = $1, sinon $APP_MODE, sinon "app".
#     - Fixe PORT par défaut selon le mode si non fourni.
#     - Exécute la commande correspondante via 'exec' pour propager correctement les signaux (PID 1).
#     - Pour le mode "app" (Dash), APP_DEBUG=1 active debug et reloader côté Python (géré dans app.py).
#
# Arguments
#     $1 (optionnel)
#         "app" | "api" | "doc"
#
# Variables d’environnement
#     APP_MODE (optionnel)
#         Même sémantique que l’argument. Ignoré si $1 est fourni.
#     PORT (optionnel)
#         Port d’écoute interne du conteneur. Si absent, valeurs par défaut :
#         app=8050, api=8000, doc=8080.
#     APP_DEBUG (optionnel, uniquement mode "app")
#         "1" pour activer le debug/reloader Dash (utile en local), sinon désactivé.
#
# Codes de sortie
#     Propage le code de retour de mkdocs/uvicorn/python (0 en cas de succès).
#
# Exemples
#     # Pilotage par argument :
#     ./start.sh app
#     ./start.sh api
#     ./start.sh doc
#
#     # Pilotage par variables (aucun argument) :
#     APP_MODE=api PORT=8000 ./start.sh
#
#     # Docker Compose (service "app" par défaut) :
#     docker compose up -d
#     # Profils :
#     docker compose --profile api up -d obyia-api
#     docker compose --profile doc up -d obyia-doc
#
# Notes
#     - En environnement orchestré (CI/PaaS), PORT peut être imposé : le script le respecte.
#     - Mapper un seul port par service côté hôte pour éviter les collisio

set -e

MODE="${1:-${APP_MODE:-app}}"

# Port par défaut selon le mode, sauf si $PORT est déjà défini
if [ -z "$PORT" ]; then
  case "$MODE" in
    doc) PORT=8080 ;;
    api) PORT=8000 ;;
    *)   PORT=8050 ;;  # app
  esac
fi
export PORT

echo "Mode: $MODE | Port: $PORT"

case "$MODE" in
  doc)
    echo "📚 Lancement doc..."
    exec mkdocs serve --dev-addr=0.0.0.0:$PORT
    ;;
  api)
    echo "🌐 Lancement API..."
    exec uvicorn src.api.main_api:app --host 0.0.0.0 --port $PORT
    ;;
  app|*)
    echo "🚀 Lancement app (Dash)..."
    exec python -m src.app
    ;;
esac


# Utilisation:
# App (Dash) : docker compose up -d → http://localhost:8050
# API : docker compose --profile api up -d obyia-api → http://localhost:8000
# Doc : docker compose --profile doc up -d obyia-doc → http://localhost:8080
