#!/bin/bash
# MuseTalk 依赖安装脚本 - 锁定版本
# 适用于：Ubuntu 22.04 + CUDA 12.x + Python 3.10

set -e  # 遇到错误立即退出

echo "=========================================="
echo "🔧 MuseTalk 依赖安装（锁定版本）"
echo "=========================================="
echo ""
echo "环境信息："
echo "  - Ubuntu: 22.04"
echo "  - CUDA: 12.x"
echo "  - Python: 3.10+"
echo "  - GPU: RTX 4090D x2"
echo ""

# 检查 Python 版本
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo "Python 版本: $PYTHON_VERSION"

# 检查 CUDA
if command -v nvidia-smi &> /dev/null; then
    echo "CUDA 驱动: 已安装"
    nvidia-smi --query-gpu=name,driver_version --format=csv,noheader | head -1
else
    echo "⚠️  警告: 未检测到 NVIDIA 驱动"
fi

echo ""
echo "=========================================="
echo "开始安装依赖..."
echo "=========================================="

# 更新 pip
echo ""
echo "[1/4] 更新 pip..."
python3 -m pip install --upgrade pip

# 安装 PyTorch（最关键）
echo ""
echo "[2/4] 安装 PyTorch (CUDA 12.1)..."
echo "   这是最大的包，约 2-3GB，请耐心等待..."
python3 -m pip install torch==2.1.2 torchvision==0.16.2 torchaudio==2.1.2 \
    --index-url https://download.pytorch.org/whl/cu121

# 验证 PyTorch
echo ""
echo "验证 PyTorch 安装..."
python3 -c "
import torch
print(f'✅ PyTorch {torch.__version__}')
print(f'✅ CUDA 可用: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'✅ CUDA 版本: {torch.version.cuda}')
    print(f'✅ GPU 数量: {torch.cuda.device_count()}')
    for i in range(torch.cuda.device_count()):
        print(f'   GPU {i}: {torch.cuda.get_device_name(i)}')
" || {
    echo "❌ PyTorch 安装失败！"
    exit 1
}

# 安装其他依赖
echo ""
echo "[3/4] 安装其他依赖..."
cd /opt/musetalk/repo
python3 -m pip install -r MuseTalkEngine/requirements_locked.txt

# 验证关键库
echo ""
echo "[4/4] 验证关键库..."

LIBS=(
    "numpy:NumPy"
    "cv2:OpenCV"
    "PIL:Pillow"
    "fastapi:FastAPI"
    "transformers:Transformers"
    "diffusers:Diffusers"
    "librosa:Librosa"
    "face_alignment:Face-Alignment"
)

FAILED=0
for lib_info in "${LIBS[@]}"; do
    IFS=':' read -r lib name <<< "$lib_info"
    if python3 -c "import $lib" 2>/dev/null; then
        echo "✅ $name"
    else
        echo "❌ $name - 安装失败"
        FAILED=$((FAILED + 1))
    fi
done

echo ""
echo "=========================================="
if [ $FAILED -eq 0 ]; then
    echo "✅ 所有依赖安装成功！"
    echo "=========================================="
    echo ""
    echo "下一步："
    echo "  1. cd /opt/musetalk/repo"
    echo "  2. bash quick_check.sh"
    echo "  3. python3 MuseTalkEngine/check_env.py"
    echo ""
else
    echo "❌ $FAILED 个库安装失败"
    echo "=========================================="
    echo ""
    echo "请检查错误信息并重试"
    exit 1
fi
