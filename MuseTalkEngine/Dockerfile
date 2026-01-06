# 基于已有的工作镜像
FROM musetalk-python:working

# 设置工作目录
WORKDIR /opt/musetalk/repo

# 配置清华源（加速国内下载）
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 升级pip和构建工具（避免构建错误）
RUN python3 -m pip install --upgrade pip setuptools wheel

# 安装 OpenMMLab 基础库（关键依赖）
# 注意：mmcv版本必须==2.1.0（mmdet兼容性要求）
RUN pip install -U openmim && \
    mim install mmengine && \
    mim install "mmcv==2.1.0" && \
    mim install "mmdet>=3.1.0"

# 安装mmpose（使用--no-build-isolation避免chumpy构建问题）
RUN pip install -U numpy cython && \
    pip install chumpy --no-build-isolation && \
    pip install mmpose --no-build-isolation

# 确保face-alignment已安装
RUN pip list | grep face-alignment || pip install face-alignment==1.4.1 --no-deps

# 复制项目代码
COPY . /opt/musetalk/repo/

# 安装项目依赖
RUN pip install -r /opt/musetalk/repo/MuseTalkEngine/requirements.txt || true

# 设置环境变量
ENV TORCH_HOME=/opt/musetalk/cache/torch
ENV MODEL_PATH=/opt/musetalk/models
ENV MUSE_TEMPLATE_CACHE_DIR=/opt/musetalk/template_cache
ENV PYTHONUNBUFFERED=1

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:28888/health || exit 1

# 暴露端口
EXPOSE 28888

# 默认命令
CMD ["python3", "/opt/musetalk/repo/MuseTalkEngine/streaming/api_service.py"]