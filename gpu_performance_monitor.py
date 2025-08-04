#!/usr/bin/env python3
"""
GPU性能监控脚本 - 监控4x RTX 4090的利用率
"""

import time
import subprocess
import json
import os
from datetime import datetime

def get_gpu_stats():
    """获取GPU统计信息"""
    try:
        result = subprocess.run([
            'nvidia-smi', 
            '--query-gpu=index,name,utilization.gpu,utilization.memory,memory.used,memory.total,temperature.gpu,power.draw',
            '--format=csv,noheader,nounits'
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            gpu_stats = []
            
            for line in lines:
                parts = [p.strip() for p in line.split(',')]
                if len(parts) >= 8:
                    gpu_stats.append({
                        'index': int(parts[0]),
                        'name': parts[1],
                        'gpu_util': int(parts[2]) if parts[2] != '[Not Supported]' else 0,
                        'mem_util': int(parts[3]) if parts[3] != '[Not Supported]' else 0,
                        'mem_used': int(parts[4]),
                        'mem_total': int(parts[5]),
                        'temperature': int(parts[6]) if parts[6] != '[Not Supported]' else 0,
                        'power': float(parts[7]) if parts[7] != '[Not Supported]' else 0
                    })
            
            return gpu_stats
        else:
            print(f"nvidia-smi错误: {result.stderr}")
            return []
            
    except Exception as e:
        print(f"获取GPU状态失败: {e}")
        return []

def monitor_performance(duration_minutes=5, interval_seconds=5):
    """监控GPU性能"""
    print(f"🚀 开始监控GPU性能 - 时长: {duration_minutes}分钟, 间隔: {interval_seconds}秒")
    print("=" * 100)
    
    start_time = time.time()
    end_time = start_time + (duration_minutes * 60)
    
    max_utils = [0, 0, 0, 0]  # 4个GPU的最大利用率
    avg_utils = [0, 0, 0, 0]  # 平均利用率
    sample_count = 0
    
    while time.time() < end_time:
        gpu_stats = get_gpu_stats()
        
        if gpu_stats:
            sample_count += 1
            current_time = datetime.now().strftime("%H:%M:%S")
            
            print(f"\n⏰ {current_time}")
            print("-" * 100)
            
            total_gpu_util = 0
            total_mem_used = 0
            total_mem_total = 0
            
            for i, gpu in enumerate(gpu_stats):
                if i < 4:  # 只显示前4个GPU
                    gpu_util = gpu['gpu_util']
                    mem_used = gpu['mem_used']
                    mem_total = gpu['mem_total']
                    mem_percent = (mem_used / mem_total * 100) if mem_total > 0 else 0
                    
                    # 更新统计
                    max_utils[i] = max(max_utils[i], gpu_util)
                    avg_utils[i] = ((avg_utils[i] * (sample_count - 1)) + gpu_util) / sample_count
                    
                    total_gpu_util += gpu_util
                    total_mem_used += mem_used
                    total_mem_total += mem_total
                    
                    # 显示GPU状态
                    utilization_bar = "█" * (gpu_util // 5) + "░" * (20 - gpu_util // 5)
                    memory_bar = "█" * int(mem_percent // 5) + "░" * (20 - int(mem_percent // 5))
                    
                    print(f"GPU {i}: {gpu['name']}")
                    print(f"  利用率: {gpu_util:3d}% [{utilization_bar}] 温度: {gpu['temperature']:2d}°C 功耗: {gpu['power']:5.1f}W")
                    print(f"  显存:   {mem_percent:5.1f}% [{memory_bar}] {mem_used:5d}/{mem_total:5d}MB")
            
            # 总体统计
            avg_gpu_util = total_gpu_util / 4
            total_mem_percent = (total_mem_used / total_mem_total * 100) if total_mem_total > 0 else 0
            
            print("-" * 100)
            print(f"📊 总体: GPU平均利用率 {avg_gpu_util:.1f}%, 总显存使用 {total_mem_percent:.1f}% ({total_mem_used}MB/{total_mem_total}MB)")
            
            # 性能提示
            if avg_gpu_util < 50:
                print("💡 GPU利用率较低，可能存在性能瓶颈")
            elif avg_gpu_util > 90:
                print("🔥 GPU利用率很高，性能良好")
            
        time.sleep(interval_seconds)
    
    print("\n" + "=" * 100)
    print("📈 监控总结:")
    for i in range(4):
        print(f"GPU {i}: 最大利用率 {max_utils[i]}%, 平均利用率 {avg_utils[i]:.1f}%")
    
    overall_max = max(max_utils)
    overall_avg = sum(avg_utils) / 4
    
    print(f"\n🎯 总体性能: 最大利用率 {overall_max}%, 平均利用率 {overall_avg:.1f}%")
    
    if overall_avg < 30:
        print("❌ GPU利用率过低，可能的原因:")
        print("   1. 批处理大小太小")
        print("   2. CPU成为瓶颈")
        print("   3. I/O操作耗时过长")
        print("   4. 代码未充分利用GPU并行")
    elif overall_avg < 70:
        print("⚠️  GPU利用率中等，有优化空间")
    else:
        print("✅ GPU利用率良好")

def main():
    print("🖥️  GPU性能监控工具 - 专为4x RTX 4090优化")
    print("适用于监控MuseTalk运行时的GPU使用情况")
    print()
    
    # 检查nvidia-smi是否可用
    try:
        subprocess.run(['nvidia-smi', '-v'], capture_output=True, timeout=5)
    except:
        print("❌ nvidia-smi不可用，请检查NVIDIA驱动安装")
        return
    
    # 检查GPU数量
    gpu_stats = get_gpu_stats()
    if not gpu_stats:
        print("❌ 无法获取GPU信息")
        return
    
    print(f"✅ 检测到 {len(gpu_stats)} 个GPU:")
    for gpu in gpu_stats:
        print(f"   GPU {gpu['index']}: {gpu['name']} ({gpu['mem_total']}MB)")
    print()
    
    try:
        duration = int(input("监控时长（分钟，默认5）: ") or "5")
        interval = int(input("采样间隔（秒，默认3）: ") or "3")
    except ValueError:
        duration, interval = 5, 3
    
    monitor_performance(duration, interval)

if __name__ == "__main__":
    main()