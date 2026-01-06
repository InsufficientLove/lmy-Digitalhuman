#!/bin/bash
# 修复mmpose安装（绕过chumpy问题）

set -e

echo "=========================================="
echo "修复mmpose安装问题"
echo "=========================================="

echo ""
echo "问题: chumpy构建失败（pip模块找不到）"
echo "解决: 使用--no-build-isolation绕过构建隔离"
echo ""

# 先确保numpy和cython已安装
echo "步骤 1/4: 确保基础依赖"
pip install -U numpy cython

# 尝试安装chumpy（使用--no-build-isolation）
echo ""
echo "步骤 2/4: 安装chumpy（无构建隔离）"
pip install chumpy --no-build-isolation || echo "⚠️ chumpy安装失败，继续尝试mmpose"

# 如果chumpy失败，尝试直接从源码安装
if ! python3 -c "import chumpy" 2>/dev/null; then
    echo ""
    echo "步骤 2.1/4: 尝试从GitHub安装chumpy"
    pip install git+https://github.com/mattloper/chumpy.git --no-build-isolation || echo "⚠️ GitHub安装也失败"
fi

# 尝试安装mmpose（即使chumpy失败也尝试）
echo ""
echo "步骤 3/4: 安装mmpose"
# 使用pip直接安装（避免mim的额外检查）
pip install mmpose --no-build-isolation || pip install mmpose || echo "❌ mmpose安装失败"

# 验证
echo ""
echo "步骤 4/4: 验证安装"
echo "=========================================="
echo "验证结果"
echo "=========================================="

if python3 -c "import mmpose" 2>/dev/null; then
    python3 -c "import mmpose; print('✅ mmpose:', mmpose.__version__)"
    echo ""
    echo "=========================================="
    echo "✅ mmpose安装成功"
    echo "=========================================="
    exit 0
else
    echo "❌ mmpose: 未安装"
    echo ""
    echo "⚠️ 注意："
    echo "mmpose安装失败可能不影响基础功能"
    echo "如果只使用人脸推理，可以暂时跳过"
    echo ""
    echo "手动修复建议："
    echo "1. 检查Python环境是否完整"
    echo "2. 尝试使用虚拟环境"
    echo "3. 考虑重新构建Docker镜像"
    exit 1
fi
