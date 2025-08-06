#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import torch
from pathlib import Path

def fix_unet_model():
    """修复UNet模型加载问题"""
    print("=== UNet模型修复工具 ===")
    
    # 切换到MuseTalk目录
    script_dir = Path(__file__).parent
    musetalk_path = script_dir / "MuseTalk"
    
    if not musetalk_path.exists():
        print(f"❌ MuseTalk目录不存在: {musetalk_path}")
        print("正在创建MuseTalk目录结构...")
        musetalk_path.mkdir(parents=True, exist_ok=True)
        (musetalk_path / "models" / "musetalkV15").mkdir(parents=True, exist_ok=True)
        (musetalk_path / "models" / "sd-vae").mkdir(parents=True, exist_ok=True)
        (musetalk_path / "models" / "dwpose").mkdir(parents=True, exist_ok=True)
        print(f"✅ MuseTalk目录结构已创建: {musetalk_path}")
        print("⚠️ 注意: 模型文件仍需要下载，请运行 setup_musetalk_models.py")
        return False
    
    os.chdir(musetalk_path)
    sys.path.insert(0, str(musetalk_path))
    print(f"✅ 工作目录: {os.getcwd()}")
    
    # 检查UNet模型文件
    unet_path = "models/musetalkV15/unet.pth"
    if not os.path.exists(unet_path):
        print(f"❌ UNet模型文件不存在: {unet_path}")
        print("请运行以下命令下载模型文件:")
        print("  python setup_musetalk_models.py")
        print("或手动下载模型文件，详见 MuseTalk/DOWNLOAD_INSTRUCTIONS.md")
        return False
    
    print(f"✅ UNet模型文件存在: {unet_path}")
    print(f"文件大小: {os.path.getsize(unet_path) / (1024*1024):.1f}MB")
    
    try:
        # 尝试直接加载PyTorch模型
        print("测试直接加载UNet模型...")
        model_data = torch.load(unet_path, map_location='cpu')
        print(f"✅ UNet模型加载成功")
        print(f"模型类型: {type(model_data)}")
        
        if isinstance(model_data, dict):
            print(f"模型键: {list(model_data.keys())}")
        
        # 尝试使用MuseTalk的UNet类加载
        print("\n测试MuseTalk UNet类加载...")
        from musetalk.models.unet import UNet
        
        unet_config = "models/musetalkV15/musetalk.json"
        if not os.path.exists(unet_config):
            print(f"❌ UNet配置文件不存在: {unet_config}")
            return False
        
        print(f"✅ UNet配置文件存在: {unet_config}")
        
        # 测试在CPU上加载
        print("在CPU上测试加载UNet...")
        unet = UNet(
            unet_config=unet_config,
            model_path=unet_path,
            device='cpu'  # 先在CPU上测试
        )
        print("✅ UNet在CPU上加载成功")
        
        # 测试移动到GPU
        if torch.cuda.is_available():
            print("测试移动到GPU...")
            try:
                unet.model.to('cuda:0')
                print("✅ UNet成功移动到GPU")
            except Exception as gpu_error:
                print(f"❌ UNet移动到GPU失败: {gpu_error}")
                
                # 尝试修复：重新保存模型
                print("尝试修复模型...")
                try:
                    # 保存修复后的模型
                    backup_path = unet_path + ".backup"
                    if not os.path.exists(backup_path):
                        os.rename(unet_path, backup_path)
                        print(f"✅ 原模型已备份到: {backup_path}")
                    
                    # 重新保存模型（这会修复meta tensor问题）
                    torch.save(unet.model.state_dict(), unet_path)
                    print(f"✅ 模型已修复并保存到: {unet_path}")
                    
                    # 验证修复结果
                    unet_fixed = UNet(
                        unet_config=unet_config,
                        model_path=unet_path,
                        device='cuda:0'
                    )
                    print("✅ 修复后的UNet模型在GPU上加载成功")
                    return True
                    
                except Exception as fix_error:
                    print(f"❌ 模型修复失败: {fix_error}")
                    # 恢复备份
                    if os.path.exists(backup_path):
                        os.rename(backup_path, unet_path)
                        print("已恢复原始模型")
                    return False
        else:
            print("⚠️ CUDA不可用，跳过GPU测试")
            return True
            
    except Exception as e:
        print(f"❌ UNet模型测试失败: {e}")
        print(f"错误类型: {type(e).__name__}")
        return False
    
    return True

def check_model_files():
    """检查所有模型文件"""
    print("\n=== 模型文件完整性检查 ===")
    
    # 切换到正确的工作目录
    script_dir = Path(__file__).parent
    musetalk_path = script_dir / "MuseTalk"
    
    if not musetalk_path.exists():
        print(f"❌ MuseTalk目录不存在: {musetalk_path}")
        return False
    
    os.chdir(musetalk_path)
    print(f"✅ 工作目录: {os.getcwd()}")
    
    required_files = {
        "models/sd-vae/config.json": "VAE配置文件",
        "models/sd-vae/diffusion_pytorch_model.bin": "VAE模型文件(.bin)",
        "models/sd-vae/diffusion_pytorch_model.safetensors": "VAE模型文件(.safetensors)",
        "models/musetalkV15/unet.pth": "UNet模型文件",
        "models/musetalkV15/musetalk.json": "UNet配置文件",
        "models/dwpose/dw-ll_ucoco_384.pth": "DWPose模型文件"
    }
    
    all_good = True
    for file_path, description in required_files.items():
        if os.path.exists(file_path):
            size = os.path.getsize(file_path) / (1024*1024)
            print(f"✅ {description}: {size:.1f}MB")
        else:
            print(f"❌ {description}: 不存在")
            all_good = False
    
    return all_good

if __name__ == "__main__":
    print("MuseTalk模型修复工具")
    print("=" * 50)
    
    if check_model_files():
        print("\n模型文件检查通过")
        if fix_unet_model():
            print("\n✅ UNet模型修复完成！")
            print("现在可以重新启动Python服务")
        else:
            print("\n❌ UNet模型修复失败")
    else:
        print("\n❌ 模型文件不完整，请检查模型文件")