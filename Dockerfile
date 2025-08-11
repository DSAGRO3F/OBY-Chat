# Étape 1 : Image de base
FROM python:3.12-slim

# Étape 2 : Créer le dossier de travail
WORKDIR /app

# Étape 3 : Rendre src/ importable en tant que module
ENV PYTHONPATH=/app

# Étape 3 bis : variable d'environnement fichier plantuml.jar
ENV PLANTUML_JAR_PATH=/usr/local/bin/plantuml.jar

# Étape 4 : Copier les fichiers de dépendances
COPY pyproject.toml requirements.txt ./

# Étape 5 : Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Étape 6 : Copier les dossiers sources
COPY src/ ./src/
COPY config/ ./config/
COPY docs/ ./docs/
COPY scripts/ ./scripts/
COPY outputs/ ./outputs/
COPY assets/ ./assets/

# Étape 7: Installer Java (nécessaire pour PlantUML)
RUN apt-get update && apt-get install -y default-jre curl && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Étape 8: Télécharger plantuml.jar (dans /usr/local/bin/plantuml.jar)
RUN curl -o /usr/local/bin/plantuml.jar https://github.com/plantuml/plantuml/releases/latest/download/plantuml.jar

# Étape 9 : Copier la config de MkDocs
COPY mkdocs.yml ./mkdocs.yml


# Étape 10: 8050 pour Dash (mose app), 8080 pour MkDocs (mode doc), 8000 mode API
EXPOSE 8050
EXPOSE 8080
EXPOSE 8000

# Étape 11 : Copier les données si nécessaire (optionnel, utile en prod)
# COPY data/input/ ./data/input/

# Étape 12 Script de démarrage
COPY scripts/start.sh ./start.sh
RUN chmod +x ./start.sh

# Étape 13 : Définir le point d’entrée (à ajuster selon besoin)
# CMD ["python", "-m", "src.app"] plus utilisé, géré par start.sh
CMD ["./start.sh"]