#!/usr/bin/env bash
set -euo pipefail

export PYTHONUNBUFFERED=1

MUSE_DIR=${MUSE_TALK_DIR:-/opt/musetalk/repo/MuseTalk}
ENGINE_DIR=/opt/musetalk/repo/MuseTalkEngine
STAMP_FILE=/opt/musetalk/.musetalk_reqs_installed

python3 -m pip install --upgrade pip >/dev/null 2>&1 || true

if [ -f "$MUSE_DIR/requirements.txt" ] && [ ! -f "$STAMP_FILE" ]; then
  echo "Detected MuseTalk requirements: $MUSE_DIR/requirements.txt"
  python3 -m pip install --no-cache-dir -r "$MUSE_DIR/requirements.txt"
  touch "$STAMP_FILE"
fi

# Ensure caches exist
mkdir -p /root/.cache/huggingface /root/.cache/torch

cd "$ENGINE_DIR"
exec python3 direct_launcher.py