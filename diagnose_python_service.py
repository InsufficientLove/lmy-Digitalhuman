#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import time
import socket

def check_environment():
    """检查环境配置"""
    print("=== 环境检查 ===")
    
    # 检查Python版本
    print(f"Python版本: {sys.version}")
    
    # 检查CUDA
    try:
        import torch
        print(f"PyTorch版本: {torch.__version__}")
        print(f"CUDA可用: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"CUDA版本: {torch.version.cuda}")
            print(f"GPU数量: {torch.cuda.device_count()}")
            for i in range(torch.cuda.device_count()):
                print(f"  GPU{i}: {torch.cuda.get_device_name(i)}")
    except ImportError as e:
        print(f"PyTorch导入失败: {e}")
    
    print()

def check_model_files():
    """检查模型文件"""
    print("=== 模型文件检查 ===")
    
    # 检查VAE模型
    vae_paths = [
        "models/sd-vae",
        "models/sd-vae-ft-mse"
    ]
    
    for vae_path in vae_paths:
        print(f"检查VAE路径: {vae_path}")
        if os.path.exists(vae_path):
            files = os.listdir(vae_path)
            print(f"  文件列表: {files}")
            
            # 检查关键文件
            key_files = ["config.json", "diffusion_pytorch_model.bin", "diffusion_pytorch_model.safetensors"]
            for key_file in key_files:
                file_path = os.path.join(vae_path, key_file)
                if os.path.exists(file_path):
                    size = os.path.getsize(file_path) / (1024*1024)  # MB
                    print(f"  ✅ {key_file}: {size:.1f}MB")
                else:
                    print(f"  ❌ {key_file}: 不存在")
        else:
            print(f"  ❌ 目录不存在")
    
    # 检查其他模型
    other_models = [
        "models/musetalk",
        "models/dwpose", 
        "models/whisper"
    ]
    
    for model_path in other_models:
        if os.path.exists(model_path):
            print(f"✅ {model_path}: 存在")
        else:
            print(f"❌ {model_path}: 不存在")
    
    print()

def test_model_loading():
    """测试模型加载"""
    print("=== 模型加载测试 ===")
    
    try:
        # 添加路径
        current_dir = os.path.dirname(os.path.abspath(__file__))
        musetalk_path = os.path.join(current_dir, "MuseTalk")
        if os.path.exists(musetalk_path):
            sys.path.insert(0, musetalk_path)
            print(f"添加路径: {musetalk_path}")
        
        # 测试导入
        print("测试导入musetalk模块...")
        from musetalk.utils.utils import load_all_model
        print("✅ musetalk.utils.utils导入成功")
        
        # 测试VAE加载
        print("测试VAE模型加载...")
        try:
            vae, unet, pe = load_all_model()
            print("✅ 默认VAE模型加载成功")
        except Exception as e:
            print(f"❌ 默认VAE模型加载失败: {e}")
            
            # 尝试备用VAE
            try:
                print("尝试备用VAE模型...")
                vae, unet, pe = load_all_model(vae_type="sd-vae-ft-mse")
                print("✅ 备用VAE模型加载成功")
            except Exception as e2:
                print(f"❌ 备用VAE模型也失败: {e2}")
        
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
    except Exception as e:
        print(f"❌ 测试失败: {e}")
    
    print()

def check_port():
    """检查端口占用"""
    print("=== 端口检查 ===")
    
    port = 28888
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', port))
        if result == 0:
            print(f"❌ 端口{port}已被占用")
        else:
            print(f"✅ 端口{port}可用")
        sock.close()
    except Exception as e:
        print(f"端口检查失败: {e}")
    
    print()

def test_manual_service_start():
    """测试手动启动服务"""
    print("=== 手动服务启动测试 ===")
    
    script_path = "start_ultra_fast_service.py"
    if os.path.exists(script_path):
        print(f"找到启动脚本: {script_path}")
        
        print("尝试手动启动服务（10秒超时）...")
        try:
            # 启动服务进程
            process = subprocess.Popen([
                sys.executable, script_path, "--port", "28888"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            # 等待一段时间
            time.sleep(10)
            
            # 检查进程状态
            if process.poll() is None:
                print("✅ 服务进程仍在运行")
                
                # 测试连接
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    result = sock.connect_ex(('127.0.0.1', 28888))
                    if result == 0:
                        print("✅ 端口28888可连接")
                    else:
                        print("❌ 端口28888不可连接")
                    sock.close()
                except:
                    print("❌ 连接测试失败")
                
                # 终止进程
                process.terminate()
                process.wait()
            else:
                print("❌ 服务进程已退出")
                stdout, stderr = process.communicate()
                print(f"标准输出: {stdout}")
                print(f"错误输出: {stderr}")
                
        except Exception as e:
            print(f"启动测试失败: {e}")
    else:
        print(f"❌ 启动脚本不存在: {script_path}")
    
    print()

def main():
    """主诊断函数"""
    print("Python服务启动诊断工具")
    print("=" * 50)
    
    # 切换到正确的工作目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    engine_dir = os.path.join(script_dir, "MuseTalkEngine")
    if os.path.exists(engine_dir):
        os.chdir(engine_dir)
        print(f"工作目录: {engine_dir}")
    else:
        print(f"警告: MuseTalkEngine目录不存在: {engine_dir}")
    
    print()
    
    check_environment()
    check_model_files()
    test_model_loading()
    check_port()
    test_manual_service_start()
    
    print("诊断完成！")
    print("请将以上输出发送给开发者进行分析。")

if __name__ == "__main__":
    main()