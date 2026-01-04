# ⚡ MuseTalk 快速参考

## 🎯 核心信息

**访问地址**: `http://192.168.20.250:5000`  
**Python API**: `http://192.168.20.250:28888`  
**WebSocket**: `ws://192.168.20.250:8766`

---

## 🚀 5 分钟快速上手

```bash
# 1. 启动服务
docker-compose up -d

# 2. 创建模板（准备一张人脸照片）
./create_template.sh default photo.jpg

# 3. 浏览器访问
http://192.168.20.250:5000

# 完成！开始使用
```

---

## 📦 容器速查

| 容器 | 端口 | 命令 |
|-----|------|------|
| traefik | 80/443 | `docker logs traefik` |
| musetalk-python | 28888/8766 | `docker logs musetalk-python` |
| lmy-digitalhuman | 5000 | `docker logs lmy-digitalhuman` |

---

## 🛠️ 常用命令

### 服务管理
```bash
docker-compose up -d      # 启动
docker-compose stop       # 停止
docker-compose restart    # 重启
docker-compose ps         # 状态
docker-compose logs -f    # 日志
```

### 测试服务
```bash
# Python API
curl http://192.168.20.250:28888/health

# C# Web
curl http://192.168.20.250:5000/health

# GPU 状态
docker exec musetalk-python nvidia-smi
```

### 模板管理
```bash
# 创建图片模板
./create_template.sh <ID> <图片>

# 创建视频模板
./create_video_template.sh <ID> <视频>

# 列出模板
docker exec musetalk-python ls /opt/musetalk/template_cache/

# 删除模板
docker exec musetalk-python rm -rf /opt/musetalk/template_cache/<ID>/
```

---

## 🐛 快速故障排查

### 问题：无法访问 5000 端口
```bash
# 使用内网 IP 而非 127.0.0.1
http://192.168.20.250:5000  ✅
http://127.0.0.1:5000       ❌
```

### 问题：服务无响应
```bash
# 1. 检查容器状态
docker-compose ps

# 2. 查看错误日志
docker-compose logs --tail 50 musetalk-python
docker-compose logs --tail 50 lmy-digitalhuman

# 3. 重启服务
docker-compose restart
```

### 问题：GPU 不可用
```bash
# 检查 GPU
docker exec musetalk-python nvidia-smi

# 如果失败，重启 Docker
sudo systemctl restart docker
docker-compose up -d
```

### 问题：显存不足
```bash
# 重启 Python 容器释放显存
docker-compose restart musetalk-python

# 查看显存使用
docker exec musetalk-python nvidia-smi
```

---

## 📝 API 快速示例

### 预处理模板
```bash
curl -X POST "http://192.168.20.250:28888/api/preprocess_template" \
  -H "Content-Type: application/json" \
  -d '{
    "template_id": "john",
    "image_path": "/app/wwwroot/templates/john.jpg"
  }'
```

### 创建会话
```bash
curl -X POST "http://192.168.20.250:28888/api/start_session" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "session001",
    "template_id": "default"
  }'
```

### 处理音频
```bash
curl -X POST "http://192.168.20.250:28888/api/process_segment" \
  -F "session_id=session001" \
  -F "segment_index=0" \
  -F "audio=@input.wav"
```

### 结束会话
```bash
curl -X POST "http://192.168.20.250:28888/api/end_session" \
  -H "Content-Type: application/json" \
  -d '{"session_id": "session001"}'
```

---

## 📊 性能监控

```bash
# 容器资源
docker stats

# GPU 实时监控
watch -n 1 nvidia-smi

# 磁盘占用
du -sh /opt/musetalk/*

# 进程监控
htop
```

---

## 🎨 模板要求

### 图片模板
- ✅ 格式：JPG、PNG
- ✅ 分辨率：≥512x512
- ✅ 内容：清晰正面人脸
- ✅ 光线：均匀充足

### 视频模板
- ✅ 格式：MP4
- ✅ 分辨率：≥512x512
- ✅ 帧率：25fps
- ✅ 时长：3-10秒
- ✅ 内容：正面视频

---

## 📚 完整文档

| 文档 | 内容 |
|------|------|
| [README.md](README.md) | 项目概览 |
| [DOCKER_USAGE.md](DOCKER_USAGE.md) | Docker 详细使用 |
| [SETUP_GUIDE.md](SETUP_GUIDE.md) | 完整设置指南 |
| [CREATE_TEMPLATE_GUIDE.md](CREATE_TEMPLATE_GUIDE.md) | 模板创建详解 |

---

## 🔗 重要路径

### 宿主机路径
```
/opt/musetalk/models           # 模型文件
/opt/musetalk/template_cache   # 模板缓存
/opt/musetalk/templates        # 模板图片
/opt/musetalk/videos           # 生成的视频
/opt/musetalk/cache            # 其他缓存
```

### 容器内路径
```
# Python 容器
/opt/musetalk/repo/MuseTalk/models     # 模型
/opt/musetalk/template_cache           # 模板缓存
/videos                                # 视频目录
/temp                                  # 临时文件

# C# 容器
/app/wwwroot/templates                 # 模板图片
/videos                                # 视频目录
```

---

## 💡 专业技巧

### 批量创建模板
```bash
# 批量处理多张照片
for photo in photos/*.jpg; do
    name=$(basename "$photo" .jpg)
    ./create_template.sh "$name" "$photo"
done
```

### 自动备份
```bash
# 创建备份脚本
cat > backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d)
tar -czf backup_${DATE}.tar.gz \
  /opt/musetalk/template_cache \
  /opt/musetalk/videos \
  /workspace/docker-compose.yml
EOF

chmod +x backup.sh
```

### 查看系统状态
```bash
# 一键查看所有关键信息
echo "=== 容器状态 ===" && docker-compose ps && \
echo "=== GPU 状态 ===" && docker exec musetalk-python nvidia-smi && \
echo "=== 磁盘占用 ===" && df -h /opt/musetalk && \
echo "=== 模板列表 ===" && docker exec musetalk-python ls /opt/musetalk/template_cache/
```

---

## 🆘 紧急恢复

### 完全重启
```bash
# 停止所有服务
docker-compose down

# 清理悬空镜像（可选）
docker system prune -f

# 重新启动
docker-compose up -d

# 查看日志
docker-compose logs -f
```

### 重建容器
```bash
# 完全重建（保留数据）
docker-compose down
docker-compose up -d --build --force-recreate
```

---

**打印此页作为快速参考！** 📄✨
