# MuseTalk Docker快速部署指南

## 🚀 快速开始（5分钟部署）

### 1. 前置要求

- Linux服务器（Ubuntu 20.04/22.04 推荐）
- NVIDIA GPU（支持CUDA 11.8+）
- Docker 20.10+
- NVIDIA Container Toolkit

### 2. 一键部署

```bash
# 克隆项目
git clone <your-repo-url>
cd musetalk-docker

# 赋予执行权限
chmod +x deploy.sh

# 初始化环境并部署
./deploy.sh setup
./deploy.sh build
./deploy.sh deploy
```

就这么简单！服务已经在运行了。

### 3. 验证部署

```bash
# 查看服务状态
./deploy.sh status

# 运行快速测试
./deploy.sh test

# 查看日志
./deploy.sh logs -f
```

---

## 📦 Docker镜像说明

### 镜像特性

- **完整的Python环境**：包含所有必需的Python包和依赖
- **预装PyTorch**：支持CUDA 11.8，优化的深度学习环境
- **自动模型下载**：首次启动时自动下载所需模型
- **多运行模式**：支持推理、API、Web界面等多种模式
- **健康检查**：内置健康检查，确保服务稳定运行

### 镜像大小

- 基础镜像：约8GB
- 包含模型：约15GB（模型会自动下载到持久卷）

---

## 🔧 配置说明

### 环境变量配置

编辑 `.env` 文件来配置服务：

```bash
# GPU配置
CUDA_VISIBLE_DEVICES=0,1,2,3  # 使用哪些GPU
GPU_CONFIG_MODE=auto           # auto/single_gpu/multi_gpu
BATCH_SIZE_PER_GPU=8          # 每个GPU的批处理大小

# 运行模式
RUN_MODE=inference             # inference/benchmark/gradio/api

# 性能优化
ENABLE_AMP=true               # 启用混合精度
ENABLE_CUDNN_BENCHMARK=true   # CuDNN优化

# 服务端口
API_PORT=8000                 # API服务端口
WEB_PORT=7860                 # Web界面端口
```

### 运行模式

Docker容器支持多种运行模式：

1. **推理模式**（默认）
```bash
docker run --rm --runtime=nvidia --gpus all \
  -e RUN_MODE=inference \
  musetalk:gpu-latest
```

2. **Gradio Web界面**
```bash
docker run -d --runtime=nvidia --gpus all \
  -e RUN_MODE=gradio \
  -p 7860:7860 \
  musetalk:gpu-latest
```

3. **API服务**
```bash
docker run -d --runtime=nvidia --gpus all \
  -e RUN_MODE=api \
  -p 8000:8000 \
  musetalk:gpu-latest
```

4. **交互式Shell**
```bash
docker run -it --runtime=nvidia --gpus all \
  -e RUN_MODE=shell \
  musetalk:gpu-latest
```

---

## 🖥️ 多服务器部署

### 方法1：使用Docker Hub

```bash
# 在第一台服务器上构建并推送
./deploy.sh build
docker tag musetalk:gpu-latest your-dockerhub/musetalk:gpu-latest
docker push your-dockerhub/musetalk:gpu-latest

# 在其他服务器上拉取并运行
docker pull your-dockerhub/musetalk:gpu-latest
docker-compose -f docker-compose.gpu.yml up -d
```

### 方法2：使用私有Registry

```bash
# 启动私有Registry
docker run -d -p 5000:5000 --name registry registry:2

# 标记并推送
docker tag musetalk:gpu-latest localhost:5000/musetalk:gpu-latest
docker push localhost:5000/musetalk:gpu-latest

# 在其他服务器上
docker pull <registry-server>:5000/musetalk:gpu-latest
```

### 方法3：导出镜像文件

```bash
# 导出镜像
docker save musetalk:gpu-latest | gzip > musetalk-gpu.tar.gz

# 传输到其他服务器
scp musetalk-gpu.tar.gz user@server:/path/

# 在目标服务器导入
docker load < musetalk-gpu.tar.gz
```

---

## 📊 性能测试

### 单GPU测试（RTX 4090D 48GB）

```bash
docker run --rm --runtime=nvidia --gpus '"device=0"' \
  -e GPU_CONFIG_MODE=single_gpu \
  -e BATCH_SIZE_PER_GPU=20 \
  musetalk:gpu-latest \
  python /app/benchmark_gpu.py --config single_4090d_48gb
```

### 多GPU测试（4x RTX 4090 24GB）

```bash
docker run --rm --runtime=nvidia --gpus all \
  -e CUDA_VISIBLE_DEVICES=0,1,2,3 \
  -e GPU_CONFIG_MODE=multi_gpu \
  -e BATCH_SIZE_PER_GPU=8 \
  musetalk:gpu-latest \
  python /app/benchmark_gpu.py --config quad_4090_24gb
```

### 性能监控

```bash
# 启动监控服务
./deploy.sh monitor

# 访问监控面板
# Grafana: http://localhost:3000 (admin/admin)
# Prometheus: http://localhost:9091
```

---

## 🔍 故障排除

### 1. Docker无法访问GPU

```bash
# 检查NVIDIA运行时
docker info | grep nvidia

# 测试GPU访问
docker run --rm --runtime=nvidia --gpus all \
  nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

### 2. 模型下载失败

```bash
# 手动下载模型
docker exec -it musetalk-gpu-service python /app/download_models.py

# 或使用国内镜像
docker exec -it musetalk-gpu-service bash
export HF_ENDPOINT=https://hf-mirror.com
python /app/download_models.py
```

### 3. 内存不足

```bash
# 调整批处理大小
echo "BATCH_SIZE_PER_GPU=4" >> .env
./deploy.sh restart

# 清理GPU内存
docker exec musetalk-gpu-service python -c "
import torch
torch.cuda.empty_cache()
"
```

### 4. 容器启动失败

```bash
# 查看详细日志
docker logs musetalk-gpu-service --tail 100

# 进入调试模式
docker run -it --rm --runtime=nvidia --gpus all \
  --entrypoint /bin/bash \
  musetalk:gpu-latest
```

---

## 📈 生产环境部署

### 1. 使用Docker Swarm

```bash
# 初始化Swarm
docker swarm init

# 部署服务
docker stack deploy -c docker-compose.gpu.yml musetalk

# 扩展服务
docker service scale musetalk_gpu=3
```

### 2. 使用Kubernetes

```yaml
# musetalk-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: musetalk-gpu
spec:
  replicas: 2
  selector:
    matchLabels:
      app: musetalk
  template:
    metadata:
      labels:
        app: musetalk
    spec:
      containers:
      - name: musetalk
        image: musetalk:gpu-latest
        resources:
          limits:
            nvidia.com/gpu: 1
```

### 3. 负载均衡

```nginx
# nginx.conf
upstream musetalk_backend {
    server musetalk-gpu-1:8000;
    server musetalk-gpu-2:8000;
    server musetalk-gpu-3:8000;
}

server {
    listen 80;
    location / {
        proxy_pass http://musetalk_backend;
    }
}
```

---

## 🛠️ 维护操作

### 备份和恢复

```bash
# 备份模型和配置
./deploy.sh backup

# 恢复备份
./deploy.sh restore backups/20240101_120000
```

### 更新镜像

```bash
# 拉取最新代码
git pull

# 重新构建镜像
./deploy.sh build --no-cache

# 更新服务
./deploy.sh deploy
```

### 清理资源

```bash
# 停止服务
./deploy.sh stop

# 清理所有容器和卷（谨慎使用）
./deploy.sh clean
```

---

## 📝 常用命令速查

```bash
# 部署管理
./deploy.sh setup          # 初始化环境
./deploy.sh build          # 构建镜像
./deploy.sh deploy         # 部署服务
./deploy.sh start          # 启动服务
./deploy.sh stop           # 停止服务
./deploy.sh restart        # 重启服务
./deploy.sh status         # 查看状态

# 调试和测试
./deploy.sh logs -f        # 查看日志
./deploy.sh shell          # 进入容器
./deploy.sh test           # 运行测试
./deploy.sh benchmark      # 性能测试

# 监控和维护
./deploy.sh monitor        # 启动监控
./deploy.sh backup         # 备份数据
./deploy.sh clean          # 清理资源
```

---

## 🤝 支持

如有问题，请提供以下信息：

1. Docker版本：`docker --version`
2. GPU信息：`nvidia-smi`
3. 错误日志：`./deploy.sh logs --tail 100`
4. 环境配置：`.env`文件内容

---

## 📄 许可证

本项目基于MuseTalk开源项目，请遵守相应的开源协议。