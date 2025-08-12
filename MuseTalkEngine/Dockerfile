FROM nvidia/cuda:12.1.1-cudnn8-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y \
    python3.10 python3.10-venv python3-pip \
    ffmpeg git curl wget \
    libgl1 libglib2.0-0 libsndfile1 \
    build-essential pkg-config \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/musetalk/repo/MuseTalkEngine

# 复制代码（仅Python目录，避免层过大）
COPY MuseTalkEngine /opt/musetalk/repo/MuseTalkEngine
COPY requirements.txt /opt/musetalk/repo/requirements.txt

# 安装依赖（先装 PyTorch cu121，再装通用依赖）
RUN python3 -m pip install --upgrade pip setuptools wheel && \
    python3 -m pip install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cu121 \
      torch==2.3.1+cu121 torchvision==0.18.1+cu121 torchaudio==2.3.1+cu121 && \
    python3 -m pip install --no-cache-dir -r /opt/musetalk/repo/requirements.txt

EXPOSE 28888
COPY MuseTalkEngine/start.sh /usr/local/bin/muse-start
RUN chmod +x /usr/local/bin/muse-start
CMD ["muse-start"]