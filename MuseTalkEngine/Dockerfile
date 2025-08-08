FROM nvidia/cuda:12.1.1-cudnn8-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y \
    python3.10 python3.10-venv python3-pip \
    ffmpeg git curl wget \
    libgl1 libglib2.0-0 \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/musetalk/repo/MuseTalkEngine

# 复制代码（仅Python目录，避免层过大）
COPY MuseTalkEngine /opt/musetalk/repo/MuseTalkEngine

# 安装依赖（可按需补充/调整）
RUN python3 -m pip install --upgrade pip && \
    python3 -m pip install --index-url https://download.pytorch.org/whl/cu121 torch torchvision torchaudio && \
    python3 -m pip install \
      numpy scipy opencv-python-headless pillow moviepy soundfile pydub tqdm psutil \
      onnxruntime-gpu==1.18.0 \
      openai-whisper faster-whisper \
      requests pyyaml

EXPOSE 28888
CMD ["python3", "direct_launcher.py"]