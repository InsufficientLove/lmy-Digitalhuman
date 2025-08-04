#!/usr/bin/env python3
"""
MuseTalk启动前环境检查脚本
"""

import os
import sys
import subprocess
import torch
import time
import threading
from pathlib import Path

def check_gpu_availability():
    """检查GPU可用性"""
    print("🔍 GPU检查...")
    
    if not torch.cuda.is_available():
        print("❌ CUDA不可用")
        return False
    
    gpu_count = torch.cuda.device_count()
    print(f"✅ 检测到 {gpu_count} 个GPU")
    
    # 检查GPU 0状态
    try:
        torch.cuda.set_device(0)
        # 简单的GPU测试
        x = torch.randn(100, 100, device='cuda:0')
        y = torch.mm(x, x)
        del x, y
        torch.cuda.empty_cache()
        print("✅ GPU 0 测试通过")
        return True
    except Exception as e:
        print(f"❌ GPU 0 测试失败: {e}")
        return False

def check_model_files():
    """检查模型文件"""
    print("\n📁 模型文件检查...")
    
    required_files = [
        'models/musetalk/musetalk.json',
        'models/musetalk/pytorch_model.bin',
        'models/sd-vae/config.json',
        'models/sd-vae/diffusion_pytorch_model.bin',
        'configs/inference/test.yaml'
    ]
    
    for file_path in required_files:
        if os.path.exists(file_path):
            size = os.path.getsize(file_path) / (1024 * 1024)  # MB
            print(f"✅ {file_path} ({size:.1f}MB)")
        else:
            print(f"❌ {file_path} 缺失")
            return False
    
    return True

def quick_import_test():
    """快速导入测试"""
    print("\n🧪 快速导入测试...")
    
    imports = [
        ("torch", "import torch"),
        ("scripts", "import scripts"),
        ("musetalk", "import musetalk"),
        ("load_all_model", "from musetalk.utils.utils import load_all_model")
    ]
    
    for name, import_code in imports:
        try:
            exec(import_code)
            print(f"✅ {name}")
        except Exception as e:
            print(f"❌ {name}: {e}")
            return False
    
    return True

def timeout_wrapper(func, timeout_sec=30):
    """超时包装器"""
    result = [None]
    exception = [None]
    
    def target():
        try:
            result[0] = func()
        except Exception as e:
            exception[0] = e
    
    thread = threading.Thread(target=target)
    thread.daemon = True
    thread.start()
    thread.join(timeout_sec)
    
    if thread.is_alive():
        print(f"⚠️  操作超时 ({timeout_sec}秒)")
        return False
    
    if exception[0]:
        print(f"❌ 操作失败: {exception[0]}")
        return False
    
    return result[0]

def test_minimal_inference():
    """最小化inference测试"""
    print("\n🚀 最小化inference测试...")
    
    # 设置环境变量
    os.environ['CUDA_VISIBLE_DEVICES'] = '0'
    os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'max_split_size_mb:512'
    os.environ['CUDA_LAUNCH_BLOCKING'] = '1'
    
    def run_test():
        try:
            # 只导入，不加载模型
            from musetalk.utils.utils import load_all_model
            print("✅ 导入成功")
            
            # 测试能否创建CUDA张量
            import torch
            device = torch.device('cuda:0')
            test_tensor = torch.randn(10, 10, device=device)
            result = test_tensor * 2
            del test_tensor, result
            torch.cuda.empty_cache()
            print("✅ CUDA操作成功")
            
            return True
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            return False
    
    return timeout_wrapper(run_test, 15)

def diagnose_hanging_issue():
    """诊断卡死问题"""
    print("\n🔍 卡死问题诊断...")
    
    # 1. 检查其他Python进程
    try:
        result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq python.exe'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            lines = result.stdout.split('\n')
            python_processes = [line for line in lines if 'python.exe' in line.lower()]
            if len(python_processes) > 1:
                print(f"⚠️  检测到 {len(python_processes)} 个Python进程:")
                for proc in python_processes[:5]:  # 只显示前5个
                    print(f"   {proc.strip()}")
                print("💡 建议：关闭其他Python进程避免冲突")
    except:
        pass
    
    # 2. 检查GPU进程
    try:
        result = subprocess.run(['nvidia-smi', '--query-compute-apps=pid,process_name,gpu_uuid,used_memory', 
                               '--format=csv,noheader'], capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            print("⚠️  检测到GPU上的其他进程:")
            print(result.stdout)
            print("💡 建议：结束其他GPU进程")
    except:
        pass
    
    # 3. 环境变量检查
    cuda_devices = os.environ.get('CUDA_VISIBLE_DEVICES')
    print(f"📋 CUDA_VISIBLE_DEVICES: {cuda_devices}")
    
    return True

def main():
    print("🛠️  MuseTalk启动前环境检查")
    print("=" * 60)
    
    # 确保在MuseTalk目录中
    if 'MuseTalk' not in os.getcwd():
        print("❌ 请在MuseTalk目录中运行此脚本")
        print(f"当前目录: {os.getcwd()}")
        return
    
    checks = [
        ("GPU可用性", check_gpu_availability),
        ("模型文件", check_model_files),
        ("模块导入", quick_import_test),
        ("最小化测试", test_minimal_inference),
        ("问题诊断", diagnose_hanging_issue)
    ]
    
    all_passed = True
    for check_name, check_func in checks:
        print(f"\n{'='*20} {check_name} {'='*20}")
        if not check_func():
            all_passed = False
            print(f"❌ {check_name} 失败")
        else:
            print(f"✅ {check_name} 通过")
    
    print("\n" + "="*60)
    if all_passed:
        print("🎉 所有检查通过！MuseTalk应该可以正常启动")
        print("\n💡 如果仍然卡死，建议:")
        print("1. 重启系统清理GPU状态")
        print("2. 检查输入文件格式是否正确")
        print("3. 尝试更小的输入文件")
    else:
        print("❌ 部分检查失败，请先解决上述问题")

if __name__ == "__main__":
    main()