#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MuseTalk 路径配置 - 适配服务器环境
Server: Ubuntu 22.04, CUDA 12.9
Models: /opt/musetalk/models/
"""

import os
from pathlib import Path


class ModelPaths:
    """
    模型路径配置类
    
    重要提示：
    如果启动时报错 "Model not found"，请检查 /opt/musetalk/models/ 目录结构，
    并根据实际文件名调整以下路径。
    """
    
    # ==================== 基础路径 ====================
    # 模型根目录（服务器上的绝对路径）
    MODEL_ROOT = Path("/opt/musetalk/models")
    
    # 代码仓库根目录
    REPO_ROOT = Path("/opt/musetalk/repo")
    
    # ==================== 核心模型路径 ====================
    
    # 1. UNet 模型（MuseTalk 核心扩散模型）
    # 路径示例：/opt/musetalk/models/musetalk/pytorch_model.bin
    # 可能的文件名：pytorch_model.bin, unet.pth, musetalk.pt
    UNET_PATH = MODEL_ROOT / "musetalk" / "pytorch_model.bin"
    UNET_CONFIG = MODEL_ROOT / "musetalk" / "musetalk.json"
    
    # 如果文件名不同，请取消注释并修改：
    # UNET_PATH = MODEL_ROOT / "musetalk" / "unet.pth"  # 示例备用名称
    
    # 2. VAE 模型（Stable Diffusion VAE）
    # 路径示例：/opt/musetalk/models/sd-vae/
    # 可能的目录名：sd-vae-ft-mse, sd-vae, vae
    VAE_PATH = MODEL_ROOT / "sd-vae"
    VAE_TYPE = "sd-vae"
    
    # 3. Whisper 模型（音频特征提取）
    # 路径示例：/opt/musetalk/models/whisper/tiny.pt
    # 可能的文件名：tiny.pt, base.pt, small.pt, medium.pt, large.pt
    WHISPER_DIR = MODEL_ROOT / "whisper"
    WHISPER_MODEL = WHISPER_DIR / "tiny.pt"
    
    # 如果使用更大的模型，请取消注释并修改：
    # WHISPER_MODEL = WHISPER_DIR / "base.pt"
    # WHISPER_MODEL = WHISPER_DIR / "small.pt"
    
    # 4. DWPose 模型（人体姿态估计，可选）
    # 路径示例：/opt/musetalk/models/dwpose/
    DWPOSE_PATH = MODEL_ROOT / "dwpose"
    
    # 5. Face Detection 模型（人脸检测）
    # 路径示例：/opt/musetalk/models/face_detection/
    FACE_DETECTION_PATH = MODEL_ROOT / "face_detection"
    
    # ==================== 辅助方法 ====================
    
    @classmethod
    def validate_all(cls):
        """
        验证所有关键路径是否存在
        返回：(is_valid, missing_paths)
        """
        critical_paths = {
            "UNet": cls.UNET_PATH,
            "VAE": cls.VAE_PATH,
            "Whisper Directory": cls.WHISPER_DIR,
        }
        
        missing = []
        for name, path in critical_paths.items():
            if not path.exists():
                missing.append(f"{name}: {path}")
        
        return len(missing) == 0, missing
    
    @classmethod
    def setup_environment(cls):
        """
        设置环境变量（兼容旧代码）
        """
        os.environ['MODEL_PATH'] = str(cls.MODEL_ROOT)
        os.environ['MUSETALK_MODEL_PATH'] = str(cls.MODEL_ROOT)
        os.environ['VAE_PATH'] = str(cls.VAE_PATH)
        os.environ['UNET_PATH'] = str(cls.UNET_PATH)
        os.environ['WHISPER_PATH'] = str(cls.WHISPER_DIR)
        
        # 添加 MuseTalk 源码路径到 Python Path
        musetalk_src = cls.REPO_ROOT / "MuseTalk"
        if musetalk_src.exists():
            import sys
            if str(musetalk_src) not in sys.path:
                sys.path.insert(0, str(musetalk_src))
    
    @classmethod
    def print_config(cls):
        """打印当前配置"""
        print("=" * 60)
        print("📁 MuseTalk 路径配置")
        print("=" * 60)
        print(f"模型根目录:  {cls.MODEL_ROOT}")
        print(f"代码根目录:  {cls.REPO_ROOT}")
        print()
        print("核心模型路径:")
        print(f"  UNet:      {cls.UNET_PATH}")
        print(f"  VAE:       {cls.VAE_PATH}")
        print(f"  Whisper:   {cls.WHISPER_DIR}")
        print(f"  DWPose:    {cls.DWPOSE_PATH}")
        print()
        
        # 验证
        is_valid, missing = cls.validate_all()
        if is_valid:
            print("✅ 所有关键路径验证通过")
        else:
            print("❌ 缺失以下路径:")
            for path in missing:
                print(f"   - {path}")
        print("=" * 60)


# ==================== 快速使用 ====================
if __name__ == "__main__":
    # 打印配置信息
    ModelPaths.print_config()
    
    # 设置环境变量
    ModelPaths.setup_environment()
    
    print("\n✅ 环境变量已设置")
    print("可以在其他脚本中导入使用：")
    print("  from config_paths import ModelPaths")
    print("  ModelPaths.setup_environment()")
