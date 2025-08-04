#!/usr/bin/env python3
"""
MuseTalk性能优化和监控脚本
基于官方MuseTalk仓库的最佳实践
"""

import os
import sys
import time
import psutil
import subprocess
import torch
import GPUtil
from pathlib import Path
import json
import argparse

def check_system_requirements():
    """检查系统要求"""
    print("🔍 检查系统要求...")
    
    # 检查CUDA
    if torch.cuda.is_available():
        gpu_count = torch.cuda.device_count()
        print(f"✅ CUDA可用，检测到 {gpu_count} 个GPU")
        for i in range(gpu_count):
            gpu_name = torch.cuda.get_device_name(i)
            gpu_memory = torch.cuda.get_device_properties(i).total_memory / 1024**3
            print(f"   GPU {i}: {gpu_name} ({gpu_memory:.1f}GB)")
    else:
        print("❌ CUDA不可用")
        return False
    
    # 检查内存
    memory = psutil.virtual_memory()
    print(f"💾 系统内存: {memory.total / 1024**3:.1f}GB (可用: {memory.available / 1024**3:.1f}GB)")
    
    # 检查CPU
    cpu_count = psutil.cpu_count()
    print(f"🖥️ CPU核心数: {cpu_count}")
    
    return True

def optimize_environment():
    """设置优化的环境变量"""
    print("⚡ 设置性能优化环境变量...")
    
    # MuseTalk官方推荐的环境变量
    env_vars = {
        "CUDA_VISIBLE_DEVICES": "0,1,2,3",  # 使用所有GPU
        "PYTORCH_CUDA_ALLOC_CONF": "max_split_size_mb:1024",  # 增加内存分配
        "OMP_NUM_THREADS": "16",  # CPU线程数
        "CUDA_LAUNCH_BLOCKING": "0",  # 异步执行
        "TORCH_CUDNN_V8_API_ENABLED": "1",  # 启用cuDNN v8
        "TORCH_BACKENDS_CUDNN_BENCHMARK": "1",  # 启用cuDNN自动调优
        "TOKENIZERS_PARALLELISM": "false",  # 避免tokenizer警告
        "CUBLAS_WORKSPACE_CONFIG": ":16:8",  # CUBLAS工作空间
    }
    
    for key, value in env_vars.items():
        os.environ[key] = value
        print(f"   {key} = {value}")

def check_musetalk_models():
    """检查MuseTalk模型文件"""
    print("📦 检查MuseTalk模型文件...")
    
    model_paths = {
        "UNet配置": "models/musetalk/musetalk.json",
        "UNet模型": "models/musetalk/pytorch_model.bin",
        "Whisper模型": "models/whisper",
        "DWPose模型": "models/dwpose/dw-ll_ucoco_384.pth",
        "VAE模型": "models/sd-vae",
    }
    
    all_exists = True
    for name, path in model_paths.items():
        if os.path.exists(path):
            if os.path.isfile(path):
                size = os.path.getsize(path) / 1024**2  # MB
                print(f"   ✅ {name}: {path} ({size:.1f}MB)")
            else:
                print(f"   ✅ {name}: {path} (目录)")
        else:
            print(f"   ❌ {name}: {path} (缺失)")
            all_exists = False
    
    return all_exists

def monitor_inference_process(pid, duration=300):
    """监控推理进程性能"""
    print(f"📊 监控进程 PID={pid}，持续{duration}秒...")
    
    try:
        process = psutil.Process(pid)
        start_time = time.time()
        
        while time.time() - start_time < duration:
            if not process.is_running():
                print("⚠️ 进程已结束")
                break
                
            # CPU和内存使用
            cpu_percent = process.cpu_percent()
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / 1024**2
            
            # GPU使用情况
            gpus = GPUtil.getGPUs()
            gpu_usage = []
            for gpu in gpus:
                gpu_usage.append(f"GPU{gpu.id}: {gpu.load*100:.1f}%")
            
            print(f"   PID={pid} | CPU: {cpu_percent:.1f}% | 内存: {memory_mb:.1f}MB | {' | '.join(gpu_usage)}")
            
            time.sleep(10)  # 每10秒监控一次
            
    except psutil.NoSuchProcess:
        print("❌ 进程不存在")
    except Exception as e:
        print(f"❌ 监控错误: {e}")

def benchmark_musetalk():
    """MuseTalk性能基准测试"""
    print("🏃 执行MuseTalk性能基准测试...")
    
    # 创建测试配置
    test_config = {
        "task_001": {
            "video_path": "data/test_image.jpg",  # 需要准备测试图片
            "audio_path": "data/test_audio.wav",  # 需要准备测试音频
            "bbox_shift": 0,
            "result_name": "benchmark_output.mp4"
        }
    }
    
    config_path = "configs/inference/benchmark.yaml"
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    
    with open(config_path, 'w') as f:
        import yaml
        yaml.dump(test_config, f)
    
    # 测试不同配置的性能
    configs = [
        {"batch_size": 1, "use_float16": True, "description": "低内存模式"},
        {"batch_size": 4, "use_float16": True, "description": "平衡模式"},
        {"batch_size": 8, "use_float16": True, "description": "高性能模式"},
    ]
    
    results = []
    
    for config in configs:
        print(f"\n🧪 测试配置: {config['description']}")
        
        cmd = [
            sys.executable, "-m", "scripts.inference",
            "--inference_config", config_path,
            "--result_dir", "benchmark_results",
            "--batch_size", str(config["batch_size"]),
            "--fps", "25",
            "--version", "v1"
        ]
        
        if config["use_float16"]:
            cmd.append("--use_float16")
        
        start_time = time.time()
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            end_time = time.time()
            
            duration = end_time - start_time
            success = result.returncode == 0
            
            results.append({
                "config": config["description"],
                "duration": duration,
                "success": success,
                "batch_size": config["batch_size"],
                "use_float16": config["use_float16"]
            })
            
            print(f"   结果: {'成功' if success else '失败'} | 耗时: {duration:.1f}秒")
            if not success:
                print(f"   错误: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            print("   结果: 超时 (>10分钟)")
            results.append({
                "config": config["description"],
                "duration": 600,
                "success": False,
                "batch_size": config["batch_size"],
                "use_float16": config["use_float16"],
                "error": "timeout"
            })
    
    # 输出基准测试结果
    print("\n📈 基准测试结果:")
    print("=" * 60)
    for result in results:
        status = "✅" if result["success"] else "❌"
        print(f"{status} {result['config']}: {result['duration']:.1f}秒")
    
    # 保存结果到文件
    with open("musetalk_benchmark_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    return results

def get_optimal_settings():
    """获取当前系统的最优设置建议"""
    print("💡 分析最优设置...")
    
    # 检查GPU数量和内存
    gpu_count = torch.cuda.device_count() if torch.cuda.is_available() else 0
    
    if gpu_count == 0:
        print("❌ 未检测到CUDA GPU，无法运行MuseTalk")
        return None
    
    # 获取GPU内存
    gpu_memory = []
    for i in range(gpu_count):
        memory = torch.cuda.get_device_properties(i).total_memory / 1024**3
        gpu_memory.append(memory)
    
    min_gpu_memory = min(gpu_memory)
    total_gpu_memory = sum(gpu_memory)
    
    print(f"🎯 检测到 {gpu_count} 个GPU，最小内存: {min_gpu_memory:.1f}GB，总内存: {total_gpu_memory:.1f}GB")
    
    # 推荐设置
    if min_gpu_memory >= 20:  # RTX 4090级别
        recommended = {
            "batch_size": 8,
            "use_float16": True,
            "cuda_devices": f"0,1,2,3" if gpu_count >= 4 else ",".join(map(str, range(gpu_count))),
            "omp_threads": 16,
            "memory_alloc": "max_split_size_mb:1024",
            "description": "高性能模式 (RTX 4090级别)"
        }
    elif min_gpu_memory >= 10:  # RTX 3080级别
        recommended = {
            "batch_size": 4,
            "use_float16": True,
            "cuda_devices": f"0,1" if gpu_count >= 2 else "0",
            "omp_threads": 8,
            "memory_alloc": "max_split_size_mb:512",
            "description": "平衡模式 (RTX 3080级别)"
        }
    else:  # 较低端GPU
        recommended = {
            "batch_size": 1,
            "use_float16": True,
            "cuda_devices": "0",
            "omp_threads": 4,
            "memory_alloc": "max_split_size_mb:256",
            "description": "低内存模式"
        }
    
    print(f"📋 推荐配置: {recommended['description']}")
    print(f"   - batch_size: {recommended['batch_size']}")
    print(f"   - CUDA_VISIBLE_DEVICES: {recommended['cuda_devices']}")
    print(f"   - OMP_NUM_THREADS: {recommended['omp_threads']}")
    print(f"   - PYTORCH_CUDA_ALLOC_CONF: {recommended['memory_alloc']}")
    
    return recommended

def main():
    parser = argparse.ArgumentParser(description="MuseTalk性能优化和监控工具")
    parser.add_argument("--check", action="store_true", help="检查系统要求和模型文件")
    parser.add_argument("--optimize", action="store_true", help="设置优化环境变量")
    parser.add_argument("--monitor", type=int, help="监控指定PID的进程")
    parser.add_argument("--benchmark", action="store_true", help="执行性能基准测试")
    parser.add_argument("--recommend", action="store_true", help="获取最优设置建议")
    
    args = parser.parse_args()
    
    if args.check:
        check_system_requirements()
        check_musetalk_models()
    
    if args.optimize:
        optimize_environment()
    
    if args.monitor:
        monitor_inference_process(args.monitor)
    
    if args.benchmark:
        benchmark_musetalk()
    
    if args.recommend:
        get_optimal_settings()
    
    if not any(vars(args).values()):
        # 默认执行全面检查
        print("🚀 MuseTalk性能优化工具")
        print("=" * 50)
        
        if check_system_requirements():
            check_musetalk_models()
            get_optimal_settings()
            optimize_environment()
            
            print("\n✅ 系统检查完成！")
            print("💡 建议:")
            print("   1. 确保所有模型文件都已下载")
            print("   2. 根据推荐配置调整C#代码中的参数")
            print("   3. 使用 --monitor <PID> 监控运行中的进程")
            print("   4. 使用 --benchmark 测试不同配置的性能")

if __name__ == "__main__":
    main()