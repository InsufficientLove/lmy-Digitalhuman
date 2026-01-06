# 基于已有的工作镜像
FROM musetalk-python:working

# 设置工作目录
WORKDIR /opt/musetalk/repo

# 复制最新代码（如果需要）
# COPY ./MuseTalkEngine /opt/musetalk/repo/MuseTalkEngine
# COPY ./musetalk /opt/musetalk/repo/musetalk

# 配置清华源（加速国内下载）
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 安装 OpenMMLab 基础库（关键依赖）
# 注意：mmcv版本必须<2.2.0（mmdet兼容性要求）
RUN pip install -U openmim && \
    mim install mmengine && \
    mim install "mmcv==2.1.0" && \
    mim install "mmdet>=3.1.0" && \
    mim install "mmpose>=1.1.0"

# 确保face-alignment已安装
RUN pip list | grep face-alignment || pip install face-alignment==1.4.1 --no-deps

# 安装项目依赖
COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

# 设置环境变量
ENV TORCH_HOME=/opt/musetalk/cache/torch
ENV MODEL_PATH=/opt/musetalk/models
ENV PYTHONUNBUFFERED=1

# 默认命令
CMD ["python3", "MuseTalkEngine/streaming/api_service.py"]