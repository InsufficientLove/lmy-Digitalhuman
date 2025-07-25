#!/bin/bash

echo "========================================"
echo "    下载 SadTalker 预训练模型"
echo "========================================"
echo

# 设置工作目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 创建必要的目录
mkdir -p checkpoints
mkdir -p gfpgan/weights

echo "[步骤1] 下载 SadTalker 主模型..."

# 主模型文件列表
MODELS=(
    "SadTalker_V0.0.2_256.safetensors"
    "SadTalker_V0.0.2_512.safetensors"
    "mapping_00229-model.pth.tar"
    "mapping_00109-model.pth.tar"
)

# Google Drive 下载（需要 gdown）
if command -v gdown &> /dev/null; then
    echo "使用 gdown 从 Google Drive 下载..."
    # 这里需要实际的 Google Drive 文件 ID
    # gdown https://drive.google.com/uc?id=FILE_ID -O checkpoints/
else
    echo "[警告] 未安装 gdown，无法从 Google Drive 下载"
    echo "请手动下载模型文件到 checkpoints 目录"
fi

echo
echo "[步骤2] 下载 GFPGAN 增强模型..."

# GFPGAN 模型
if [ ! -f "gfpgan/weights/GFPGANv1.4.pth" ]; then
    echo "下载 GFPGANv1.4.pth..."
    wget -P gfpgan/weights/ https://github.com/TencentARC/GFPGAN/releases/download/v1.3.0/GFPGANv1.4.pth
fi

# 人脸检测模型
if [ ! -f "gfpgan/weights/detection_Resnet50_Final.pth" ]; then
    echo "下载 detection_Resnet50_Final.pth..."
    wget -P gfpgan/weights/ https://github.com/xinntao/facexlib/releases/download/v0.1.0/detection_Resnet50_Final.pth
fi

# 人脸解析模型
if [ ! -f "gfpgan/weights/parsing_parsenet.pth" ]; then
    echo "下载 parsing_parsenet.pth..."
    wget -P gfpgan/weights/ https://github.com/xinntao/facexlib/releases/download/v0.2.2/parsing_parsenet.pth
fi

echo
echo "[步骤3] 验证模型文件..."

# 检查必要的模型文件
REQUIRED_FILES=(
    "checkpoints/SadTalker_V0.0.2_256.safetensors"
    "checkpoints/mapping_00229-model.pth.tar"
    "gfpgan/weights/GFPGANv1.4.pth"
)

MISSING=0
for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo "[缺失] $file"
        MISSING=1
    else
        echo "[存在] $file"
    fi
done

echo
if [ $MISSING -eq 0 ]; then
    echo "[成功] 所有必要的模型文件都已就位！"
else
    echo "[警告] 部分模型文件缺失，请手动下载："
    echo
    echo "下载地址："
    echo "- 百度网盘：https://pan.baidu.com/s/1tb0pBh2vZO5YD5vRNe_ZXg （提取码：sadt）"
    echo "- Google Drive：https://drive.google.com/drive/folders/1Wd88VDoLhVzYsQ30_qDVluQHjqQHrmYKr"
    echo
    echo "请将下载的文件放置到相应目录："
    echo "- SadTalker 模型 -> checkpoints/"
    echo "- GFPGAN 模型 -> gfpgan/weights/"
fi

echo
echo "========================================"
echo "    模型下载脚本执行完成"
echo "========================================"