#!/bin/bash

echo "🔧 修复模型路径..."

# 在容器内创建软链接
docker exec musetalk-python bash -c "
    # 如果/opt/musetalk/repo/MuseTalk/models不存在或不是链接，创建链接
    if [ ! -L /opt/musetalk/repo/MuseTalk/models ]; then
        rm -rf /opt/musetalk/repo/MuseTalk/models
        ln -s /opt/musetalk/models /opt/musetalk/repo/MuseTalk/models
        echo '✅ 创建MuseTalk模型软链接'
    fi
    
    # 如果当前目录下没有models，也创建链接
    cd /opt/musetalk/repo/MuseTalkEngine
    if [ ! -L ./models ]; then
        rm -rf ./models
        ln -s /opt/musetalk/models ./models
        echo '✅ 创建MuseTalkEngine模型软链接'
    fi
    
    # 检查sd-vae
    if [ -d /opt/musetalk/models/sd-vae ]; then
        echo '✅ sd-vae模型目录存在'
        ls -la /opt/musetalk/models/sd-vae/ | head -5
    else
        echo '❌ sd-vae模型目录不存在'
    fi
    
    # 检查musetalk模型
    if [ -d /opt/musetalk/models/musetalk ]; then
        echo '✅ musetalk模型目录存在'
        ls -la /opt/musetalk/models/musetalk/ | head -5
    else
        echo '❌ musetalk模型目录不存在'
    fi
"

echo "🔄 拉取最新代码..."
cd /opt/musetalk/repo && git pull origin main

echo "🔄 重启容器..."
docker compose restart musetalk-python

echo "✅ 完成！等待服务启动..."
sleep 5

echo "📋 查看日志..."
docker compose logs --tail=50 musetalk-python