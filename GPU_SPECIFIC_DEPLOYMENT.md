# MuseTalk GPU精确指定部署指南

## 🎯 核心特性

1. **精确GPU指定** - 可以手动指定使用哪些GPU
2. **自动检测空闲GPU** - 智能选择未被占用的GPU
3. **预设配置** - 针对不同GPU型号的优化配置
4. **批处理优化** - 基于MuseTalk官方代码的批处理策略
5. **预加载机制** - 提前加载数据到GPU内存提升性能

## 📋 快速开始

### 1. 检查GPU状态

```bash
# 查看所有GPU状态
nvidia-smi

# 查看GPU占用情况（更详细）
nvidia-smi --query-gpu=index,name,memory.total,memory.used,memory.free,utilization.gpu --format=csv
```

### 2. 克隆代码

```bash
# 克隆指定分支
git clone -b cursor/test-muse-talk-gpu-parallelization-and-batch-inference-84c5 \
    YOUR_REPO_URL musetalk-gpu
cd musetalk-gpu
```

### 3. 构建Docker镜像

```bash
# 构建支持CUDA 12.x的镜像
docker build -f Dockerfile.gpu -t musetalk:gpu-latest .
```

## 🚀 运行示例

### 场景1: 单张RTX 4090D 48GB

```bash
# 方式1: 使用预设配置
./run_musetalk_gpu.sh \
    --gpu-config single_4090d_48gb \
    --mode benchmark

# 方式2: 手动指定GPU 0
./run_musetalk_gpu.sh \
    --gpu-ids 0 \
    --batch-size 20 \
    --mode benchmark

# 方式3: 使用Docker Compose
docker-compose -f docker-compose.gpu-specific.yml \
    --profile single \
    up musetalk-single-4090d
```

### 场景2: 4张RTX 4090 24GB

```bash
# 方式1: 使用预设配置
./run_musetalk_gpu.sh \
    --gpu-config quad_4090_24gb \
    --mode benchmark

# 方式2: 手动指定GPU 0,1,2,3
./run_musetalk_gpu.sh \
    --gpu-ids 0,1,2,3 \
    --batch-size 8 \
    --mode benchmark

# 方式3: 使用Docker Compose
docker-compose -f docker-compose.gpu-specific.yml \
    --profile quad \
    up musetalk-quad-4090
```

### 场景3: 部分GPU被占用（只使用GPU 2和3）

```bash
# 手动指定空闲的GPU
./run_musetalk_gpu.sh \
    --gpu-ids 2,3 \
    --batch-size 10 \
    --mode inference \
    --video input.mp4 \
    --audio audio.wav

# 或使用环境变量
export GPU_IDS=2,3
docker-compose -f docker-compose.gpu-specific.yml \
    --profile dual \
    up musetalk-dual-4090
```

### 场景4: 自动选择空闲GPU

```bash
# 自动检测并使用空闲GPU
./run_musetalk_gpu.sh \
    --gpu-config auto \
    --mode benchmark

# Docker方式
docker-compose -f docker-compose.gpu-specific.yml \
    --profile auto \
    up musetalk-auto
```

## 🔧 高级配置

### 环境变量配置

创建 `.env` 文件：

```bash
# GPU配置
CUDA_VISIBLE_DEVICES=0,2  # 只使用GPU 0和2
GPU_MODE=manual
GPU_IDS=[0,2]
BATCH_SIZE_PER_GPU=12
MAX_BATCH_SIZE=24

# 预加载配置
PRELOAD_FRAMES=150
PRELOAD_LATENTS=true

# 性能优化
ENABLE_AMP=true
ENABLE_CUDNN_BENCHMARK=true
PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:256

# 内存管理
MEMORY_CLEANUP_INTERVAL=50
MEMORY_THRESHOLD=0.85
```

### Python代码直接调用

```python
from MuseTalkEngine.gpu_parallel_engine_v2 import MuseTalkGPUEngine, GPUConfig

# 方式1: 使用预设
engine = MuseTalkGPUEngine("single_4090d_48gb")

# 方式2: 手动配置
config = GPUConfig(
    mode="manual",
    gpu_ids=[0, 2],  # 只使用GPU 0和2
    batch_size_per_gpu=12,
    max_batch_size=24,
    preload_frames=150,
    preload_latents=True,
    enable_amp=True
)
engine = MuseTalkGPUEngine(config)

# 方式3: 自动选择
engine = MuseTalkGPUEngine("auto")

# 运行推理
result = engine.inference(
    video_path="input.mp4",
    audio_path="audio.wav",
    models=models,  # 加载的模型
    args={}
)

print(f"FPS: {result['statistics']['fps']}")
```

## 📊 性能基准测试

### 运行完整基准测试

```bash
# 单GPU测试
docker run --rm \
    --runtime=nvidia \
    --gpus '"device=0"' \
    -v $(pwd):/workspace \
    musetalk:gpu-latest \
    python /workspace/benchmark_gpu.py --config single_4090d_48gb

# 多GPU测试
docker run --rm \
    --runtime=nvidia \
    --gpus '"device=0,1,2,3"' \
    -v $(pwd):/workspace \
    musetalk:gpu-latest \
    python /workspace/benchmark_gpu.py --config quad_4090_24gb

# 自定义GPU测试
docker run --rm \
    --runtime=nvidia \
    --gpus all \
    -v $(pwd):/workspace \
    -e CUDA_VISIBLE_DEVICES=1,3 \
    musetalk:gpu-latest \
    python /workspace/benchmark_gpu.py --gpu_ids 1,3 --batch_size 10
```

### 监控GPU使用

```bash
# 实时监控
watch -n 1 nvidia-smi

# 监控特定GPU
nvidia-smi -i 0,2 -l 1

# 详细监控
nvidia-smi dmon -i 0,1,2,3
```

## 🐛 故障排除

### 问题1: GPU不可见

```bash
# 检查Docker GPU支持
docker run --rm --runtime=nvidia --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi

# 检查CUDA_VISIBLE_DEVICES
echo $CUDA_VISIBLE_DEVICES
```

### 问题2: 显存不足

```bash
# 减小批处理大小
./run_musetalk_gpu.sh --gpu-ids 0 --batch-size 4 --mode inference

# 清理GPU内存
nvidia-smi --gpu-reset -i 0
```

### 问题3: GPU被占用

```bash
# 查找占用GPU的进程
nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv

# 使用其他空闲GPU
./run_musetalk_gpu.sh --gpu-ids 2,3 --mode inference
```

## 📈 批处理大小建议

| GPU型号 | 显存 | 推荐batch_size | 最大batch_size |
|---------|------|----------------|----------------|
| RTX 4090D | 48GB | 20 | 32 |
| RTX 4090 | 24GB | 8 | 12 |
| RTX 4080 | 16GB | 4 | 8 |
| RTX 3090 | 24GB | 6 | 10 |
| RTX 3080 | 10GB | 2 | 4 |

## 🎯 最佳实践

1. **预加载优化**
   - 对于长视频，增加 `PRELOAD_FRAMES`
   - 启用 `PRELOAD_LATENTS` 提升性能

2. **内存管理**
   - 设置合适的 `MEMORY_THRESHOLD`
   - 定期清理GPU内存

3. **批处理策略**
   - 根据显存大小调整 `BATCH_SIZE_PER_GPU`
   - 使用 `MAX_BATCH_SIZE` 限制总批次大小

4. **GPU选择**
   - 优先使用空闲GPU
   - 避免与其他任务共享GPU

## 📝 完整命令速查

```bash
# 查看GPU状态
nvidia-smi --query-gpu=index,name,utilization.gpu,memory.used,memory.free --format=csv

# 单GPU运行
./run_musetalk_gpu.sh --gpu-ids 0 --batch-size 20 --mode benchmark

# 多GPU运行
./run_musetalk_gpu.sh --gpu-ids 0,1,2,3 --batch-size 8 --mode benchmark

# 自动选择GPU
./run_musetalk_gpu.sh --gpu-config auto --mode inference --video in.mp4 --audio audio.wav

# Docker运行
docker-compose -f docker-compose.gpu-specific.yml --profile single up

# 进入容器调试
docker exec -it musetalk-single-4090d bash

# 查看日志
docker logs musetalk-single-4090d --tail 100
```

## ✅ 验证部署

```bash
# 运行验证脚本
docker run --rm \
    --runtime=nvidia \
    --gpus all \
    musetalk:gpu-latest \
    python -c "
import torch
import pynvml
from MuseTalkEngine.gpu_parallel_engine_v2 import GPUManager, GPUConfig

# 初始化
pynvml.nvmlInit()
config = GPUConfig(mode='auto')
manager = GPUManager(config)

# 显示信息
print(f'检测到GPU: {manager.available_gpus}')
print(f'使用GPU: {manager.gpu_ids}')
for gpu_id in manager.gpu_ids:
    info = manager.get_gpu_memory_info(gpu_id)
    print(f'GPU {gpu_id}: Total={info[\"total\"]:.1f}GB, Free={info[\"free\"]:.1f}GB')
"
```

这样配置后，您可以：
1. **精确指定GPU** - 完全控制使用哪些GPU
2. **自动检测空闲GPU** - 智能避开被占用的GPU
3. **优化批处理** - 根据GPU配置自动调整批处理大小
4. **预加载加速** - 提前加载数据到GPU内存

现在您可以根据服务器的实际GPU使用情况，灵活选择空闲的GPU来运行MuseTalk！