#!/bin/bash
# 完整重建脚本 - 包含所有修复

set -e

echo "🚀 开始完整重建 MuseTalk 数字人系统"
echo "=================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. 拉取最新代码
echo -e "${YELLOW}📥 拉取最新代码...${NC}"
cd /opt/musetalk/repo
git pull origin main

# 2. 应用Python服务修复
echo -e "${YELLOW}🔧 应用服务修复...${NC}"
cd MuseTalkEngine
if [ -f "fix_ultra_fast_service.py" ]; then
    python3 fix_ultra_fast_service.py
    echo -e "${GREEN}✅ 服务修复已应用${NC}"
else
    echo -e "${RED}⚠️ 修复脚本不存在，跳过${NC}"
fi
cd ..

# 3. 清理旧容器和镜像
echo -e "${YELLOW}🧹 清理旧容器...${NC}"
docker compose down || true
docker rm -f musetalk-python lmy-digitalhuman 2>/dev/null || true

# 4. 清理模板数据
echo -e "${YELLOW}🗑️ 清理模板数据...${NC}"
rm -rf /opt/musetalk/repo/LmyDigitalHuman/wwwroot/templates/*
rm -rf /opt/musetalk/models/templates/*
rm -rf /opt/musetalk/temp/templates/*
echo -e "${GREEN}✅ 模板数据已清理${NC}"

# 5. 构建 musetalk-python
echo -e "${YELLOW}🔨 构建 musetalk-python (预计14分钟)...${NC}"
START_TIME=$(date +%s)
docker compose build musetalk-python
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))
echo -e "${GREEN}✅ musetalk-python 构建完成 (耗时: ${DURATION}秒)${NC}"

# 6. 并行拉取.NET镜像
echo -e "${YELLOW}📦 拉取.NET镜像...${NC}"
(
    for i in {1..5}; do
        docker pull mcr.microsoft.com/dotnet/sdk:8.0 && break
        echo "重试 $i/5..."
        sleep 30
    done
) &
PID1=$!

(
    for i in {1..5}; do
        docker pull mcr.microsoft.com/dotnet/aspnet:8.0 && break
        echo "重试 $i/5..."
        sleep 30
    done
) &
PID2=$!

wait $PID1 $PID2
echo -e "${GREEN}✅ .NET镜像拉取完成${NC}"

# 7. 构建 lmy-digitalhuman  
echo -e "${YELLOW}🔨 构建 lmy-digitalhuman...${NC}"
docker compose build lmy-digitalhuman
echo -e "${GREEN}✅ lmy-digitalhuman 构建完成${NC}"

# 8. 启动所有服务
echo -e "${YELLOW}🚀 启动服务...${NC}"
docker compose up -d

# 9. 等待服务就绪
echo -e "${YELLOW}⏳ 等待服务就绪...${NC}"
for i in {1..15}; do
    echo -n "."
    sleep 1
done
echo ""

# 10. 检查服务状态
echo -e "${YELLOW}✅ 检查服务状态...${NC}"
echo ""
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "NAME|musetalk|lmy"

# 11. 显示日志
echo ""
echo -e "${YELLOW}📊 服务日志:${NC}"
echo "---musetalk-python---"
docker logs musetalk-python --tail 5 2>&1 | grep -E "(成功|就绪|失败|Error)" || echo "服务启动中..."
echo ""
echo "---lmy-digitalhuman---"
docker logs lmy-digitalhuman --tail 5 2>&1 | grep -E "(started|listening|error)" || echo "服务启动中..."

# 12. 测试连接
echo ""
echo -e "${YELLOW}🔍 测试服务连接...${NC}"
sleep 5

# 测试健康检查
if curl -s http://localhost:5000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ lmy-digitalhuman 服务正常${NC}"
else
    echo -e "${RED}❌ lmy-digitalhuman 服务未响应${NC}"
fi

# 获取IP地址
IP=$(hostname -I | awk '{print $1}')

echo ""
echo "=================================="
echo -e "${GREEN}✅ 重建完成!${NC}"
echo ""
echo -e "${YELLOW}🌐 访问地址:${NC}"
echo "  主界面: http://${IP}:5000/digital-human-test.html"
echo "  WebRTC: http://${IP}:5000/webrtc-test.html"
echo ""
echo -e "${YELLOW}📝 常用命令:${NC}"
echo "  查看日志: docker logs -f musetalk-python"
echo "  查看日志: docker logs -f lmy-digitalhuman"
echo "  重启服务: docker compose restart"
echo "  停止服务: docker compose down"
echo ""
echo "=================================="