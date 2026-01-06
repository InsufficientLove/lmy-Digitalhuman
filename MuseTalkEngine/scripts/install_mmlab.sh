#!/bin/bash
# OpenMMLab依赖快速安装脚本
# 用于Docker容器内或本地环境

set -e  # 出错立即退出

echo "=========================================="
echo "安装OpenMMLab依赖"
echo "=========================================="

# 检查是否在中国（使用清华源）
if ping -c 1 pypi.tuna.tsinghua.edu.cn &> /dev/null; then
    echo "✅ 检测到国内网络，使用清华源"
    pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
else
    echo "✅ 使用默认PyPI源"
fi

# 安装openmim
echo ""
echo "步骤 1/5: 安装openmim"
pip install -U openmim

# 安装mmengine
echo ""
echo "步骤 2/5: 安装mmengine"
mim install mmengine

# 安装mmcv
echo ""
echo "步骤 3/5: 安装mmcv"
mim install "mmcv>=2.0.1"

# 安装mmdet
echo ""
echo "步骤 4/5: 安装mmdet"
mim install "mmdet>=3.1.0"

# 安装mmpose
echo ""
echo "步骤 5/5: 安装mmpose"
mim install "mmpose>=1.1.0"

# 验证安装
echo ""
echo "=========================================="
echo "验证安装"
echo "=========================================="

python3 -c "import mmengine; print('✅ mmengine:', mmengine.__version__)"
python3 -c "import mmcv; print('✅ mmcv:', mmcv.__version__)"
python3 -c "import mmdet; print('✅ mmdet:', mmdet.__version__)"
python3 -c "import mmpose; print('✅ mmpose:', mmpose.__version__)"

echo ""
echo "=========================================="
echo "✅ OpenMMLab依赖安装完成"
echo "=========================================="
