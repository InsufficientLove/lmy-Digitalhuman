#!/bin/bash

# MuseTalk准备脚本 - 克隆代码和下载模型

set -e

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}MuseTalk 准备脚本${NC}"
echo -e "${GREEN}========================================${NC}"

# Step 1: 克隆MuseTalk
echo -e "\n${GREEN}[1/3] 克隆MuseTalk源码...${NC}"
if [ -d "MuseTalk" ]; then
    echo -e "${YELLOW}MuseTalk目录已存在，跳过克隆${NC}"
else
    git clone https://github.com/TMElyralab/MuseTalk.git
    echo -e "${GREEN}✓ MuseTalk克隆完成${NC}"
fi

# Step 2: 下载模型
echo -e "\n${GREEN}[2/3] 下载模型文件...${NC}"
cd MuseTalk

# 检查是否有下载脚本
if [ -f "download_weights.sh" ]; then
    echo "运行官方下载脚本..."
    bash download_weights.sh
else
    echo -e "${YELLOW}下载脚本不存在，手动下载模型...${NC}"
    
    # 创建模型目录
    mkdir -p ../models/musetalk ../models/dwpose ../models/face-parse-bisent ../models/sd-vae-ft-mse
    
    # 下载MuseTalk模型
    echo "下载MuseTalk模型..."
    # 这里需要根据实际的模型链接进行下载
    # wget -O ../models/musetalk/musetalk.pth https://huggingface.co/TMElyralab/MuseTalk/resolve/main/musetalk.pth
    
    echo -e "${YELLOW}请手动下载模型文件到models目录${NC}"
    echo "模型下载链接："
    echo "1. MuseTalk: https://huggingface.co/TMElyralab/MuseTalk"
    echo "2. DWPose: https://huggingface.co/yzd-v/DWPose/resolve/main/yolox_l.onnx"
    echo "3. Face Parsing: https://github.com/zllrunning/face-parsing.PyTorch"
    echo "4. SD-VAE: https://huggingface.co/stabilityai/sd-vae-ft-mse"
fi

cd ..

# Step 3: 创建必要目录
echo -e "\n${GREEN}[3/3] 创建必要目录...${NC}"
mkdir -p models inputs outputs logs

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}准备完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "\n目录结构："
ls -la

echo -e "\n${GREEN}下一步：${NC}"
echo "1. 确认模型文件已下载到models目录"
echo "2. 运行: docker build -t musetalk:latest ."
echo "3. 运行: docker run --runtime=nvidia --gpus all -p 7860:7860 musetalk:latest"