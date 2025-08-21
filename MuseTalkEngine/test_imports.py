#!/usr/bin/env python3
"""
测试所有必需的导入
"""

import sys

def test_imports():
    """测试所有关键模块的导入"""
    
    errors = []
    
    # 测试列表
    tests = [
        # PyTorch
        ("torch", "import torch"),
        ("torchvision", "import torchvision"),
        ("torchaudio", "import torchaudio"),
        
        # Hugging Face
        ("diffusers", "from diffusers import AutoencoderKL"),
        ("transformers", "import transformers"),
        ("accelerate", "import accelerate"),
        ("huggingface_hub", "from huggingface_hub import cached_download"),
        
        # MMCV生态
        ("mmcv", "import mmcv"),
        ("mmpose", "from mmpose.apis import inference_topdown, init_model"),
        ("mmdet", "import mmdet"),
        
        # 音视频
        ("cv2", "import cv2"),
        ("librosa", "import librosa"),
        ("imageio", "import imageio"),
        ("soundfile", "import soundfile"),
        
        # 深度学习工具
        ("einops", "from einops import rearrange"),
        ("omegaconf", "import omegaconf"),
        
        # 人脸处理
        ("facexlib", "import facexlib"),
        ("gfpgan", "import gfpgan"),
        
        # Web服务
        ("fastapi", "from fastapi import FastAPI"),
        ("uvicorn", "import uvicorn"),
        
        # MuseTalk模块（如果存在）
        ("musetalk.utils", "from musetalk.utils.utils import datagen, load_all_model"),
        ("musetalk.preprocessing", "from musetalk.utils.preprocessing import get_landmark_and_bbox, read_imgs"),
        ("musetalk.face_parsing", "from musetalk.utils.face_parsing import FaceParsing"),
        ("musetalk.blending", "from musetalk.utils.blending import get_image"),
        ("musetalk.audio_processor", "from musetalk.utils.audio_processor import AudioProcessor"),
    ]
    
    print("=" * 60)
    print("测试依赖导入")
    print("=" * 60)
    
    for name, import_str in tests:
        try:
            exec(import_str)
            print(f"✅ {name:30} - 成功")
        except ImportError as e:
            error_msg = f"❌ {name:30} - 失败: {str(e)}"
            print(error_msg)
            errors.append(error_msg)
        except Exception as e:
            error_msg = f"⚠️ {name:30} - 其他错误: {str(e)}"
            print(error_msg)
            errors.append(error_msg)
    
    print("=" * 60)
    
    # 检查版本
    print("\n版本信息:")
    print("-" * 60)
    
    try:
        import torch
        print(f"PyTorch: {torch.__version__}")
        print(f"CUDA Available: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"CUDA Version: {torch.version.cuda}")
            print(f"GPU Count: {torch.cuda.device_count()}")
    except:
        pass
    
    try:
        import mmcv
        print(f"MMCV: {mmcv.__version__}")
    except:
        pass
    
    try:
        import diffusers
        print(f"Diffusers: {diffusers.__version__}")
    except:
        pass
    
    try:
        import transformers
        print(f"Transformers: {transformers.__version__}")
    except:
        pass
    
    print("=" * 60)
    
    if errors:
        print(f"\n❌ 发现 {len(errors)} 个导入错误:")
        for error in errors:
            print(f"  {error}")
        return False
    else:
        print("\n✅ 所有导入测试通过!")
        return True

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)