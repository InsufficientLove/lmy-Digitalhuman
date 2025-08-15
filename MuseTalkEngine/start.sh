#!/usr/bin/env bash
set -euo pipefail

export PYTHONUNBUFFERED=1

MUSE_DIR=${MUSE_TALK_DIR:-/opt/musetalk/repo/MuseTalk}
ENGINE_DIR=/opt/musetalk/repo/MuseTalkEngine

# 自动选择最空闲 GPU（当未显式指定或设为 auto 时）
if [ -z "${CUDA_VISIBLE_DEVICES:-}" ] || [ "${CUDA_VISIBLE_DEVICES}" = "auto" ]; then
	GPU_ID=""
	# 优先使用 GPUtil
	GPU_ID=$(python3 - <<'PY'
try:
	import os
	import GPUtil
	gpus = GPUtil.getGPUs()
	if gpus:
		best = sorted(gpus, key=lambda g: (g.memoryUtil, g.load))[0]
		print(best.id)
	else:
		print("")
except Exception:
	print("")
PY
)
	if [ -z "$GPU_ID" ]; then
		# 回退使用 nvidia-smi 查询空闲显存最多的 GPU
		if command -v nvidia-smi >/dev/null 2>&1; then
			GPU_ID=$(nvidia-smi --query-gpu=index,memory.free --format=csv,noheader | sort -t, -k2 -nr | head -n1 | cut -d, -f1 | tr -d ' ' || echo "")
		fi
	fi
	if [ -n "$GPU_ID" ]; then
		export CUDA_VISIBLE_DEVICES="$GPU_ID"
		echo "[AutoGPU] Selected GPU: $GPU_ID (export CUDA_VISIBLE_DEVICES=$GPU_ID)"
	else
		echo "[AutoGPU] No GPU auto-selected (leaving CUDA_VISIBLE_DEVICES unchanged)"
	fi
fi

# 保证缓存与模型目录存在；若未挂载 ./models 但存在 /models，则建立符号链接
mkdir -p /root/.cache/huggingface /root/.cache/torch "$MUSE_DIR"
if [ -d "/models" ] && [ ! -e "$MUSE_DIR/models" ]; then
	echo "[Models] Linking $MUSE_DIR/models -> /models"
	ln -s /models "$MUSE_DIR/models"
fi

cd "$ENGINE_DIR"
exec python3 direct_launcher.py