#!/bin/bash
# 修复mmcv版本兼容性问题

set -e

echo "=========================================="
echo "修复mmcv版本兼容性"
echo "=========================================="

echo ""
echo "问题: mmcv 2.2.0与mmdet不兼容"
echo "解决: 降级到mmcv 2.1.0"
echo ""

# 卸载不兼容的mmcv
echo "步骤 1/3: 卸载mmcv 2.2.0"
pip uninstall mmcv -y

# 安装兼容版本
echo ""
echo "步骤 2/3: 安装mmcv 2.1.0"
mim install "mmcv==2.1.0"

# 重新安装mmdet和mmpose（确保依赖正确）
echo ""
echo "步骤 3/3: 重新安装mmdet和mmpose"
mim install "mmdet>=3.1.0"
mim install "mmpose>=1.1.0"

# 验证
echo ""
echo "=========================================="
echo "验证修复结果"
echo "=========================================="

python3 -c "import mmcv; print('✅ mmcv:', mmcv.__version__)"
python3 -c "import mmdet; print('✅ mmdet:', mmdet.__version__)"
python3 -c "import mmpose; print('✅ mmpose:', mmpose.__version__)"

echo ""
echo "=========================================="
echo "✅ 版本兼容性问题已修复"
echo "=========================================="
