#!/bin/bash
echo "=== 检查Docker服务状态 ==="
echo "1. 检查容器状态："
docker ps -a | grep musetalk-python

echo -e "\n2. 检查容器日志（最后20行）："
docker logs --tail=20 musetalk-python 2>&1

echo -e "\n3. 检查容器是否在重启循环："
docker inspect musetalk-python --format='{{.State.Status}} - RestartCount: {{.RestartCount}}'

echo -e "\n4. 检查端口占用："
netstat -tlnp | grep -E "28888|8766" || echo "端口未被占用"

echo -e "\n5. 尝试停止并重新启动："
docker stop musetalk-python
sleep 2
docker start musetalk-python
sleep 3
docker ps | grep musetalk-python

echo -e "\n6. 再次查看日志："
docker logs --tail=10 musetalk-python 2>&1
