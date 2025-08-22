#!/bin/bash
echo "=== 修复模型路径问题 ==="

# 在容器中创建符号链接
echo "在容器中创建模型符号链接..."

# 方法1: 在工作目录创建models链接
docker exec musetalk-python bash -c "
cd /opt/musetalk/repo
ln -sf /opt/musetalk/models models 2>/dev/null
ls -la models/
"

# 方法2: 在MuseTalk目录创建models链接
docker exec musetalk-python bash -c "
cd /opt/musetalk/repo/MuseTalk
ln -sf /opt/musetalk/models models 2>/dev/null
ls -la models/
"

# 方法3: 在MuseTalkEngine目录创建models链接
docker exec musetalk-python bash -c "
cd /opt/musetalk/repo/MuseTalkEngine
ln -sf /opt/musetalk/models models 2>/dev/null
ls -la models/
"

echo -e "\n检查链接创建结果："
docker exec musetalk-python bash -c "
echo '=== /opt/musetalk/repo/models ==='
ls -la /opt/musetalk/repo/models/ | head -5
echo '=== /opt/musetalk/repo/MuseTalk/models ==='
ls -la /opt/musetalk/repo/MuseTalk/models/ | head -5
echo '=== /opt/musetalk/repo/MuseTalkEngine/models ==='
ls -la /opt/musetalk/repo/MuseTalkEngine/models/ | head -5
"

echo -e "\n重启服务..."
docker restart musetalk-python
sleep 5

echo -e "\n查看日志："
docker logs --tail=30 musetalk-python | grep -E "GPU|模型|初始化"
