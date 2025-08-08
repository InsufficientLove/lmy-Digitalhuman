#!/usr/bin/env bash
set -euo pipefail

sudo mkdir -p /opt/musetalk/{models,videos,temp}
sudo chown -R $USER:$USER /opt/musetalk

if [ ! -f .env ]; then
  cp -n .env.example .env || true
  echo "Created .env from .env.example. Please edit DOMAIN and ACME_EMAIL."
fi

echo "Setup done. Next steps:\n  1) Edit .env (DOMAIN / ACME_EMAIL)\n  2) Put models under /opt/musetalk/models\n  3) docker compose up -d --build\n  4) Visit https://\${DOMAIN}" 