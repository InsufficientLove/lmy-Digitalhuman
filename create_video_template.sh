#!/bin/bash
# MuseTalk 视频模板创建脚本
# 用法: ./create_video_template.sh <模板ID> <视频路径>

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查参数
if [ "$#" -lt 2 ]; then
    echo -e "${RED}用法: $0 <模板ID> <视频路径>${NC}"
    echo ""
    echo "示例:"
    echo "  $0 idle ./videos/idle.mp4"
    echo "  $0 smile ~/videos/smile.mp4"
    echo ""
    echo "说明:"
    echo "  模板ID: 用于标识模板的唯一名称（如：idle, smile, wave）"
    echo "  视频路径: MP4 格式的视频文件"
    echo ""
    echo "视频要求:"
    echo "  - 格式: MP4"
    echo "  - 分辨率: 至少 512x512"
    echo "  - 帧率: 25fps（推荐）"
    echo "  - 时长: 3-10 秒"
    echo "  - 内容: 一个人的正面视频"
    exit 1
fi

TEMPLATE_ID=$1
VIDEO_PATH=$2
SERVER_IP="192.168.20.250"

echo -e "${GREEN}🚀 开始创建视频模板: $TEMPLATE_ID${NC}"
echo -e "${YELLOW}⚠️ 注意: 视频预处理可能需要较长时间（几分钟到十几分钟）${NC}"
echo ""

# 检查视频文件是否存在
if [ ! -f "$VIDEO_PATH" ]; then
    echo -e "${RED}❌ 错误: 视频文件不存在: $VIDEO_PATH${NC}"
    exit 1
fi

# 检查文件格式
EXT="${VIDEO_PATH##*.}"
EXT_LOWER=$(echo "$EXT" | tr '[:upper:]' '[:lower:]')

if [[ "$EXT_LOWER" != "mp4" ]]; then
    echo -e "${RED}❌ 错误: 不支持的视频格式: $EXT${NC}"
    echo "支持的格式: MP4"
    echo ""
    echo "提示: 使用 ffmpeg 转换格式:"
    echo "  ffmpeg -i input.mov -c:v libx264 -preset medium -crf 23 -s 512x512 -r 25 output.mp4"
    exit 1
fi

echo -e "${YELLOW}📦 步骤 1/5: 复制视频到容器...${NC}"
docker cp "$VIDEO_PATH" musetalk-python:/videos/${TEMPLATE_ID}.mp4

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ 复制失败，请检查容器是否运行${NC}"
    echo "提示: 运行 docker-compose ps 查看容器状态"
    exit 1
fi

echo -e "${GREEN}✅ 视频已复制${NC}"
echo ""

echo -e "${YELLOW}⚙️ 步骤 2/5: 预处理视频（提取人脸坐标，这可能需要几分钟）...${NC}"
docker exec musetalk-python bash -c "
cd /opt/musetalk/repo/MuseTalkEngine && \
python3 preprocess_assets.py \
  --video /videos/${TEMPLATE_ID}.mp4 \
  --output /temp/preprocessed
"

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ 预处理失败${NC}"
    echo "可能的原因:"
    echo "  1. 视频中没有检测到清晰的人脸"
    echo "  2. 视频格式不兼容"
    echo "  3. GPU 内存不足"
    echo ""
    echo "提示: 查看日志"
    echo "  docker logs musetalk-python --tail 100"
    exit 1
fi

echo -e "${GREEN}✅ 视频预处理完成${NC}"
echo ""

echo -e "${YELLOW}📋 步骤 3/5: 整理预处理结果...${NC}"
docker exec musetalk-python mkdir -p /opt/musetalk/preprocessed
docker exec musetalk-python cp /temp/preprocessed/${TEMPLATE_ID}_bbox.pkl /opt/musetalk/preprocessed/

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ 找不到预处理结果文件${NC}"
    exit 1
fi

echo -e "${GREEN}✅ 预处理结果已保存${NC}"
echo ""

echo -e "${YELLOW}🔄 步骤 4/5: 加载视频资产到服务...${NC}"
RESPONSE=$(curl -s -X POST "http://${SERVER_IP}:28888/load_asset" \
  -H "Content-Type: application/json" \
  -d "{
    \"asset_id\": \"$TEMPLATE_ID\",
    \"video_path\": \"/videos/${TEMPLATE_ID}.mp4\",
    \"bbox_path\": \"/opt/musetalk/preprocessed/${TEMPLATE_ID}_bbox.pkl\"
  }")

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ API 调用失败${NC}"
    exit 1
fi

# 检查返回结果
if echo "$RESPONSE" | grep -q '"success":true'; then
    echo -e "${GREEN}✅ 资产加载成功${NC}"
else
    echo -e "${RED}❌ 资产加载失败${NC}"
    echo "响应: $RESPONSE"
    exit 1
fi

echo ""

echo -e "${YELLOW}🔍 步骤 5/5: 验证模板文件...${NC}"
echo "预处理文件:"
docker exec musetalk-python ls -lh /opt/musetalk/preprocessed/${TEMPLATE_ID}_bbox.pkl 2>/dev/null

echo ""
echo "视频文件:"
docker exec musetalk-python ls -lh /videos/${TEMPLATE_ID}.mp4 2>/dev/null

echo ""
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo -e "${GREEN}🎉 视频模板创建完成！${NC}"
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo ""
echo -e "📋 模板信息:"
echo -e "   ID: ${GREEN}${TEMPLATE_ID}${NC}"
echo -e "   视频: ${VIDEO_PATH}"
echo ""
echo -e "🌐 使用方式:"
echo -e "   1. 浏览器访问: ${GREEN}http://${SERVER_IP}:5000${NC}"
echo -e "   2. 在界面中选择视频资产: ${GREEN}${TEMPLATE_ID}${NC}"
echo -e "   3. 开始生成数字人视频"
echo ""
echo -e "🧪 测试 API:"
echo -e "   curl -X POST \"http://${SERVER_IP}:28888/stream\" \\"
echo -e "     -F \"audio=@test.wav\" \\"
echo -e "     -F \"asset_id=${TEMPLATE_ID}\" \\"
echo -e "     -o output.mp4"
echo ""
