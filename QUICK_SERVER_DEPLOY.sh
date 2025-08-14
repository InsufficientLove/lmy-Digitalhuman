#!/bin/bash

# MuseTalk GPU快速服务器部署脚本
# 直接在服务器上运行，无需预先准备

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 部署目录
DEPLOY_DIR="$HOME/musetalk-gpu"

log_info "=========================================="
log_info "MuseTalk GPU 快速部署脚本"
log_info "=========================================="

# Step 1: 检查环境
log_info "Step 1: 检查环境..."

# 检查Docker
if ! command -v docker &> /dev/null; then
    log_error "Docker未安装，请先安装Docker"
    exit 1
fi
log_info "✓ Docker已安装: $(docker --version)"

# 检查GPU
if ! nvidia-smi &> /dev/null; then
    log_error "NVIDIA驱动未安装"
    exit 1
fi
log_info "✓ NVIDIA驱动已安装"

# 显示GPU信息
log_info "GPU信息:"
nvidia-smi --query-gpu=index,name,memory.total --format=csv

# Step 2: 创建部署目录
log_info "Step 2: 创建部署目录..."
mkdir -p "$DEPLOY_DIR"
cd "$DEPLOY_DIR"

# Step 3: 克隆MuseTalk官方代码
log_info "Step 3: 克隆MuseTalk官方代码..."
if [ -d "MuseTalk" ]; then
    log_warn "MuseTalk目录已存在，跳过克隆"
else
    git clone https://github.com/TMElyralab/MuseTalk.git
fi

# Step 4: 创建必要的文件
log_info "Step 4: 创建Docker和配置文件..."

# 创建Dockerfile.gpu
cat > Dockerfile.gpu << 'EOF'
FROM nvidia/cuda:12.1.0-cudnn8-devel-ubuntu22.04

# 设置环境变量
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV CUDA_HOME=/usr/local/cuda
ENV PATH=${CUDA_HOME}/bin:${PATH}
ENV LD_LIBRARY_PATH=${CUDA_HOME}/lib64:${LD_LIBRARY_PATH}

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    python3.10 python3-pip python3.10-dev \
    git wget curl vim \
    ffmpeg libsm6 libxext6 libxrender-dev libgomp1 \
    libglib2.0-0 libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

# 设置Python
RUN ln -s /usr/bin/python3.10 /usr/bin/python

# 升级pip
RUN pip install --upgrade pip setuptools wheel

# 安装PyTorch (CUDA 12.1版本)
RUN pip install --no-cache-dir \
    torch==2.2.0+cu121 \
    torchvision==0.17.0+cu121 \
    torchaudio==2.2.0+cu121 \
    --index-url https://download.pytorch.org/whl/cu121

# 复制MuseTalk代码
COPY MuseTalk /app/MuseTalk
WORKDIR /app

# 安装MuseTalk依赖
RUN pip install --no-cache-dir \
    numpy==1.24.3 \
    opencv-python==4.8.1.78 \
    opencv-contrib-python==4.8.1.78 \
    imageio==2.31.1 \
    imageio-ffmpeg==0.4.8 \
    moviepy==1.0.3 \
    tqdm \
    scikit-image==0.21.0 \
    pillow==10.0.0 \
    gradio==4.19.2 \
    accelerate==0.24.1 \
    transformers==4.30.2 \
    diffusers==0.27.2 \
    omegaconf==2.3.0 \
    einops \
    facenet-pytorch \
    mediapipe \
    protobuf==3.20.3 \
    gdown

# GPU优化包
RUN pip install --no-cache-dir \
    nvidia-ml-py3 \
    pynvml \
    gpustat

# 创建工作目录
RUN mkdir -p /app/models /app/inputs /app/outputs /app/logs

# 设置Python路径
ENV PYTHONPATH=/app:/app/MuseTalk:$PYTHONPATH

# 下载模型脚本
RUN cat > /app/download_models.py << 'SCRIPT'
#!/usr/bin/env python3
import os
import gdown
import subprocess

def download_models():
    model_dir = "/app/models"
    os.makedirs(model_dir, exist_ok=True)
    
    # MuseTalk模型下载链接
    models = {
        "musetalk": {
            "url": "https://drive.google.com/drive/folders/1YourModelID",  # 替换为实际链接
            "path": f"{model_dir}/musetalk"
        },
        "dwpose": {
            "url": "https://download.openmmlab.com/mmpose/v1/projects/rtmposev1/rtmpose-l_simcc-ucoco_dw-ucoco_270e-256x192-4d6dfc62_20230728.pth",
            "path": f"{model_dir}/dwpose"
        }
    }
    
    print("开始下载模型...")
    # 这里需要根据实际的模型下载链接进行修改
    
if __name__ == "__main__":
    download_models()
SCRIPT

# 创建入口脚本
RUN cat > /app/entrypoint.sh << 'SCRIPT'
#!/bin/bash
set -e

# 检查GPU
nvidia-smi

# 设置CUDA设备
if [ -n "$CUDA_VISIBLE_DEVICES" ]; then
    echo "使用GPU: $CUDA_VISIBLE_DEVICES"
fi

# 下载模型（如果需要）
if [ "$AUTO_DOWNLOAD_MODELS" = "true" ] && [ ! -d "/app/models/musetalk" ]; then
    echo "下载模型..."
    cd /app/MuseTalk && bash download_weights.sh
fi

# 运行命令
exec "$@"
SCRIPT

RUN chmod +x /app/entrypoint.sh /app/download_models.py

WORKDIR /app
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["python", "-c", "print('MuseTalk GPU Container Ready')"]
EOF

# 创建docker-compose.yml
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  musetalk-gpu:
    build:
      context: .
      dockerfile: Dockerfile.gpu
    image: musetalk:gpu
    container_name: musetalk-gpu
    runtime: nvidia
    environment:
      - CUDA_VISIBLE_DEVICES=${GPU_IDS:-0}
      - BATCH_SIZE=${BATCH_SIZE:-8}
      - AUTO_DOWNLOAD_MODELS=true
    volumes:
      - ./models:/app/models
      - ./inputs:/app/inputs
      - ./outputs:/app/outputs
      - ./logs:/app/logs
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              capabilities: [gpu]
              count: all
    ports:
      - "7860:7860"
      - "8000:8000"
    command: python /app/MuseTalk/app.py

  musetalk-benchmark:
    image: musetalk:gpu
    container_name: musetalk-benchmark
    runtime: nvidia
    environment:
      - CUDA_VISIBLE_DEVICES=${GPU_IDS:-all}
    volumes:
      - ./models:/app/models
      - ./results:/app/results
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              capabilities: [gpu]
              count: all
    profiles:
      - benchmark
    command: python /app/benchmark.py

networks:
  default:
    name: musetalk-network
EOF

# 创建基准测试脚本
cat > benchmark.py << 'EOF'
#!/usr/bin/env python3
"""
MuseTalk GPU基准测试脚本
"""
import os
import torch
import time
import json
from datetime import datetime

def benchmark_gpu():
    """运行GPU基准测试"""
    results = {
        "timestamp": datetime.now().isoformat(),
        "gpu_count": torch.cuda.device_count(),
        "gpus": []
    }
    
    print("="*50)
    print("MuseTalk GPU 基准测试")
    print("="*50)
    
    # 检测GPU
    if not torch.cuda.is_available():
        print("错误: CUDA不可用")
        return results
    
    gpu_count = torch.cuda.device_count()
    print(f"检测到 {gpu_count} 个GPU")
    
    # 测试每个GPU
    for i in range(gpu_count):
        props = torch.cuda.get_device_properties(i)
        gpu_info = {
            "id": i,
            "name": props.name,
            "memory_total": props.total_memory / (1024**3),
            "compute_capability": f"{props.major}.{props.minor}"
        }
        
        print(f"\nGPU {i}: {props.name}")
        print(f"  总显存: {gpu_info['memory_total']:.1f} GB")
        print(f"  计算能力: {gpu_info['compute_capability']}")
        
        # 简单性能测试
        torch.cuda.set_device(i)
        
        # 测试矩阵乘法
        size = 4096
        a = torch.randn(size, size, device=f'cuda:{i}', dtype=torch.float32)
        b = torch.randn(size, size, device=f'cuda:{i}', dtype=torch.float32)
        
        # 预热
        for _ in range(3):
            c = torch.matmul(a, b)
        torch.cuda.synchronize()
        
        # 测试
        start = time.time()
        for _ in range(10):
            c = torch.matmul(a, b)
        torch.cuda.synchronize()
        elapsed = time.time() - start
        
        tflops = (10 * 2 * size**3) / (elapsed * 1e12)
        gpu_info["tflops"] = tflops
        print(f"  性能: {tflops:.2f} TFLOPS")
        
        results["gpus"].append(gpu_info)
        
        # 清理
        del a, b, c
        torch.cuda.empty_cache()
    
    # 保存结果
    with open("/app/results/benchmark_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print("\n测试完成！结果已保存到 benchmark_results.json")
    return results

if __name__ == "__main__":
    benchmark_gpu()
EOF

# 创建运行脚本
cat > run.sh << 'EOF'
#!/bin/bash

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}MuseTalk GPU 运行脚本${NC}"
echo "======================="

# 显示GPU状态
echo -e "\n${GREEN}GPU状态:${NC}"
nvidia-smi --query-gpu=index,name,utilization.gpu,memory.used,memory.free --format=csv

# 选择操作
echo -e "\n${GREEN}选择操作:${NC}"
echo "1) 构建Docker镜像"
echo "2) 运行Gradio界面"
echo "3) 运行基准测试"
echo "4) 进入容器Shell"
echo "5) 停止所有容器"

read -p "请选择 (1-5): " choice

case $choice in
    1)
        echo "构建Docker镜像..."
        docker-compose build
        ;;
    2)
        echo "启动Gradio界面..."
        docker-compose up -d musetalk-gpu
        echo -e "${GREEN}Gradio界面运行在: http://localhost:7860${NC}"
        ;;
    3)
        echo "运行基准测试..."
        docker-compose --profile benchmark run --rm musetalk-benchmark
        ;;
    4)
        echo "进入容器Shell..."
        docker-compose run --rm musetalk-gpu bash
        ;;
    5)
        echo "停止所有容器..."
        docker-compose down
        ;;
    *)
        echo "无效选择"
        exit 1
        ;;
esac
EOF

chmod +x run.sh

# 创建.env文件
cat > .env << 'EOF'
# GPU配置
GPU_IDS=0
BATCH_SIZE=8

# 如果有多个GPU，可以设置为：
# GPU_IDS=0,1,2,3
# BATCH_SIZE=32
EOF

# 创建必要目录
mkdir -p models inputs outputs logs results

# Step 5: 构建Docker镜像
log_info "Step 5: 构建Docker镜像..."
docker-compose build

# Step 6: 完成
log_info "=========================================="
log_info "✅ 部署准备完成！"
log_info "=========================================="
echo
log_info "目录结构:"
ls -la
echo
log_info "下一步操作:"
echo "1. 编辑 .env 文件设置GPU配置"
echo "2. 运行 ./run.sh 选择操作"
echo "3. 或直接运行:"
echo "   - 启动Gradio: docker-compose up musetalk-gpu"
echo "   - 运行测试: docker-compose --profile benchmark run musetalk-benchmark"
echo
log_info "GPU配置示例:"
echo "   单GPU: GPU_IDS=0"
echo "   双GPU: GPU_IDS=0,1"
echo "   四GPU: GPU_IDS=0,1,2,3"
echo "   指定GPU: GPU_IDS=2,3 (使用GPU 2和3)"
echo
log_info "部署目录: $DEPLOY_DIR"