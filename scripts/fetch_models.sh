#!/usr/bin/env bash
set -euo pipefail

# 自动创建模型目录（容器内路径，已挂载到宿主机）
BASE_DIR="/opt/musetalk/repo/MuseTalk/models"
mkdir -p "$BASE_DIR"/{musetalk,musetalkV15,sd-vae,whisper,dwpose,syncnet,face-parse-bisent}
mkdir -p /root/.cache/torch/hub/checkpoints

# 下载函数：依次尝试多个镜像源
_download_with_mirrors() {
	local out="$1"; shift
	for url in "$@"; do
		echo "==> Trying: $url"
		if curl -fL --retry 10 --retry-delay 2 -C - -o "$out" "$url"; then
			return 0
		fi
	done
	return 1
}

# 仅下载 FaceParsing 权重（默认）
fetch_face_parsing() {
	local out="$BASE_DIR/face-parse-bisent/79999_iter.pth"
	if [ -s "$out" ]; then
		echo "[OK] face-parsing weight already exists: $out"
		return 0
	fi
	echo "[INFO] downloading face-parsing weight to $out"
	_download_with_mirrors "$out" \
		https://ghproxy.com/https://raw.githubusercontent.com/zllrunning/face-parsing.PyTorch/master/res/cp/79999_iter.pth \
		https://mirror.ghproxy.com/https://raw.githubusercontent.com/zllrunning/face-parsing.PyTorch/master/res/cp/79999_iter.pth \
		https://kgithub.com/zllrunning/face-parsing.PyTorch/raw/master/res/cp/79999_iter.pth \
		https://raw.githubusercontent.com/zllrunning/face-parsing.PyTorch/master/res/cp/79999_iter.pth \
		|| {
			echo "[ERROR] failed to fetch face-parsing weight from mirrors" >&2
			return 1
		}
	echo "[OK] face-parsing weight downloaded: $(ls -lh "$out")"
}

# 可选：下载人脸检测/关键点缓存（避免运行期再下载）
fetch_face_detection_cache() {
	local s3fd="/root/.cache/torch/hub/checkpoints/s3fd-619a316812.pth"
	if [ ! -s "$s3fd" ]; then
		echo "[INFO] downloading S3FD to $s3fd"
		_download_with_mirrors "$s3fd" \
			https://www.adrianbulat.com/downloads/python-fan/s3fd-619a316812.pth \
			https://ghproxy.com/https://raw.githubusercontent.com/1adrianb/face-alignment/master/requirements/s3fd-619a316812.pth \
			|| true
	fi
	local fan4="/root/.cache/torch/hub/checkpoints/2DFAN4-11f355bf06.pth"
	if [ ! -s "$fan4" ]; then
		echo "[INFO] downloading 2DFAN4 to $fan4"
		_download_with_mirrors "$fan4" \
			https://www.adrianbulat.com/downloads/python-fan/2DFAN4-11f355bf06.pth \
			https://ghproxy.com/https://raw.githubusercontent.com/1adrianb/face-alignment/master/requirements/2DFAN4-11f355bf06.pth \
			|| true
	fi
	echo "[OK] face detection cache prepared"
}

usage() {
	echo "Usage: $0 [face|face+cache|all]"
	echo "  face        : only download face-parsing weight (default)"
	echo "  face+cache  : face-parsing + S3FD/2DFAN4 cache"
	echo "  all         : same as face+cache (reserved for future extension)"
}

MODE="${1:-face}"
case "$MODE" in
	face)
		fetch_face_parsing
		;;
	face+cache|all)
		fetch_face_parsing
		fetch_face_detection_cache
		;;
	*)
		usage; exit 1;;
 esac

echo "[DONE] fetch_models ($MODE) finished"