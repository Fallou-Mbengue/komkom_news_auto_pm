#!/usr/bin/env bash
set -euo pipefail

# Ensure DB schema is up to date
make migrate

# Build docker image
docker build -t komkom_scraper \
  -f deep_research/komkom_scraper/Dockerfile .

# Run spider with same network & env so it can hit Postgres on host
docker run --rm --network host \
  -e DB_HOST -e DB_PORT -e DB_USER -e DB_PASSWORD -e DB_NAME \
  komkom_scraper