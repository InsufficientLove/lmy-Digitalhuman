#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
from pathlib import Path

def simple_self_check():
    """简单的自检工具"""
    print("MuseTalk 虚拟环境自检工具")
    print("=" * 40)
    
    # 检查当前Python环境
    print(f"当前Python版本: {sys.version}")
    print(f"当前Python路径: {sys.executable}")
    print(f"当前工作目录: {os.getcwd()}")
    
    # 检查是否在虚拟环境中
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✅ 当前运行在虚拟环境中")
        print(f"虚拟环境路径: {sys.prefix}")
    else:
        print("❌ 当前未运行在虚拟环境中")
        print("请使用: venv_musetalk\\Scripts\\python.exe simple_venv_check.py")
        return False
    
    # 检查PyTorch
    print("\n=== PyTorch检查 ===")
    try:
        import torch
        print(f"✅ PyTorch已安装: {torch.__version__}")
        print(f"CUDA可用: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"CUDA版本: {torch.version.cuda}")
            print(f"GPU数量: {torch.cuda.device_count()}")
            for i in range(torch.cuda.device_count()):
                try:
                    gpu_name = torch.cuda.get_device_name(i)
                    print(f"  GPU {i}: {gpu_name}")
                except:
                    print(f"  GPU {i}: [无法获取名称]")
    except ImportError:
        print("❌ PyTorch未安装")
        return False
    except Exception as e:
        print(f"❌ PyTorch检查失败: {e}")
        return False
    
    # 检查MuseTalk目录和文件
    print("\n=== MuseTalk文件检查 ===")
    script_dir = Path(__file__).parent
    musetalk_dir = script_dir / "MuseTalk"
    
    if not musetalk_dir.exists():
        print(f"❌ MuseTalk目录不存在: {musetalk_dir}")
        return False
    
    print(f"✅ MuseTalk目录存在: {musetalk_dir}")
    
    # 检查关键文件
    required_files = {
        "UNet模型": "models/musetalkV15/unet.pth",
        "UNet配置": "models/musetalkV15/musetalk.json", 
        "VAE配置": "models/sd-vae/config.json",
        "VAE模型(.bin)": "models/sd-vae/diffusion_pytorch_model.bin",
        "DWPose模型": "models/dwpose/dw-ll_ucoco_384.pth"
    }
    
    all_files_ok = True
    for name, rel_path in required_files.items():
        full_path = musetalk_dir / rel_path
        if full_path.exists():
            size_mb = full_path.stat().st_size / (1024*1024)
            print(f"✅ {name}: {size_mb:.1f}MB")
        else:
            print(f"❌ {name}: 不存在")
            all_files_ok = False
    
    if not all_files_ok:
        print("❌ 部分模型文件缺失")
        return False
    
    # 简单测试PyTorch操作
    print("\n=== PyTorch基本操作测试 ===")
    try:
        x = torch.randn(2, 3, 4, 4)
        y = torch.nn.functional.relu(x)
        print("✅ PyTorch基本操作正常")
    except Exception as e:
        print(f"❌ PyTorch基本操作失败: {e}")
        return False
    
    # 测试UNet模型文件加载
    print("\n=== UNet模型文件测试 ===")
    try:
        # 切换到MuseTalk目录
        original_cwd = os.getcwd()
        os.chdir(musetalk_dir)
        
        unet_path = "models/musetalkV15/unet.pth"
        print(f"正在测试加载: {unet_path}")
        
        # 直接加载模型数据
        model_data = torch.load(unet_path, map_location='cpu')
        print("✅ UNet模型文件读取成功")
        print(f"模型数据类型: {type(model_data)}")
        
        # 检查meta tensor
        meta_tensor_count = 0
        total_tensors = 0
        meta_tensor_keys = []
        
        if isinstance(model_data, dict):
            for key, value in model_data.items():
                if torch.is_tensor(value):
                    total_tensors += 1
                    if hasattr(value, 'is_meta') and value.is_meta:
                        meta_tensor_count += 1
                        meta_tensor_keys.append(key)
        
        print(f"总张量数: {total_tensors}")
        print(f"Meta张量数: {meta_tensor_count}")
        
        if meta_tensor_count > 0:
            print("❌ 发现meta tensor问题！")
            print(f"Meta tensor示例: {meta_tensor_keys[:3]}")
            print("这就是导致 'Cannot copy out of meta tensor' 错误的原因")
            return "meta_tensor_issue"
        else:
            print("✅ 没有发现meta tensor问题")
        
        # 恢复工作目录
        os.chdir(original_cwd)
        
    except Exception as e:
        print(f"❌ UNet模型测试失败: {e}")
        os.chdir(original_cwd)
        if "Cannot copy out of meta tensor" in str(e):
            print("确认这是meta tensor问题")
            return "meta_tensor_issue"
        return False
    
    # 尝试导入MuseTalk模块
    print("\n=== MuseTalk模块导入测试 ===")
    try:
        # 添加MuseTalk路径
        sys.path.insert(0, str(musetalk_dir))
        
        from musetalk.utils.utils import load_all_model
        print("✅ 成功导入load_all_model")
        
        # 简单测试（不完整加载，避免GPU占用）
        print("MuseTalk模块导入正常")
        
    except ImportError as e:
        print(f"❌ MuseTalk模块导入失败: {e}")
        return False
    except Exception as e:
        print(f"❌ MuseTalk模块测试失败: {e}")
        return False
    
    return True

def main():
    result = simple_self_check()
    
    print("\n" + "=" * 40)
    print("=== 自检结果 ===")
    
    if result == "meta_tensor_issue":
        print("🔧 检测到meta tensor问题")
        print("这就是导致您的MuseTalk服务启动失败的原因")
        print("建议: 需要修复UNet模型中的meta tensor")
        print("\n推荐解决方案:")
        print("1. 重新下载UNet模型文件")
        print("2. 或使用模型修复工具")
    elif result == True:
        print("🎉 所有检查都通过！")
        print("虚拟环境和MuseTalk组件都正常")
        print("如果仍有问题，可能是运行时的GPU内存或其他问题")
    else:
        print("❌ 发现问题，请根据上述检查结果进行修复")
    
    print("\n按任意键退出...")
    try:
        input()
    except:
        pass

if __name__ == "__main__":
    main()