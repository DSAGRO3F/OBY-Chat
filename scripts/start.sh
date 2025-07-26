#!/bin/bash

if [ "$APP_MODE" = "doc" ]; then
    echo "📚 Lancement de la documentation MkDocs..."
    mkdocs serve --dev-addr=0.0.0.0:8080
else
    echo "🚀 Lancement de l'application OBY-Chat..."
    python -m src.app
fi
