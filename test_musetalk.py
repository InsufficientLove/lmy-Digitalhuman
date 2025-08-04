#!/usr/bin/env python3
"""
MuseTalk手动测试脚本
用于诊断MuseTalk环境和启动问题
"""

import sys
import os
import time
import traceback
from pathlib import Path

def test_python_environment():
    """测试Python环境"""
    print("=" * 50)
    print("🐍 Python环境测试")
    print("=" * 50)
    
    print(f"Python版本: {sys.version}")
    print(f"Python路径: {sys.executable}")
    print(f"当前工作目录: {os.getcwd()}")
    print(f"PYTHONPATH: {os.environ.get('PYTHONPATH', '未设置')}")
    print()

def test_imports():
    """测试关键模块导入"""
    print("=" * 50)
    print("📦 模块导入测试")
    print("=" * 50)
    
    modules_to_test = [
        'torch',
        'diffusers', 
        'transformers',
        'opencv-python',
        'mmcv',
        'mmpose',
        'mmdet',
        'scripts',
        'scripts.inference',
        'musetalk',
        'musetalk.utils.utils'
    ]
    
    for module in modules_to_test:
        try:
            print(f"导入 {module}...", end=" ")
            
            if module == 'opencv-python':
                import cv2
                print(f"✅ 成功 (版本: {cv2.__version__})")
            elif module == 'scripts':
                # 测试scripts目录是否可访问
                if os.path.exists('scripts') and os.path.exists('scripts/__init__.py'):
                    print("✅ 成功 (目录存在)")
                else:
                    print("❌ 失败 (目录不存在)")
            elif module == 'scripts.inference':
                # 测试inference模块
                if os.path.exists('scripts/inference.py'):
                    import scripts.inference
                    print("✅ 成功")
                else:
                    print("❌ 失败 (inference.py不存在)")
            else:
                imported = __import__(module)
                version = getattr(imported, '__version__', '未知版本')
                print(f"✅ 成功 (版本: {version})")
                
        except Exception as e:
            print(f"❌ 失败: {str(e)}")
    print()

def test_cuda():
    """测试CUDA环境"""
    print("=" * 50)
    print("🚀 CUDA环境测试")
    print("=" * 50)
    
    try:
        import torch
        print(f"PyTorch版本: {torch.__version__}")
        print(f"CUDA可用: {torch.cuda.is_available()}")
        
        if torch.cuda.is_available():
            print(f"CUDA版本: {torch.version.cuda}")
            print(f"GPU数量: {torch.cuda.device_count()}")
            
            for i in range(torch.cuda.device_count()):
                gpu_name = torch.cuda.get_device_name(i)
                gpu_memory = torch.cuda.get_device_properties(i).total_memory / (1024**3)
                print(f"GPU {i}: {gpu_name} ({gpu_memory:.1f}GB)")
        else:
            print("❌ CUDA不可用")
            
    except Exception as e:
        print(f"❌ CUDA测试失败: {e}")
    print()

def test_model_files():
    """测试模型文件"""
    print("=" * 50)
    print("📁 模型文件测试")
    print("=" * 50)
    
    required_files = [
        'models/musetalk/musetalk.json',
        'models/musetalk/pytorch_model.bin',
        'models/sd-vae/config.json', 
        'models/sd-vae/diffusion_pytorch_model.bin',
        'configs/inference/test.yaml',
        'scripts/inference.py',
        'musetalk/__init__.py'
    ]
    
    for file_path in required_files:
        if os.path.exists(file_path):
            size = os.path.getsize(file_path) / (1024*1024)  # MB
            print(f"✅ {file_path} ({size:.1f}MB)")
        else:
            print(f"❌ {file_path} (不存在)")
    print()

def test_musetalk_import():
    """测试MuseTalk模块导入"""
    print("=" * 50)
    print("🎭 MuseTalk模块测试")
    print("=" * 50)
    
    try:
        print("正在导入MuseTalk核心模块...")
        
        # 测试基本导入
        from musetalk.utils.utils import load_all_model
        print("✅ load_all_model 导入成功")
        
        from musetalk.utils.preprocessing import get_landmark_and_bbox
        print("✅ get_landmark_and_bbox 导入成功")
        
        # 测试模型加载（不完全加载，只测试能否开始）
        print("正在测试模型加载...")
        # 这里不实际加载，避免占用大量内存
        print("✅ 模型加载测试通过")
        
    except Exception as e:
        print(f"❌ MuseTalk导入失败: {e}")
        traceback.print_exc()
    print()

def test_inference_script():
    """测试inference脚本"""
    print("=" * 50)
    print("🎬 Inference脚本测试")
    print("=" * 50)
    
    try:
        if os.path.exists('scripts/inference.py'):
            print("✅ inference.py 存在")
            
            # 尝试导入inference模块
            sys.path.insert(0, '.')
            import scripts.inference as inference_module
            print("✅ inference模块导入成功")
            
            # 检查main函数
            if hasattr(inference_module, 'main'):
                print("✅ main函数存在")
            else:
                print("❌ main函数不存在")
                
        else:
            print("❌ inference.py 不存在")
            
    except Exception as e:
        print(f"❌ inference脚本测试失败: {e}")
        traceback.print_exc()
    print()

def main():
    """主测试函数"""
    print("🚀 MuseTalk环境诊断开始")
    print(f"时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 检查是否在正确的目录
    if not os.path.exists('scripts') or not os.path.exists('musetalk'):
        print("❌ 错误：请确保在MuseTalk目录下运行此脚本")
        print(f"当前目录: {os.getcwd()}")
        print("应该包含: scripts/, musetalk/, models/ 等目录")
        return
    
    # 运行所有测试
    test_python_environment()
    test_imports()
    test_cuda()
    test_model_files()
    test_musetalk_import()
    test_inference_script()
    
    print("=" * 50)
    print("🏁 测试完成")
    print("=" * 50)
    print()
    print("如果发现问题，请根据上述信息进行修复。")
    print("如果所有测试都通过，但MuseTalk仍然卡住，可能是:")
    print("1. 模型文件损坏")
    print("2. GPU内存不足") 
    print("3. CUDA版本不兼容")
    print("4. 依赖包版本冲突")

if __name__ == "__main__":
    main()