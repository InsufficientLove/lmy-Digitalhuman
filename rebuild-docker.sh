#!/bin/bash

echo "========================================="
echo "完全重建 LmyDigitalHuman Docker 镜像"
echo "========================================="

# 停止并删除旧容器
echo "1. 停止旧容器..."
docker compose -f docker-compose.yml -f docker-compose.override.yml down lmy-digitalhuman || true

# 删除旧镜像
echo "2. 删除旧镜像..."
docker rmi $(docker images -q lmy-digitalhuman) 2>/dev/null || true
docker rmi $(docker images -q *lmy-digitalhuman*) 2>/dev/null || true

# 清理Docker构建缓存
echo "3. 清理Docker构建缓存..."
docker builder prune -f

# 拉取最新代码
echo "4. 拉取最新代码..."
git pull origin main

# 检查模型文件
echo "5. 检查Whisper模型文件..."
if [ -f "/opt/musetalk/models/whisper/ggml-large-v3.bin" ]; then
    echo "✓ 找到 ggml-large-v3.bin"
    ls -lh /opt/musetalk/models/whisper/ggml-large-v3.bin
else
    echo "✗ 未找到 ggml-large-v3.bin"
fi

if [ -f "/opt/musetalk/models/whisper/ggml-small.bin" ]; then
    echo "✓ 找到 ggml-small.bin"
    ls -lh /opt/musetalk/models/whisper/ggml-small.bin
else
    echo "✗ 未找到 ggml-small.bin"
fi

# 重新构建镜像（不使用缓存）
echo "6. 重新构建Docker镜像（不使用缓存）..."
docker compose -f docker-compose.yml -f docker-compose.override.yml build --no-cache lmy-digitalhuman

# 启动新容器
echo "7. 启动新容器..."
docker compose -f docker-compose.yml -f docker-compose.override.yml up -d lmy-digitalhuman

# 等待几秒让容器启动
sleep 5

# 查看日志
echo "8. 查看容器日志..."
docker logs --tail 50 lmy-digitalhuman

echo "========================================="
echo "重建完成！"
echo "========================================="
echo ""
echo "查看实时日志："
echo "docker logs -f lmy-digitalhuman"
echo ""
echo "检查容器内的模型目录："
echo "docker exec lmy-digitalhuman ls -la /models/whisper/"