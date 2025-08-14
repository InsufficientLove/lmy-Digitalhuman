# 完整的Linux服务器部署命令步骤

## 📋 前置准备
确保服务器已安装：
- Docker 20.10+
- NVIDIA Driver
- NVIDIA Container Toolkit

---

## 🚀 完整命令步骤

### Step 1: SSH登录到服务器

```bash
# 登录到您的Linux服务器
ssh user@your-server-ip

# 或使用密钥
ssh -i your-key.pem user@your-server-ip
```

### Step 2: 检查环境

```bash
# 检查GPU和CUDA版本
nvidia-smi

# 检查Docker
docker --version

# 检查NVIDIA Container Toolkit
docker run --rm --runtime=nvidia --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi

# 如果上面命令失败，安装NVIDIA Container Toolkit
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker
```

### Step 3: 克隆指定分支代码

```bash
# 创建工作目录
mkdir -p ~/musetalk-test && cd ~/musetalk-test

# 克隆指定分支 (cursor/test-muse-talk-gpu-parallelization-and-batch-inference-84c5)
git clone -b cursor/test-muse-talk-gpu-parallelization-and-batch-inference-84c5 \
    https://github.com/your-username/your-repo.git .

# 验证当前分支
git branch
# 应该显示: * cursor/test-muse-talk-gpu-parallelization-and-batch-inference-84c5

# 查看文件
ls -la
```

### Step 4: 设置权限和配置

```bash
# 赋予脚本执行权限
chmod +x deploy.sh setup_gpu_env.sh

# 创建必要的目录
mkdir -p inputs outputs logs models

# 复制并编辑环境配置
cp .env.example .env

# 编辑配置（根据您的GPU调整）
cat > .env << 'EOF'
# GPU配置
CUDA_VISIBLE_DEVICES=0,1,2,3
GPU_CONFIG_MODE=auto
BATCH_SIZE_PER_GPU=8
INFERENCE_MODE=parallel

# 性能优化
ENABLE_AMP=true
ENABLE_CUDNN_BENCHMARK=true

# 运行模式
RUN_MODE=shell
AUTO_DOWNLOAD_MODELS=true
AUTO_CLONE_REPO=true

# 使用中国镜像（如果在中国）
USE_CHINA_MIRROR=false
HF_ENDPOINT=https://huggingface.co

# 服务配置
API_PORT=8000
WEB_PORT=7860
LOG_LEVEL=INFO
EOF
```

### Step 5: 构建Docker镜像

```bash
# 构建Docker镜像（支持CUDA 12.x）
docker build -f Dockerfile.gpu -t musetalk:gpu-test .

# 查看构建的镜像
docker images | grep musetalk
```

### Step 6: 首次运行测试（交互式Shell）

```bash
# 启动交互式容器进行测试
docker run -it --rm \
    --name musetalk-test \
    --runtime=nvidia \
    --gpus all \
    -v $(pwd):/workspace \
    -v $(pwd)/models:/app/models \
    -v $(pwd)/inputs:/app/inputs \
    -v $(pwd)/outputs:/app/outputs \
    -e RUN_MODE=shell \
    musetalk:gpu-test
```

### Step 7: 在容器内执行测试

```bash
# === 以下命令在Docker容器内执行 ===

# 1. 检查环境
python -c "
import torch
print(f'PyTorch Version: {torch.__version__}')
print(f'CUDA Available: {torch.cuda.is_available()}')
print(f'CUDA Version: {torch.version.cuda}')
print(f'GPU Count: {torch.cuda.device_count()}')
for i in range(torch.cuda.device_count()):
    props = torch.cuda.get_device_properties(i)
    print(f'GPU {i}: {props.name}, Memory: {props.total_memory/1024**3:.1f}GB')
"

# 2. 克隆MuseTalk官方代码（如果需要）
if [ ! -d "/app/MuseTalk" ]; then
    cd /app
    git clone https://github.com/TMElyralab/MuseTalk.git
fi

# 3. 下载模型（自动下载）
python /app/download_models.py

# 4. 运行GPU基准测试
cd /workspace
python benchmark_gpu.py --config auto --quick

# 5. 退出容器
exit
```

### Step 8: 运行完整测试

```bash
# 单GPU测试（RTX 4090D 48GB）
docker run --rm \
    --runtime=nvidia \
    --gpus '"device=0"' \
    -v $(pwd):/workspace \
    -e CUDA_VISIBLE_DEVICES=0 \
    -e GPU_CONFIG=single_4090d_48gb \
    -e BATCH_SIZE_PER_GPU=20 \
    musetalk:gpu-test \
    bash -c "cd /workspace && python benchmark_gpu.py --config single_4090d_48gb"

# 多GPU测试（4x RTX 4090 24GB）
docker run --rm \
    --runtime=nvidia \
    --gpus all \
    -v $(pwd):/workspace \
    -e CUDA_VISIBLE_DEVICES=0,1,2,3 \
    -e GPU_CONFIG=quad_4090_24gb \
    -e BATCH_SIZE_PER_GPU=8 \
    musetalk:gpu-test \
    bash -c "cd /workspace && python benchmark_gpu.py --config quad_4090_24gb"
```

### Step 9: 使用Docker Compose运行服务

```bash
# 启动所有服务
docker-compose -f docker-compose.gpu.yml up -d

# 查看服务状态
docker-compose -f docker-compose.gpu.yml ps

# 查看日志
docker-compose -f docker-compose.gpu.yml logs -f musetalk-gpu

# 进入运行中的容器
docker exec -it musetalk-gpu-service bash

# 停止服务
docker-compose -f docker-compose.gpu.yml down
```

### Step 10: 运行推理测试

```bash
# 准备测试文件
echo "请将测试视频放入 inputs/video.mp4"
echo "请将测试音频放入 inputs/audio.wav"

# 运行推理
docker run --rm \
    --runtime=nvidia \
    --gpus all \
    -v $(pwd):/workspace \
    -v $(pwd)/inputs:/app/inputs \
    -v $(pwd)/outputs:/app/outputs \
    -e RUN_MODE=inference \
    -e VIDEO_PATH=/app/inputs/video.mp4 \
    -e AUDIO_PATH=/app/inputs/audio.wav \
    -e OUTPUT_PATH=/app/outputs/result.mp4 \
    musetalk:gpu-test

# 查看输出
ls -la outputs/
```

---

## ✅ 测试成功后合并到主分支

### Step 11: 提交测试结果

```bash
# 保存测试结果
mkdir -p test_results
cp benchmark_results_*.json test_results/
cp outputs/* test_results/ 2>/dev/null || true

# 提交到当前分支
git add test_results/
git commit -m "test: GPU parallelization benchmark results

- Tested on [GPU型号]
- Single GPU: [性能数据]
- Multi GPU: [性能数据]
- Docker deployment successful"

git push origin cursor/test-muse-talk-gpu-parallelization-and-batch-inference-84c5
```

### Step 12: 合并到主分支

```bash
# 方法1: 在服务器上直接合并（如果有权限）
git checkout main
git pull origin main
git merge cursor/test-muse-talk-gpu-parallelization-and-batch-inference-84c5
git push origin main

# 方法2: 通过GitHub/GitLab创建Pull Request
echo "请在GitHub/GitLab上创建Pull Request："
echo "From: cursor/test-muse-talk-gpu-parallelization-and-batch-inference-84c5"
echo "To: main"
```

---

## 🚢 在其他服务器部署

### Step 13: 导出Docker镜像

```bash
# 在第一台服务器上
docker save musetalk:gpu-test | gzip > musetalk-gpu-test.tar.gz
ls -lh musetalk-gpu-test.tar.gz
```

### Step 14: 在新服务器上部署

```bash
# 在新服务器上
# 1. 传输镜像文件
scp user@first-server:~/musetalk-test/musetalk-gpu-test.tar.gz .

# 2. 加载镜像
docker load < musetalk-gpu-test.tar.gz

# 3. 克隆相同分支的代码
git clone -b cursor/test-muse-talk-gpu-parallelization-and-batch-inference-84c5 \
    https://github.com/your-username/your-repo.git musetalk-test
cd musetalk-test

# 4. 运行测试
docker run --rm --runtime=nvidia --gpus all \
    -v $(pwd):/workspace \
    musetalk:gpu-test \
    python /workspace/benchmark_gpu.py --config auto
```

---

## 📊 性能监控命令

```bash
# 实时监控GPU使用
watch -n 1 nvidia-smi

# 在另一个终端监控Docker容器
docker stats musetalk-test

# 查看容器内GPU使用
docker exec musetalk-test nvidia-smi

# 监控内存使用
docker exec musetalk-test python -c "
import torch
for i in range(torch.cuda.device_count()):
    print(f'GPU {i}:')
    print(f'  Allocated: {torch.cuda.memory_allocated(i)/1024**3:.2f} GB')
    print(f'  Reserved: {torch.cuda.memory_reserved(i)/1024**3:.2f} GB')
"
```

---

## 🔧 故障排除命令

```bash
# 如果GPU不可见
docker run --rm --runtime=nvidia --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi

# 如果模型下载失败（使用中国镜像）
docker run -it --rm \
    -v $(pwd)/models:/app/models \
    -e HF_ENDPOINT=https://hf-mirror.com \
    musetalk:gpu-test \
    python /app/download_models.py

# 清理Docker资源
docker system prune -a --volumes

# 查看详细错误日志
docker logs musetalk-test --tail 100 2>&1 | grep -i error

# 调试模式
docker run -it --rm \
    --runtime=nvidia \
    --gpus all \
    -v $(pwd):/workspace \
    --entrypoint /bin/bash \
    musetalk:gpu-test
```

---

## ✅ 完整测试检查清单

```bash
# 运行此脚本检查所有项目
cat > check_deployment.sh << 'EOF'
#!/bin/bash
echo "=== Deployment Check ==="
echo "1. Docker Version:"
docker --version

echo -e "\n2. NVIDIA Docker:"
docker run --rm --runtime=nvidia --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi | head -5

echo -e "\n3. Current Branch:"
git branch | grep "*"

echo -e "\n4. Docker Images:"
docker images | grep musetalk

echo -e "\n5. GPU Test:"
docker run --rm --runtime=nvidia --gpus all musetalk:gpu-test python -c "
import torch
print(f'GPUs Available: {torch.cuda.device_count()}')
"

echo -e "\n6. Model Files:"
ls -la models/ 2>/dev/null | head -5 || echo "Models not downloaded yet"

echo -e "\n=== Check Complete ==="
EOF

chmod +x check_deployment.sh
./check_deployment.sh
```

---

## 📝 总结

完整流程：
1. SSH登录服务器
2. 克隆指定分支 `cursor/test-muse-talk-gpu-parallelization-and-batch-inference-84c5`
3. 构建Docker镜像
4. 运行测试
5. 验证成功后合并到main分支

这套命令已经：
- ✅ 适配CUDA 12.9
- ✅ 包含完整的Python环境
- ✅ 自动下载模型
- ✅ 支持多GPU并行
- ✅ 可在多服务器复用