#!/usr/bin/env python3
"""
精确模拟C#调用环境的MuseTalk诊断脚本
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def simulate_csharp_environment():
    """模拟C#设置的环境变量"""
    print("🔧 模拟C#环境配置...")
    
    # 模拟C#设置的环境变量
    env_vars = {
        'CUDA_VISIBLE_DEVICES': '0,1,2,3',
        'PYTORCH_CUDA_ALLOC_CONF': 'max_split_size_mb:1024,garbage_collection_threshold:0.6',
        'OMP_NUM_THREADS': '16',
        'CUDA_LAUNCH_BLOCKING': '0',
        'TORCH_CUDNN_V8_API_ENABLED': '1',
        'CUBLAS_WORKSPACE_CONFIG': ':4096:8'
    }
    
    for key, value in env_vars.items():
        os.environ[key] = value
        print(f"✅ {key} = {value}")
    
    # 设置PYTHONPATH（假设在MuseTalk目录中运行）
    current_dir = os.getcwd()
    if 'MuseTalk' not in current_dir:
        print("❌ 请在MuseTalk目录中运行此脚本")
        return False
        
    os.environ['PYTHONPATH'] = current_dir
    print(f"✅ PYTHONPATH = {current_dir}")
    
    return True

def test_inference_command():
    """测试实际的inference命令"""
    print("\n🧪 测试scripts.inference命令...")
    
    # 构建与C#相同的命令
    cmd = [
        sys.executable, '-m', 'scripts.inference',
        '--inference_config', 'configs/inference/test.yaml',
        '--result_dir', './test_output',
        '--unet_model_path', 'models/musetalk/pytorch_model.bin',
        '--unet_config', 'models/musetalk/musetalk.json',
        '--version', 'v1',
        '--use_float16',
        '--batch_size', '8',
        '--fps', '25',
        '--gpu_id', '0',
        '--help'  # 只显示帮助，不实际运行
    ]
    
    print(f"命令: {' '.join(cmd)}")
    
    try:
        # 使用短超时来测试命令是否能启动
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            timeout=10,
            cwd=os.getcwd()
        )
        
        print(f"返回码: {result.returncode}")
        if result.stdout:
            print(f"标准输出:\n{result.stdout}")
        if result.stderr:
            print(f"错误输出:\n{result.stderr}")
            
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("⚠️  命令超时（10秒）- 可能在等待输入或卡住")
        return False
    except Exception as e:
        print(f"❌ 命令执行失败: {e}")
        return False

def test_step_by_step_import():
    """逐步测试导入过程"""
    print("\n🔍 逐步导入测试...")
    
    steps = [
        ("导入PyTorch", "import torch"),
        ("检查CUDA", "print(f'CUDA可用: {torch.cuda.is_available()}')"),
        ("设置GPU", "torch.cuda.set_device(0)"),
        ("导入scripts", "import scripts"),
        ("导入inference", "from scripts import inference"),
        ("导入musetalk", "import musetalk"),
        ("导入utils", "from musetalk.utils.utils import load_all_model"),
    ]
    
    for step_name, code in steps:
        print(f"\n📝 {step_name}...")
        try:
            exec(code)
            print(f"✅ 成功")
        except Exception as e:
            print(f"❌ 失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    return True

def test_model_loading_minimal():
    """最小化模型加载测试"""
    print("\n🏗️  最小化模型加载测试...")
    
    try:
        print("检查模型文件...")
        model_files = [
            'models/musetalk/musetalk.json',
            'models/musetalk/pytorch_model.bin'
        ]
        
        for file_path in model_files:
            if os.path.exists(file_path):
                size = os.path.getsize(file_path) / (1024 * 1024)  # MB
                print(f"✅ {file_path} ({size:.1f}MB)")
            else:
                print(f"❌ {file_path} 不存在")
                return False
        
        print("\n开始导入load_all_model...")
        from musetalk.utils.utils import load_all_model
        print("✅ load_all_model导入成功")
        
        print("\n⚠️  跳过实际模型加载以避免卡死")
        print("如需测试实际加载，请手动运行:")
        print("vae, unet, pe = load_all_model('models/musetalk/pytorch_model.bin', 'models/musetalk/musetalk.json', 'v1')")
        
        return True
        
    except Exception as e:
        print(f"❌ 模型加载测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_config_files():
    """检查配置文件"""
    print("\n📄 检查配置文件...")
    
    config_files = [
        'configs/inference/test.yaml',
        'musetalk/utils/dwpose/rtmpose-l_8xb32-270e_coco-ubody-wholebody-384x288.py',
        'musetalk/utils/dwpose/default_runtime.py'
    ]
    
    for config_file in config_files:
        if os.path.exists(config_file):
            print(f"✅ {config_file}")
        else:
            print(f"❌ {config_file} 不存在")
            return False
    
    return True

def main():
    print("🚀 MuseTalk精确环境诊断")
    print("=" * 80)
    
    # 1. 环境配置
    if not simulate_csharp_environment():
        return
    
    # 2. 配置文件检查
    if not check_config_files():
        print("\n❌ 配置文件检查失败")
        return
    
    # 3. 逐步导入测试
    if not test_step_by_step_import():
        print("\n❌ 模块导入失败")
        return
    
    # 4. 模型加载测试
    if not test_model_loading_minimal():
        print("\n❌ 模型加载准备失败")
        return
    
    # 5. 命令测试
    if not test_inference_command():
        print("\n❌ inference命令测试失败")
        return
    
    print("\n" + "=" * 80)
    print("✅ 所有基础测试通过!")
    print("\n💡 下一步建议:")
    print("1. 检查是否有其他进程占用GPU")
    print("2. 尝试单GPU运行（CUDA_VISIBLE_DEVICES=0）")
    print("3. 减少batch_size到1或2")
    print("4. 检查输入文件是否有问题")

if __name__ == "__main__":
    main()