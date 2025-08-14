#!/bin/bash

# MuseTalk GPU运行脚本
# 支持精确GPU指定和批处理优化

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 日志函数
log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_debug() { echo -e "${BLUE}[DEBUG]${NC} $1"; }

# 显示帮助
show_help() {
    cat << EOF
使用方法: $0 [选项]

选项:
    --gpu-config    GPU配置预设 (single_4090d_48gb|quad_4090_24gb|dual_4090_24gb|auto)
    --gpu-ids       手动指定GPU ID列表 (例如: 0,1,2,3)
    --batch-size    每个GPU的批处理大小 (默认: 8)
    --mode          运行模式 (inference|benchmark|shell|gradio)
    --video         输入视频路径
    --audio         输入音频路径
    --output        输出路径
    --docker        使用Docker运行 (默认: false)
    --profile       Docker Compose配置文件 (single|quad|dual|auto)
    --help          显示此帮助信息

示例:
    # 使用单个RTX 4090D 48GB
    $0 --gpu-config single_4090d_48gb --mode inference --video input.mp4 --audio audio.wav

    # 使用4个RTX 4090 24GB
    $0 --gpu-config quad_4090_24gb --mode benchmark

    # 手动指定GPU 2和3
    $0 --gpu-ids 2,3 --batch-size 10 --mode inference

    # 使用Docker运行
    $0 --docker --profile single --mode inference

    # 自动检测空闲GPU
    $0 --gpu-config auto --mode inference

EOF
}

# 默认参数
GPU_CONFIG="auto"
GPU_IDS=""
BATCH_SIZE=8
MODE="inference"
VIDEO_PATH=""
AUDIO_PATH=""
OUTPUT_PATH=""
USE_DOCKER=false
DOCKER_PROFILE=""

# 解析参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --gpu-config)
            GPU_CONFIG="$2"
            shift 2
            ;;
        --gpu-ids)
            GPU_IDS="$2"
            shift 2
            ;;
        --batch-size)
            BATCH_SIZE="$2"
            shift 2
            ;;
        --mode)
            MODE="$2"
            shift 2
            ;;
        --video)
            VIDEO_PATH="$2"
            shift 2
            ;;
        --audio)
            AUDIO_PATH="$2"
            shift 2
            ;;
        --output)
            OUTPUT_PATH="$2"
            shift 2
            ;;
        --docker)
            USE_DOCKER=true
            shift
            ;;
        --profile)
            DOCKER_PROFILE="$2"
            shift 2
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            log_error "未知参数: $1"
            show_help
            exit 1
            ;;
    esac
done

# 检查GPU状态
check_gpu_status() {
    log_info "检查GPU状态..."
    
    if ! command -v nvidia-smi &> /dev/null; then
        log_error "nvidia-smi未找到，请确保已安装NVIDIA驱动"
        exit 1
    fi
    
    # 显示GPU信息
    nvidia-smi --query-gpu=index,name,memory.total,memory.used,memory.free,utilization.gpu \
        --format=csv,noheader,nounits | while IFS=',' read -r idx name total used free util; do
        # 去除空格
        idx=$(echo $idx | xargs)
        name=$(echo $name | xargs)
        total=$(echo $total | xargs)
        used=$(echo $used | xargs)
        free=$(echo $free | xargs)
        util=$(echo $util | xargs)
        
        # 计算使用百分比
        mem_percent=$(awk "BEGIN {printf \"%.1f\", $used/$total*100}")
        
        # 判断状态
        if [ "$util" -lt 30 ] && [ $(echo "$mem_percent < 30" | bc -l) -eq 1 ]; then
            status="${GREEN}空闲${NC}"
        elif [ "$util" -lt 70 ] && [ $(echo "$mem_percent < 70" | bc -l) -eq 1 ]; then
            status="${YELLOW}使用中${NC}"
        else
            status="${RED}繁忙${NC}"
        fi
        
        echo -e "GPU $idx: $name | 总显存: ${total}MB | 已用: ${used}MB | 空闲: ${free}MB | 利用率: ${util}% | 状态: $status"
    done
}

# 选择GPU
select_gpus() {
    if [ -n "$GPU_IDS" ]; then
        # 手动指定的GPU
        log_info "使用手动指定的GPU: $GPU_IDS"
        export CUDA_VISIBLE_DEVICES="$GPU_IDS"
    elif [ "$GPU_CONFIG" == "auto" ]; then
        # 自动选择空闲GPU
        log_info "自动选择空闲GPU..."
        
        # 获取空闲GPU列表
        IDLE_GPUS=$(nvidia-smi --query-gpu=index,utilization.gpu,memory.used \
            --format=csv,noheader,nounits | \
            awk -F',' '$2 < 30 && $3 < 3000 {print $1}' | tr '\n' ',' | sed 's/,$//')
        
        if [ -z "$IDLE_GPUS" ]; then
            log_warn "没有空闲GPU，使用所有可用GPU"
            export CUDA_VISIBLE_DEVICES=""
        else
            log_info "选择空闲GPU: $IDLE_GPUS"
            export CUDA_VISIBLE_DEVICES="$IDLE_GPUS"
        fi
    else
        # 使用预设配置
        case $GPU_CONFIG in
            single_4090d_48gb)
                export CUDA_VISIBLE_DEVICES="0"
                BATCH_SIZE=20
                ;;
            quad_4090_24gb)
                export CUDA_VISIBLE_DEVICES="0,1,2,3"
                BATCH_SIZE=8
                ;;
            dual_4090_24gb)
                export CUDA_VISIBLE_DEVICES="0,1"
                BATCH_SIZE=10
                ;;
            *)
                log_error "未知的GPU配置: $GPU_CONFIG"
                exit 1
                ;;
        esac
        log_info "使用GPU配置: $GPU_CONFIG (GPUs: $CUDA_VISIBLE_DEVICES)"
    fi
}

# Docker运行
run_with_docker() {
    log_info "使用Docker运行..."
    
    # 确定Docker profile
    if [ -z "$DOCKER_PROFILE" ]; then
        case $GPU_CONFIG in
            single_4090d_48gb)
                DOCKER_PROFILE="single"
                ;;
            quad_4090_24gb)
                DOCKER_PROFILE="quad"
                ;;
            dual_4090_24gb)
                DOCKER_PROFILE="dual"
                ;;
            auto)
                DOCKER_PROFILE="auto"
                ;;
            *)
                DOCKER_PROFILE="auto"
                ;;
        esac
    fi
    
    log_info "使用Docker profile: $DOCKER_PROFILE"
    
    # 设置环境变量
    if [ -n "$GPU_IDS" ]; then
        export GPU_IDS="$GPU_IDS"
        export GPU_DEVICE_IDS="[$(echo $GPU_IDS | sed 's/,/, /g')]"
    fi
    
    # 构建镜像
    log_info "构建Docker镜像..."
    docker build -f Dockerfile.gpu -t musetalk:gpu-latest .
    
    # 运行容器
    case $MODE in
        inference)
            if [ -z "$VIDEO_PATH" ] || [ -z "$AUDIO_PATH" ]; then
                log_error "推理模式需要指定 --video 和 --audio"
                exit 1
            fi
            
            docker-compose -f docker-compose.gpu-specific.yml \
                --profile $DOCKER_PROFILE \
                run --rm \
                -e VIDEO_PATH="/app/inputs/$(basename $VIDEO_PATH)" \
                -e AUDIO_PATH="/app/inputs/$(basename $AUDIO_PATH)" \
                -e OUTPUT_PATH="/app/outputs/$(basename ${OUTPUT_PATH:-output.mp4})" \
                musetalk-$DOCKER_PROFILE
            ;;
            
        benchmark)
            docker-compose -f docker-compose.gpu-specific.yml \
                --profile $DOCKER_PROFILE \
                run --rm \
                musetalk-$DOCKER_PROFILE \
                python /workspace/benchmark_gpu.py --config $GPU_CONFIG
            ;;
            
        shell)
            docker-compose -f docker-compose.gpu-specific.yml \
                --profile $DOCKER_PROFILE \
                run --rm \
                musetalk-$DOCKER_PROFILE \
                /bin/bash
            ;;
            
        gradio)
            docker-compose -f docker-compose.gpu-specific.yml \
                --profile $DOCKER_PROFILE \
                up -d musetalk-$DOCKER_PROFILE
            log_info "Gradio界面运行在: http://localhost:786${DOCKER_PROFILE:0:1}"
            ;;
            
        *)
            log_error "未知的运行模式: $MODE"
            exit 1
            ;;
    esac
}

# 本地运行
run_locally() {
    log_info "本地运行..."
    
    # 检查Python环境
    if ! command -v python &> /dev/null; then
        log_error "Python未找到"
        exit 1
    fi
    
    # 激活虚拟环境（如果存在）
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
    fi
    
    # 设置Python路径
    export PYTHONPATH="${PYTHONPATH}:$(pwd):$(pwd)/MuseTalk:$(pwd)/MuseTalkEngine"
    
    case $MODE in
        inference)
            if [ -z "$VIDEO_PATH" ] || [ -z "$AUDIO_PATH" ]; then
                log_error "推理模式需要指定 --video 和 --audio"
                exit 1
            fi
            
            python -c "
from MuseTalkEngine.gpu_parallel_engine_v2 import MuseTalkGPUEngine, GPUConfig

# 创建配置
if '$GPU_IDS':
    config = GPUConfig(
        mode='manual',
        gpu_ids=[int(x) for x in '$GPU_IDS'.split(',')],
        batch_size_per_gpu=$BATCH_SIZE
    )
else:
    config = '$GPU_CONFIG'

# 初始化引擎
engine = MuseTalkGPUEngine(config)

# 运行推理
result = engine.inference(
    video_path='$VIDEO_PATH',
    audio_path='$AUDIO_PATH',
    models={},  # 需要加载模型
    args={}
)

print(f'处理完成: {result[\"statistics\"]}')"
            ;;
            
        benchmark)
            python benchmark_gpu.py \
                --config "$GPU_CONFIG" \
                $([ -n "$GPU_IDS" ] && echo "--gpu_ids $GPU_IDS") \
                --batch_size "$BATCH_SIZE"
            ;;
            
        shell)
            python
            ;;
            
        gradio)
            cd MuseTalk && python app.py
            ;;
            
        *)
            log_error "未知的运行模式: $MODE"
            exit 1
            ;;
    esac
}

# 主函数
main() {
    log_info "MuseTalk GPU运行脚本"
    log_info "===================="
    
    # 显示GPU状态
    check_gpu_status
    echo
    
    # 选择GPU
    select_gpus
    echo
    
    # 显示配置
    log_info "运行配置:"
    echo "  GPU配置: $GPU_CONFIG"
    echo "  GPU IDs: ${CUDA_VISIBLE_DEVICES:-all}"
    echo "  批处理大小: $BATCH_SIZE"
    echo "  运行模式: $MODE"
    if [ -n "$VIDEO_PATH" ]; then
        echo "  输入视频: $VIDEO_PATH"
    fi
    if [ -n "$AUDIO_PATH" ]; then
        echo "  输入音频: $AUDIO_PATH"
    fi
    echo
    
    # 运行
    if [ "$USE_DOCKER" = true ]; then
        run_with_docker
    else
        run_locally
    fi
    
    log_info "运行完成"
}

# 执行主函数
main