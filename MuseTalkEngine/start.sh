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

# Ensure mmpose stack present (use mmcv-lite to avoid CUDA builds)
python3 - <<'PY'
try:
    import mmpose  # type: ignore
except Exception:
    import subprocess, sys
    pkgs = [
        'mmengine==0.10.4',
        'mmcv-lite==2.0.1',
        'mmpose==1.3.2'
    ]
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--no-cache-dir', *pkgs])
PY

cd "$ENGINE_DIR"
exec python3 direct_launcher.py