FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04

# 设置环境变量
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV CUDA_HOME=/usr/local/cuda
ENV PATH=${CUDA_HOME}/bin:${PATH}
ENV LD_LIBRARY_PATH=${CUDA_HOME}/lib64:${LD_LIBRARY_PATH}

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    ffmpeg \
    git \
    wget \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

# 创建工作目录
WORKDIR /opt/musetalk/repo/MuseTalkEngine

# 先复制requirements.txt并安装依赖（利用Docker缓存）
COPY MuseTalkEngine/requirements.txt .
# 使用国内镜像源加速下载
RUN pip3 install --no-cache-dir \
    -i https://pypi.tuna.tsinghua.edu.cn/simple \
    --trusted-host pypi.tuna.tsinghua.edu.cn \
    torch==2.0.1 torchvision==0.15.2 torchaudio==2.0.2 --index-url https://download.pytorch.org/whl/cu118

# 分批安装其他依赖，避免超时
RUN pip3 install --no-cache-dir \
    -i https://pypi.tuna.tsinghua.edu.cn/simple \
    --trusted-host pypi.tuna.tsinghua.edu.cn \
    --timeout 120 \
    transformers==4.30.2 \
    numpy==1.24.3 \
    scipy==1.10.1

RUN pip3 install --no-cache-dir \
    -i https://pypi.tuna.tsinghua.edu.cn/simple \
    --trusted-host pypi.tuna.tsinghua.edu.cn \
    --timeout 120 \
    opencv-python==4.8.0.74 \
    librosa==0.10.0 \
    soundfile==0.12.1

RUN pip3 install --no-cache-dir \
    -i https://pypi.tuna.tsinghua.edu.cn/simple \
    --trusted-host pypi.tuna.tsinghua.edu.cn \
    imageio==2.31.1 \
    imageio-ffmpeg==0.4.8 \
    websockets==11.0.3

# 复制应用代码（新的目录结构）
COPY MuseTalkEngine/core /opt/musetalk/repo/MuseTalkEngine/core/
COPY MuseTalkEngine/offline /opt/musetalk/repo/MuseTalkEngine/offline/
COPY MuseTalkEngine/streaming /opt/musetalk/repo/MuseTalkEngine/streaming/
COPY MuseTalkEngine/main.py /opt/musetalk/repo/MuseTalkEngine/

# 创建必要的目录
RUN mkdir -p /opt/musetalk/template_cache \
    /opt/musetalk/cache/torch_compile \
    /opt/musetalk/templates \
    /opt/musetalk/repo/MuseTalk \
    /temp

# 设置Python路径
ENV PYTHONPATH=/opt/musetalk/repo/MuseTalkEngine:/opt/musetalk/repo/MuseTalk:$PYTHONPATH

# 暴露端口
EXPOSE 8000 8766

# 启动命令
CMD ["python3", "main.py", "--mode", "hybrid"]