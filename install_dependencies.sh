#!/bin/bash
# MuseTalk 依赖安装脚本 - 锁定版本 + 国内镜像加速
# 适用于：Ubuntu 22.04 + CUDA 12.x + Python 3.10

set -e  # 遇到错误立即退出

echo "=========================================="
echo "🔧 MuseTalk 依赖安装"
echo "=========================================="
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
echo "配置 pip 国内镜像..."
echo "=========================================="

# 配置 pip 使用清华镜像
mkdir -p ~/.pip
cat > ~/.pip/pip.conf << 'EOF'
[global]
index-url = https://pypi.tuna.tsinghua.edu.cn/simple
trusted-host = pypi.tuna.tsinghua.edu.cn

[install]
trusted-host = pypi.tuna.tsinghua.edu.cn
EOF

echo "✅ pip 镜像已配置为清华源（加速 pip 包下载）"
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
echo "[2/4] 检查 PyTorch..."
if python3 -c "import torch" 2>/dev/null; then
    TORCH_VERSION=$(python3 -c "import torch; print(torch.__version__)")
    echo "✅ PyTorch 已安装: $TORCH_VERSION"
else
    echo "安装 PyTorch (CUDA 12.1)..."
    echo "   约 2-3GB，使用官方源..."
    python3 -m pip install torch==2.1.2 torchvision==0.16.2 torchaudio==2.1.2 \
        --index-url https://download.pytorch.org/whl/cu121
fi

# 验证 PyTorch
echo ""
echo "验证 PyTorch..."
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
    echo "❌ PyTorch 验证失败！"
    exit 1
}

# 安装其他依赖（逐个检查，跳过已安装）
echo ""
echo "[3/4] 安装其他依赖（跳过已安装的包）..."

# 定义依赖包
PACKAGES=(
    "fastapi==0.104.1"
    "uvicorn[standard]==0.24.0"
    "python-multipart==0.0.6"
    "opencv-python==4.8.1.78"
    "pillow==10.1.0"
    "imageio==2.31.5"
    "imageio-ffmpeg==0.4.9"
    "librosa==0.10.1"
    "soundfile==0.12.1"
    "scipy==1.11.4"
    "transformers==4.35.2"
    "diffusers==0.24.0"
    "accelerate==0.25.0"
    "safetensors==0.4.1"
    "face-alignment==1.3.5"
    "numpy==1.24.3"
    "tqdm==4.66.1"
    "pyyaml==6.0.1"
    "pydantic==2.5.0"
    "httpx==0.25.2"
    "aiofiles==23.2.1"
    "requests==2.31.0"
    "einops==0.7.0"
    "omegaconf==2.3.0"
)

# 检查并安装
for pkg in "${PACKAGES[@]}"; do
    pkg_name=$(echo "$pkg" | cut -d'=' -f1 | tr '-' '_')
    echo -n "检查 $pkg_name... "
    
    # 特殊处理
    if [ "$pkg_name" = "opencv_python" ]; then
        check_name="cv2"
    elif [ "$pkg_name" = "pillow" ]; then
        check_name="PIL"
    elif [ "$pkg_name" = "python_multipart" ]; then
        check_name="multipart"
    else
        check_name="$pkg_name"
    fi
    
    if python3 -c "import $check_name" 2>/dev/null; then
        echo "✅ 已安装"
    else
        echo "⏳ 安装中..."
        python3 -m pip install "$pkg" --no-cache-dir
    fi
done

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
    exit 1
fi
