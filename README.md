# 🎭 MuseTalk 数字人系统

基于 MuseTalk 的实时数字人对话系统，支持图片和视频模板，Docker 一键部署，科幻风格 Web 管理界面。

## 🚀 快速开始

### 1. 启动服务
```bash
docker-compose up -d
```

### 2. 访问管理界面
```
# 模板管理系统（推荐）
http://192.168.20.250:8126/template-manager.html

# 主系统界面
http://192.168.20.250:8126
```

### 3. 创建模板
通过 Web 界面上传图片或视频，系统自动完成预处理。

---

## 📦 系统架构

| 容器 | 宿主机端口 | 容器内端口 | 作用 |
|-----|---------|-----------|------|
| traefik | 8122/8123 | 80/443 | 反向代理 + HTTPS |
| musetalk-python | 8124/8125 | 28888/8766 | Python 推理引擎（GPU 0,1） |
| lmy-digitalhuman | 8126 | 5000 | C# Web 前端 |

---

## 🎨 模板管理系统

### ✨ 功能特性
- 🖼️ **双模式支持**: 图片模板 & 视频模板
- 🚀 **拖拽上传**: 支持点击或拖拽文件上传
- 👁️ **实时预览**: 上传前预览图片/视频
- ⚡ **自动预处理**: 后台自动完成 MuseTalk 预处理
- 📊 **统计仪表板**: 查看模板使用情况
- 🎭 **模板测试**: 一键生成测试视频
- 🗑️ **快速删除**: 轻松管理模板

### 🎯 使用步骤
1. 打开 `http://192.168.20.250:8126/template-manager.html`
2. 选择资源类型（图片/视频）
3. 上传文件（支持拖拽）
4. 填写模板信息（中文名、英文名、描述等）
5. 点击"创建模板"，等待自动预处理
6. 在"模板列表"中查看和管理

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

### 容器维护
```bash
# 查看GPU状态
docker exec musetalk-python nvidia-smi

# 查看模板列表
docker exec musetalk-python ls /opt/musetalk/template_cache/

# 查看容器日志
docker logs musetalk-python --tail 100
docker logs lmy-digitalhuman --tail 100

# 重启Python服务（显存不足时）
docker-compose restart musetalk-python
```

---

## 🧪 测试方法

```bash
# 健康检查
curl http://192.168.20.250:8124/health
curl http://192.168.20.250:8126/health

# 查看容器状态
docker-compose ps

# 查看GPU使用
docker exec musetalk-python nvidia-smi

# 实时日志
docker-compose logs -f musetalk-python
```

---

## 📝 模板要求

### 图片模板（推荐用于静态场景）
- ✅ **格式**: JPG、PNG
- ✅ **分辨率**: ≥512x512 像素
- ✅ **内容**: 清晰正面人脸
- ✅ **光线**: 均匀充足
- ✅ **优点**: 预处理快、显存占用低
- ❌ **避免**: 侧脸、遮挡、多人、模糊

### 视频模板（用于动态场景）
- ✅ **格式**: MP4
- ✅ **分辨率**: ≥512x512（推荐 512x512 或 720p）
- ✅ **帧率**: 25fps
- ✅ **时长**: 3-10 秒
- ✅ **内容**: 正面视频，自然表情
- ✅ **优点**: 支持更自然的动态效果
- ⚠️ **注意**: 预处理时间较长（约1-5分钟），显存需求更高

---

## 🔧 常见问题

### Q: 为什么 127.0.0.1:8126 无法访问？
**A**: 使用内网IP访问
```
http://192.168.20.250:8126  ✅ 正确
http://127.0.0.1:8126      ❌ 无法访问
```
**原因**: Docker 容器网络配置，C# 服务监听 `0.0.0.0:5000`，需要通过内网IP访问。

### Q: 如何创建初始模板？
**A**: 通过 Web 界面创建
1. 访问 `http://192.168.20.250:8126/template-manager.html`
2. 上传图片或视频
3. 等待自动预处理完成

### Q: 显存不足怎么办？
**A**: 重启 Python 容器释放显存
```bash
docker-compose restart musetalk-python
```

### Q: 视频预处理失败怎么办？
**A**: 检查以下几点
- 视频分辨率是否 ≥512x512
- 视频时长是否 3-10 秒
- 视频中是否有清晰的正面人脸
- 查看容器日志排查错误
```bash
docker logs musetalk-python --tail 100
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

### 图片模板预处理
```bash
curl -X POST "http://192.168.20.250:8124/api/preprocess_template" \
  -H "Content-Type: application/json" \
  -d '{
    "template_id": "john",
    "image_path": "/app/wwwroot/templates/john.jpg",
    "force": false
  }'
```

### 视频模板预处理
```bash
curl -X POST "http://192.168.20.250:8124/api/preprocess_video" \
  -H "Content-Type: application/json" \
  -d '{
    "template_id": "mary",
    "video_path": "/app/wwwroot/templates/mary.mp4",
    "force": false
  }'
```

### 创建推理会话
```bash
curl -X POST "http://192.168.20.250:8124/api/start_session" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test001",
    "template_id": "john"
  }'
```

### 处理音频生成视频
```bash
curl -X POST "http://192.168.20.250:8124/api/process_segment" \
  -F "session_id=test001" \
  -F "segment_index=0" \
  -F "audio=@input.wav"
```

### 结束会话
```bash
curl -X POST "http://192.168.20.250:8124/api/end_session" \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test001"}'
```

---

## 🗂️ 重要路径

### 宿主机
```
/opt/musetalk/models          # 模型文件（需提前下载）
/opt/musetalk/template_cache  # 模板预处理缓存
/opt/musetalk/templates       # 用户上传的模板文件
/opt/musetalk/videos          # 生成的视频
/opt/musetalk/preprocessed    # 视频模板bbox文件
```

### 容器内
```
# Python 容器 (musetalk-python)
/opt/musetalk/template_cache  # 模板缓存（挂载）
/opt/musetalk/preprocessed    # 视频bbox文件（挂载）
/videos                       # 视频目录（挂载）

# C# 容器 (lmy-digitalhuman)
/app/wwwroot/templates        # 模板文件（挂载自 /opt/musetalk/templates）
/videos                       # 视频目录（挂载自 /opt/musetalk/videos）
```

---

## 🏗️ 项目结构

```
/workspace/
├── docker-compose.yml                    # Docker 编排配置
├── LmyDigitalHuman/                      # C# Web 前端
│   ├── Dockerfile
│   ├── Controllers/
│   │   └── DigitalHumanTemplateController.cs  # 模板管理API
│   ├── Services/
│   │   ├── Core/
│   │   │   └── DigitalHumanTemplateService.cs # 模板业务逻辑
│   │   └── Offline/
│   │       ├── OptimizedMuseTalkService.cs    # MuseTalk服务实现
│   │       └── MuseTalkApiClient.cs           # HTTP API客户端
│   ├── Models/
│   │   └── UnifiedModels.cs                   # 统一数据模型
│   └── wwwroot/
│       ├── template-manager.html              # 模板管理界面 🎨
│       └── js/
│           └── template-manager.js            # 前端交互逻辑
├── MuseTalkEngine/                       # Python 推理引擎
│   ├── Dockerfile
│   ├── streaming/
│   │   └── api_service.py                    # FastAPI服务 🐍
│   ├── core/
│   │   ├── preprocessing.py                  # 图片预处理
│   │   ├── gpu_inference_pool.py             # GPU推理池
│   │   └── template_manager.py               # 模板管理
│   └── preprocess_assets.py                  # 视频预处理脚本
└── README.md                                  # 本文档
```

---

## 💡 高级技巧

### 批量导入模板
通过 Web 界面逐个上传，或使用 API 批量处理：

```bash
# 批量预处理图片模板
for photo in /path/to/photos/*.jpg; do
    name=$(basename "$photo" .jpg)
    docker cp "$photo" lmy-digitalhuman:/app/wwwroot/templates/${name}.jpg
    curl -X POST "http://192.168.20.250:8124/api/preprocess_template" \
      -H "Content-Type: application/json" \
      -d "{\"template_id\": \"${name}\", \"image_path\": \"/app/wwwroot/templates/${name}.jpg\"}"
done
```

### 自动备份
```bash
tar -czf backup_$(date +%Y%m%d).tar.gz \
  /opt/musetalk/template_cache \
  /opt/musetalk/videos \
  /opt/musetalk/templates
```

### 监控资源
```bash
# 容器资源
docker stats

# GPU 监控
watch -n 1 'docker exec musetalk-python nvidia-smi'

# 磁盘占用
du -sh /opt/musetalk/*
```

### 性能优化
```bash
# 1. 清理旧视频（释放磁盘空间）
find /opt/musetalk/videos -name "*.mp4" -mtime +7 -delete

# 2. 清理失败的模板缓存
docker exec musetalk-python python -c "
import os, shutil
cache_dir = '/opt/musetalk/template_cache'
for d in os.listdir(cache_dir):
    pkl_file = os.path.join(cache_dir, d, f'{d}_preprocessed.pkl')
    if not os.path.exists(pkl_file):
        shutil.rmtree(os.path.join(cache_dir, d))
        print(f'Deleted incomplete cache: {d}')
"

# 3. 定期重启Python容器（释放显存）
docker-compose restart musetalk-python
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
docker logs musetalk-python --tail 100 -f

# C# 服务日志
docker logs lmy-digitalhuman --tail 100 -f

# 进入容器调试
docker exec -it musetalk-python bash
docker exec -it lmy-digitalhuman bash
```

### 数据库/缓存问题
```bash
# 清除模板缓存
docker exec musetalk-python rm -rf /opt/musetalk/template_cache/*

# 清除生成的视频
docker exec lmy-digitalhuman rm -rf /videos/*

# 重启服务
docker-compose restart
```

---

## 🎯 系统特性

### 🚀 高性能
- GPU 加速推理（支持双卡并行）
- 模板预处理缓存
- 异步处理队列
- 流式视频生成

### 🎨 科幻风格 UI
- 响应式设计
- 动态背景效果
- 渐变色彩方案
- 流畅动画过渡
- 拖拽上传支持

### 🔧 易于管理
- Web 可视化界面
- 一键创建模板
- 实时预览功能
- 统计信息仪表板
- RESTful API

### 🔒 生产就绪
- Docker 容器化部署
- HTTPS 支持（Traefik）
- 健康检查
- 日志管理
- 自动重启

---

## 📄 许可证

基于 [MuseTalk](https://github.com/TMElyralab/MuseTalk) 开发。

---

## 🎉 快速开始总结

```bash
# 1. 启动服务
docker-compose up -d

# 2. 访问管理界面
# http://192.168.20.250:8126/template-manager.html

# 3. 上传模板（图片或视频）

# 4. 开始使用数字人系统
# http://192.168.20.250:8126
```

**祝使用愉快！** 🎭✨
