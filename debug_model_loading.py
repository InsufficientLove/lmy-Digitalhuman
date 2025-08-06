#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
from pathlib import Path

def debug_model_loading():
    """调试模型加载问题"""
    print("=== 模型加载调试 ===")
    
    # 设置正确的工作目录和路径
    script_dir = Path(__file__).parent
    project_root = script_dir
    musetalk_path = project_root / "MuseTalk"
    musetalk_official_path = project_root / "MuseTalk_official"
    
    print(f"脚本目录: {script_dir}")
    print(f"项目根目录: {project_root}")
    print(f"MuseTalk路径: {musetalk_path}")
    print(f"MuseTalk_official路径: {musetalk_official_path}")
    
    # 检查目录是否存在
    if not musetalk_path.exists():
        print(f"❌ MuseTalk目录不存在: {musetalk_path}")
        return
    
    if not musetalk_official_path.exists():
        print(f"❌ MuseTalk_official目录不存在: {musetalk_official_path}")
        return
    
    # 切换到MuseTalk目录（包含models文件夹）
    os.chdir(musetalk_path)
    print(f"✅ 工作目录切换为: {os.getcwd()}")
    
    # 添加Python路径
    sys.path.insert(0, str(musetalk_path))
    sys.path.insert(0, str(musetalk_official_path))
    print(f"✅ Python路径已添加")
    
    # 检查models目录结构
    models_dir = Path("models")
    if models_dir.exists():
        print(f"✅ models目录存在: {models_dir.absolute()}")
        
        # 列出models下的所有子目录
        subdirs = [d for d in models_dir.iterdir() if d.is_dir()]
        print(f"models子目录: {[d.name for d in subdirs]}")
        
        # 检查VAE相关目录
        vae_dirs = ["sd-vae", "sd-vae-ft-mse"]
        for vae_dir in vae_dirs:
            vae_path = models_dir / vae_dir
            if vae_path.exists():
                print(f"✅ {vae_dir}目录存在: {vae_path.absolute()}")
                
                # 列出VAE目录内容
                files = list(vae_path.iterdir())
                print(f"  {vae_dir}内容: {[f.name for f in files]}")
                
                # 检查关键文件
                config_file = vae_path / "config.json"
                bin_file = vae_path / "diffusion_pytorch_model.bin"
                safetensors_file = vae_path / "diffusion_pytorch_model.safetensors"
                
                if config_file.exists():
                    print(f"  ✅ config.json: {config_file.stat().st_size / 1024:.1f}KB")
                else:
                    print(f"  ❌ config.json: 不存在")
                    
                if bin_file.exists():
                    print(f"  ✅ diffusion_pytorch_model.bin: {bin_file.stat().st_size / (1024*1024):.1f}MB")
                else:
                    print(f"  ❌ diffusion_pytorch_model.bin: 不存在")
                    
                if safetensors_file.exists():
                    print(f"  ✅ diffusion_pytorch_model.safetensors: {safetensors_file.stat().st_size / (1024*1024):.1f}MB")
                else:
                    print(f"  ❌ diffusion_pytorch_model.safetensors: 不存在")
            else:
                print(f"❌ {vae_dir}目录不存在: {vae_path.absolute()}")
    else:
        print(f"❌ models目录不存在: {models_dir.absolute()}")
        return
    
    # 测试模型导入
    try:
        print("\n=== 测试模型导入 ===")
        from musetalk.utils.utils import load_all_model
        print("✅ musetalk.utils.utils导入成功")
        
        # 测试VAE模型加载 - 使用绝对路径避免网络请求
        print("\n=== 测试VAE模型加载 ===")
        
        # 首先尝试sd-vae
        sd_vae_path = models_dir / "sd-vae"
        if sd_vae_path.exists():
            print(f"尝试加载sd-vae: {sd_vae_path.absolute()}")
            try:
                # 设置离线模式环境变量
                os.environ['TRANSFORMERS_OFFLINE'] = '1'
                os.environ['HF_DATASETS_OFFLINE'] = '1'
                
                vae, unet, pe = load_all_model(vae_type="sd-vae")
                print("✅ sd-vae模型加载成功")
            except Exception as e:
                print(f"❌ sd-vae模型加载失败: {e}")
                print(f"错误类型: {type(e).__name__}")
                
                # 尝试sd-vae-ft-mse
                sd_vae_ft_mse_path = models_dir / "sd-vae-ft-mse"
                if sd_vae_ft_mse_path.exists():
                    print(f"尝试加载sd-vae-ft-mse: {sd_vae_ft_mse_path.absolute()}")
                    try:
                        vae, unet, pe = load_all_model(vae_type="sd-vae-ft-mse")
                        print("✅ sd-vae-ft-mse模型加载成功")
                    except Exception as e2:
                        print(f"❌ sd-vae-ft-mse模型也加载失败: {e2}")
                        print(f"错误类型: {type(e2).__name__}")
        
    except ImportError as e:
        print(f"❌ 模块导入失败: {e}")
    except Exception as e:
        print(f"❌ 其他错误: {e}")

if __name__ == "__main__":
    debug_model_loading()