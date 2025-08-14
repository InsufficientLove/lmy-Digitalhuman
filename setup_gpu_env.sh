#!/bin/bash
# MuseTalk GPU环境一键部署脚本
# 支持Ubuntu 20.04/22.04 和 CentOS 7/8

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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
    log_info "检查GPU..."
    if ! command -v nvidia-smi &> /dev/null; then
        log_warn "nvidia-smi未找到，需要安装NVIDIA驱动"
        return 1
    fi
    
    nvidia-smi
    GPU_COUNT=$(nvidia-smi -L | wc -l)
    log_info "检测到 $GPU_COUNT 个GPU"
    
    # 检测GPU型号和内存
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
    
    return 0
}

# 安装NVIDIA驱动（Ubuntu）
install_nvidia_driver_ubuntu() {
    log_info "安装NVIDIA驱动..."
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

# 安装Docker
install_docker() {
    log_info "安装Docker..."
    
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
    
    log_info "Docker安装完成"
    docker --version
}

# 安装NVIDIA Container Toolkit
install_nvidia_container_toolkit() {
    log_info "安装NVIDIA Container Toolkit..."
    
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
    
    log_info "NVIDIA Container Toolkit安装完成"
}

# 测试GPU Docker支持
test_gpu_docker() {
    log_info "测试Docker GPU支持..."
    
    docker run --rm --runtime=nvidia --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
    
    if [ $? -eq 0 ]; then
        log_info "Docker GPU支持测试成功！"
    else
        log_error "Docker GPU支持测试失败"
        return 1
    fi
}

# 克隆并设置项目
setup_project() {
    log_info "设置MuseTalk项目..."
    
    # 克隆项目
    if [ ! -d "MuseTalk" ]; then
        git clone https://github.com/TMElyralab/MuseTalk.git
    fi
    
    cd MuseTalk
    
    # 复制配置文件
    if [ -f ".env.example" ]; then
        cp .env.example .env
        log_info "请编辑 .env 文件配置GPU参数"
    fi
    
    # 创建必要目录
    mkdir -p models inputs outputs logs
    
    log_info "项目设置完成"
}

# 构建Docker镜像
build_docker_image() {
    log_info "构建Docker镜像..."
    
    read -p "是否构建Docker镜像？(y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker build -f Dockerfile.gpu -t musetalk:gpu-latest .
        log_info "Docker镜像构建完成"
    fi
}

# 运行性能测试
run_benchmark() {
    log_info "运行性能基准测试..."
    
    read -p "是否运行性能测试？(y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # 检测GPU配置
        GPU_COUNT=$(nvidia-smi -L | wc -l)
        
        if [ $GPU_COUNT -eq 1 ]; then
            # 单GPU测试
            docker run --rm --runtime=nvidia --gpus all \
                -v $(pwd):/workspace \
                musetalk:gpu-latest \
                python /workspace/benchmark_gpu.py --config single_4090d_48gb --quick
        else
            # 多GPU测试
            docker run --rm --runtime=nvidia --gpus all \
                -v $(pwd):/workspace \
                musetalk:gpu-latest \
                python /workspace/benchmark_gpu.py --config quad_4090_24gb --quick
        fi
    fi
}

# 主函数
main() {
    echo "=========================================="
    echo "MuseTalk GPU环境一键部署脚本"
    echo "=========================================="
    
    # 检测操作系统
    detect_os
    
    # 检查是否有root权限
    if [ "$EUID" -eq 0 ]; then 
       log_warn "请不要使用root用户运行此脚本"
       exit 1
    fi
    
    # 检查GPU
    if ! check_gpu; then
        if [ "$OS" == "ubuntu" ]; then
            install_nvidia_driver_ubuntu
        else
            log_error "请手动安装NVIDIA驱动"
            exit 1
        fi
    fi
    
    # 检查Docker
    if ! command -v docker &> /dev/null; then
        install_docker
    else
        log_info "Docker已安装: $(docker --version)"
    fi
    
    # 检查NVIDIA Container Toolkit
    if ! docker info | grep -q nvidia; then
        install_nvidia_container_toolkit
    else
        log_info "NVIDIA Container Toolkit已安装"
    fi
    
    # 测试GPU Docker支持
    test_gpu_docker
    
    # 设置项目
    setup_project
    
    # 构建镜像
    build_docker_image
    
    # 运行测试
    run_benchmark
    
    echo "=========================================="
    log_info "环境部署完成！"
    echo "=========================================="
    echo ""
    echo "后续步骤："
    echo "1. 编辑 .env 文件配置GPU参数"
    echo "2. 运行: docker-compose -f docker-compose.gpu.yml up -d"
    echo "3. 查看日志: docker-compose -f docker-compose.gpu.yml logs -f"
    echo "4. 运行测试: python benchmark_gpu.py"
    echo ""
    echo "注意：可能需要重新登录以使docker组权限生效"
    echo "或运行: newgrp docker"
}

# 运行主函数
main