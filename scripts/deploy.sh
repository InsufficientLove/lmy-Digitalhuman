#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

git fetch origin main
git reset --hard origin/main

docker compose up -d --build

echo "Deployed. If certificates are new, wait up to 1-2 minutes for Traefik to obtain TLS certs."