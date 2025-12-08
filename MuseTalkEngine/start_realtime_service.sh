#!/bin/bash
# MuseTalk 实时推理服务启动脚本

set -e

echo "=================================================="
echo "🚀 MuseTalk 实时推理服务启动脚本"
echo "=================================================="

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. 检查环境变量
echo -e "\n${YELLOW}[1/5] 检查环境变量...${NC}"

if [ -z "$MUSE_TALK_DIR" ]; then
    export MUSE_TALK_DIR=/opt/musetalk/repo/MuseTalk
    echo "设置默认 MUSE_TALK_DIR: $MUSE_TALK_DIR"
else
    echo "MUSE_TALK_DIR: $MUSE_TALK_DIR"
fi

if [ ! -d "$MUSE_TALK_DIR" ]; then
    echo -e "${RED}❌ MuseTalk 目录不存在: $MUSE_TALK_DIR${NC}"
    exit 1
fi

# 设置默认视频路径
if [ -z "$AVATAR_VIDEO_PATH" ]; then
    export AVATAR_VIDEO_PATH=./data/video/idle.mp4
    echo "设置默认 AVATAR_VIDEO_PATH: $AVATAR_VIDEO_PATH"
fi

# 设置端口
if [ -z "$PORT" ]; then
    export PORT=8000
fi
echo "服务端口: $PORT"

# 2. 检查 GPU
echo -e "\n${YELLOW}[2/5] 检查 GPU...${NC}"
if command -v nvidia-smi &> /dev/null; then
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
    echo -e "${GREEN}✅ GPU 可用${NC}"
else
    echo -e "${RED}❌ 未检测到 NVIDIA GPU${NC}"
    echo "继续运行（将使用 CPU）..."
fi

# 3. 检查 Python 依赖
echo -e "\n${YELLOW}[3/5] 检查 Python 依赖...${NC}"
python3 -c "
import sys
packages = ['fastapi', 'uvicorn', 'torch', 'cv2', 'numpy']
missing = []
for pkg in packages:
    try:
        __import__(pkg if pkg != 'cv2' else 'cv2')
    except ImportError:
        missing.append(pkg)
if missing:
    print(f'❌ 缺少依赖: {missing}')
    print('请运行: pip install -r requirements_realtime.txt')
    sys.exit(1)
else:
    print('✅ 所有依赖已安装')
"
if [ $? -ne 0 ]; then
    exit 1
fi

# 4. 检查预处理文件
echo -e "\n${YELLOW}[4/5] 检查预处理文件...${NC}"
VIDEO_NAME=$(basename "$AVATAR_VIDEO_PATH" .mp4)
BBOX_FILE="./data/preprocessed/${VIDEO_NAME}_bbox.pkl"

if [ ! -f "$AVATAR_VIDEO_PATH" ]; then
    echo -e "${RED}❌ 视频文件不存在: $AVATAR_VIDEO_PATH${NC}"
    exit 1
fi

if [ ! -f "$BBOX_FILE" ]; then
    echo -e "${YELLOW}⚠️ 边界框文件不存在: $BBOX_FILE${NC}"
    echo "正在运行预处理..."
    python3 preprocess_assets.py --video "$AVATAR_VIDEO_PATH" --output ./data/preprocessed
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ 预处理完成${NC}"
    else
        echo -e "${RED}❌ 预处理失败${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✅ 预处理文件已存在: $BBOX_FILE${NC}"
fi

# 5. 启动服务
echo -e "\n${YELLOW}[5/5] 启动服务...${NC}"
echo "=================================================="

# 可选：启用 torch.compile
# export USE_TORCH_COMPILE=1

# 启动方式选择
MODE=${1:-"direct"}

case $MODE in
    "direct")
        echo "直接运行模式"
        python3 main_realtime.py
        ;;
    "uvicorn")
        echo "Uvicorn 模式 (推荐生产环境)"
        uvicorn main_realtime:app --host 0.0.0.0 --port $PORT --workers 1 --log-level info
        ;;
    "dev")
        echo "开发模式 (自动重载)"
        uvicorn main_realtime:app --host 0.0.0.0 --port $PORT --reload
        ;;
    *)
        echo -e "${RED}未知模式: $MODE${NC}"
        echo "用法: $0 [direct|uvicorn|dev]"
        exit 1
        ;;
esac
