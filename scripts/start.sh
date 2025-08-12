#!/bin/bash

if [ "$APP_MODE" = "doc" ]; then
    echo "📚 Lancement de la documentation MkDocs..."
    mkdocs serve --dev-addr=0.0.0.0:8080

elif [ "$APP_MODE" = "api" ]; then
    echo "🌐 Lancement du service OBY-IA en mode API..."
    uvicorn src.api.main_api:app --host 0.0.0.0 --port 8000

else
    echo "🚀 Lancement de l'application OBY-Chat (mode Dash)..."
    python -m src.app
fi
