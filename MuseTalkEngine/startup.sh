#!/bin/bash
# MuseTalk Python服务启动脚本

echo "🚀 启动MuseTalk Python服务..."

# 设置环境变量
export TORCH_HOME=/opt/musetalk/cache/torch
export HF_HOME=/opt/musetalk/cache/huggingface
export TRANSFORMERS_CACHE=/opt/musetalk/cache/transformers

# 创建必要的目录
mkdir -p /root/.cache/torch/hub/checkpoints/
mkdir -p /opt/musetalk/cache/torch/hub/checkpoints/

# 创建模型软链接（如果存在）
if [ -f "/opt/musetalk/cache/torch/hub/checkpoints/s3fd-619a316812.pth" ]; then
    ln -sf /opt/musetalk/cache/torch/hub/checkpoints/s3fd-619a316812.pth /root/.cache/torch/hub/checkpoints/
fi

if [ -f "/opt/musetalk/cache/torch/hub/checkpoints/2DFAN4-cd938726ad.zip" ]; then
    ln -sf /opt/musetalk/cache/torch/hub/checkpoints/2DFAN4-cd938726ad.zip /root/.cache/torch/hub/checkpoints/
fi

# 切换到工作目录
cd /opt/musetalk/repo/MuseTalkEngine

# 启动服务
python3 main.py --mode hybrid