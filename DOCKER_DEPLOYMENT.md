# 🐳 Docker 部署指南

## 前置要求

### 1. 安装 Docker
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
```

### 2. 安装 NVIDIA Container Toolkit
```bash
# 添加仓库
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
    sudo tee /etc/apt/sources.list.d/nvidia-docker.list

# 安装
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit

# 重启 Docker
sudo systemctl restart docker
```

### 3. 验证 GPU 可用
```bash
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi
```

---

## 快速部署

### 方法 1：Docker Compose（推荐）

```bash
cd /opt/musetalk/repo

# 构建并启动
docker-compose -f docker-compose-musetalk.yml up -d

# 查看日志
docker-compose -f docker-compose-musetalk.yml logs -f

# 停止
docker-compose -f docker-compose-musetalk.yml down
```

### 方法 2：Docker 命令

```bash
cd /opt/musetalk/repo

# 构建镜像
docker build -t musetalk:latest -f Dockerfile.musetalk .

# 运行容器
docker run -d \
  --name musetalk-realtime \
  --gpus '"device=1"' \
  -p 8888:8888 \
  -v /opt/musetalk/models:/models:ro \
  -v /opt/musetalk/assets:/app/assets:rw \
  -e PORT=8888 \
  -e GPU_ID=1 \
  -e WHISPER_MODEL_PATH=/models/whisper \
  musetalk:latest

# 查看日志
docker logs -f musetalk-realtime

# 停止
docker stop musetalk-realtime
docker rm musetalk-realtime
```

---

## 配置说明

### 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `PORT` | 8000 | 服务端口 |
| `GPU_ID` | 1 | 使用的 GPU 编号 |
| `WHISPER_MODEL_PATH` | `/models/whisper` | Whisper 模型路径 |
| `MUSE_TALK_DIR` | `/app/MuseTalk` | MuseTalk 源码路径 |

### 挂载卷

- `/opt/musetalk/models` → `/models` (只读)
  - 模型文件
- `/opt/musetalk/assets` → `/app/assets` (读写)
  - 视频资产、预处理结果

---

## 测试

```bash
# 健康检查
curl http://192.168.20.250:8888/health

# 查看 API 文档
# 浏览器访问：http://192.168.20.250:8888/docs
```

---

## 故障排查

### 1. GPU 不可用
```bash
# 检查容器内 GPU
docker exec musetalk-realtime nvidia-smi
```

### 2. 查看详细日志
```bash
docker logs musetalk-realtime --tail 100
```

### 3. 进入容器调试
```bash
docker exec -it musetalk-realtime bash
```

---

## 优势

✅ **无需安装运行时**：Docker 镜像包含所有依赖  
✅ **环境隔离**：不污染宿主机  
✅ **一键部署**：`docker-compose up -d`  
✅ **易于扩展**：支持多副本、负载均衡  
✅ **版本管理**：镜像标签管理版本  

---

## 下一步

- [ ] 构建镜像
- [ ] 启动服务
- [ ] 测试 API
- [ ] 部署前端（可选）
