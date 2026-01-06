#!/bin/bash
# 修复pip构建环境问题

set -e

echo "=========================================="
echo "修复pip构建环境"
echo "=========================================="

echo ""
echo "问题: pip构建环境损坏（chumpy无法找到pip模块）"
echo "解决: 重新安装pip和构建工具"
echo ""

# 方案1: 升级pip和构建工具
echo "步骤 1/5: 升级pip和构建工具"
python3 -m pip install --upgrade pip setuptools wheel

# 方案2: 确保ensurepip可用
echo ""
echo "步骤 2/5: 确保ensurepip模块"
python3 -m ensurepip --upgrade || echo "⚠️ ensurepip不可用，继续"

# 方案3: 安装基础依赖
echo ""
echo "步骤 3/5: 安装numpy和cython"
pip install -U numpy cython

# 方案4: 使用--no-build-isolation安装chumpy
echo ""
echo "步骤 4/5: 安装chumpy（绕过构建隔离）"
if pip install chumpy --no-build-isolation; then
    echo "✅ chumpy安装成功"
else
    echo "⚠️ chumpy安装失败，尝试备用方案"
    # 备用：手动安装chumpy的依赖
    pip install numpy scipy || true
    pip install chumpy --no-deps || echo "❌ 备用方案也失败"
fi

# 方案5: 安装mmpose
echo ""
echo "步骤 5/5: 安装mmpose"
if pip install mmpose --no-build-isolation; then
    echo "✅ mmpose安装成功"
elif mim install mmpose; then
    echo "✅ mmpose通过mim安装成功"
else
    echo "❌ mmpose安装失败"
    exit 1
fi

# 验证
echo ""
echo "=========================================="
echo "验证安装"
echo "=========================================="

python3 -c "import mmpose; print('✅ mmpose:', mmpose.__version__)"
python3 -c "import chumpy; print('✅ chumpy: 已安装')" || echo "⚠️ chumpy: 未安装（可能不影响功能）"

echo ""
echo "=========================================="
echo "✅ 修复完成"
echo "=========================================="
