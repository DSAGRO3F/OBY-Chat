# Étape 1 : Image de base
FROM python:3.12-slim

# Étape 2 : Créer le dossier de travail
WORKDIR /app

# Étape 3 : Rendre src/ importable en tant que module
ENV PYTHONPATH=/app

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

# Étape 7 : Copier les données si nécessaire (optionnel, utile en prod)
# COPY data/input/ ./data/input/

# Étape 8 : Définir le point d’entrée (à ajuster selon besoin)
CMD ["python", "-m", "src.app"]
