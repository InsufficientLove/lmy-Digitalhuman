#!/bin/bash

echo "========================================="
echo "直接构建并运行 LmyDigitalHuman（绕过docker-compose缓存）"
echo "========================================="

cd /opt/musetalk/repo

echo "1. 停止旧容器..."
docker stop lmy-digitalhuman 2>/dev/null
docker rm lmy-digitalhuman 2>/dev/null

echo ""
echo "2. 直接构建镜像..."
docker build --no-cache --pull -t lmy-digitalhuman:latest -f LmyDigitalHuman/Dockerfile .

echo ""
echo "3. 运行新容器..."
docker run -d \
  --name lmy-digitalhuman \
  -p 5000:5000 \
  -v /opt/musetalk/models:/models \
  -v /opt/musetalk/videos:/videos \
  -v /opt/musetalk/temp:/temp \
  -e ASPNETCORE_URLS=http://0.0.0.0:5000 \
  -e ASPNETCORE_ENVIRONMENT=Linux \
  --restart unless-stopped \
  lmy-digitalhuman:latest

echo ""
echo "4. 查看日志..."
sleep 3
docker logs --tail 50 lmy-digitalhuman

echo ""
echo "========================================="
echo "容器已启动！"
echo "访问: http://$(hostname -I | awk '{print $1}'):5000/swagger"
echo "========================================="