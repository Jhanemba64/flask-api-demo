# Image Python légère
FROM python:3.13-slim

# Bonnes pratiques d'environnement
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=5000

WORKDIR /app

# Installer les dépendances d'abord (optimise le cache de couches Docker),
# puis retirer pip, inutile à l'exécution et source de vulnérabilités
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && pip uninstall -y pip

# Copier le code de l'API
COPY app/ ./app/

# Exposer le port de l'application
EXPOSE 5000

# Exécuter en utilisateur non-root
RUN useradd --create-home --uid 1000 appuser
USER 1000

# Démarrer l'application Flask via gunicorn.
# Bind sur $PORT (injecté par Render) avec repli sur 5000.
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT:-5000} --workers 2 --access-logfile - app.main:app"]
