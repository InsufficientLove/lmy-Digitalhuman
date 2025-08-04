#!/usr/bin/env python3
"""
MuseTalk涡轮增压模式
实现极速推理，目标：3秒视频在10秒内完成
"""

import os
import sys
import time
import torch
import yaml
import argparse
from pathlib import Path

def setup_turbo_environment():
    """设置涡轮增压环境变量"""
    print("🚀 设置涡轮增压环境...")
    
    # 极致性能环境变量
    turbo_env = {
        # GPU优化
        "CUDA_VISIBLE_DEVICES": "0,1,2,3",
        "PYTORCH_CUDA_ALLOC_CONF": "max_split_size_mb:4096,expandable_segments:True,roundup_power2_divisions:16",
        "TORCH_BACKENDS_CUDNN_BENCHMARK": "1",
        "TORCH_BACKENDS_CUDNN_DETERMINISTIC": "0",
        "TORCH_CUDNN_V8_API_ENABLED": "1",
        "TORCH_CUDNN_SDPA_ENABLED": "1",
        
        # CPU优化
        "OMP_NUM_THREADS": "32",
        "MKL_NUM_THREADS": "32",
        "NUMEXPR_NUM_THREADS": "32",
        
        # PyTorch优化
        "TORCH_COMPILE": "1",
        "TORCH_COMPILE_MODE": "max-autotune",
        "TORCH_INDUCTOR_CACHE_SIZE": "1024",
        
        # 内存优化
        "PYTORCH_CUDA_MEMORY_FRACTION": "0.95",
        "TORCH_SHOW_CPP_STACKTRACES": "0",
        
        # 并行优化
        "TOKENIZERS_PARALLELISM": "false",
        "CUBLAS_WORKSPACE_CONFIG": ":4096:8",
        
        # 调试关闭
        "TORCH_WARN": "0",
        "PYTHONWARNINGS": "ignore",
    }
    
    for key, value in turbo_env.items():
        os.environ[key] = value
        print(f"   {key} = {value}")

def create_turbo_config(video_path, audio_path, output_path, bbox_shift=0):
    """创建涡轮增压配置文件"""
    config = {
        "task_001": {
            "video_path": video_path.replace("\\", "/"),
            "audio_path": audio_path.replace("\\", "/"),
            "bbox_shift": bbox_shift,
            "result_name": Path(output_path).name
        }
    }
    
    config_path = f"configs/inference/turbo_{int(time.time())}.yaml"
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    
    with open(config_path, 'w') as f:
        yaml.dump(config, f)
    
    print(f"📝 创建涡轮配置: {config_path}")
    return config_path

def run_turbo_inference(video_path, audio_path, output_dir, bbox_shift=0):
    """运行涡轮增压推理"""
    print("⚡ 启动涡轮增压推理...")
    
    # 设置环境
    setup_turbo_environment()
    
    # 创建输出路径
    output_filename = f"turbo_output_{int(time.time())}.mp4"
    output_path = os.path.join(output_dir, output_filename)
    os.makedirs(output_dir, exist_ok=True)
    
    # 创建配置
    config_path = create_turbo_config(video_path, audio_path, output_path, bbox_shift)
    
    # 构建命令
    cmd = [
        sys.executable, "-m", "scripts.inference",
        "--inference_config", config_path,
        "--result_dir", output_dir,
        "--gpu_id", "0",  # 主GPU
        "--batch_size", "16",  # 大批处理
        "--fps", "25",
        "--use_float16",
        "--version", "v1",
        "--bbox_shift", str(bbox_shift),
        "--skip_save_images",  # 跳过中间图片
        "--low_latency",       # 低延迟模式
        "--optimize_memory",   # 内存优化
    ]
    
    print(f"🎬 执行命令: {' '.join(cmd)}")
    
    # 记录开始时间
    start_time = time.time()
    
    try:
        import subprocess
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)  # 2分钟超时
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        if result.returncode == 0:
            print(f"✅ 涡轮推理成功! 耗时: {processing_time:.2f}秒")
            
            # 查找生成的视频
            possible_paths = [
                output_path,
                os.path.join(output_dir, "v1", output_filename),
                os.path.join(output_dir, "v15", output_filename)
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    print(f"📹 找到输出视频: {path}")
                    file_size = os.path.getsize(path) / 1024  # KB
                    print(f"📊 文件大小: {file_size:.1f}KB")
                    return path
            
            print("⚠️ 推理成功但未找到输出文件")
            return None
            
        else:
            print(f"❌ 推理失败 (退出码: {result.returncode})")
            print(f"错误输出: {result.stderr}")
            return None
            
    except subprocess.TimeoutExpired:
        print("⏰ 推理超时 (>2分钟)")
        return None
    except Exception as e:
        print(f"💥 推理异常: {e}")
        return None
    finally:
        # 清理配置文件
        try:
            if os.path.exists(config_path):
                os.remove(config_path)
        except:
            pass

def benchmark_turbo_mode():
    """基准测试涡轮模式"""
    print("🏁 涡轮模式基准测试")
    
    # 测试文件（需要用户提供）
    test_cases = [
        {
            "name": "短音频测试",
            "video": "data/test_image.jpg",
            "audio": "data/short_audio.wav",  # 1-2秒音频
            "target_time": 5  # 目标5秒内完成
        },
        {
            "name": "中等音频测试", 
            "video": "data/test_image.jpg",
            "audio": "data/medium_audio.wav",  # 3-5秒音频
            "target_time": 10  # 目标10秒内完成
        }
    ]
    
    results = []
    
    for test in test_cases:
        print(f"\n🧪 执行测试: {test['name']}")
        
        if not (os.path.exists(test['video']) and os.path.exists(test['audio'])):
            print(f"⚠️ 测试文件不存在，跳过: {test['name']}")
            continue
        
        start_time = time.time()
        output_path = run_turbo_inference(
            test['video'], 
            test['audio'], 
            "benchmark_results"
        )
        end_time = time.time()
        
        processing_time = end_time - start_time
        success = output_path is not None
        meets_target = processing_time <= test['target_time']
        
        result = {
            "name": test['name'],
            "success": success,
            "time": processing_time,
            "target": test['target_time'],
            "meets_target": meets_target,
            "speedup": test['target_time'] / processing_time if processing_time > 0 else 0
        }
        
        results.append(result)
        
        status = "✅" if success and meets_target else "⚠️" if success else "❌"
        print(f"{status} {test['name']}: {processing_time:.2f}s (目标: {test['target_time']}s)")
    
    # 输出总结
    print("\n📊 基准测试总结:")
    print("=" * 60)
    for result in results:
        status = "✅" if result['success'] and result['meets_target'] else "⚠️" if result['success'] else "❌"
        print(f"{status} {result['name']}: {result['time']:.2f}s / {result['target']}s")
    
    return results

def main():
    parser = argparse.ArgumentParser(description="MuseTalk涡轮增压模式")
    parser.add_argument("--video", help="输入视频/图片路径")
    parser.add_argument("--audio", help="输入音频路径")
    parser.add_argument("--output", default="turbo_results", help="输出目录")
    parser.add_argument("--bbox_shift", type=int, default=0, help="bbox_shift参数")
    parser.add_argument("--benchmark", action="store_true", help="运行基准测试")
    
    args = parser.parse_args()
    
    if args.benchmark:
        benchmark_turbo_mode()
    elif args.video and args.audio:
        result = run_turbo_inference(args.video, args.audio, args.output, args.bbox_shift)
        if result:
            print(f"🎉 涡轮推理完成: {result}")
        else:
            print("💥 涡轮推理失败")
    else:
        print("🚀 MuseTalk涡轮增压模式")
        print("使用方法:")
        print("  python musetalk_turbo_mode.py --video image.jpg --audio audio.wav")
        print("  python musetalk_turbo_mode.py --benchmark")

if __name__ == "__main__":
    main()