#!/bin/bash
# MuseTalk GPU环境一键部署脚本
# 支持Ubuntu 20.04/22.04 和 CentOS 7/8

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# 检测操作系统
detect_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$ID
        VER=$VERSION_ID
    else
        log_error "无法检测操作系统"
        exit 1
    fi
    log_info "检测到操作系统: $OS $VER"
}

# 检查GPU
check_gpu() {
    log_step "检查GPU环境..."
    
    # 检查NVIDIA驱动
    if command -v nvidia-smi &> /dev/null; then
        log_info "✅ NVIDIA驱动已安装"
        nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader
        
        GPU_COUNT=$(nvidia-smi -L | wc -l)
        log_info "检测到 $GPU_COUNT 个GPU"
        
        # 检查CUDA
        if command -v nvcc &> /dev/null; then
            CUDA_VERSION=$(nvcc --version | grep "release" | awk '{print $6}' | cut -c2-)
            log_info "✅ CUDA已安装: 版本 $CUDA_VERSION"
        else
            log_warn "CUDA编译器未找到，但不影响Docker运行"
        fi
        
        return 0
    else
        log_warn "❌ NVIDIA驱动未安装"
        return 1
    fi
}

# 安装NVIDIA驱动（Ubuntu）
install_nvidia_driver_ubuntu() {
    log_step "安装NVIDIA驱动..."
    
    # 检查是否已安装
    if command -v nvidia-smi &> /dev/null; then
        log_info "✅ NVIDIA驱动已安装，跳过"
        return 0
    fi
    
    sudo apt update
    sudo apt install -y ubuntu-drivers-common
    
    # 检测推荐驱动
    ubuntu-drivers devices
    
    read -p "是否安装推荐的NVIDIA驱动？(y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo ubuntu-drivers autoinstall
        log_info "NVIDIA驱动安装完成，需要重启系统"
        read -p "是否立即重启？(y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            sudo reboot
        fi
    fi
}

# 检查Docker
check_docker() {
    log_step "检查Docker环境..."
    
    if command -v docker &> /dev/null; then
        DOCKER_VERSION=$(docker --version | awk '{print $3}' | sed 's/,//')
        log_info "✅ Docker已安装: 版本 $DOCKER_VERSION"
        
        # 检查Docker服务状态
        if systemctl is-active --quiet docker; then
            log_info "✅ Docker服务运行中"
        else
            log_warn "Docker服务未运行，正在启动..."
            sudo systemctl start docker
            sudo systemctl enable docker
        fi
        
        # 检查当前用户是否在docker组
        if groups $USER | grep -q docker; then
            log_info "✅ 用户已在docker组中"
        else
            log_warn "将用户添加到docker组..."
            sudo usermod -aG docker $USER
            log_warn "需要重新登录以使组权限生效"
        fi
        
        return 0
    else
        log_warn "❌ Docker未安装"
        return 1
    fi
}

# 安装Docker
install_docker() {
    log_step "安装Docker..."
    
    # 检查是否已安装
    if command -v docker &> /dev/null; then
        log_info "✅ Docker已安装，跳过"
        return 0
    fi
    
    if [ "$OS" == "ubuntu" ]; then
        # Ubuntu安装
        sudo apt-get remove -y docker docker-engine docker.io containerd runc || true
        
        sudo apt-get update
        sudo apt-get install -y \
            ca-certificates \
            curl \
            gnupg \
            lsb-release
        
        # 添加Docker GPG密钥
        sudo mkdir -m 0755 -p /etc/apt/keyrings
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
        
        # 设置仓库
        echo \
          "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
          $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
        
        # 安装Docker
        sudo apt-get update
        sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
        
    elif [ "$OS" == "centos" ] || [ "$OS" == "rhel" ]; then
        # CentOS/RHEL安装
        sudo yum remove -y docker \
                          docker-client \
                          docker-client-latest \
                          docker-common \
                          docker-latest \
                          docker-latest-logrotate \
                          docker-logrotate \
                          docker-engine || true
        
        sudo yum install -y yum-utils
        sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
        sudo yum install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    fi
    
    # 启动Docker
    sudo systemctl start docker
    sudo systemctl enable docker
    
    # 添加当前用户到docker组
    sudo usermod -aG docker $USER
    
    log_info "✅ Docker安装完成"
}

# 检查NVIDIA Container Toolkit
check_nvidia_container_toolkit() {
    log_step "检查NVIDIA Container Toolkit..."
    
    # 检查nvidia-container-runtime
    if docker info 2>/dev/null | grep -q nvidia; then
        log_info "✅ NVIDIA Container Toolkit已安装"
        return 0
    else
        log_warn "❌ NVIDIA Container Toolkit未安装"
        return 1
    fi
}

# 安装NVIDIA Container Toolkit
install_nvidia_container_toolkit() {
    log_step "安装NVIDIA Container Toolkit..."
    
    # 检查是否已安装
    if docker info 2>/dev/null | grep -q nvidia; then
        log_info "✅ NVIDIA Container Toolkit已安装，跳过"
        return 0
    fi
    
    if [ "$OS" == "ubuntu" ]; then
        distribution=$(. /etc/os-release;echo $ID$VERSION_ID) \
           && curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg \
           && curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | \
                sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
                sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
        
        sudo apt-get update
        sudo apt-get install -y nvidia-container-toolkit
        
    elif [ "$OS" == "centos" ] || [ "$OS" == "rhel" ]; then
        distribution=$(. /etc/os-release;echo $ID$VERSION_ID) \
           && curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.repo | sudo tee /etc/yum.repos.d/nvidia-container-toolkit.repo
        
        sudo yum clean expire-cache
        sudo yum install -y nvidia-container-toolkit
    fi
    
    # 配置Docker
    sudo nvidia-ctk runtime configure --runtime=docker
    sudo systemctl restart docker
    
    log_info "✅ NVIDIA Container Toolkit安装完成"
}

# 测试GPU Docker支持
test_gpu_docker() {
    log_step "测试Docker GPU支持..."
    
    # 先检查是否需要使用sudo
    if docker ps >/dev/null 2>&1; then
        DOCKER_CMD="docker"
    else
        DOCKER_CMD="sudo docker"
        log_warn "需要使用sudo运行docker，建议将用户添加到docker组"
    fi
    
    log_info "运行GPU测试容器..."
    if $DOCKER_CMD run --rm --runtime=nvidia --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi; then
        log_info "✅ Docker GPU支持测试成功！"
        return 0
    else
        log_error "❌ Docker GPU支持测试失败"
        return 1
    fi
}

# 下载模型权重
download_models() {
    log_step "下载MuseTalk模型权重..."
    
    # 检查是否已下载
    if [ -d "models/musetalkV15" ] && [ -f "models/musetalkV15/unet.pth" ]; then
        log_info "✅ MuseTalk V1.5模型已存在"
        MODELS_EXIST=true
    else
        MODELS_EXIST=false
    fi
    
    if [ -d "models/sd-vae" ] && [ -f "models/sd-vae/diffusion_pytorch_model.bin" ]; then
        log_info "✅ VAE模型已存在"
        VAE_EXISTS=true
    else
        VAE_EXISTS=false
    fi
    
    if [ "$MODELS_EXIST" = true ] && [ "$VAE_EXISTS" = true ]; then
        read -p "模型已存在，是否重新下载？(y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "跳过模型下载"
            return 0
        fi
    fi
    
    # 执行下载脚本
    if [ -f "download_weights.sh" ]; then
        log_info "执行模型下载脚本..."
        bash download_weights.sh
    else
        log_warn "下载脚本不存在，请手动下载模型"
        log_info "模型下载地址："
        log_info "  - MuseTalk: https://huggingface.co/TMElyralab/MuseTalk"
        log_info "  - SD-VAE: https://huggingface.co/stabilityai/sd-vae-ft-mse"
        log_info "  - Whisper: https://huggingface.co/openai/whisper-tiny"
    fi
}

# 克隆并设置项目
setup_project() {
    log_step "设置MuseTalk项目..."
    
    # 检查当前目录是否已经是项目目录
    if [ -f "MuseTalk/README.md" ] || [ -f "README.md" ]; then
        log_info "✅ 项目已存在"
        
        # 如果在项目根目录
        if [ -f "README.md" ] && grep -q "MuseTalk" README.md; then
            PROJECT_DIR="."
        else
            PROJECT_DIR="MuseTalk"
        fi
    else
        # 克隆项目
        log_info "克隆MuseTalk项目..."
        git clone https://github.com/TMElyralab/MuseTalk.git
        PROJECT_DIR="MuseTalk"
    fi
    
    cd "$PROJECT_DIR"
    
    # 复制配置文件
    if [ ! -f ".env" ] && [ -f ".env.example" ]; then
        cp .env.example .env
        log_info "已创建.env配置文件"
    fi
    
    # 创建必要目录
    mkdir -p models inputs outputs logs
    
    # 下载模型
    download_models
    
    log_info "✅ 项目设置完成"
}

# 构建Docker镜像
build_docker_image() {
    log_step "构建Docker镜像..."
    
    # 检查镜像是否已存在
    if docker images | grep -q "musetalk.*gpu-latest"; then
        log_info "✅ Docker镜像已存在"
        read -p "是否重新构建Docker镜像？(y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            return 0
        fi
    fi
    
    if [ -f "Dockerfile.gpu" ]; then
        log_info "构建GPU版本Docker镜像..."
        docker build -f Dockerfile.gpu -t musetalk:gpu-latest .
        log_info "✅ Docker镜像构建完成"
    else
        log_warn "Dockerfile.gpu不存在，使用我们提供的版本"
        # 这里会使用workspace中的Dockerfile.gpu
        if [ -f "../Dockerfile.gpu" ]; then
            docker build -f ../Dockerfile.gpu -t musetalk:gpu-latest ..
        fi
    fi
}

# 运行性能测试
run_benchmark() {
    log_step "性能基准测试..."
    
    read -p "是否运行性能测试？(y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        return 0
    fi
    
    # 检测GPU配置
    GPU_COUNT=$(nvidia-smi -L | wc -l)
    GPU_MEMORY=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits | head -1)
    
    log_info "检测到 $GPU_COUNT 个GPU，显存: ${GPU_MEMORY}MB"
    
    # 判断配置类型
    if [ $GPU_COUNT -eq 1 ] && [ $GPU_MEMORY -gt 40000 ]; then
        CONFIG="single_4090d_48gb"
        log_info "使用单GPU配置 (48GB)"
    elif [ $GPU_COUNT -ge 4 ] && [ $GPU_MEMORY -gt 20000 ]; then
        CONFIG="quad_4090_24gb"
        log_info "使用4GPU配置 (4x24GB)"
    else
        CONFIG="auto"
        log_info "使用自动配置"
    fi
    
    # 运行测试
    if [ -f "../benchmark_gpu.py" ]; then
        docker run --rm --runtime=nvidia --gpus all \
            -v $(pwd)/..:/workspace \
            musetalk:gpu-latest \
            python /workspace/benchmark_gpu.py --config $CONFIG --quick
    else
        log_warn "基准测试脚本不存在"
    fi
}

# 显示总结
show_summary() {
    echo ""
    echo "=========================================="
    log_info "环境检查总结"
    echo "=========================================="
    
    # GPU状态
    if command -v nvidia-smi &> /dev/null; then
        echo -e "GPU驱动: ${GREEN}✅ 已安装${NC}"
        GPU_COUNT=$(nvidia-smi -L | wc -l)
        echo -e "GPU数量: ${GREEN}$GPU_COUNT${NC}"
    else
        echo -e "GPU驱动: ${RED}❌ 未安装${NC}"
    fi
    
    # Docker状态
    if command -v docker &> /dev/null; then
        echo -e "Docker: ${GREEN}✅ 已安装${NC}"
    else
        echo -e "Docker: ${RED}❌ 未安装${NC}"
    fi
    
    # NVIDIA Container Toolkit状态
    if docker info 2>/dev/null | grep -q nvidia; then
        echo -e "NVIDIA Container: ${GREEN}✅ 已安装${NC}"
    else
        echo -e "NVIDIA Container: ${YELLOW}⚠ 未安装${NC}"
    fi
    
    # 模型状态
    if [ -d "models/musetalkV15" ] && [ -f "models/musetalkV15/unet.pth" ]; then
        echo -e "MuseTalk模型: ${GREEN}✅ 已下载${NC}"
    else
        echo -e "MuseTalk模型: ${YELLOW}⚠ 未下载${NC}"
    fi
    
    echo "=========================================="
}

# 主函数
main() {
    echo "=========================================="
    echo "MuseTalk GPU环境一键部署脚本 v2.0"
    echo "=========================================="
    echo ""
    
    # 检测操作系统
    detect_os
    
    # 检查是否有root权限
    if [ "$EUID" -eq 0 ]; then 
       log_warn "请不要使用root用户运行此脚本"
       exit 1
    fi
    
    # 1. 检查和安装GPU驱动
    if ! check_gpu; then
        if [ "$OS" == "ubuntu" ]; then
            install_nvidia_driver_ubuntu
        else
            log_error "请手动安装NVIDIA驱动"
            log_info "参考: https://docs.nvidia.com/datacenter/tesla/tesla-installation-notes/index.html"
            exit 1
        fi
    fi
    
    # 2. 检查和安装Docker
    if ! check_docker; then
        install_docker
    fi
    
    # 3. 检查和安装NVIDIA Container Toolkit
    if ! check_nvidia_container_toolkit; then
        install_nvidia_container_toolkit
    fi
    
    # 4. 测试GPU Docker支持
    test_gpu_docker
    
    # 5. 设置项目和下载模型
    setup_project
    
    # 6. 构建Docker镜像
    build_docker_image
    
    # 7. 运行性能测试
    run_benchmark
    
    # 显示总结
    show_summary
    
    echo ""
    echo "后续步骤："
    echo "1. 编辑 .env 文件配置GPU参数"
    echo "2. 运行: docker-compose -f docker-compose.gpu.yml up -d"
    echo "3. 查看日志: docker-compose -f docker-compose.gpu.yml logs -f"
    echo "4. 访问Web界面: http://localhost:8080"
    echo ""
    
    if ! groups $USER | grep -q docker; then
        echo -e "${YELLOW}注意：需要重新登录以使docker组权限生效${NC}"
        echo "或运行: newgrp docker"
    fi
}

# 运行主函数
main "$@"