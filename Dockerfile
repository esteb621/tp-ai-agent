FROM python:3.12-slim

# Empêcher Python de créer des fichiers .pyc et forcer l'affichage direct des logs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Mettre à jour pip
RUN pip install --upgrade pip

# Copier les fichiers de configuration pour installer les dépendances (optimisation du cache Docker)
COPY pyproject.toml README.md ./

# Installer le projet et ses dépendances
RUN pip install .

# Copier le reste du code source
COPY . .

# Lancement de l'agent
CMD ["python", "main.py"]
