#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
from pathlib import Path

def quick_fix():
    """快速修复当前问题"""
    print("=== 快速修复工具 ===")
    
    # 切换到正确的工作目录
    script_dir = Path(__file__).parent
    musetalk_path = script_dir / "MuseTalk"
    
    if not musetalk_path.exists():
        print(f"❌ MuseTalk目录不存在: {musetalk_path}")
        return False
    
    os.chdir(musetalk_path)
    sys.path.insert(0, str(musetalk_path))
    print(f"✅ 工作目录: {os.getcwd()}")
    
    # 检查关键模型文件
    print("\n=== 检查关键模型文件 ===")
    key_files = {
        "models/sd-vae/config.json": "VAE配置",
        "models/sd-vae/diffusion_pytorch_model.bin": "VAE模型(.bin)",
        "models/sd-vae/diffusion_pytorch_model.safetensors": "VAE模型(.safetensors)",
    }
    
    for file_path, desc in key_files.items():
        if os.path.exists(file_path):
            size = os.path.getsize(file_path) / (1024*1024)
            print(f"✅ {desc}: {size:.1f}MB")
        else:
            print(f"❌ {desc}: 不存在")
    
    # 测试模型加载
    print("\n=== 测试模型加载 ===")
    try:
        from musetalk.utils.utils import load_all_model
        print("✅ 导入load_all_model成功")
        
        # 测试加载VAE模型
        print("测试加载sd-vae模型...")
        vae, unet, pe = load_all_model(vae_type="sd-vae")
        print("✅ sd-vae模型加载成功")
        
        # 测试移动到GPU
        if hasattr(vae, 'vae'):
            print("测试VAE移动到GPU...")
            vae.vae.to('cuda:0')
            print("✅ VAE移动到GPU成功")
        
        if hasattr(unet, 'model'):
            print("测试UNet移动到GPU...")
            unet.model.to('cuda:0')
            print("✅ UNet移动到GPU成功")
        
        print("测试PE移动到GPU...")
        pe.to('cuda:0')
        print("✅ PE移动到GPU成功")
        
        print("✅ 所有模型组件都能正常加载到GPU")
        return True
        
    except Exception as e:
        print(f"❌ 模型加载失败: {e}")
        print(f"错误类型: {type(e).__name__}")
        
        # 提供具体的修复建议
        if "config.json" in str(e):
            print("\n💡 修复建议:")
            print("1. 检查VAE模型目录是否完整")
            print("2. 确认config.json文件存在且不为空")
        elif "meta tensor" in str(e):
            print("\n💡 修复建议:")
            print("1. UNet模型文件可能损坏")
            print("2. 尝试重新下载UNet模型")
        
        return False

if __name__ == "__main__":
    print("数字人系统快速修复工具")
    print("=" * 50)
    
    if quick_fix():
        print("\n✅ 快速修复完成！模型加载正常")
        print("现在可以重新启动服务")
    else:
        print("\n❌ 发现问题，请查看上面的修复建议")