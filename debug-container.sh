#!/bin/bash

echo "========================================="
echo "调试 LmyDigitalHuman 容器"
echo "========================================="

echo ""
echo "1. 检查容器内的模型目录："
docker exec lmy-digitalhuman ls -la /models/ 2>/dev/null || echo "容器未运行或目录不存在"

echo ""
echo "2. 检查容器内的 /models/whisper 目录："
docker exec lmy-digitalhuman ls -la /models/whisper/ 2>/dev/null || echo "目录不存在"

echo ""
echo "3. 检查容器内的代码版本（Program.cs的MD5）："
docker exec lmy-digitalhuman md5sum /app/LmyDigitalHuman.dll 2>/dev/null || echo "无法获取"

echo ""
echo "4. 检查容器内的WhisperNetService代码（查看InitializeAsync方法）："
docker exec lmy-digitalhuman cat /src/LmyDigitalHuman/Services/WhisperNetService.cs 2>/dev/null | grep -A 10 "InitializeAsync" | head -20 || echo "源代码不在容器内"

echo ""
echo "5. 检查容器的环境变量："
docker exec lmy-digitalhuman printenv | grep -E "ASPNETCORE|MODEL" || echo "无相关环境变量"

echo ""
echo "6. 检查容器挂载的卷："
docker inspect lmy-digitalhuman | jq '.[0].Mounts' 2>/dev/null || docker inspect lmy-digitalhuman | grep -A 20 '"Mounts"'

echo ""
echo "7. 容器最新日志（最后20行）："
docker logs --tail 20 lmy-digitalhuman 2>&1

echo "========================================="