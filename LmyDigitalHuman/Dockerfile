# 使用 NVIDIA CUDA 基础镜像，包含 CUDA 11.8
FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04

# 安装基础依赖
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    git \
    python3 \
    python3-pip \
    ffmpeg \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# 安装 .NET 8.0 SDK
RUN wget https://packages.microsoft.com/config/ubuntu/22.04/packages-microsoft-prod.deb -O packages-microsoft-prod.deb \
    && dpkg -i packages-microsoft-prod.deb \
    && rm packages-microsoft-prod.deb \
    && apt-get update \
    && apt-get install -y dotnet-sdk-8.0 \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 安装 Python 依赖
RUN pip3 install --upgrade pip \
    && pip3 install \
    edge-tts \
    openai-whisper \
    torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# 复制项目文件
COPY . .

# 设置环境变量
ENV ASPNETCORE_URLS=http://+:5000;https://+:5001
ENV ASPNETCORE_ENVIRONMENT=Production
ENV PYTHONUNBUFFERED=1
ENV CUDA_VISIBLE_DEVICES=0

# 暴露端口
EXPOSE 5000 5001

# 远程调试端口
EXPOSE 4024

# 启动命令 - 支持远程调试
ENTRYPOINT ["dotnet", "run", "--urls", "http://0.0.0.0:5000;https://0.0.0.0:5001"]