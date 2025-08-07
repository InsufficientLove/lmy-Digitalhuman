#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import torch
from pathlib import Path
import time
import gc

def test_gpu_memory():
    """测试GPU内存状况"""
    print("=== GPU内存检查 ===")
    
    if not torch.cuda.is_available():
        print("❌ CUDA不可用")
        return False
    
    gpu_count = torch.cuda.device_count()
    print(f"检测到 {gpu_count} 个GPU")
    
    for i in range(gpu_count):
        try:
            torch.cuda.set_device(i)
            total_memory = torch.cuda.get_device_properties(i).total_memory / (1024**3)
            allocated = torch.cuda.memory_allocated(i) / (1024**3)
            reserved = torch.cuda.memory_reserved(i) / (1024**3)
            free = total_memory - reserved
            
            print(f"GPU {i} ({torch.cuda.get_device_name(i)}):")
            print(f"  总显存: {total_memory:.1f}GB")
            print(f"  已分配: {allocated:.1f}GB")
            print(f"  已保留: {reserved:.1f}GB") 
            print(f"  可用: {free:.1f}GB")
            
            if free < 8.0:  # MuseTalk建议至少8GB
                print(f"  ⚠️ GPU {i} 可用显存不足，建议至少8GB")
            else:
                print(f"  ✅ GPU {i} 显存充足")
                
        except Exception as e:
            print(f"❌ GPU {i} 检查失败: {e}")
    
    return True

def test_single_gpu_loading():
    """测试单GPU加载"""
    print("\n=== 单GPU模型加载测试 ===")
    
    script_dir = Path(__file__).parent
    musetalk_dir = script_dir / "MuseTalk"
    
    if not musetalk_dir.exists():
        print(f"❌ MuseTalk目录不存在: {musetalk_dir}")
        return False
    
    # 切换到MuseTalk目录
    original_cwd = os.getcwd()
    os.chdir(musetalk_dir)
    sys.path.insert(0, str(musetalk_dir))
    
    try:
        print("正在导入MuseTalk模块...")
        from musetalk.utils.utils import load_all_model
        print("✅ 模块导入成功")
        
        # 清理GPU内存
        if torch.cuda.is_available():
            for i in range(torch.cuda.device_count()):
                torch.cuda.set_device(i)
                torch.cuda.empty_cache()
        gc.collect()
        
        print("测试在GPU 0上加载模型...")
        torch.cuda.set_device(0)
        
        start_time = time.time()
        vae, unet, pe = load_all_model(vae_type="sd-vae")
        load_time = time.time() - start_time
        
        print(f"✅ 单GPU加载成功！耗时: {load_time:.1f}秒")
        
        # 检查模型是否正确加载到GPU
        if hasattr(unet, 'model'):
            device = next(unet.model.parameters()).device
            print(f"UNet模型设备: {device}")
        
        # 清理内存
        del vae, unet, pe
        torch.cuda.empty_cache()
        gc.collect()
        
        return True
        
    except Exception as e:
        print(f"❌ 单GPU加载失败: {e}")
        if "Cannot copy out of meta tensor" in str(e):
            print("这是meta tensor问题，但自检显示模型文件正常")
            print("可能是模型加载到GPU时出现的问题")
        return False
    finally:
        os.chdir(original_cwd)

def test_sequential_gpu_loading():
    """测试顺序GPU加载"""
    print("\n=== 顺序GPU加载测试 ===")
    
    script_dir = Path(__file__).parent
    musetalk_dir = script_dir / "MuseTalk"
    
    # 切换到MuseTalk目录
    original_cwd = os.getcwd()
    os.chdir(musetalk_dir)
    sys.path.insert(0, str(musetalk_dir))
    
    try:
        from musetalk.utils.utils import load_all_model
        
        gpu_count = min(4, torch.cuda.device_count())
        loaded_models = []
        
        for i in range(gpu_count):
            print(f"\n正在GPU {i}上加载模型...")
            
            # 清理当前GPU内存
            torch.cuda.set_device(i)
            torch.cuda.empty_cache()
            gc.collect()
            
            try:
                start_time = time.time()
                vae, unet, pe = load_all_model(vae_type="sd-vae")
                load_time = time.time() - start_time
                
                # 确保模型在正确的GPU上
                if hasattr(unet, 'model'):
                    unet.model = unet.model.to(f'cuda:{i}')
                if hasattr(vae, 'model'):
                    vae.model = vae.model.to(f'cuda:{i}')
                if hasattr(pe, 'model'):
                    pe.model = pe.model.to(f'cuda:{i}')
                
                loaded_models.append((vae, unet, pe))
                print(f"✅ GPU {i} 加载成功！耗时: {load_time:.1f}秒")
                
                # 检查GPU内存使用
                allocated = torch.cuda.memory_allocated(i) / (1024**3)
                print(f"GPU {i} 内存使用: {allocated:.1f}GB")
                
            except Exception as e:
                print(f"❌ GPU {i} 加载失败: {e}")
                if "Cannot copy out of meta tensor" in str(e):
                    print(f"GPU {i} 出现meta tensor错误")
                elif "out of memory" in str(e).lower():
                    print(f"GPU {i} 显存不足")
                return False
        
        print(f"\n✅ 所有 {gpu_count} 个GPU都加载成功！")
        
        # 清理所有模型
        for models in loaded_models:
            del models
        
        for i in range(gpu_count):
            torch.cuda.set_device(i)
            torch.cuda.empty_cache()
        gc.collect()
        
        return True
        
    except Exception as e:
        print(f"❌ 顺序加载测试失败: {e}")
        return False
    finally:
        os.chdir(original_cwd)

def fix_ultra_fast_service_script():
    """修复ultra_fast_service脚本中的问题"""
    print("\n=== 检查Ultra Fast Service脚本 ===")
    
    script_dir = Path(__file__).parent
    service_script = script_dir / "MuseTalkEngine" / "ultra_fast_realtime_inference_v2.py"
    
    if not service_script.exists():
        print(f"❌ 服务脚本不存在: {service_script}")
        return False
    
    print(f"✅ 服务脚本存在: {service_script}")
    
    # 读取脚本内容检查问题
    try:
        with open(service_script, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否有并发加载问题
        if "load_all_model" in content:
            print("✅ 发现load_all_model调用")
            
            # 检查是否有适当的错误处理
            if "Cannot copy out of meta tensor" in content:
                print("✅ 脚本已包含meta tensor错误处理")
            else:
                print("⚠️ 脚本可能缺少meta tensor错误处理")
            
            # 检查GPU内存清理
            if "torch.cuda.empty_cache()" in content:
                print("✅ 脚本包含GPU内存清理")
            else:
                print("⚠️ 脚本可能缺少GPU内存清理")
        
        return True
        
    except Exception as e:
        print(f"❌ 脚本检查失败: {e}")
        return False

def generate_fixed_service_config():
    """生成修复建议的服务配置"""
    print("\n=== 生成修复建议 ===")
    
    suggestions = [
        "基于测试结果，以下是修复建议:",
        "",
        "1. **减少并行GPU数量**",
        "   - 如果4GPU同时加载失败，尝试使用2GPU或单GPU",
        "   - 修改启动脚本中的GPU配置",
        "",
        "2. **增加GPU内存清理**",
        "   - 在每次模型加载前调用 torch.cuda.empty_cache()",
        "   - 添加垃圾回收 gc.collect()",
        "",
        "3. **顺序加载而非并行加载**",
        "   - 先在一个GPU上加载成功，再复制到其他GPU",
        "   - 避免同时访问模型文件",
        "",
        "4. **添加重试机制**",
        "   - 如果meta tensor错误，清理内存后重试",
        "   - 添加指数退避重试策略",
        "",
        "5. **检查模型文件锁定**",
        "   - 确保没有其他进程占用模型文件",
        "   - 添加文件访问检查"
    ]
    
    for suggestion in suggestions:
        print(suggestion)
    
    # 生成修复配置文件
    config_file = Path(__file__).parent / "gpu_loading_fix_config.txt"
    with open(config_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(suggestions))
    
    print(f"\n✅ 修复建议已保存到: {config_file}")

def main():
    print("MuseTalk GPU并行加载问题诊断和修复工具")
    print("=" * 50)
    
    # 检查GPU内存
    if not test_gpu_memory():
        return
    
    # 测试单GPU加载
    if not test_single_gpu_loading():
        print("❌ 单GPU加载失败，问题可能在模型加载逻辑")
        return
    
    # 测试顺序GPU加载
    if not test_sequential_gpu_loading():
        print("❌ 多GPU加载失败，建议使用单GPU或减少并行数")
    else:
        print("✅ 多GPU顺序加载成功")
    
    # 检查服务脚本
    fix_ultra_fast_service_script()
    
    # 生成修复建议
    generate_fixed_service_config()
    
    print("\n" + "=" * 50)
    print("=== 诊断完成 ===")
    print("请根据上述建议修改MuseTalk服务配置")
    print("如果问题仍然存在，建议:")
    print("1. 重启系统清理GPU状态")
    print("2. 使用单GPU模式启动服务")
    print("3. 检查是否有其他进程占用GPU")
    
    print("\n按任意键退出...")
    try:
        input()
    except:
        pass

if __name__ == "__main__":
    main()