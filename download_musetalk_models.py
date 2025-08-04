#!/usr/bin/env python3
"""
MuseTalk模型文件下载脚本
根据错误日志，需要下载以下缺失的模型文件：
- models/musetalk/musetalk.json
- models/sd-vae/diffusion_pytorch_model.safetensors (或 diffusion_pytorch_model.bin)
"""

import os
import sys
import json
import requests
from pathlib import Path
from tqdm import tqdm

def download_file(url, filepath, description=""):
    """下载文件到指定路径"""
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"正在下载 {description}: {filepath.name}")
    
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        
        with open(filepath, 'wb') as f:
            with tqdm(total=total_size, unit='B', unit_scale=True) as pbar:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        pbar.update(len(chunk))
        
        print(f"✅ 下载完成: {filepath}")
        return True
        
    except Exception as e:
        print(f"❌ 下载失败: {filepath} - {e}")
        return False

def create_musetalk_config():
    """创建基本的musetalk.json配置文件"""
    config = {
        "_name_or_path": "musetalk",
        "activation_fn": "gelu",
        "attention_head_dim": 8,
        "attention_type": "default",
        "block_out_channels": [320, 640, 1280, 1280],
        "center_input_sample": False,
        "class_embed_type": None,
        "conv_in_kernel": 3,
        "conv_out_kernel": 3,
        "cross_attention_dim": 768,
        "cross_attention_norm": None,
        "down_block_types": [
            "CrossAttnDownBlock2D",
            "CrossAttnDownBlock2D", 
            "CrossAttnDownBlock2D",
            "DownBlock2D"
        ],
        "downsample_padding": 1,
        "dual_cross_attention": False,
        "flip_sin_to_cos": True,
        "freq_shift": 0,
        "in_channels": 4,
        "layers_per_block": 2,
        "mid_block_scale_factor": 1,
        "norm_eps": 1e-05,
        "norm_num_groups": 32,
        "num_attention_heads": None,
        "num_class_embeds": None,
        "only_cross_attention": False,
        "out_channels": 4,
        "projection_class_embeddings_input_dim": None,
        "resnet_time_scale_shift": "default",
        "sample_size": 64,
        "time_cond_proj_dim": None,
        "time_embedding_dim": None,
        "time_embedding_type": "positional",
        "timestep_post_act": None,
        "up_block_types": [
            "UpBlock2D",
            "CrossAttnUpBlock2D",
            "CrossAttnUpBlock2D", 
            "CrossAttnUpBlock2D"
        ],
        "upcast_attention": False,
        "use_linear_projection": False
    }
    
    filepath = Path("models/musetalk/musetalk.json")
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 创建配置文件: {filepath}")

def create_sd_vae_config():
    """创建sd-vae配置文件"""
    config = {
        "_class_name": "AutoencoderKL",
        "_diffusers_version": "0.21.4",
        "act_fn": "silu",
        "block_out_channels": [128, 256, 512, 512],
        "down_block_types": [
            "DownEncoderBlock2D",
            "DownEncoderBlock2D",
            "DownEncoderBlock2D",
            "DownEncoderBlock2D"
        ],
        "in_channels": 3,
        "latent_channels": 4,
        "layers_per_block": 2,
        "norm_num_groups": 32,
        "out_channels": 3,
        "sample_size": 512,
        "scaling_factor": 0.18215,
        "up_block_types": [
            "UpDecoderBlock2D",
            "UpDecoderBlock2D", 
            "UpDecoderBlock2D",
            "UpDecoderBlock2D"
        ]
    }
    
    filepath = Path("models/sd-vae/config.json")
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 创建配置文件: {filepath}")

def main():
    print("🚀 开始下载MuseTalk模型文件...")
    
    # MuseTalk模型下载链接 (这些是示例链接，实际使用时需要替换为真实链接)
    model_urls = {
        # MuseTalk主模型
        "models/musetalk/pytorch_model.bin": "https://huggingface.co/TMElyralab/MuseTalk/resolve/main/pytorch_model.bin",
        
        # SD-VAE模型
        "models/sd-vae/diffusion_pytorch_model.safetensors": "https://huggingface.co/stabilityai/sd-vae-ft-mse/resolve/main/diffusion_pytorch_model.safetensors",
        
        # 备用：如果safetensors不可用，使用bin格式
        # "models/sd-vae/diffusion_pytorch_model.bin": "https://huggingface.co/stabilityai/sd-vae-ft-mse/resolve/main/diffusion_pytorch_model.bin",
    }
    
    # 创建配置文件
    print("\n📝 创建配置文件...")
    create_musetalk_config()
    create_sd_vae_config()
    
    # 下载模型文件
    print("\n📥 下载模型文件...")
    success_count = 0
    total_count = len(model_urls)
    
    for filepath, url in model_urls.items():
        if download_file(url, filepath, f"模型文件"):
            success_count += 1
    
    print(f"\n📊 下载结果: {success_count}/{total_count} 文件下载成功")
    
    if success_count == total_count:
        print("🎉 所有模型文件下载完成！")
        print("\n📁 模型文件结构:")
        print("models/")
        print("├── musetalk/")
        print("│   ├── musetalk.json")
        print("│   └── pytorch_model.bin")
        print("└── sd-vae/")
        print("    ├── config.json")
        print("    └── diffusion_pytorch_model.safetensors")
    else:
        print("⚠️  部分文件下载失败，请检查网络连接或手动下载")
        print("\n🔗 手动下载链接：")
        print("MuseTalk模型: https://huggingface.co/TMElyralab/MuseTalk")
        print("SD-VAE模型: https://huggingface.co/stabilityai/sd-vae-ft-mse")
    
    print("\n✨ 提示：如果自动下载失败，请访问以上链接手动下载模型文件")

if __name__ == "__main__":
    main()