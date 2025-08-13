#!/usr/bin/env bash
set -euo pipefail

export PYTHONUNBUFFERED=1

MUSE_DIR=${MUSE_TALK_DIR:-/opt/musetalk/repo/MuseTalk}
ENGINE_DIR=/opt/musetalk/repo/MuseTalkEngine

# Skip re-installing upstream requirements if present
mkdir -p /root/.cache/huggingface /root/.cache/torch
[ -f "$MUSE_DIR/.musetalk_reqs_installed" ] || true

# 1) Pin core stack to avoid ABI conflicts
python3 -m pip install --no-cache-dir --upgrade --force-reinstall \
  numpy==1.26.4 scipy==1.11.4 pillow==10.0.1 opencv-python==4.9.0.80 matplotlib==3.8.2

# 2) Install mmengine and precompiled mmcv wheels (GPU cu121/torch2.3.1, fallback CPU)
python3 -m pip install --no-cache-dir -U mmengine==0.10.4
python3 - <<'PY'
import subprocess, sys
cmds = [
  [sys.executable,'-m','pip','install','--no-cache-dir','--only-binary=:all:',
   '-f','https://download.openmmlab.com/mmcv/dist/cu121/torch2.3.1/index.html','mmcv==2.0.1'],
  [sys.executable,'-m','pip','install','--no-cache-dir','--only-binary=:all:',
   '-f','https://download.openmmlab.com/mmcv/dist/cpu/torch2.3.1/index.html','mmcv==2.0.1'],
]
for c in cmds:
  try:
    subprocess.check_call(c)
    break
  except subprocess.CalledProcessError:
    continue
else:
  sys.exit(1)
PY

# 3) xtcocotools without deps to avoid numpy being upgraded
python3 -m pip install --no-cache-dir --no-deps -U xtcocotools==1.14.3

# 4) mmpose/mmdet and small runtime deps
python3 -m pip install --no-cache-dir -U mmpose==1.3.2 mmdet==3.3.0 \
  json-tricks==3.17.3 munkres==1.1.4 chumpy==0.70 pycocotools==2.0.7 shapely==2.0.6

# 5) Ensure diffusers stack (MuseTalk VAE)
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
        'safetensors':'safetensors==0.6.2',
    }
    args = [pins[n] for n in missing]
    subprocess.check_call([sys.executable,'-m','pip','install','--no-cache-dir',*args])
PY

cd "$ENGINE_DIR"
exec python3 direct_launcher.py