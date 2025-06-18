#!/usr/bin/env bash
set -euo pipefail

# --- ENV VAR DEFAULTS (IMPORTANT: Assurez-vous que ces valeurs correspondent à votre configuration PostgreSQL) ---
# DB_HOST: Utilise 127.0.0.1 pour forcer la connexion TCP/IP et éviter les problèmes de socket UNIX.
: "${DB_HOST:=127.0.0.1}"
: "${DB_PORT:=5432}"
# DB_USER: Basé sur votre capture d'écran ServerPro, l'utilisateur par défaut pour komkom_db est 'pro'.
: "${DB_USER:=postgres}"
# DB_PASSWORD: Basé sur votre contexte précédent.
: "${DB_PASSWORD:=Fallou96}"
: "${DB_NAME:=komkom_news_db}"
# LOCAL_STATIC_DIR: Dossier pour les fichiers générés localement (peut être ajusté plus tard pour les MP3, etc.)
: "${LOCAL_STATIC_DIR:=./local_static}"


echo "Creating tables..."
# Ensure DB schema is up to date
make migrate
echo "Tables created."

echo "Building Scrapy Docker image..."
# Build docker image from deep_research/komkom_scraper directory.
# This ensures the build context is correct for COPY commands inside the Dockerfile.
(cd deep_research/komkom_scraper && docker build -t komkom_scraper_image .)

echo "Running scrapy spider (wekomkom) via Docker..."
# Run spider with same network & env so it can hit Postgres on host.
# --rm: Supprime le conteneur après l'exécution.
# --network host: Permet au conteneur de se connecter à localhost (votre machine hôte) sur le port 5432.
# -e DB_*: Passe les variables d'environnement de la DB au conteneur.
# komkom_scraper_image: Le nom de l'image Docker à exécuter.
# scrapy crawl wekomkom: La commande spécifique à exécuter à l'intérieur du conteneur.
docker run --rm --network host \
  -e DB_HOST="${DB_HOST}" \
  -e DB_PORT="${DB_PORT}" \
  -e DB_USER="${DB_USER}" \
  -e DB_PASSWORD="${DB_PASSWORD}" \
  -e DB_NAME="${DB_NAME}" \
  komkom_scraper_image \
  scrapy crawl wekomkom

echo "Scrapy spider run completed."

# --- PROCHAINES ÉTAPES (à ajouter lorsque les modules Episode Builder, API, Frontend seront implémentés) ---
# echo "Building episode..."
# # Logic for Episode Builder goes here
# echo "Episode built."

# echo "Starting API Backend..."
# # Logic for FastAPI Backend goes here
# echo "API Backend started."

# echo "Starting Frontend Application..."
# # Logic for React Frontend goes here
# echo "Frontend Application started. Open your browser at http://localhost:3000"

echo "End-to-end script finished."
