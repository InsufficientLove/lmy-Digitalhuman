# 🎭 MuseTalk 数字人系统

基于 MuseTalk 的实时数字人对话系统，Docker 一键部署。

## 🚀 快速开始

### 1. 启动服务
```bash
docker-compose up -d
```

### 2. 创建模板
```bash
# 准备一张清晰的人脸照片（JPG/PNG，512x512以上）
./create_template.sh default your_photo.jpg
```

### 3. 访问系统
```
http://192.168.20.250:5000
```

---

## 📦 系统架构

| 容器 | 端口 | 作用 |
|-----|------|------|
| traefik | 80/443 | 反向代理 + HTTPS |
| musetalk-python | 28888/8766 | Python 推理引擎（GPU 0,1） |
| lmy-digitalhuman | 5000 | C# Web 前端 |

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

### 模板管理
```bash
# 创建图片模板
./create_template.sh <模板ID> <图片路径>

# 创建视频模板（高级）
./create_video_template.sh <模板ID> <视频路径>

# 列出模板
docker exec musetalk-python ls /opt/musetalk/template_cache/

# 删除模板
docker exec musetalk-python rm -rf /opt/musetalk/template_cache/<模板ID>/
```

---

## 🧪 测试方法

```bash
# 健康检查
curl http://192.168.20.250:28888/health
curl http://192.168.20.250:5000/health

# 查看容器
docker-compose ps

# 查看GPU
docker exec musetalk-python nvidia-smi

# 查看日志
docker-compose logs -f musetalk-python
```

---

## 📝 模板要求

### 图片模板（推荐）
- ✅ 格式：JPG、PNG
- ✅ 分辨率：≥512x512 像素
- ✅ 内容：清晰正面人脸
- ✅ 光线：均匀充足
- ❌ 避免：侧脸、遮挡、多人、模糊

### 视频模板（可选）
- ✅ 格式：MP4
- ✅ 分辨率：≥512x512
- ✅ 帧率：25fps
- ✅ 时长：3-10 秒
- ✅ 内容：正面视频

---

## 🔧 常见问题

### Q: 为什么 127.0.0.1:5000 无法访问？
**A**: 使用内网IP访问
```
http://192.168.20.250:5000  ✅ 正确
http://127.0.0.1:5000      ❌ 无法访问
```

### Q: 如何创建初始模板？
**A**: 运行一键脚本
```bash
./create_template.sh default photo.jpg
```

### Q: 显存不足怎么办？
**A**: 重启 Python 容器
```bash
docker-compose restart musetalk-python
```

### Q: 服务无响应怎么办？
**A**: 查看日志排查
```bash
docker-compose logs --tail 50 musetalk-python
docker-compose logs --tail 50 lmy-digitalhuman
```

---

## 🔒 HTTPS 配置（可选）

```bash
# 1. 创建环境变量
cat > .env << EOF
DOMAIN=your-domain.com
ACME_EMAIL=your-email@example.com
EOF

# 2. 重启服务
docker-compose down
docker-compose up -d

# 3. 访问
https://your-domain.com
```

---

## 📊 API 使用示例

### 预处理模板
```bash
curl -X POST "http://192.168.20.250:28888/api/preprocess_template" \
  -H "Content-Type: application/json" \
  -d '{"template_id": "john", "image_path": "/app/wwwroot/templates/john.jpg"}'
```

### 创建会话
```bash
curl -X POST "http://192.168.20.250:28888/api/start_session" \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test001", "template_id": "default"}'
```

### 处理音频
```bash
curl -X POST "http://192.168.20.250:28888/api/process_segment" \
  -F "session_id=test001" \
  -F "segment_index=0" \
  -F "audio=@input.wav"
```

### 结束会话
```bash
curl -X POST "http://192.168.20.250:28888/api/end_session" \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test001"}'
```

---

## 🗂️ 重要路径

### 宿主机
```
/opt/musetalk/models          # 模型文件
/opt/musetalk/template_cache  # 模板缓存
/opt/musetalk/templates       # 模板图片
/opt/musetalk/videos          # 生成的视频
```

### 容器内
```
# Python 容器
/opt/musetalk/template_cache  # 模板缓存
/videos                       # 视频目录

# C# 容器
/app/wwwroot/templates        # 模板图片
/videos                       # 视频目录
```

---

## 🏗️ 项目结构

```
/workspace/
├── docker-compose.yml          # Docker 编排配置
├── LmyDigitalHuman/            # C# Web 前端
│   └── Dockerfile
├── MuseTalkEngine/             # Python 推理引擎
│   ├── Dockerfile
│   ├── streaming/              # 流式处理
│   └── core/                   # 核心功能
├── create_template.sh          # 创建图片模板
├── create_video_template.sh    # 创建视频模板
└── README.md                   # 本文档
```

---

## 💡 高级技巧

### 批量创建模板
```bash
for photo in photos/*.jpg; do
    name=$(basename "$photo" .jpg)
    ./create_template.sh "$name" "$photo"
done
```

### 自动备份
```bash
tar -czf backup_$(date +%Y%m%d).tar.gz \
  /opt/musetalk/template_cache \
  /opt/musetalk/videos
```

### 监控资源
```bash
# 容器资源
docker stats

# GPU 监控
watch -n 1 nvidia-smi

# 磁盘占用
du -sh /opt/musetalk/*
```

---

## 🆘 故障排查

### 完全重启
```bash
docker-compose down
docker-compose up -d
docker-compose logs -f
```

### 重建容器
```bash
docker-compose down
docker-compose up -d --build --force-recreate
```

### 查看详细状态
```bash
# 容器状态
docker-compose ps

# GPU 状态  
docker exec musetalk-python nvidia-smi

# Python 服务日志
docker logs musetalk-python --tail 100

# C# 服务日志
docker logs lmy-digitalhuman --tail 100
```

---

## 📄 许可证

基于 [MuseTalk](https://github.com/TMElyralab/MuseTalk) 开发。

---

**快速开始**: 
```bash
docker-compose up -d
./create_template.sh default photo.jpg
# 访问 http://192.168.20.250:5000
```

🎉 **祝使用愉快！**
