#!/usr/bin/env bash
set -euo pipefail

TARGET=/opt/musetalk/models
mkdir -p "$TARGET"

# 推荐：从旧服务器直接拷贝整个 models 目录到 $TARGET
#   scp -r user@old-server:/path/to/models/* $TARGET/
# 或者使用图形工具（WinSCP/FTP）拷贝

# 若需要在线下载（示例占位，按你的实际模型来源补充）：
# mkdir -p "$TARGET/dwpose"
# wget -O "$TARGET/dwpose/dw-ll_ucoco_384.pth" "<YOUR_LINK>"
# mkdir -p "$TARGET/musetalkV15"
# wget -O "$TARGET/musetalkV15/unet.pth" "<YOUR_LINK>"

# 验证
find "$TARGET" -maxdepth 2 -type f | sed 's/^/MODEL: /'

echo "Models prepared under: $TARGET"