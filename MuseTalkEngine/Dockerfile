FROM nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu22.04

# 设置环境变量
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV CUDA_HOME=/usr/local/cuda
ENV PATH=${CUDA_HOME}/bin:${PATH}
ENV LD_LIBRARY_PATH=${CUDA_HOME}/lib64:${LD_LIBRARY_PATH}
ENV TORCH_CUDA_ARCH_LIST="6.0;6.1;7.0;7.5;8.0;8.6;8.9;9.0"

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3.10-dev \
    python3-pip \
    build-essential \
    cmake \
    git \
    wget \
    curl \
    ffmpeg \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libffi-dev \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# 升级pip
RUN python3 -m pip install --upgrade pip setuptools wheel

# 创建工作目录
WORKDIR /opt/musetalk/repo/MuseTalkEngine

# 安装PyTorch（CUDA 12.1版本）
RUN pip3 install --no-cache-dir \
    torch==2.1.0 \
    torchvision==0.16.0 \
    torchaudio==2.1.0 \
    --index-url https://download.pytorch.org/whl/cu121

# 安装numpy（其他包依赖）
RUN pip3 install --no-cache-dir numpy==1.24.3

# 安装MMCV（对应CUDA 12.1和torch 2.1）
RUN pip3 install --no-cache-dir \
    mmcv==2.1.0 -f https://download.openmmlab.com/mmcv/dist/cu121/torch2.1/index.html

# 安装MM系列（与mmcv 2.1兼容的版本）
RUN pip3 install --no-cache-dir \
    mmengine==0.10.1 \
    mmdet==3.2.0 \
    mmpose==1.2.0

# 安装Hugging Face生态（与torch 2.1兼容）
RUN pip3 install --no-cache-dir \
    huggingface-hub==0.19.4 \
    transformers==4.35.2 \
    diffusers==0.24.0 \
    accelerate==0.25.0 \
    tokenizers==0.15.0 \
    safetensors==0.4.1

# 安装音视频处理
RUN pip3 install --no-cache-dir \
    opencv-python==4.8.1.78 \
    opencv-contrib-python==4.8.1.78 \
    imageio==2.33.0 \
    imageio-ffmpeg==0.4.9 \
    moviepy==1.0.3 \
    Pillow==10.1.0 \
    scikit-image==0.22.0

# 安装音频处理
RUN pip3 install --no-cache-dir \
    librosa==0.10.1 \
    soundfile==0.12.1 \
    audioread==3.0.1 \
    numba==0.58.1 \
    resampy==0.4.2

# 安装科学计算
RUN pip3 install --no-cache-dir \
    scipy==1.11.4 \
    scikit-learn==1.3.2 \
    pandas==2.1.4

# 安装人脸处理
RUN pip3 install --no-cache-dir \
    basicsr==1.4.2 \
    facexlib==0.3.0 \
    gfpgan==1.3.8 \
    realesrgan==0.3.0 \
    filterpy==1.4.5

# 安装深度学习工具
RUN pip3 install --no-cache-dir \
    einops==0.7.0 \
    omegaconf==2.3.0 \
    hydra-core==1.3.2 \
    tqdm==4.66.1 \
    matplotlib==3.8.2 \
    tensorboard==2.15.1 \
    pyyaml==6.0.1

# 安装Web服务
RUN pip3 install --no-cache-dir \
    fastapi==0.104.1 \
    uvicorn==0.24.0 \
    python-multipart==0.0.6 \
    websockets==12.0 \
    aiofiles==23.2.1 \
    httpx==0.25.2

# 复制应用代码
COPY MuseTalkEngine/core /opt/musetalk/repo/MuseTalkEngine/core/
COPY MuseTalkEngine/offline /opt/musetalk/repo/MuseTalkEngine/offline/
COPY MuseTalkEngine/streaming /opt/musetalk/repo/MuseTalkEngine/streaming/
COPY MuseTalkEngine/main.py /opt/musetalk/repo/MuseTalkEngine/
COPY MuseTalkEngine/requirements.txt /opt/musetalk/repo/MuseTalkEngine/

# 创建必要的目录
RUN mkdir -p /opt/musetalk/template_cache \
    /opt/musetalk/cache/torch_compile \
    /opt/musetalk/templates \
    /opt/musetalk/repo/MuseTalk \
    /temp

# 设置Python路径
ENV PYTHONPATH=/opt/musetalk/repo/MuseTalkEngine:/opt/musetalk/repo/MuseTalk:$PYTHONPATH

# 暴露端口
EXPOSE 8000 8766 28888

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python3 -c "import torch; import mmpose; import diffusers; print('OK')" || exit 1

# 启动命令
CMD ["python3", "main.py", "--mode", "hybrid"]