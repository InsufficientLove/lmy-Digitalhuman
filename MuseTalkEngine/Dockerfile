# 基于已有的工作镜像
FROM musetalk-python:working

# 设置工作目录
WORKDIR /opt/musetalk/repo

# 复制最新代码（如果需要）
# COPY ./MuseTalkEngine /opt/musetalk/repo/MuseTalkEngine
# COPY ./MuseTalk /opt/musetalk/repo/MuseTalk

# 确保face-alignment已安装
RUN pip list | grep face-alignment || pip install face-alignment==1.4.1 --no-deps

# 设置环境变量
ENV TORCH_HOME=/opt/musetalk/cache/torch
ENV MODEL_PATH=/opt/musetalk/models
ENV PYTHONUNBUFFERED=1

# 默认命令
CMD ["python3", "MuseTalkEngine/streaming/api_service.py"]