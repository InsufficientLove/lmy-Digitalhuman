FROM nvidia/cuda:12.1.0-cudnn8-devel-ubuntu22.04

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

RUN ln -s /usr/bin/python3.10 /usr/bin/python
RUN pip install --upgrade pip setuptools wheel

# 安装PyTorch CUDA 12.1
RUN pip install --no-cache-dir \
    torch==2.2.0+cu121 \
    torchvision==0.17.0+cu121 \
    torchaudio==2.2.0+cu121 \
    --index-url https://download.pytorch.org/whl/cu121

# 克隆MuseTalk - 支持代理和重试
ARG HTTP_PROXY
ARG HTTPS_PROXY
ENV http_proxy=${HTTP_PROXY}
ENV https_proxy=${HTTPS_PROXY}

# 复制本地的MuseTalk（需要先在本地克隆）
COPY MuseTalk /app/MuseTalk

# 清除代理设置
ENV http_proxy=
ENV https_proxy=

# 安装MuseTalk依赖
WORKDIR /app/MuseTalk
RUN pip install -r requirements.txt

# 安装额外依赖
RUN pip install --no-cache-dir \
    gradio==4.19.2 \
    accelerate==0.24.1 \
    transformers==4.30.2 \
    diffusers==0.27.2 \
    omegaconf==2.3.0 \
    einops \
    facenet-pytorch \
    mediapipe \
    protobuf==3.20.3 \
    gdown \
    nvidia-ml-py3 \
    pynvml \
    gpustat

# 复制自定义代码
COPY gpu_optimizer.py /app/
COPY entrypoint.py /app/

# 创建必要目录
RUN mkdir -p /app/models /app/inputs /app/outputs /app/logs

# 复制模型文件（如果存在）
COPY models /app/models 2>/dev/null || true

WORKDIR /app
ENV PYTHONPATH=/app:/app/MuseTalk:$PYTHONPATH

EXPOSE 7860 8000

ENTRYPOINT ["python", "/app/entrypoint.py"]