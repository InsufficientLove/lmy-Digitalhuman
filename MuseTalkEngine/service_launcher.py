#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
服务启动器 - 根据GPU配置选择最佳服务
"""

import os
import sys
import torch
import argparse

def detect_gpu_config():
    """检测GPU配置"""
    if not torch.cuda.is_available():
        return "cpu", 0, 0
    
    gpu_count = torch.cuda.device_count()
    gpu_name = torch.cuda.get_device_name(0)
    gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)
    
    print(f"🔍 检测到GPU配置:")
    print(f"   GPU数量: {gpu_count}")
    print(f"   GPU型号: {gpu_name}")
    print(f"   显存大小: {gpu_memory:.1f}GB")
    
    return gpu_name, gpu_count, gpu_memory

def main():
    parser = argparse.ArgumentParser(description='MuseTalk服务启动器')
    parser.add_argument('--port', type=int, default=28888, help='服务端口')
    parser.add_argument('--service', type=str, choices=['auto', 'single', 'multi', 'ultra'], 
                       default='auto', help='服务类型')
    args = parser.parse_args()
    
    gpu_name, gpu_count, gpu_memory = detect_gpu_config()
    
    # 自动选择最佳服务
    if args.service == 'auto':
        if gpu_count == 0:
            print("❌ 未检测到GPU，无法运行")
            sys.exit(1)
        elif gpu_count == 1:
            if gpu_memory >= 40:  # 40GB以上显存
                print("✅ 选择: 单GPU优化服务（大显存优化）")
                service_module = 'single_gpu_optimized_service'
            else:
                print("✅ 选择: 标准单GPU服务")
                service_module = 'global_musetalk_service'
        else:
            print(f"✅ 选择: {gpu_count}GPU并行服务")
            service_module = 'ultra_fast_realtime_inference_v2'
    else:
        service_map = {
            'single': 'single_gpu_optimized_service',
            'multi': 'ultra_fast_realtime_inference_v2',
            'ultra': 'ultra_fast_realtime_inference_v2'
        }
        service_module = service_map[args.service]
        print(f"✅ 手动选择: {service_module}")
    
    # 导入并启动服务
    try:
        if service_module == 'single_gpu_optimized_service':
            from single_gpu_optimized_service import start_optimized_service
            start_optimized_service(args.port)
        elif service_module == 'ultra_fast_realtime_inference_v2':
            from ultra_fast_realtime_inference_v2 import start_ultra_fast_service
            start_ultra_fast_service(args.port)
        elif service_module == 'global_musetalk_service':
            from global_musetalk_service import start_global_service
            start_global_service(args.port)
        else:
            print(f"❌ 未知服务: {service_module}")
            sys.exit(1)
            
    except ImportError as e:
        print(f"❌ 无法导入服务模块: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 服务启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()