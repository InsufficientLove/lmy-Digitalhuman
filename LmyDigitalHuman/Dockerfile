# 使用 NVIDIA CUDA 基础镜像，包含 CUDA 11.3（与 SadTalker 兼容）
FROM nvidia/cuda:11.3.1-cudnn8-runtime-ubuntu20.04

# 设置非交互式安装
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Asia/Shanghai

# 安装基础依赖和构建工具
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    git \
    python3.8 \
    python3.8-dev \
    python3.8-venv \
    python3-pip \
    build-essential \
    cmake \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    ffmpeg \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    && rm -rf /var/lib/apt/lists/*

# 设置 Python 3.8 为默认版本
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.8 1 \
    && update-alternatives --install /usr/bin/python python /usr/bin/python3.8 1

# 安装 .NET 8.0 SDK
RUN wget https://packages.microsoft.com/config/ubuntu/20.04/packages-microsoft-prod.deb -O packages-microsoft-prod.deb \
    && dpkg -i packages-microsoft-prod.deb \
    && rm packages-microsoft-prod.deb \
    && apt-get update \
    && apt-get install -y dotnet-sdk-8.0 \
    && rm -rf /var/lib/apt/lists/*

# 创建 SadTalker 虚拟环境
WORKDIR /opt
RUN python3 -m venv sadtalker_venv

# 激活虚拟环境并安装 SadTalker 依赖
ENV PATH="/opt/sadtalker_venv/bin:$PATH"
RUN pip install --upgrade pip setuptools wheel

# 安装 PyTorch 1.12.1 + CUDA 11.3（与 SadTalker 兼容）
RUN pip install torch==1.12.1+cu113 torchvision==0.13.1+cu113 torchaudio==0.12.1 --extra-index-url https://download.pytorch.org/whl/cu113

# 安装 SadTalker 依赖（按照您提供的版本）
RUN pip install \
    numpy==1.23.4 \
    face_alignment==1.3.5 \
    imageio==2.19.3 \
    imageio-ffmpeg==0.4.7 \
    librosa==0.9.2 \
    numba \
    resampy==0.3.1 \
    pydub==0.25.1 \
    scipy==1.10.1 \
    kornia==0.6.8 \
    tqdm \
    yacs==0.1.8 \
    pyyaml \
    joblib==1.1.0 \
    scikit-image==0.19.3 \
    basicsr==1.4.2 \
    facexlib==0.3.0 \
    gradio \
    gfpgan \
    av \
    safetensors

# 安装额外的依赖（Edge-TTS 和 Whisper）
RUN pip install edge-tts openai-whisper

# 设置工作目录
WORKDIR /app

# 克隆 SadTalker 仓库
RUN git clone https://github.com/OpenTalker/SadTalker.git /opt/SadTalker

# 复制项目文件
COPY . .

# 设置环境变量
ENV ASPNETCORE_URLS=http://+:5000;https://+:5001
ENV ASPNETCORE_ENVIRONMENT=Production
ENV PYTHONUNBUFFERED=1
ENV CUDA_VISIBLE_DEVICES=0
ENV SADTALKER_PATH=/opt/SadTalker
ENV SADTALKER_VENV=/opt/sadtalker_venv
ENV PYTHONPATH="${PYTHONPATH}:/opt/SadTalker"

# 创建必要的目录
RUN mkdir -p /app/checkpoints \
    && mkdir -p /app/gfpgan \
    && mkdir -p /app/temp \
    && mkdir -p /app/logs \
    && mkdir -p /app/wwwroot/videos \
    && mkdir -p /app/wwwroot/templates

# 下载 SadTalker 模型（可选，建议在构建时下载）
# RUN cd /opt/SadTalker && bash scripts/download_models.sh

# 暴露端口
EXPOSE 5000 5001

# 远程调试端口
EXPOSE 4024

# 创建启动脚本
RUN echo '#!/bin/bash\n\
source /opt/sadtalker_venv/bin/activate\n\
cd /app\n\
dotnet run --urls http://0.0.0.0:5000;https://0.0.0.0:5001' > /app/start.sh \
    && chmod +x /app/start.sh

# 启动命令
ENTRYPOINT ["/app/start.sh"]