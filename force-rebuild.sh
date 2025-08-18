#!/bin/bash

echo "========================================="
echo "强制完全重建 LmyDigitalHuman"
echo "========================================="

# 确保在正确的目录
cd /opt/musetalk/repo

echo ""
echo "1. 拉取最新代码..."
git pull origin main

echo ""
echo "2. 停止并删除容器..."
docker stop lmy-digitalhuman 2>/dev/null || true
docker rm lmy-digitalhuman 2>/dev/null || true

echo ""
echo "3. 删除旧镜像..."
# 获取所有相关镜像ID并删除
docker images | grep lmy-digitalhuman | awk '{print $3}' | xargs -r docker rmi -f 2>/dev/null || true
docker images | grep "^<none>" | awk '{print $3}' | xargs -r docker rmi -f 2>/dev/null || true

echo ""
echo "4. 清理Docker构建缓存..."
docker builder prune -af
docker system prune -f

echo ""
echo "5. 验证最新代码（Program.cs应该包含IPathManager）..."
grep "IPathManager" LmyDigitalHuman/Program.cs || echo "警告：代码可能未更新！"

echo ""
echo "6. 构建新镜像（完全不使用缓存）..."
# 使用时间戳强制不使用缓存
export DOCKER_BUILDKIT=0
docker-compose -f docker-compose.yml -f docker-compose.local.yml build --no-cache --pull lmy-digitalhuman

echo ""
echo "7. 启动新容器..."
docker-compose -f docker-compose.yml -f docker-compose.local.yml up -d lmy-digitalhuman

echo ""
echo "8. 等待容器启动..."
sleep 5

echo ""
echo "9. 验证容器内的代码版本..."
echo "检查Program.cs是否包含IPathManager注册："
docker exec lmy-digitalhuman grep -n "IPathManager" /app/Program.cs 2>/dev/null || echo "无法在容器内找到Program.cs"

echo ""
echo "10. 显示容器日志..."
docker logs --tail 30 lmy-digitalhuman

echo ""
echo "========================================="
echo "重建完成！"
echo "========================================="
echo ""
echo "测试命令："
echo "  curl http://localhost:5000/health"
echo "  docker logs -f lmy-digitalhuman"
echo ""
echo "如果还有问题，请运行："
echo "  docker exec lmy-digitalhuman cat /app/Program.cs | grep -A5 -B5 PathManager"