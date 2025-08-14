#!/bin/bash
# MuseTalk GPU 快速部署脚本
# 使用指定分支进行测试

set -e

# 配置
BRANCH_NAME="cursor/test-muse-talk-gpu-parallelization-and-batch-inference-84c5"
REPO_URL="https://github.com/your-username/your-repo.git"  # 请替换为您的仓库地址
WORK_DIR="$HOME/musetalk-test"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Step 1: 检查环境
check_environment() {
    log_info "检查环境..."
    
    # 检查Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker未安装"
        exit 1
    fi
    log_info "✓ Docker已安装: $(docker --version)"
    
    # 检查GPU
    if ! nvidia-smi &> /dev/null; then
        log_error "NVIDIA驱动未安装"
        exit 1
    fi
    log_info "✓ NVIDIA驱动已安装"
    nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv
    
    # 检查NVIDIA Container Toolkit
    if ! docker run --rm --runtime=nvidia --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi &> /dev/null; then
        log_warn "NVIDIA Container Toolkit可能未安装，尝试安装..."
        install_nvidia_toolkit
    else
        log_info "✓ NVIDIA Container Toolkit已安装"
    fi
}

# 安装NVIDIA Container Toolkit
install_nvidia_toolkit() {
    log_info "安装NVIDIA Container Toolkit..."
    distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
    curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
    curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
    sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit
    sudo systemctl restart docker
    log_info "✓ NVIDIA Container Toolkit安装完成"
}

# Step 2: 克隆代码
clone_repository() {
    log_info "克隆代码仓库..."
    
    # 创建工作目录
    mkdir -p "$WORK_DIR"
    cd "$WORK_DIR"
    
    # 如果目录已存在，先备份
    if [ -d ".git" ]; then
        log_warn "目录已存在Git仓库，备份并重新克隆..."
        mv . ../musetalk-backup-$(date +%Y%m%d-%H%M%S)
        mkdir -p "$WORK_DIR"
        cd "$WORK_DIR"
    fi
    
    # 克隆指定分支
    git clone -b "$BRANCH_NAME" "$REPO_URL" .
    
    # 验证分支
    CURRENT_BRANCH=$(git branch --show-current)
    if [ "$CURRENT_BRANCH" != "$BRANCH_NAME" ]; then
        log_error "分支错误: 期望 $BRANCH_NAME, 实际 $CURRENT_BRANCH"
        exit 1
    fi
    
    log_info "✓ 成功克隆分支: $BRANCH_NAME"
}

# Step 3: 设置环境
setup_environment() {
    log_info "设置环境..."
    
    # 设置权限
    chmod +x *.sh 2>/dev/null || true
    
    # 创建目录
    mkdir -p inputs outputs logs models
    
    # 创建配置文件
    if [ ! -f .env ]; then
        cat > .env << 'EOF'
# GPU配置
CUDA_VISIBLE_DEVICES=all
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

# 服务配置
API_PORT=8000
WEB_PORT=7860
LOG_LEVEL=INFO
EOF
        log_info "✓ 配置文件已创建"
    fi
}

# Step 4: 构建Docker镜像
build_docker_image() {
    log_info "构建Docker镜像..."
    
    docker build -f Dockerfile.gpu -t musetalk:gpu-test . || {
        log_error "Docker镜像构建失败"
        exit 1
    }
    
    log_info "✓ Docker镜像构建成功"
    docker images | grep musetalk
}

# Step 5: 运行快速测试
run_quick_test() {
    log_info "运行快速GPU测试..."
    
    docker run --rm \
        --runtime=nvidia \
        --gpus all \
        musetalk:gpu-test \
        python -c "
import torch
print('='*50)
print(f'PyTorch Version: {torch.__version__}')
print(f'CUDA Available: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'CUDA Version: {torch.version.cuda}')
    print(f'GPU Count: {torch.cuda.device_count()}')
    for i in range(torch.cuda.device_count()):
        props = torch.cuda.get_device_properties(i)
        print(f'GPU {i}: {props.name}, Memory: {props.total_memory/1024**3:.1f}GB')
print('='*50)
"
    
    if [ $? -eq 0 ]; then
        log_info "✓ GPU测试通过"
    else
        log_error "GPU测试失败"
        exit 1
    fi
}

# Step 6: 运行基准测试
run_benchmark() {
    log_info "运行性能基准测试..."
    
    # 检测GPU数量
    GPU_COUNT=$(nvidia-smi -L | wc -l)
    log_info "检测到 $GPU_COUNT 个GPU"
    
    # 运行测试
    docker run --rm \
        --runtime=nvidia \
        --gpus all \
        -v $(pwd):/workspace \
        musetalk:gpu-test \
        bash -c "cd /workspace && python benchmark_gpu.py --config auto --quick"
    
    if [ $? -eq 0 ]; then
        log_info "✓ 基准测试完成"
        
        # 显示结果文件
        if ls benchmark_results_*.json 1> /dev/null 2>&1; then
            log_info "测试结果已保存："
            ls -la benchmark_results_*.json
        fi
    else
        log_error "基准测试失败"
        exit 1
    fi
}

# Step 7: 交互式Shell（可选）
start_interactive_shell() {
    read -p "是否启动交互式Shell进行进一步测试？(y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "启动交互式容器..."
        docker run -it --rm \
            --name musetalk-interactive \
            --runtime=nvidia \
            --gpus all \
            -v $(pwd):/workspace \
            -v $(pwd)/models:/app/models \
            -e RUN_MODE=shell \
            musetalk:gpu-test
    fi
}

# 主函数
main() {
    echo "=========================================="
    echo "MuseTalk GPU 快速部署脚本"
    echo "分支: $BRANCH_NAME"
    echo "=========================================="
    echo
    
    # 执行步骤
    check_environment
    clone_repository
    setup_environment
    build_docker_image
    run_quick_test
    run_benchmark
    
    echo
    echo "=========================================="
    log_info "部署和测试完成！"
    echo "=========================================="
    echo
    echo "后续操作："
    echo "1. 查看测试结果: cat benchmark_results_*.json"
    echo "2. 运行Docker Compose: docker-compose -f docker-compose.gpu.yml up -d"
    echo "3. 进入容器: docker exec -it musetalk-gpu-service bash"
    echo "4. 合并到主分支: git checkout main && git merge $BRANCH_NAME"
    echo
    
    # 询问是否启动交互式Shell
    start_interactive_shell
}

# 运行主函数
main "$@"