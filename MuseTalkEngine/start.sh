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

# 1) Pin core numeric/IO stack to avoid ABI conflicts
python3 - <<'PY'
import subprocess, sys
pins = [
    'numpy==1.26.4',
    'scipy==1.11.4',
    'pillow==10.0.1',
    'opencv-python==4.9.0.80',
    'matplotlib==3.8.2'
]
subprocess.check_call([sys.executable,'-m','pip','install','--no-cache-dir','--upgrade','--force-reinstall',*pins])
PY

# 2) Install xtcocotools without deps so it does not force numpy upgrade
python3 -m pip install --no-cache-dir --no-deps --upgrade --force-reinstall xtcocotools==1.14.3

# 3) Install mmpose/mmdet stack (avoid deps to prevent opencv/numpy changes)
python3 -m pip install --no-cache-dir --upgrade mmengine==0.10.4 mmcv-lite==2.0.1
python3 -m pip install --no-cache-dir --no-deps --upgrade mmpose==1.3.2
python3 -m pip install --no-cache-dir --no-deps --upgrade mmdet==3.3.0
# minimal runtime helpers for mmdet
python3 -m pip install --no-cache-dir --upgrade pycocotools==2.0.7 shapely==2.0.6

# 4) Ensure diffusers stack present (needed by musetalk.models.vae)
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