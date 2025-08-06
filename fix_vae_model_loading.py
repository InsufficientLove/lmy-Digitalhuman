#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import shutil
from pathlib import Path

def fix_vae_model_path():
    """修复VAE模型路径问题"""
    
    # 定义可能的VAE模型路径
    possible_vae_paths = [
        "models/sd-vae",
        "models/sd-vae-ft-mse", 
        "../MuseTalk/models/sd-vae",
        "../MuseTalk/models/sd-vae-ft-mse"
    ]
    
    print("检查VAE模型文件...")
    
    for vae_path in possible_vae_paths:
        if os.path.exists(vae_path):
            print(f"找到VAE目录: {vae_path}")
            
            # 检查是否存在.bin文件但缺少.safetensors文件
            bin_file = os.path.join(vae_path, "diffusion_pytorch_model.bin")
            safetensors_file = os.path.join(vae_path, "diffusion_pytorch_model.safetensors")
            
            if os.path.exists(bin_file) and not os.path.exists(safetensors_file):
                print(f"发现.bin文件但缺少.safetensors文件: {bin_file}")
                print("这是正常的，HuggingFace会自动处理")
                
                # 检查config.json是否存在
                config_file = os.path.join(vae_path, "config.json")
                if not os.path.exists(config_file):
                    print(f"警告: 缺少config.json文件: {config_file}")
                else:
                    print(f"config.json存在: {config_file}")
            
            elif os.path.exists(safetensors_file):
                print(f"找到.safetensors文件: {safetensors_file}")
            
            # 列出目录内容
            try:
                files = os.listdir(vae_path)
                print(f"VAE目录内容: {files}")
            except Exception as e:
                print(f"无法列出目录内容: {e}")
    
    print("VAE模型检查完成")

def create_vae_loading_patch():
    """创建VAE加载的补丁"""
    
    patch_content = '''
# VAE模型加载补丁
# 这个补丁确保能正确加载.bin格式的VAE模型

import os
from diffusers import AutoencoderKL

def load_vae_with_fallback(model_path):
    """
    加载VAE模型，支持.bin和.safetensors格式
    """
    try:
        # 首先尝试正常加载
        vae = AutoencoderKL.from_pretrained(model_path)
        print(f"VAE模型加载成功: {model_path}")
        return vae
    except Exception as e:
        print(f"VAE模型加载失败: {e}")
        
        # 检查是否是因为缺少.safetensors文件
        bin_file = os.path.join(model_path, "diffusion_pytorch_model.bin")
        if os.path.exists(bin_file):
            print(f"尝试强制加载.bin文件: {bin_file}")
            try:
                # 强制使用本地文件
                vae = AutoencoderKL.from_pretrained(
                    model_path,
                    use_safetensors=False,  # 强制不使用safetensors
                    local_files_only=True   # 只使用本地文件
                )
                print("VAE模型(.bin格式)加载成功")
                return vae
            except Exception as e2:
                print(f"强制加载.bin文件也失败: {e2}")
        
        raise e

# 使用示例:
# vae = load_vae_with_fallback("./models/sd-vae")
'''
    
    with open("vae_loading_patch.py", "w", encoding="utf-8") as f:
        f.write(patch_content)
    
    print("VAE加载补丁已创建: vae_loading_patch.py")

if __name__ == "__main__":
    fix_vae_model_path()
    create_vae_loading_patch()