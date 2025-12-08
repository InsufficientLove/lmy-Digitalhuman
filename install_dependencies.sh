#!/bin/bash
# MuseTalk 依赖安装脚本 - 锁定版本 + 国内镜像加速
# 适用于：Ubuntu 22.04 + CUDA 12.x + Python 3.10

set -e  # 遇到错误立即退出

echo "=========================================="
echo "🔧 MuseTalk 依赖安装（国内镜像加速）"
echo "=========================================="
echo ""
echo "环境信息："
echo "  - Ubuntu: 22.04"
echo "  - CUDA: 12.x"
echo "  - Python: 3.10+"
echo "  - GPU: RTX 4090D x2"
echo "  - 镜像源: 清华大学 TUNA"
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
echo "配置国内镜像源..."
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

echo "✅ pip 镜像已配置为清华源"

# 备用镜像说明
cat << 'EOF'

📝 国内镜像源列表（按速度排序）：
   1. 清华大学: https://pypi.tuna.tsinghua.edu.cn/simple
   2. 阿里云:   https://mirrors.aliyun.com/pypi/simple
   3. 腾讯云:   https://mirrors.cloud.tencent.com/pypi/simple
   4. 华为云:   https://repo.huaweicloud.com/repository/pypi/simple

   如需切换，修改 ~/.pip/pip.conf 中的 index-url
EOF

echo ""
echo "=========================================="
echo "开始安装依赖..."
echo "=========================================="

# 更新 pip
echo ""
echo "[1/4] 更新 pip..."
python3 -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple

# 安装 PyTorch（最关键）
echo ""
echo "[2/4] 安装 PyTorch (CUDA 12.1)..."
echo "   使用清华镜像，约 2-3GB，速度快很多..."
python3 -m pip install torch==2.1.2 torchvision==0.16.2 torchaudio==2.1.2 \
    --index-url https://download.pytorch.org/whl/cu121 \
    -i https://pypi.tuna.tsinghua.edu.cn/simple

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

# 创建临时 requirements 文件（已包含镜像源）
cat > /tmp/requirements_install.txt << 'EOF'
# FastAPI 核心
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6

# 图像处理
opencv-python==4.8.1.78
pillow==10.1.0
imageio==2.31.5
imageio-ffmpeg==0.4.9

# 音频处理
librosa==0.10.1
soundfile==0.12.1
scipy==1.11.4

# 深度学习工具
transformers==4.35.2
diffusers==0.24.0
accelerate==0.25.0
safetensors==0.4.1

# 人脸检测
face-alignment==1.3.5

# 基础工具
numpy==1.24.3
tqdm==4.66.1
pyyaml==6.0.1
pydantic==2.5.0

# 网络请求
httpx==0.25.2
aiofiles==23.2.1
requests==2.31.0

# 其他
einops==0.7.0
omegaconf==2.3.0
EOF

python3 -m pip install -r /tmp/requirements_install.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

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
    "soundfile:SoundFile"
    "scipy:SciPy"
)

FAILED=0
for lib_info in "${LIBS[@]}"; do
    IFS=':' read -r lib name <<< "$lib_info"
    if python3 -c "import $lib" 2>/dev/null; then
        version=$(python3 -c "import $lib; print(getattr($lib, '__version__', 'N/A'))" 2>/dev/null || echo "N/A")
        echo "✅ $name ($version)"
    else
        echo "❌ $name - 安装失败"
        FAILED=$((FAILED + 1))
    fi
done

# 清理临时文件
rm -f /tmp/requirements_install.txt

echo ""
echo "=========================================="
if [ $FAILED -eq 0 ]; then
    echo "✅ 所有依赖安装成功！"
    echo "=========================================="
    echo ""
    echo "📊 安装统计："
    echo "   总计: ${#LIBS[@]} 个核心库"
    echo "   成功: ${#LIBS[@]} 个"
    echo "   失败: 0 个"
    echo ""
    echo "🚀 下一步："
    echo "   1. cd /opt/musetalk/repo"
    echo "   2. bash quick_check.sh"
    echo "   3. python3 MuseTalkEngine/check_env.py"
    echo ""
else
    echo "❌ $FAILED 个库安装失败"
    echo "=========================================="
    echo ""
    echo "请检查错误信息并重试"
    exit 1
fi
