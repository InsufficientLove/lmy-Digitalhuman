# 🎭 MuseTalk 数字人系统 - Docker 部署版

基于 MuseTalk 的实时数字人对话系统，支持图片和视频模板，可生成逼真的唇形同步视频。

## 📦 系统架构

```
┌─────────────────────────────────────────────────┐
│                   Traefik                       │  反向代理 + HTTPS
│                  (端口 80/443)                  │
└─────────────────────────────────────────────────┘
                      │
         ┌────────────┴────────────┐
         ▼                         ▼
┌──────────────────┐    ┌──────────────────────┐
│ C# Web Frontend  │    │  Python 推理引擎     │
│  (端口 5000)     │───▶│  (端口 28888/8766)   │
│                  │    │  GPU 0,1 加速        │
└──────────────────┘    └──────────────────────┘
```

## 🚀 快速开始

### 1. 启动所有服务
```bash
cd /workspace
docker-compose up -d
```

### 2. 创建模板（选择一种）

#### 方式 A: 使用图片模板（推荐，最简单）
```bash
# 准备一张清晰的人脸照片
./create_template.sh default my_photo.jpg
```

#### 方式 B: 使用视频模板（高级）
```bash
# 准备一个 3-10 秒的 MP4 视频
./create_video_template.sh idle idle_video.mp4
```

### 3. 访问系统
```
浏览器访问: http://192.168.20.250:5000
```

## 📦 容器信息

| 容器名称 | 作用 | 端口 | GPU |
|---------|------|------|-----|
| **traefik** | 反向代理 + HTTPS | 80, 443 | - |
| **musetalk-python** | Python 推理引擎 | 28888, 8766 | GPU 0,1 |
| **lmy-digitalhuman** | C# Web 前端 | 5000 | - |

## 🧪 测试方法

### 健康检查
```bash
# 测试 Python 服务
curl http://192.168.20.250:28888/health

# 测试 C# 服务
curl http://192.168.20.250:5000/health

# 查看容器状态
docker-compose ps

# 查看 GPU 使用
docker exec musetalk-python nvidia-smi
```

### 查看日志
```bash
# 所有服务日志
docker-compose logs -f

# 特定服务日志
docker-compose logs -f musetalk-python
docker-compose logs -f lmy-digitalhuman
```

## 📚 详细文档

| 文档 | 说明 |
|------|------|
| [DOCKER_USAGE.md](DOCKER_USAGE.md) | Docker 使用指南（容器管理、测试方法） |
| [SETUP_GUIDE.md](SETUP_GUIDE.md) | 完整设置指南（问题解决、API 使用） |
| [CREATE_TEMPLATE_GUIDE.md](CREATE_TEMPLATE_GUIDE.md) | 模板创建详细指南（图片/视频要求） |

## 🛠️ 常用命令

```bash
# 启动服务
docker-compose up -d

# 停止服务
docker-compose stop

# 重启服务
docker-compose restart

# 查看状态
docker-compose ps

# 查看日志
docker-compose logs -f [service-name]

# 进入容器
docker exec -it musetalk-python bash
docker exec -it lmy-digitalhuman bash
```

## 📋 模板管理

### 创建图片模板
```bash
./create_template.sh <模板ID> <图片路径>

# 示例
./create_template.sh john photos/john.jpg
./create_template.sh mary photos/mary.png
```

### 创建视频模板
```bash
./create_video_template.sh <模板ID> <视频路径>

# 示例
./create_video_template.sh idle videos/idle.mp4
./create_video_template.sh smile videos/smile.mp4
```

### 列出模板
```bash
# 列出图片模板
docker exec musetalk-python ls -la /opt/musetalk/template_cache/

# 列出视频资产
curl http://192.168.20.250:28888/assets
```

### 删除模板
```bash
# 删除图片模板
docker exec musetalk-python rm -rf /opt/musetalk/template_cache/<模板ID>/

# 删除视频模板
docker exec musetalk-python rm /videos/<模板ID>.mp4
docker exec musetalk-python rm /opt/musetalk/preprocessed/<模板ID>_bbox.pkl
```

## 🔧 常见问题

### Q1: 为什么 127.0.0.1:5000 无法访问？
**A**: 使用内网 IP 访问：`http://192.168.20.250:5000`

容器配置为监听所有接口（0.0.0.0），在某些系统上本地回环地址无法访问容器服务。

### Q2: 系统需要什么样的初始化文件？
**A**: 需要创建一个数字人模板（图片或视频）

- **推荐**: 使用图片模板，运行 `./create_template.sh default photo.jpg`
- **高级**: 使用视频模板，运行 `./create_video_template.sh idle video.mp4`

详见 [CREATE_TEMPLATE_GUIDE.md](CREATE_TEMPLATE_GUIDE.md)

### Q3: 如何生成数字人视频？
**A**: 三种方式：

1. **Web 界面**: 访问 `http://192.168.20.250:5000`，选择模板，输入文字或上传音频
2. **API 调用**: 见 [SETUP_GUIDE.md](SETUP_GUIDE.md) 的 API 示例
3. **命令行测试**: 
   ```bash
   curl -X POST "http://192.168.20.250:28888/stream" \
     -F "audio=@test.wav" \
     -F "asset_id=default" \
     -o output.mp4
   ```

### Q4: GPU 显存不足怎么办？
**A**: 
```bash
# 1. 查看 GPU 使用情况
docker exec musetalk-python nvidia-smi

# 2. 重启容器释放显存
docker-compose restart musetalk-python

# 3. 调整配置（如果问题持续）
# 在 docker-compose.yml 中修改 batch_size 等参数
```

## 🎯 性能优化

### 提升推理速度
- 确保使用 GPU（检查 `nvidia-smi`）
- 使用较小的 batch_size（如果显存充足可增大）
- 使用图片模板而非视频模板（更快）

### 减少显存占用
- 降低 batch_size
- 使用 FP16 精度（默认已启用）
- 及时清理不用的模板

## 🔒 生产部署建议

### HTTPS 配置
```bash
# 1. 配置域名和邮箱
echo "DOMAIN=your-domain.com" > .env
echo "ACME_EMAIL=your-email@example.com" >> .env

# 2. 重启服务（Traefik 会自动申请证书）
docker-compose down
docker-compose up -d

# 3. 访问
https://your-domain.com
```

### 备份重要数据
```bash
# 备份模板
tar -czf templates_backup.tar.gz /opt/musetalk/template_cache/
tar -czf videos_backup.tar.gz /opt/musetalk/videos/

# 备份配置
tar -czf config_backup.tar.gz /workspace/docker-compose.yml /workspace/.env
```

## 📊 系统监控

```bash
# 查看容器资源占用
docker stats

# 实时监控 GPU
watch -n 1 nvidia-smi

# 查看磁盘占用
du -sh /opt/musetalk/*
```

## 🆘 故障排查

```bash
# 1. 检查容器状态
docker-compose ps

# 2. 查看日志
docker-compose logs --tail 100 musetalk-python
docker-compose logs --tail 100 lmy-digitalhuman

# 3. 检查 GPU
docker exec musetalk-python nvidia-smi

# 4. 测试服务
curl http://192.168.20.250:28888/health
curl http://192.168.20.250:5000/health

# 5. 进入容器调试
docker exec -it musetalk-python bash
docker exec -it lmy-digitalhuman bash
```

如果问题无法解决，请提供上述命令的输出结果。

## 🏗️ 项目结构

```
/workspace/
├── docker-compose.yml          # Docker 编排配置
├── .dockerignore               # Docker 构建忽略
├── LmyDigitalHuman/            # C# Web 前端
│   ├── Dockerfile              # C# 容器构建文件
│   └── ...
├── MuseTalkEngine/             # Python 推理引擎
│   ├── Dockerfile              # Python 容器构建文件
│   ├── streaming/              # 流式处理模块
│   ├── core/                   # 核心功能
│   └── ...
├── create_template.sh          # 图片模板创建脚本
├── create_video_template.sh    # 视频模板创建脚本
├── DOCKER_USAGE.md             # Docker 使用指南
├── SETUP_GUIDE.md              # 完整设置指南
├── CREATE_TEMPLATE_GUIDE.md    # 模板创建指南
└── README.md                   # 本文档
```

## 📄 许可证

请参考原项目许可证。

## 🙏 致谢

本项目基于 [MuseTalk](https://github.com/TMElyralab/MuseTalk) 开发。

---

## 🎉 开始使用

```bash
# 1. 启动服务
docker-compose up -d

# 2. 创建模板
./create_template.sh default my_photo.jpg

# 3. 访问系统
# 浏览器打开: http://192.168.20.250:5000

# 4. 开始创作！
```

**祝您使用愉快！如有问题，请查看详细文档或提交 Issue。** 🚀
