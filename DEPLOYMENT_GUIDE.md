# MuseTalk 完整部署流程指南

## 📋 部署流程概览

您需要在服务器上执行以下步骤：

1. **拉取代码** → 2. **构建Docker镜像** → 3. **运行容器** → 4. **测试验证**

---

## 🚀 Step 1: 在服务器上拉取代码

### 方法A: 直接克隆完整项目（推荐）

```bash
# SSH登录到您的服务器
ssh user@your-server

# 创建工作目录
mkdir -p /home/user/musetalk && cd /home/user/musetalk

# 克隆您的项目代码（包含所有配置文件）
git clone <your-repo-url> .

# 赋予脚本执行权限
chmod +x deploy.sh setup_gpu_env.sh
```

### 方法B: 只复制必要文件

如果您只想复制必要的文件到服务器：

```bash
# 在本地打包必要文件
tar czf musetalk-docker.tar.gz \
    Dockerfile.gpu \
    docker-compose.gpu.yml \
    deploy.sh \
    benchmark_gpu.py \
    MuseTalkEngine/ \
    .env.example \
    requirements.txt

# 上传到服务器
scp musetalk-docker.tar.gz user@server:/home/user/

# 在服务器上解压
ssh user@server
tar xzf musetalk-docker.tar.gz
cd musetalk
```

---

## 🐳 Step 2: 构建Docker镜像

### 检查CUDA兼容性

```bash
# 检查服务器CUDA版本
nvidia-smi

# 输出示例：
# CUDA Version: 12.9  ← 您的CUDA版本
```

我们的Docker镜像使用CUDA 12.1，**兼容CUDA 12.9**。

### 构建镜像

```bash
# 方法1: 使用deploy脚本（推荐）
./deploy.sh setup    # 初始化环境
./deploy.sh build    # 构建镜像

# 方法2: 直接使用docker命令
docker build -f Dockerfile.gpu -t musetalk:gpu-latest .
```

构建过程会：
- ✅ 安装Python 3.10环境
- ✅ 安装PyTorch 2.2.0 (CUDA 12.1)
- ✅ 安装所有依赖包
- ✅ 配置GPU支持

---

## 🏃 Step 3: 运行容器

### 配置环境变量

```bash
# 复制并编辑配置文件
cp .env.example .env
vim .env

# 关键配置：
CUDA_VISIBLE_DEVICES=0,1,2,3  # 根据实际GPU调整
BATCH_SIZE_PER_GPU=8          # 根据GPU内存调整
RUN_MODE=shell                 # 首次运行建议用shell模式
AUTO_DOWNLOAD_MODELS=true      # 自动下载模型
```

### 启动容器

#### 选项1: 交互式Shell模式（推荐首次使用）

```bash
# 启动交互式容器
docker run -it --rm \
    --runtime=nvidia \
    --gpus all \
    -v $(pwd):/workspace \
    -e RUN_MODE=shell \
    musetalk:gpu-latest

# 在容器内：
# 1. 克隆MuseTalk代码
git clone https://github.com/TMElyralab/MuseTalk.git

# 2. 下载模型
python /app/download_models.py

# 3. 测试GPU
python -c "import torch; print(f'GPUs: {torch.cuda.device_count()}')"

# 4. 运行测试
python /workspace/benchmark_gpu.py --config auto
```

#### 选项2: 使用Docker Compose（生产环境）

```bash
# 启动所有服务
docker-compose -f docker-compose.gpu.yml up -d

# 查看日志
docker-compose -f docker-compose.gpu.yml logs -f

# 进入容器
docker exec -it musetalk-gpu-service bash
```

#### 选项3: 直接运行测试

```bash
# 运行性能测试
docker run --rm \
    --runtime=nvidia \
    --gpus all \
    -v $(pwd):/workspace \
    -e RUN_MODE=benchmark \
    -e GPU_CONFIG=auto \
    musetalk:gpu-latest
```

---

## 🧪 Step 4: 测试验证

### 1. 验证GPU访问

```bash
# 测试Docker GPU支持
docker run --rm --runtime=nvidia --gpus all \
    nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi

# 在容器内测试PyTorch GPU
docker run --rm --runtime=nvidia --gpus all \
    musetalk:gpu-latest \
    python -c "
import torch
print(f'CUDA Available: {torch.cuda.is_available()}')
print(f'CUDA Version: {torch.version.cuda}')
print(f'GPU Count: {torch.cuda.device_count()}')
for i in range(torch.cuda.device_count()):
    print(f'GPU {i}: {torch.cuda.get_device_name(i)}')
"
```

### 2. 运行基准测试

```bash
# 单GPU测试（RTX 4090D 48GB）
docker run --rm --runtime=nvidia --gpus '"device=0"' \
    -v $(pwd):/workspace \
    -e CUDA_VISIBLE_DEVICES=0 \
    -e BATCH_SIZE_PER_GPU=20 \
    musetalk:gpu-latest \
    python /workspace/benchmark_gpu.py --config single_4090d_48gb

# 多GPU测试（4x RTX 4090 24GB）
docker run --rm --runtime=nvidia --gpus all \
    -v $(pwd):/workspace \
    -e CUDA_VISIBLE_DEVICES=0,1,2,3 \
    -e BATCH_SIZE_PER_GPU=8 \
    musetalk:gpu-latest \
    python /workspace/benchmark_gpu.py --config quad_4090_24gb
```

---

## 📁 文件结构说明

```
服务器目录结构：
/home/user/musetalk/
├── Dockerfile.gpu          # Docker镜像定义
├── docker-compose.gpu.yml  # 服务编排
├── deploy.sh              # 部署脚本
├── .env                   # 环境配置
├── benchmark_gpu.py       # 性能测试
├── MuseTalkEngine/        # 您的引擎代码
│   ├── multi_gpu_parallel_engine.py
│   └── musetalk_realtime_engine.py
├── MuseTalk/              # 官方MuseTalk（容器内克隆）
├── models/                # 模型文件（自动下载）
├── inputs/                # 输入文件
├── outputs/               # 输出结果
└── logs/                  # 日志文件
```

---

## 🔧 常见问题解决

### 问题1: CUDA版本不匹配

```bash
# 错误: CUDA version mismatch
# 解决: 我们的镜像使用CUDA 12.1，向前兼容12.x

# 如果需要其他CUDA版本，修改Dockerfile：
FROM nvidia/cuda:12.9.0-cudnn8-devel-ubuntu22.04  # 使用12.9
```

### 问题2: 模型下载失败

```bash
# 在容器内手动下载
docker exec -it musetalk-gpu-service bash

# 使用中国镜像
export HF_ENDPOINT=https://hf-mirror.com
python /app/download_models.py

# 或手动下载到models目录
cd /app/models
wget https://huggingface.co/TMElyralab/MuseTalk/...
```

### 问题3: GPU不可见

```bash
# 检查NVIDIA运行时
docker info | grep nvidia

# 如果没有，安装nvidia-container-toolkit
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker
```

### 问题4: 内存不足

```bash
# 调整批处理大小
echo "BATCH_SIZE_PER_GPU=4" >> .env

# 重启服务
docker-compose -f docker-compose.gpu.yml restart
```

---

## 🚢 多服务器部署

### 保存镜像

```bash
# 在第一台服务器构建后保存
docker save musetalk:gpu-latest | gzip > musetalk-gpu-cuda12.tar.gz

# 大小约8-10GB
ls -lh musetalk-gpu-cuda12.tar.gz
```

### 传输到其他服务器

```bash
# 方法1: SCP传输
scp musetalk-gpu-cuda12.tar.gz user@server2:/home/user/

# 方法2: 使用rsync（支持断点续传）
rsync -avP musetalk-gpu-cuda12.tar.gz user@server2:/home/user/

# 方法3: 使用私有Registry
docker tag musetalk:gpu-latest your-registry.com/musetalk:gpu-latest
docker push your-registry.com/musetalk:gpu-latest
```

### 在新服务器加载

```bash
# 加载镜像
docker load < musetalk-gpu-cuda12.tar.gz

# 验证
docker images | grep musetalk

# 运行
docker run --rm --runtime=nvidia --gpus all \
    musetalk:gpu-latest \
    python -c "import torch; print(torch.cuda.device_count())"
```

---

## 📊 性能优化建议

### GPU内存优化

```bash
# RTX 4090D 48GB
BATCH_SIZE_PER_GPU=20
GPU_MEMORY_FRACTION=0.95

# RTX 4090 24GB
BATCH_SIZE_PER_GPU=8
GPU_MEMORY_FRACTION=0.9

# RTX 3090 24GB
BATCH_SIZE_PER_GPU=6
GPU_MEMORY_FRACTION=0.85
```

### 并行策略选择

```bash
# 数据并行（推荐）
INFERENCE_MODE=parallel
PARALLEL_STRATEGY=data_parallel

# 负载均衡
PARALLEL_STRATEGY=load_balance

# 轮询分配
PARALLEL_STRATEGY=round_robin
```

---

## ✅ 验证清单

- [ ] Docker已安装并运行
- [ ] NVIDIA Container Toolkit已安装
- [ ] GPU在Docker中可见
- [ ] PyTorch检测到所有GPU
- [ ] 模型文件已下载
- [ ] 基准测试运行成功
- [ ] 日志无错误

---

## 📞 获取帮助

如果遇到问题，请提供：

1. **系统信息**
```bash
nvidia-smi
docker --version
docker info | grep -i runtime
```

2. **错误日志**
```bash
docker logs musetalk-gpu-service --tail 50
```

3. **配置文件**
```bash
cat .env
```

---

## 🎯 快速命令参考

```bash
# 构建镜像
docker build -f Dockerfile.gpu -t musetalk:gpu-latest .

# 运行Shell
docker run -it --rm --runtime=nvidia --gpus all musetalk:gpu-latest

# 运行测试
docker run --rm --runtime=nvidia --gpus all \
    -v $(pwd):/workspace \
    musetalk:gpu-latest \
    python /workspace/benchmark_gpu.py

# 查看GPU使用
docker exec musetalk-gpu-service nvidia-smi

# 清理资源
docker system prune -a
```