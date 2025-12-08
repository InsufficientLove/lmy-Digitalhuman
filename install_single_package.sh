#!/bin/bash
# 单独安装某个包的脚本

if [ -z "$1" ]; then
    echo "用法: bash install_single_package.sh <package_name>"
    echo ""
    echo "示例:"
    echo "  bash install_single_package.sh opencv-python==4.8.1.78"
    echo "  bash install_single_package.sh fastapi"
    exit 1
fi

PACKAGE="$1"

echo "=========================================="
echo "安装单个包: $PACKAGE"
echo "=========================================="

python3 -m pip install "$PACKAGE" --no-cache-dir

echo ""
echo "=========================================="
echo "✅ 安装完成！"
echo "=========================================="
