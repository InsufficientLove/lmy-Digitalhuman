#!/usr/bin/env bash
set -euo pipefail

export PYTHONUNBUFFERED=1

MUSE_DIR=${MUSE_TALK_DIR:-/opt/musetalk/repo/MuseTalk}
ENGINE_DIR=/opt/musetalk/repo/MuseTalkEngine
# Old (non-persistent) stamp for backward compatibility
STAMP_OLD=/opt/musetalk/.musetalk_reqs_installed
# New persistent stamp inside bind-mounted MuseTalk directory
STAMP_NEW="$MUSE_DIR/.musetalk_reqs_installed"

python3 -m pip install --upgrade pip >/dev/null 2>&1 || true

if [ -f "$MUSE_DIR/requirements.txt" ] && [ ! -f "$STAMP_OLD" ] && [ ! -f "$STAMP_NEW" ]; then
  echo "Detected MuseTalk requirements: $MUSE_DIR/requirements.txt"
  python3 -m pip install --no-cache-dir -r "$MUSE_DIR/requirements.txt"
  # Write both stamps to cover old/new logic
  mkdir -p "$(dirname "$STAMP_OLD")" || true
  touch "$STAMP_OLD" || true
  touch "$STAMP_NEW" || true
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

# Ensure diffusers stack present (needed by musetalk.models.vae)
python3 - <<'PY'
missing = []
for name in ['diffusers','accelerate','huggingface_hub','tokenizers','safetensors']:
    try:
        __import__(name)
    except Exception:
        missing.append(name)
if missing:
    import subprocess, sys
    pins = {
        'diffusers':'diffusers==0.30.2',
        'accelerate':'accelerate==0.28.0',
        'huggingface_hub':'huggingface_hub==0.30.2',
        'tokenizers':'tokenizers==0.15.2',
        'safetensors':'safetensors==0.6.2'
    }
    args = [pins[n] for n in missing]
    subprocess.check_call([sys.executable,'-m','pip','install','--no-cache-dir',*args])
PY

cd "$ENGINE_DIR"
exec python3 direct_launcher.py