#!/bin/bash
# MuseTalk Docker部署管理脚本
# 支持构建、部署、测试、监控等完整功能

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# 配置
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_NAME="musetalk"
DOCKER_IMAGE="musetalk:gpu-latest"
COMPOSE_FILE="docker-compose.gpu.yml"
ENV_FILE=".env"

# 日志函数
log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_step() { echo -e "${BLUE}[STEP]${NC} $1"; }
log_success() { echo -e "${CYAN}✅${NC} $1"; }

# 显示帮助
show_help() {
    cat << EOF
使用方法: $0 [命令] [选项]

命令:
    setup           初始化环境（检查依赖、创建配置）
    build           构建Docker镜像
    deploy          部署服务
    start           启动服务
    stop            停止服务
    restart         重启服务
    status          查看服务状态
    logs            查看日志
    test            运行测试
    benchmark       运行性能基准测试
    shell           进入容器Shell
    clean           清理容器和卷
    monitor         启动监控服务
    backup          备份模型和数据
    restore         恢复备份
    
选项:
    --gpu-ids       指定GPU ID（例如: 0,1,2,3）
    --batch-size    批处理大小
    --mode          运行模式 (inference/benchmark/gradio/api)
    --profile       Docker Compose profile (production/monitoring/batch)
    --no-cache      构建时不使用缓存
    --force         强制执行（跳过确认）
    
示例:
    $0 setup                    # 初始化环境
    $0 build --no-cache        # 重新构建镜像
    $0 deploy --profile production  # 生产环境部署
    $0 test --gpu-ids 0,1,2,3  # 使用4个GPU测试
    $0 monitor                  # 启动监控面板

EOF
}

# 检查Docker和NVIDIA环境
check_environment() {
    log_step "检查环境..."
    
    # 检查Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker未安装"
        exit 1
    fi
    log_success "Docker已安装: $(docker --version)"
    
    # 检查Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        if ! docker compose version &> /dev/null; then
            log_error "Docker Compose未安装"
            exit 1
        fi
        COMPOSE_CMD="docker compose"
    else
        COMPOSE_CMD="docker-compose"
    fi
    log_success "Docker Compose已安装"
    
    # 检查NVIDIA Docker
    if ! docker info 2>/dev/null | grep -q nvidia; then
        log_warn "NVIDIA Container Toolkit未检测到"
        log_info "请安装: https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html"
    else
        log_success "NVIDIA Container Toolkit已安装"
    fi
    
    # 检查GPU
    if command -v nvidia-smi &> /dev/null; then
        GPU_COUNT=$(nvidia-smi -L | wc -l)
        log_success "检测到 $GPU_COUNT 个GPU"
        nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
    else
        log_warn "nvidia-smi未找到，无法检测GPU"
    fi
}

# 初始化环境
setup_environment() {
    log_step "初始化环境..."
    
    # 检查环境
    check_environment
    
    # 创建目录结构
    log_info "创建目录结构..."
    mkdir -p inputs outputs logs models batch/inputs batch/outputs
    mkdir -p grafana/dashboards grafana/datasources
    
    # 创建.env文件
    if [ ! -f "$ENV_FILE" ]; then
        log_info "创建.env配置文件..."
        if [ -f ".env.example" ]; then
            cp .env.example .env
            log_success ".env文件已创建，请根据需要修改配置"
        else
            log_warn ".env.example不存在，创建默认配置..."
            create_default_env
        fi
    else
        log_success ".env文件已存在"
    fi
    
    # 创建Prometheus配置
    if [ ! -f "prometheus.yml" ]; then
        log_info "创建Prometheus配置..."
        cat > prometheus.yml << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'gpu-metrics'
    static_configs:
      - targets: ['gpu-monitor:9400']
  
  - job_name: 'musetalk'
    static_configs:
      - targets: ['musetalk-gpu:9090']
EOF
        log_success "Prometheus配置已创建"
    fi
    
    log_success "环境初始化完成"
}

# 创建默认.env文件
create_default_env() {
    cat > .env << 'EOF'
# GPU配置
CUDA_VISIBLE_DEVICES=all
GPU_CONFIG_MODE=auto
BATCH_SIZE_PER_GPU=8
INFERENCE_MODE=parallel

# 性能优化
ENABLE_AMP=true
ENABLE_CUDNN_BENCHMARK=true

# 服务配置
API_PORT=8000
WEB_PORT=7860
MONITOR_PORT=9090

# 资源限制
MEM_LIMIT=64g
SHM_SIZE=8g

# 其他配置
RUN_MODE=inference
AUTO_DOWNLOAD_MODELS=true
LOG_LEVEL=INFO
RESTART_POLICY=unless-stopped
EOF
}

# 构建Docker镜像
build_image() {
    log_step "构建Docker镜像..."
    
    # 解析参数
    NO_CACHE=""
    while [[ $# -gt 0 ]]; do
        case $1 in
            --no-cache) NO_CACHE="--no-cache" ;;
        esac
        shift
    done
    
    # 构建镜像
    log_info "开始构建镜像: $DOCKER_IMAGE"
    
    if docker build $NO_CACHE \
        -f Dockerfile.gpu \
        -t $DOCKER_IMAGE \
        --build-arg BUILDKIT_INLINE_CACHE=1 \
        --cache-from $DOCKER_IMAGE \
        .; then
        log_success "镜像构建成功: $DOCKER_IMAGE"
        
        # 显示镜像信息
        docker images | grep musetalk
    else
        log_error "镜像构建失败"
        exit 1
    fi
}

# 部署服务
deploy_services() {
    log_step "部署服务..."
    
    # 解析参数
    PROFILE=""
    while [[ $# -gt 0 ]]; do
        case $1 in
            --profile) PROFILE="--profile $2"; shift ;;
        esac
        shift
    done
    
    # 拉取/构建镜像
    log_info "准备镜像..."
    $COMPOSE_CMD -f $COMPOSE_FILE build
    
    # 启动服务
    log_info "启动服务..."
    $COMPOSE_CMD -f $COMPOSE_FILE $PROFILE up -d
    
    # 等待服务就绪
    log_info "等待服务就绪..."
    sleep 10
    
    # 检查服务状态
    check_status
    
    log_success "服务部署成功"
    
    # 显示访问信息
    show_access_info
}

# 启动服务
start_services() {
    log_step "启动服务..."
    $COMPOSE_CMD -f $COMPOSE_FILE start
    log_success "服务已启动"
}

# 停止服务
stop_services() {
    log_step "停止服务..."
    $COMPOSE_CMD -f $COMPOSE_FILE stop
    log_success "服务已停止"
}

# 重启服务
restart_services() {
    log_step "重启服务..."
    $COMPOSE_CMD -f $COMPOSE_FILE restart
    log_success "服务已重启"
}

# 查看服务状态
check_status() {
    log_step "服务状态:"
    $COMPOSE_CMD -f $COMPOSE_FILE ps
    
    # 检查健康状态
    log_info "健康检查:"
    docker ps --filter "name=musetalk" --format "table {{.Names}}\t{{.Status}}"
}

# 查看日志
view_logs() {
    log_step "查看日志..."
    
    # 解析参数
    TAIL="100"
    FOLLOW=""
    SERVICE="musetalk-gpu"
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --tail) TAIL="$2"; shift ;;
            --follow|-f) FOLLOW="-f" ;;
            --service) SERVICE="$2"; shift ;;
        esac
        shift
    done
    
    $COMPOSE_CMD -f $COMPOSE_FILE logs --tail=$TAIL $FOLLOW $SERVICE
}

# 运行测试
run_tests() {
    log_step "运行测试..."
    
    # 解析参数
    GPU_IDS="auto"
    while [[ $# -gt 0 ]]; do
        case $1 in
            --gpu-ids) GPU_IDS="$2"; shift ;;
        esac
        shift
    done
    
    # 运行测试容器
    docker run --rm \
        --runtime=nvidia \
        --gpus all \
        -v $(pwd):/workspace \
        -e CUDA_VISIBLE_DEVICES=$GPU_IDS \
        $DOCKER_IMAGE \
        python /workspace/benchmark_gpu.py --config auto --quick
}

# 运行基准测试
run_benchmark() {
    log_step "运行性能基准测试..."
    
    docker exec -it musetalk-gpu-service \
        python /app/benchmark_gpu.py --config auto
}

# 进入容器Shell
enter_shell() {
    log_step "进入容器Shell..."
    docker exec -it musetalk-gpu-service /bin/bash
}

# 清理
cleanup() {
    log_step "清理容器和卷..."
    
    read -p "警告：这将删除所有容器和数据，是否继续？(y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        $COMPOSE_CMD -f $COMPOSE_FILE down -v
        docker system prune -f
        log_success "清理完成"
    else
        log_info "取消清理"
    fi
}

# 启动监控
start_monitoring() {
    log_step "启动监控服务..."
    
    # 启动监控profile
    $COMPOSE_CMD -f $COMPOSE_FILE --profile monitoring up -d
    
    log_success "监控服务已启动"
    log_info "Grafana: http://localhost:3000 (admin/admin)"
    log_info "Prometheus: http://localhost:9091"
    log_info "GPU Metrics: http://localhost:9400/metrics"
}

# 备份
backup_data() {
    log_step "备份数据..."
    
    BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p $BACKUP_DIR
    
    # 备份模型
    log_info "备份模型..."
    docker run --rm \
        -v musetalk-models:/models:ro \
        -v $(pwd)/$BACKUP_DIR:/backup \
        alpine tar czf /backup/models.tar.gz -C / models
    
    # 备份配置
    log_info "备份配置..."
    cp .env $BACKUP_DIR/
    cp docker-compose.gpu.yml $BACKUP_DIR/
    
    log_success "备份完成: $BACKUP_DIR"
}

# 恢复备份
restore_backup() {
    log_step "恢复备份..."
    
    if [ -z "$1" ]; then
        log_error "请指定备份目录"
        exit 1
    fi
    
    BACKUP_DIR="$1"
    
    if [ ! -d "$BACKUP_DIR" ]; then
        log_error "备份目录不存在: $BACKUP_DIR"
        exit 1
    fi
    
    # 恢复模型
    log_info "恢复模型..."
    docker run --rm \
        -v musetalk-models:/models \
        -v $(pwd)/$BACKUP_DIR:/backup:ro \
        alpine tar xzf /backup/models.tar.gz -C /
    
    log_success "恢复完成"
}

# 显示访问信息
show_access_info() {
    echo ""
    echo "=========================================="
    echo "服务访问信息:"
    echo "=========================================="
    echo "API服务: http://localhost:8000"
    echo "Web界面: http://localhost:7860"
    echo "监控面板: http://localhost:9090"
    echo ""
    echo "查看日志: $0 logs -f"
    echo "进入容器: $0 shell"
    echo "=========================================="
}

# 主函数
main() {
    cd "$SCRIPT_DIR"
    
    # 检查参数
    if [ $# -eq 0 ]; then
        show_help
        exit 0
    fi
    
    # 解析命令
    COMMAND=$1
    shift
    
    case $COMMAND in
        setup)
            setup_environment "$@"
            ;;
        build)
            build_image "$@"
            ;;
        deploy)
            deploy_services "$@"
            ;;
        start)
            start_services "$@"
            ;;
        stop)
            stop_services "$@"
            ;;
        restart)
            restart_services "$@"
            ;;
        status)
            check_status "$@"
            ;;
        logs)
            view_logs "$@"
            ;;
        test)
            run_tests "$@"
            ;;
        benchmark)
            run_benchmark "$@"
            ;;
        shell)
            enter_shell "$@"
            ;;
        clean)
            cleanup "$@"
            ;;
        monitor)
            start_monitoring "$@"
            ;;
        backup)
            backup_data "$@"
            ;;
        restore)
            restore_backup "$@"
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_error "未知命令: $COMMAND"
            show_help
            exit 1
            ;;
    esac
}

# 运行主函数
main "$@"