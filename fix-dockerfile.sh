#!/bin/bash

echo "🔧 修复Dockerfile中的Git冲突标记..."

cd /opt/musetalk/repo/MuseTalkEngine

# 备份有冲突的文件
cp Dockerfile Dockerfile.conflict.bak

# 创建正确的Dockerfile
cat > Dockerfile << 'EOF'
FROM nvidia/cuda:12.1.1-cudnn8-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive \
    PIP_DEFAULT_TIMEOUT=300 \
    PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple \
    PIP_TRUSTED_HOST=pypi.tuna.tsinghua.edu.cn

RUN apt-get update && apt-get install -y \
    python3.10 python3.10-venv python3-pip \
    ca-certificates \
    ffmpeg git curl wget \
    libgl1 libglib2.0-0 libsndfile1 \
    build-essential pkg-config \
  && update-ca-certificates \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/musetalk/repo/MuseTalkEngine

# 仅复制依赖文件用于缓存
COPY requirements.txt /opt/musetalk/repo/requirements.txt

# 安装依赖（固定为 torch 2.1.0 + cu121）
RUN python3 -m pip install --upgrade pip setuptools wheel && \
    python3 -m pip install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cu121 \
      torch==2.1.0+cu121 torchvision==0.16.0+cu121 torchaudio==2.1.0+cu121 && \
    python3 -m pip install --no-cache-dir -r /opt/musetalk/repo/requirements.txt && \
    python3 -m pip install --no-cache-dir -U mmengine==0.10.4 && \
    python3 -m pip install --no-cache-dir --no-deps -U xtcocotools==1.14.3 && \
    (python3 -m pip install --no-cache-dir --trusted-host download.openmmlab.com \
      --only-binary=:all: -f https://download.openmmlab.com/mmcv/dist/cu121/torch2.1.0/index.html mmcv==2.1.0 \
     || python3 -m pip install --no-cache-dir --trusted-host download.openmmlab.com \
      --only-binary=:all: -f https://download.openmmlab.com/mmcv/dist/cu121/torch2.1/index.html mmcv==2.1.0 \
     || python3 -m pip install --no-cache-dir mmcv==2.1.0) && \
    python3 -m pip install --no-cache-dir --no-deps mmpose==1.3.2 mmdet==3.3.0 && \
    python3 -m pip install --no-cache-dir json-tricks==3.17.3 munkres==1.1.4 chumpy==0.70 pycocotools==2.0.7 shapely==2.0.6 terminaltables==3.1.10 && \
    python3 -m pip install --no-cache-dir transformers==4.41.2 huggingface_hub==0.34.4 && \
    python3 -m pip install --no-cache-dir diffusers==0.30.2 accelerate==0.28.0 tokenizers==0.19.1 safetensors==0.6.2 && \
    python3 -m pip install --no-cache-dir --force-reinstall --no-deps numpy==1.26.4 scipy==1.11.4 Pillow==10.0.1 opencv-python-headless==4.9.0.80

# 再复制代码
COPY MuseTalkEngine /opt/musetalk/repo/MuseTalkEngine

EXPOSE 28888
COPY MuseTalkEngine/start.sh /usr/local/bin/muse-start
RUN chmod +x /usr/local/bin/muse-start
CMD ["muse-start"]
EOF

echo "✅ Dockerfile已修复"

# 验证没有冲突标记
if grep -q "<<<<<<\|======\|>>>>>>" Dockerfile; then
    echo "❌ 错误：Dockerfile仍包含冲突标记"
    exit 1
else
    echo "✅ 验证通过：没有冲突标记"
fi

# 现在继续构建
echo "🔨 开始构建musetalk-python镜像..."
cd /opt/musetalk/repo
docker compose build musetalk-python