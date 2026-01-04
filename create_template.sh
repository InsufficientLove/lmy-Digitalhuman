#!/bin/bash
# MuseTalk 图片模板创建脚本
# 用法: ./create_template.sh <模板ID> <图片路径>

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查参数
if [ "$#" -lt 2 ]; then
    echo -e "${RED}用法: $0 <模板ID> <图片路径>${NC}"
    echo ""
    echo "示例:"
    echo "  $0 john ./photos/john.jpg"
    echo "  $0 mary ~/pictures/mary.png"
    echo ""
    echo "说明:"
    echo "  模板ID: 用于标识模板的唯一名称（如：default, john, mary）"
    echo "  图片路径: JPG 或 PNG 格式的人脸照片"
    exit 1
fi

TEMPLATE_ID=$1
IMAGE_PATH=$2
SERVER_IP="192.168.20.250"

echo -e "${GREEN}🚀 开始创建模板: $TEMPLATE_ID${NC}"
echo ""

# 检查图片文件是否存在
if [ ! -f "$IMAGE_PATH" ]; then
    echo -e "${RED}❌ 错误: 图片文件不存在: $IMAGE_PATH${NC}"
    exit 1
fi

# 获取文件扩展名
EXT="${IMAGE_PATH##*.}"
EXT_LOWER=$(echo "$EXT" | tr '[:upper:]' '[:lower:]')

# 检查文件格式
if [[ "$EXT_LOWER" != "jpg" && "$EXT_LOWER" != "jpeg" && "$EXT_LOWER" != "png" ]]; then
    echo -e "${RED}❌ 错误: 不支持的图片格式: $EXT${NC}"
    echo "支持的格式: JPG, JPEG, PNG"
    exit 1
fi

echo -e "${YELLOW}📦 步骤 1/3: 复制图片到容器...${NC}"
docker cp "$IMAGE_PATH" lmy-digitalhuman:/app/wwwroot/templates/${TEMPLATE_ID}.${EXT_LOWER}

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ 复制失败，请检查容器是否运行${NC}"
    echo "提示: 运行 docker-compose ps 查看容器状态"
    exit 1
fi

echo -e "${GREEN}✅ 图片已复制${NC}"
echo ""

echo -e "${YELLOW}⚙️ 步骤 2/3: 开始预处理（可能需要 10-30 秒）...${NC}"
RESPONSE=$(curl -s -X POST "http://${SERVER_IP}:28888/api/preprocess_template" \
  -H "Content-Type: application/json" \
  -d "{
    \"template_id\": \"$TEMPLATE_ID\",
    \"image_path\": \"/app/wwwroot/templates/${TEMPLATE_ID}.${EXT_LOWER}\",
    \"force\": false
  }")

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ API 调用失败，请检查服务是否运行${NC}"
    echo "提示: 运行 curl http://${SERVER_IP}:28888/health 测试服务"
    exit 1
fi

# 检查返回结果
if echo "$RESPONSE" | grep -q '"success":true'; then
    echo -e "${GREEN}✅ 预处理成功${NC}"
else
    echo -e "${RED}❌ 预处理失败${NC}"
    echo "响应: $RESPONSE"
    exit 1
fi

echo ""

echo -e "${YELLOW}🔍 步骤 3/3: 验证模板文件...${NC}"
FILES=$(docker exec musetalk-python ls -la /opt/musetalk/template_cache/${TEMPLATE_ID}/ 2>/dev/null)

if [ $? -eq 0 ]; then
    echo "$FILES"
    echo ""
    echo -e "${GREEN}✅ 验证通过${NC}"
else
    echo -e "${RED}❌ 验证失败，找不到模板文件${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo -e "${GREEN}🎉 模板创建完成！${NC}"
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo ""
echo -e "📋 模板信息:"
echo -e "   ID: ${GREEN}${TEMPLATE_ID}${NC}"
echo -e "   图片: ${IMAGE_PATH}"
echo ""
echo -e "🌐 使用方式:"
echo -e "   1. 浏览器访问: ${GREEN}http://${SERVER_IP}:5000${NC}"
echo -e "   2. 在界面中选择模板: ${GREEN}${TEMPLATE_ID}${NC}"
echo -e "   3. 开始生成数字人视频"
echo ""
echo -e "🧪 测试 API:"
echo -e "   curl -X POST \"http://${SERVER_IP}:28888/api/start_session\" \\"
echo -e "     -H \"Content-Type: application/json\" \\"
echo -e "     -d '{\"session_id\": \"test\", \"template_id\": \"${TEMPLATE_ID}\"}'"
echo ""
