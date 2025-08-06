#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import requests
import hashlib
import json
from pathlib import Path
from urllib.parse import urlparse
import torch

class MuseTalkModelSetup:
    def __init__(self):
        self.base_dir = Path(__file__).parent / "MuseTalk"
        self.models_dir = self.base_dir / "models"
        
        # Model configurations and download URLs
        self.model_configs = {
            "unet": {
                "path": "models/musetalkV15/unet.pth",
                "description": "MuseTalk UNet Model",
                "size_mb": 400,
                "url": "https://huggingface.co/TMElyralab/MuseTalk/resolve/main/models/musetalk/pytorch_model.bin",
                "alternative_urls": [
                    "https://github.com/TMElyralab/MuseTalk/releases/download/v1.0.0/unet.pth"
                ]
            },
            "unet_config": {
                "path": "models/musetalkV15/musetalk.json",
                "description": "MuseTalk UNet Configuration",
                "content": {
                    "in_channels": 4,
                    "out_channels": 4,
                    "model_channels": 320,
                    "attention_resolutions": [4, 2, 1],
                    "num_res_blocks": 2,
                    "channel_mult": [1, 2, 4, 4],
                    "num_heads": 8,
                    "use_spatial_transformer": True,
                    "transformer_depth": 1,
                    "context_dim": 768,
                    "use_checkpoint": True,
                    "legacy": False
                }
            },
            "vae_config": {
                "path": "models/sd-vae/config.json",
                "description": "VAE Configuration",
                "content": {
                    "act_fn": "silu",
                    "block_out_channels": [128, 256, 512, 512],
                    "down_block_types": ["DownEncoderBlock2D", "DownEncoderBlock2D", "DownEncoderBlock2D", "DownEncoderBlock2D"],
                    "in_channels": 3,
                    "latent_channels": 4,
                    "layers_per_block": 2,
                    "norm_num_groups": 32,
                    "out_channels": 3,
                    "sample_size": 512,
                    "up_block_types": ["UpDecoderBlock2D", "UpDecoderBlock2D", "UpDecoderBlock2D", "UpDecoderBlock2D"]
                }
            },
            "vae_bin": {
                "path": "models/sd-vae/diffusion_pytorch_model.bin",
                "description": "VAE Model (.bin)",
                "size_mb": 320,
                "url": "https://huggingface.co/stabilityai/sd-vae-ft-mse/resolve/main/diffusion_pytorch_model.bin"
            },
            "vae_safetensors": {
                "path": "models/sd-vae/diffusion_pytorch_model.safetensors",
                "description": "VAE Model (.safetensors)",
                "size_mb": 320,
                "url": "https://huggingface.co/stabilityai/sd-vae-ft-mse/resolve/main/diffusion_pytorch_model.safetensors"
            },
            "dwpose": {
                "path": "models/dwpose/dw-ll_ucoco_384.pth",
                "description": "DWPose Model",
                "size_mb": 200,
                "url": "https://huggingface.co/yzd-v/DWPose/resolve/main/dw-ll_ucoco_384.pth"
            }
        }
    
    def create_directories(self):
        """Create necessary directories"""
        print("=== 创建目录结构 ===")
        
        directories = [
            self.base_dir,
            self.models_dir / "musetalkV15",
            self.models_dir / "sd-vae", 
            self.models_dir / "dwpose"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            print(f"✅ 目录创建: {directory}")
    
    def download_file(self, url, output_path, description):
        """Download a file with progress tracking"""
        print(f"正在下载 {description}...")
        print(f"URL: {url}")
        print(f"保存到: {output_path}")
        
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            percent = (downloaded / total_size) * 100
                            print(f"\r进度: {percent:.1f}% ({downloaded/1024/1024:.1f}MB/{total_size/1024/1024:.1f}MB)", end='')
            
            print(f"\n✅ {description} 下载完成")
            return True
            
        except Exception as e:
            print(f"\n❌ {description} 下载失败: {e}")
            return False
    
    def create_config_file(self, path, content, description):
        """Create a JSON configuration file"""
        try:
            full_path = self.base_dir / path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(full_path, 'w', encoding='utf-8') as f:
                json.dump(content, f, indent=2, ensure_ascii=False)
            
            print(f"✅ {description} 配置文件创建: {full_path}")
            return True
        except Exception as e:
            print(f"❌ {description} 配置文件创建失败: {e}")
            return False
    
    def verify_file(self, path, expected_size_mb=None):
        """Verify if a file exists and has the expected size"""
        full_path = self.base_dir / path
        if not full_path.exists():
            return False
        
        size_mb = full_path.stat().st_size / (1024 * 1024)
        if expected_size_mb and abs(size_mb - expected_size_mb) > expected_size_mb * 0.1:  # 10% tolerance
            print(f"⚠️ 文件大小异常: {path} ({size_mb:.1f}MB, 期望: {expected_size_mb}MB)")
            return False
        
        return True
    
    def setup_models(self):
        """Setup all required models"""
        print("=== MuseTalk 模型设置 ===")
        print("此脚本将下载和设置 MuseTalk 所需的所有模型文件")
        print("注意: 总下载大小约 1.2GB，请确保网络连接稳定")
        print()
        
        # Create directories
        self.create_directories()
        
        success_count = 0
        total_count = len(self.model_configs)
        
        for model_name, config in self.model_configs.items():
            print(f"\n--- 处理 {config['description']} ---")
            
            # Check if file already exists
            if self.verify_file(config['path'], config.get('size_mb')):
                print(f"✅ {config['description']} 已存在且完整")
                success_count += 1
                continue
            
            # Handle config files
            if 'content' in config:
                if self.create_config_file(config['path'], config['content'], config['description']):
                    success_count += 1
                continue
            
            # Handle downloadable files
            if 'url' in config:
                full_path = self.base_dir / config['path']
                if self.download_file(config['url'], full_path, config['description']):
                    if self.verify_file(config['path'], config.get('size_mb')):
                        success_count += 1
                    else:
                        print(f"❌ {config['description']} 下载后验证失败")
                else:
                    # Try alternative URLs if available
                    if 'alternative_urls' in config:
                        for alt_url in config['alternative_urls']:
                            print(f"尝试备用链接...")
                            if self.download_file(alt_url, full_path, config['description']):
                                if self.verify_file(config['path'], config.get('size_mb')):
                                    success_count += 1
                                    break
                                else:
                                    print(f"❌ {config['description']} 备用链接下载后验证失败")
        
        print(f"\n=== 设置完成 ===")
        print(f"成功: {success_count}/{total_count}")
        
        if success_count == total_count:
            print("✅ 所有模型文件设置完成！")
            return True
        else:
            print("❌ 部分模型文件设置失败")
            print("\n缺失的文件需要手动下载:")
            
            for model_name, config in self.model_configs.items():
                if not self.verify_file(config['path'], config.get('size_mb')):
                    print(f"- {config['description']}: {config['path']}")
                    if 'url' in config:
                        print(f"  下载链接: {config['url']}")
            
            return False
    
    def create_download_instructions(self):
        """Create a file with manual download instructions"""
        instructions_path = self.base_dir / "DOWNLOAD_INSTRUCTIONS.md"
        
        content = """# MuseTalk 模型下载说明

由于网络或其他原因，某些模型文件可能需要手动下载。请按照以下说明操作：

## 必需的模型文件

### 1. MuseTalk UNet 模型
- 文件路径: `models/musetalkV15/unet.pth`
- 大小: ~400MB
- 下载链接: 
  - https://huggingface.co/TMElyralab/MuseTalk/resolve/main/models/musetalk/pytorch_model.bin
  - https://github.com/TMElyralab/MuseTalk/releases/download/v1.0.0/unet.pth

### 2. VAE 模型 (.bin)
- 文件路径: `models/sd-vae/diffusion_pytorch_model.bin`
- 大小: ~320MB
- 下载链接: https://huggingface.co/stabilityai/sd-vae-ft-mse/resolve/main/diffusion_pytorch_model.bin

### 3. VAE 模型 (.safetensors)
- 文件路径: `models/sd-vae/diffusion_pytorch_model.safetensors`
- 大小: ~320MB
- 下载链接: https://huggingface.co/stabilityai/sd-vae-ft-mse/resolve/main/diffusion_pytorch_model.safetensors

### 4. DWPose 模型
- 文件路径: `models/dwpose/dw-ll_ucoco_384.pth`
- 大小: ~200MB
- 下载链接: https://huggingface.co/yzd-v/DWPose/resolve/main/dw-ll_ucoco_384.pth

## 下载方法

### 方法1: 使用 wget 或 curl
```bash
# 下载 UNet 模型
wget -O models/musetalkV15/unet.pth "https://huggingface.co/TMElyralab/MuseTalk/resolve/main/models/musetalk/pytorch_model.bin"

# 下载 VAE 模型
wget -O models/sd-vae/diffusion_pytorch_model.bin "https://huggingface.co/stabilityai/sd-vae-ft-mse/resolve/main/diffusion_pytorch_model.bin"
wget -O models/sd-vae/diffusion_pytorch_model.safetensors "https://huggingface.co/stabilityai/sd-vae-ft-mse/resolve/main/diffusion_pytorch_model.safetensors"

# 下载 DWPose 模型
wget -O models/dwpose/dw-ll_ucoco_384.pth "https://huggingface.co/yzd-v/DWPose/resolve/main/dw-ll_ucoco_384.pth"
```

### 方法2: 使用 huggingface_hub
```python
from huggingface_hub import hf_hub_download

# 下载模型文件
hf_hub_download(repo_id="TMElyralab/MuseTalk", filename="models/musetalk/pytorch_model.bin", local_dir="./models/musetalkV15/", local_dir_use_symlinks=False)
hf_hub_download(repo_id="stabilityai/sd-vae-ft-mse", filename="diffusion_pytorch_model.bin", local_dir="./models/sd-vae/", local_dir_use_symlinks=False)
hf_hub_download(repo_id="stabilityai/sd-vae-ft-mse", filename="diffusion_pytorch_model.safetensors", local_dir="./models/sd-vae/", local_dir_use_symlinks=False)
hf_hub_download(repo_id="yzd-v/DWPose", filename="dw-ll_ucoco_384.pth", local_dir="./models/dwpose/", local_dir_use_symlinks=False)
```

## 验证下载

下载完成后，运行以下命令验证文件完整性：

```bash
python setup_musetalk_models.py --verify-only
```

## 故障排除

1. **网络连接问题**: 尝试使用代理或更换网络环境
2. **存储空间不足**: 确保至少有 2GB 可用空间
3. **权限问题**: 确保对目标目录有写入权限

如果仍有问题，请查看项目文档或提交 Issue。
"""
        
        with open(instructions_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ 下载说明已创建: {instructions_path}")

def main():
    setup = MuseTalkModelSetup()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--verify-only":
        print("=== 验证模型文件 ===")
        success_count = 0
        total_count = len(setup.model_configs)
        
        for model_name, config in setup.model_configs.items():
            if setup.verify_file(config['path'], config.get('size_mb')):
                print(f"✅ {config['description']}")
                success_count += 1
            else:
                print(f"❌ {config['description']} - 文件缺失或损坏")
        
        print(f"\n验证结果: {success_count}/{total_count} 文件正常")
        return success_count == total_count
    
    # Full setup
    if setup.setup_models():
        print("\n🎉 MuseTalk 模型设置完成！")
        print("现在可以运行 MuseTalk 服务了。")
    else:
        print("\n⚠️ 部分模型文件设置失败")
        setup.create_download_instructions()
        print("请查看 DOWNLOAD_INSTRUCTIONS.md 获取手动下载说明")

if __name__ == "__main__":
    main()