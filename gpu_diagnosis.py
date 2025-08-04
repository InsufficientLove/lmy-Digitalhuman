#!/usr/bin/env python3
"""
GPU诊断脚本 - 确保MuseTalk可以正确使用GPU
"""

import os
import sys
import torch
import subprocess

def diagnose_cuda_environment():
    """诊断CUDA环境"""
    print("🔍 CUDA环境诊断")
    print("=" * 50)
    
    # 1. 检查CUDA是否可用
    cuda_available = torch.cuda.is_available()
    print(f"CUDA可用: {'✅ 是' if cuda_available else '❌ 否'}")
    
    if not cuda_available:
        print("❌ CUDA不可用，请检查:")
        print("   1. NVIDIA驱动是否正确安装")
        print("   2. CUDA工具包是否安装")
        print("   3. PyTorch是否为CUDA版本")
        return False
    
    # 2. 检查GPU数量和信息
    gpu_count = torch.cuda.device_count()
    print(f"GPU数量: {gpu_count}")
    
    for i in range(gpu_count):
        gpu_name = torch.cuda.get_device_name(i)
        gpu_memory = torch.cuda.get_device_properties(i).total_memory / 1024**3
        print(f"   GPU {i}: {gpu_name} ({gpu_memory:.1f}GB)")
    
    # 3. 检查当前GPU
    current_device = torch.cuda.current_device()
    print(f"当前GPU: {current_device}")
    
    # 4. 测试GPU内存分配
    try:
        test_tensor = torch.randn(1000, 1000).cuda()
        print("✅ GPU内存分配测试通过")
        del test_tensor
        torch.cuda.empty_cache()
    except Exception as e:
        print(f"❌ GPU内存分配失败: {e}")
        return False
    
    return True

def test_model_loading():
    """测试模型加载到GPU"""
    print("\n🧪 模型GPU加载测试")
    print("=" * 50)
    
    try:
        # 测试简单模型加载
        import torch.nn as nn
        
        model = nn.Linear(100, 10)
        model = model.cuda()
        print("✅ 简单模型GPU加载成功")
        
        # 测试推理
        input_tensor = torch.randn(32, 100).cuda()
        output = model(input_tensor)
        print("✅ GPU推理测试通过")
        
        del model, input_tensor, output
        torch.cuda.empty_cache()
        
    except Exception as e:
        print(f"❌ 模型GPU加载失败: {e}")
        return False
    
    return True

def test_musetalk_dependencies():
    """测试MuseTalk依赖的GPU兼容性"""
    print("\n📦 MuseTalk依赖GPU兼容性测试")
    print("=" * 50)
    
    # 测试mmpose (DWPose依赖)
    try:
        import mmpose
        print("✅ mmpose导入成功")
    except ImportError as e:
        print(f"❌ mmpose导入失败: {e}")
        return False
    
    # 测试diffusers (VAE依赖)
    try:
        from diffusers import AutoencoderKL
        print("✅ diffusers导入成功")
    except ImportError as e:
        print(f"❌ diffusers导入失败: {e}")
        return False
    
    # 测试whisper
    try:
        import whisper
        print("✅ whisper导入成功")
    except ImportError as e:
        print(f"❌ whisper导入失败: {e}")
        return False
    
    return True

def check_environment_variables():
    """检查环境变量配置"""
    print("\n🌍 环境变量检查")
    print("=" * 50)
    
    important_vars = [
        "CUDA_VISIBLE_DEVICES",
        "PYTORCH_CUDA_ALLOC_CONF", 
        "TORCH_CUDNN_V8_API_ENABLED",
        "TORCH_BACKENDS_CUDNN_BENCHMARK"
    ]
    
    for var in important_vars:
        value = os.environ.get(var, "未设置")
        print(f"{var}: {value}")

def test_dwpose_gpu_loading():
    """专门测试DWPose模型GPU加载"""
    print("\n🤖 DWPose GPU加载测试")
    print("=" * 50)
    
    try:
        # 模拟DWPose模型加载过程
        from mmpose.apis import init_model
        
        config_file = "./musetalk/utils/dwpose/rtmpose-l_8xb32-270e_coco-ubody-wholebody-384x288.py"
        checkpoint_file = "./models/dwpose/dw-ll_ucoco_384.pth"
        
        if not os.path.exists(config_file):
            print(f"⚠️ 配置文件不存在: {config_file}")
            return False
            
        if not os.path.exists(checkpoint_file):
            print(f"⚠️ 模型文件不存在: {checkpoint_file}")
            return False
        
        # 尝试加载模型到GPU
        device = 'cuda:0'
        print(f"尝试加载DWPose模型到 {device}...")
        
        model = init_model(config_file, checkpoint_file, device=device)
        print("✅ DWPose模型GPU加载成功!")
        
        del model
        torch.cuda.empty_cache()
        return True
        
    except Exception as e:
        print(f"❌ DWPose模型GPU加载失败: {e}")
        print("这是导致回退到CPU的主要原因!")
        return False

def suggest_fixes():
    """建议修复方案"""
    print("\n💡 修复建议")
    print("=" * 50)
    
    print("1. 确保CUDA环境:")
    print("   nvidia-smi  # 检查GPU状态")
    print("   python -c \"import torch; print(torch.cuda.is_available())\"")
    
    print("\n2. 重新安装PyTorch CUDA版本:")
    print("   pip uninstall torch torchvision torchaudio")
    print("   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118")
    
    print("\n3. 设置环境变量:")
    print("   export CUDA_VISIBLE_DEVICES=0")
    print("   export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512")
    
    print("\n4. 清理GPU内存:")
    print("   python -c \"import torch; torch.cuda.empty_cache()\"")

def main():
    print("🚀 MuseTalk GPU诊断工具")
    print("=" * 50)
    
    # 执行所有诊断
    tests = [
        ("CUDA环境", diagnose_cuda_environment),
        ("模型加载", test_model_loading),
        ("依赖兼容性", test_musetalk_dependencies),
        ("DWPose GPU加载", test_dwpose_gpu_loading)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🧪 执行测试: {test_name}")
        try:
            result = test_func()
            results.append((test_name, result))
            status = "✅ 通过" if result else "❌ 失败"
            print(f"结果: {status}")
        except Exception as e:
            print(f"❌ 测试异常: {e}")
            results.append((test_name, False))
    
    # 检查环境变量
    check_environment_variables()
    
    # 输出总结
    print("\n📊 诊断总结")
    print("=" * 50)
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅" if result else "❌"
        print(f"{status} {test_name}")
    
    print(f"\n通过率: {passed}/{total} ({passed/total*100:.1f}%)")
    
    if passed < total:
        suggest_fixes()
    else:
        print("🎉 所有测试通过! GPU环境配置正确!")

if __name__ == "__main__":
    main()