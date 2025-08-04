#!/usr/bin/env python3
"""
检查MuseTalk模型文件状态
"""

import os
import sys
from pathlib import Path

def check_model_files():
    """检查所有必需的模型文件"""
    print("🔍 检查MuseTalk模型文件...")
    
    # 确保在MuseTalk目录中
    if 'MuseTalk' not in os.getcwd():
        print("❌ 请在MuseTalk目录中运行此脚本")
        return False
    
    # 检查模型文件
    model_files = {
        'UNet模型': [
            'models/musetalk/pytorch_model.bin',
            'models/musetalk/musetalk.json'
        ],
        'VAE模型': [
            'models/sd-vae/config.json',
            'models/sd-vae/diffusion_pytorch_model.bin',
            'models/sd-vae/diffusion_pytorch_model.safetensors'  # 可选
        ],
        'DWPose模型': [
            'models/dwpose/dw-ll_ucoco_384.pth'
        ],
        'Whisper模型': [
            'models/whisper/config.json',
            'models/whisper/preprocessor_config.json'
        ]
    }
    
    all_good = True
    
    for category, files in model_files.items():
        print(f"\n📁 {category}:")
        for file_path in files:
            if os.path.exists(file_path):
                size = os.path.getsize(file_path) / (1024 * 1024)  # MB
                print(f"  ✅ {file_path} ({size:.1f}MB)")
            else:
                if 'safetensors' in file_path:
                    print(f"  ⚠️  {file_path} (可选，有.bin版本即可)")
                else:
                    print(f"  ❌ {file_path}")
                    all_good = False
    
    # 检查VAE目录的所有文件
    print(f"\n📂 VAE目录所有文件:")
    vae_dir = Path('models/sd-vae')
    if vae_dir.exists():
        for file in vae_dir.iterdir():
            if file.is_file():
                size = file.stat().st_size / (1024 * 1024)
                print(f"  📄 {file.name} ({size:.1f}MB)")
    else:
        print("  ❌ VAE目录不存在")
        all_good = False
    
    return all_good

def test_model_loading():
    """测试模型加载"""
    print("\n🧪 测试模型加载...")
    
    try:
        # 设置环境
        os.environ['CUDA_VISIBLE_DEVICES'] = '0'
        
        # 导入必要模块
        import torch
        from musetalk.utils.utils import load_all_model
        
        device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
        print(f"✅ 设备: {device}")
        
        # 尝试加载模型（这可能会很慢）
        print("🔄 开始加载模型（可能需要1-2分钟）...")
        
        vae, unet, pe = load_all_model(
            unet_model_path="models/musetalk/pytorch_model.bin",
            vae_type="sd-vae",
            unet_config="models/musetalk/musetalk.json",
            device=device
        )
        
        print("✅ 模型加载成功！")
        print(f"  VAE: {type(vae)}")
        print(f"  UNet: {type(unet)}")
        print(f"  PE: {type(pe)}")
        
        return True
        
    except Exception as e:
        print(f"❌ 模型加载失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("🚀 MuseTalk模型文件检查")
    print("=" * 60)
    
    # 1. 检查文件
    files_ok = check_model_files()
    
    if not files_ok:
        print("\n❌ 部分模型文件缺失，请先解决文件问题")
        return
    
    print("\n✅ 所有必需文件都存在")
    
    # 2. 询问是否测试加载
    try:
        test_load = input("\n是否测试模型加载？(y/N): ").strip().lower()
        if test_load in ['y', 'yes']:
            test_model_loading()
    except KeyboardInterrupt:
        print("\n用户取消")

if __name__ == "__main__":
    main()