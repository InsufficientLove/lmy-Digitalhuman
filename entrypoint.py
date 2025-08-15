#!/usr/bin/env python3
"""
Docker容器入口点 - 自动优化GPU并运行MuseTalk
"""
import os
import sys
import subprocess
from gpu_optimizer import optimize_for_musetalk

def main():
    # 自动优化GPU配置
    print("正在优化GPU配置...")
    config = optimize_for_musetalk()
    
    # 获取运行模式
    mode = os.environ.get('RUN_MODE', 'gradio')
    
    if mode == 'test':
        # 测试模式
        print("\n运行测试...")
        import torch
        print(f"PyTorch版本: {torch.__version__}")
        print(f"CUDA可用: {torch.cuda.is_available()}")
        print(f"GPU数量: {torch.cuda.device_count()}")
        for i in range(torch.cuda.device_count()):
            print(f"GPU {i}: {torch.cuda.get_device_name(i)}")
            
    elif mode == 'benchmark':
        # 基准测试
        print("\n运行基准测试...")
        # 这里可以添加基准测试代码
        
    elif mode == 'inference':
        # 推理模式
        print("\n运行推理...")
        os.chdir('/app/MuseTalk')
        subprocess.run([
            'python', 'scripts/inference.py',
            '--batch_size', os.environ.get('BATCH_SIZE', '8')
        ])
        
    else:  # gradio
        # Gradio界面
        print("\n启动Gradio界面...")
        os.chdir('/app/MuseTalk')
        
        # 修改app.py的batch_size
        batch_size = os.environ.get('BATCH_SIZE', '8')
        
        # 启动Gradio
        subprocess.run([
            'python', 'app.py',
            '--server_name', '0.0.0.0',
            '--server_port', '7860'
        ])

if __name__ == "__main__":
    main()