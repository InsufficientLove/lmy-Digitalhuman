#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if [ ! -f .env ]; then
  echo "Missing .env. Please copy .env.example to .env and edit variables."
  exit 1
fi

docker compose -f docker-compose.prod.yml pull
COMPOSE_DOCKER_CLI_BUILD=0 docker compose -f docker-compose.prod.yml up -d

echo "Deployed production stack. Visit https://${DOMAIN} after certificates are issued."