# MuseTalk GPU并行处理部署指南

## 目录
1. [系统要求](#系统要求)
2. [环境准备](#环境准备)
3. [Docker部署](#docker部署)
4. [性能测试](#性能测试)
5. [故障排除](#故障排除)
6. [优化建议](#优化建议)

---

## 系统要求

### 硬件要求

#### 单GPU配置（RTX 4090D 48GB）
- GPU: 1x NVIDIA RTX 4090D (48GB VRAM)
- CPU: 至少8核心
- RAM: 32GB以上
- 存储: 100GB以上SSD空间

#### 多GPU配置（4x RTX 4090 24GB）
- GPU: 4x NVIDIA RTX 4090 (24GB VRAM each)
- CPU: 至少16核心
- RAM: 64GB以上
- 存储: 200GB以上SSD空间

### 软件要求
- Ubuntu 20.04/22.04 LTS 或 CentOS 7/8
- NVIDIA Driver >= 525.60.13
- Docker >= 20.10
- Docker Compose >= 2.0
- NVIDIA Container Toolkit

---

## 环境准备

### 1. 安装NVIDIA驱动

```bash
# Ubuntu系统
sudo apt update
sudo apt install -y ubuntu-drivers-common
sudo ubuntu-drivers autoinstall
sudo reboot

# 验证安装
nvidia-smi
```

### 2. 安装Docker

```bash
# 卸载旧版本
sudo apt-get remove docker docker-engine docker.io containerd runc

# 安装依赖
sudo apt-get update
sudo apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# 添加Docker官方GPG密钥
sudo mkdir -m 0755 -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# 设置仓库
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 安装Docker
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# 启动Docker
sudo systemctl start docker
sudo systemctl enable docker

# 添加当前用户到docker组
sudo usermod -aG docker $USER
newgrp docker
```

### 3. 安装NVIDIA Container Toolkit

```bash
# 添加仓库
distribution=$(. /etc/os-release;echo $ID$VERSION_ID) \
   && curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add - \
   && curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list

# 安装nvidia-container-toolkit
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit

# 配置Docker
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker

# 测试GPU支持
docker run --rm --runtime=nvidia --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

---

## Docker部署

### 1. 克隆项目

```bash
# 克隆项目
git clone https://github.com/TMElyralab/MuseTalk.git
cd MuseTalk

# 复制配置文件
cp .env.example .env
```

### 2. 配置环境变量

编辑 `.env` 文件：

```bash
# GPU配置
CUDA_VISIBLE_DEVICES=0,1,2,3  # 根据实际GPU数量调整
GPU_CONFIG=multi_gpu           # single_gpu 或 multi_gpu

# 批处理配置
BATCH_SIZE_PER_GPU=8          # 单GPU批次大小
TOTAL_BATCH_SIZE=32            # 总批次大小

# 内存配置
GPU_MEMORY_FRACTION=0.9        # GPU内存使用比例
PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512

# 性能优化
ENABLE_AMP=true                # 启用自动混合精度
ENABLE_CUDNN_BENCHMARK=true    # 启用CuDNN优化
```

### 3. 构建Docker镜像

```bash
# 构建GPU版本镜像
docker build -f Dockerfile.gpu -t musetalk:gpu-latest .

# 或使用docker-compose构建
docker-compose -f docker-compose.gpu.yml build
```

### 4. 启动服务

```bash
# 使用docker-compose启动
docker-compose -f docker-compose.gpu.yml up -d

# 查看日志
docker-compose -f docker-compose.gpu.yml logs -f

# 检查服务状态
docker-compose -f docker-compose.gpu.yml ps
```

---

## 性能测试

### 1. 运行基准测试

#### 单GPU测试（RTX 4090D 48GB）

```bash
# 进入容器
docker exec -it musetalk-gpu-service bash

# 运行基准测试
python benchmark_gpu.py --config single_4090d_48gb

# 快速测试
python benchmark_gpu.py --config single_4090d_48gb --quick
```

#### 多GPU测试（4x RTX 4090 24GB）

```bash
# 进入容器
docker exec -it musetalk-gpu-service bash

# 运行基准测试
python benchmark_gpu.py --config quad_4090_24gb

# 监控GPU使用
watch -n 1 nvidia-smi
```

### 2. 批处理测试

```bash
# 准备测试数据
mkdir -p inputs outputs
# 将测试视频和音频放入inputs目录

# 运行批处理
docker exec -it musetalk-gpu-service python -c "
from MuseTalkEngine.multi_gpu_parallel_engine import MultiGPUParallelEngine, create_gpu_config
from MuseTalkEngine.multi_gpu_parallel_engine import OptimizedBatchProcessor

# 创建配置
config = create_gpu_config(
    gpu_ids=[0, 1, 2, 3],  # 使用4个GPU
    batch_size_per_gpu=8
)

# 创建引擎
engine = MultiGPUParallelEngine(config)

# 创建批处理器
processor = OptimizedBatchProcessor(engine)

# 处理视频
video_paths = ['inputs/video1.mp4', 'inputs/video2.mp4']
audio_paths = ['inputs/audio1.wav', 'inputs/audio2.wav']

results = processor.process_video_batch(video_paths, audio_paths)
print(f'处理完成: {len(results)} 个视频')

# 获取性能报告
report = engine.get_performance_report()
print(report)

# 清理
engine.cleanup()
"
```

### 3. 性能监控

```bash
# 使用Grafana监控（如果已配置）
# 访问 http://localhost:3000
# 默认用户名/密码: admin/admin

# 使用nvidia-smi监控
nvidia-smi dmon -s pucvmet -d 1

# 使用gpustat监控
pip install gpustat
gpustat -cp --watch
```

---

## 故障排除

### 常见问题

#### 1. Docker无法访问GPU

```bash
# 检查nvidia-container-runtime
docker info | grep nvidia

# 重新配置
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

#### 2. CUDA内存不足

```bash
# 清理GPU内存
docker exec musetalk-gpu-service python -c "
import torch
import gc
torch.cuda.empty_cache()
gc.collect()
"

# 减小批次大小
# 编辑.env文件，减小BATCH_SIZE_PER_GPU
```

#### 3. 多GPU负载不均衡

```bash
# 使用负载均衡策略
# 在代码中使用 strategy='load_balance'
```

#### 4. Docker构建失败

```bash
# 清理Docker缓存
docker system prune -a

# 使用国内镜像源（如果在中国）
# 编辑Dockerfile.gpu，添加pip镜像源
RUN pip3 install -i https://pypi.tuna.tsinghua.edu.cn/simple --no-cache-dir -r requirements.txt
```

### 日志查看

```bash
# 查看容器日志
docker logs musetalk-gpu-service --tail 100 -f

# 查看应用日志
docker exec -it musetalk-gpu-service tail -f /app/logs/app.log

# 查看GPU日志
journalctl -u nvidia-persistenced -f
```

---

## 优化建议

### 1. GPU优化

```python
# 在代码中添加优化设置
import torch

# 启用TF32（适用于Ampere架构）
torch.backends.cuda.matmul.allow_tf32 = True
torch.backends.cudnn.allow_tf32 = True

# 启用Flash Attention（如果可用）
# pip install flash-attn
```

### 2. 批处理优化

- **单GPU（48GB）**: 批次大小16-24
- **4xGPU（24GB）**: 每GPU批次大小6-8
- 使用动态批处理适应不同输入大小

### 3. 内存优化

```python
# 梯度检查点（节省内存）
from torch.utils.checkpoint import checkpoint

# 混合精度训练
from torch.cuda.amp import autocast, GradScaler
```

### 4. 数据加载优化

```python
# 使用多进程数据加载
from torch.utils.data import DataLoader

dataloader = DataLoader(
    dataset,
    batch_size=32,
    num_workers=8,  # CPU核心数的一半
    pin_memory=True,
    prefetch_factor=2
)
```

### 5. 系统优化

```bash
# 设置GPU性能模式
sudo nvidia-smi -pm 1
sudo nvidia-smi -pl 450  # 设置功率限制（W）

# 关闭ECC（提升性能，降低可靠性）
sudo nvidia-smi -e 0

# 设置GPU时钟
sudo nvidia-smi -ac 9251,2100  # memory,graphics时钟
```

---

## 性能基准参考

### RTX 4090D 48GB（单GPU）
- 批次大小: 20
- 平均延迟: ~30ms
- 吞吐量: ~33 样本/秒
- 内存使用: ~40GB

### 4x RTX 4090 24GB（多GPU）
- 总批次大小: 32
- 平均延迟: ~25ms
- 吞吐量: ~128 样本/秒
- 每GPU内存使用: ~20GB

---

## 生产部署建议

1. **使用Kubernetes**: 对于大规模部署，考虑使用K8s + GPU Operator
2. **负载均衡**: 使用NGINX或Traefik进行负载均衡
3. **监控告警**: 集成Prometheus + Grafana进行监控
4. **日志管理**: 使用ELK Stack进行日志收集和分析
5. **模型版本管理**: 使用MLflow或DVC管理模型版本
6. **自动扩缩容**: 基于GPU利用率自动扩缩容

---

## 联系支持

如遇到问题，请提供以下信息：
- GPU型号和数量
- NVIDIA驱动版本
- Docker版本
- 错误日志
- 系统配置

创建Issue时请使用相应的模板。