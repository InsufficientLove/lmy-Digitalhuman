#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实时推理服务 - 高性能 FastAPI + PyTorch FP16
适配服务器环境：Ubuntu 22.04, CUDA 12.9
模型路径：/opt/musetalk/models/
"""

import os
import sys
import io
import cv2
import pickle
import torch
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional
from contextlib import asynccontextmanager
import asyncio
import time
import warnings
warnings.filterwarnings("ignore")

# FastAPI 核心
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# ==================== 🔧 关键修改：导入路径配置 ====================
from config_paths import ModelPaths

# 设置环境变量（在导入 MuseTalk 之前）
ModelPaths.setup_environment()
ModelPaths.print_config()

# ==================== 添加 MuseTalk 路径 ====================
MUSETALK_PATH = str(ModelPaths.REPO_ROOT / "MuseTalk")
sys.path.insert(0, MUSETALK_PATH)

try:
    from musetalk.utils.utils import load_all_model, datagen
    from musetalk.utils.blending import get_image_blending
    from musetalk.utils.audio_processor import AudioProcessor
    print("✅ 成功导入 MuseTalk 核心模块")
except ImportError as e:
    print(f"❌ 无法导入 MuseTalk 模块: {e}")
    print(f"请检查路径: {MUSETALK_PATH}")
    sys.exit(1)


# ==================== 全局状态管理 ====================
class GlobalState:
    """全局状态 - 模型和资产缓存"""
    
    def __init__(self):
        # GPU 配置
        self.device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        self.dtype = torch.float16  # 强制 FP16
        
        # 🔧 模型路径（从配置读取）
        self.model_paths = ModelPaths
        
        # 模型实例
        self.vae = None
        self.unet = None
        self.pe = None
        self.audio_processor = None
        self.whisper = None
        
        # 资产缓存（驻留内存）
        self.asset_cache = {}  # {asset_id: {"frames": [], "bboxes": [], ...}}
        
        # 预热状态
        self.is_warmed_up = False
        
        print(f"🎮 GPU 设备: {self.device}")
        print(f"📊 数据类型: {self.dtype}")
    
    def load_models(self):
        """加载所有模型到 GPU（FP16）"""
        print("=" * 60)
        print("🚀 开始加载模型...")
        print("=" * 60)
        
        try:
            # 🔧 验证模型路径
            is_valid, missing = self.model_paths.validate_all()
            if not is_valid:
                print("❌ 模型路径验证失败，缺失以下文件:")
                for path in missing:
                    print(f"   - {path}")
                raise FileNotFoundError(
                    f"请检查 /opt/musetalk/models/ 目录结构，"
                    f"并根据实际情况修改 config_paths.py"
                )
            
            # 🔧 切换到 MuseTalk 工作目录（某些模型加载需要相对路径）
            original_dir = os.getcwd()
            musetalk_dir = Path(MUSETALK_PATH)
            if musetalk_dir.exists():
                os.chdir(musetalk_dir)
                print(f"📂 工作目录: {musetalk_dir}")
            
            # 🔧 加载模型（使用配置的路径）
            print("⚙️ 加载 VAE、UNet、PE...")
            print(f"  UNet: {self.model_paths.UNET_PATH}")
            print(f"  VAE: {self.model_paths.VAE_PATH}")
            
            # load_all_model 会从环境变量中读取路径
            audio_processor, vae, unet, pe = load_all_model()
            
            # 转换为 FP16 并移动到 GPU
            print("⚡ 转换为 FP16 并移动到 GPU...")
            
            # VAE
            if hasattr(vae, 'vae'):
                vae.vae = vae.vae.to(self.device, dtype=self.dtype).eval()
                print("  ✅ VAE -> FP16")
            elif hasattr(vae, 'to'):
                vae = vae.to(self.device, dtype=self.dtype).eval()
                print("  ✅ VAE -> FP16")
            
            # UNet
            if hasattr(unet, 'model'):
                unet.model = unet.model.to(self.device, dtype=self.dtype).eval()
                print("  ✅ UNet -> FP16")
            elif hasattr(unet, 'to'):
                unet = unet.to(self.device, dtype=self.dtype).eval()
                print("  ✅ UNet -> FP16")
            
            # PE (音频编码器)
            if hasattr(pe, 'to'):
                pe = pe.to(self.device, dtype=self.dtype).eval()
                print("  ✅ PE -> FP16")
            
            # AudioProcessor
            self.audio_processor = audio_processor
            print("  ✅ AudioProcessor")
            
            # 🔧 可选：加载 Whisper（如果路径存在）
            if self.model_paths.WHISPER_DIR.exists():
                print(f"⚙️ 加载 Whisper 模型: {self.model_paths.WHISPER_DIR}")
                try:
                    from transformers import WhisperModel
                    self.whisper = WhisperModel.from_pretrained(
                        str(self.model_paths.WHISPER_DIR)
                    ).to(self.device).eval()
                    print("  ✅ Whisper -> GPU")
                except Exception as e:
                    print(f"  ⚠️ Whisper 加载失败: {e}")
                    self.whisper = None
            
            # 可选：torch.compile 加速 (PyTorch 2.0+)
            if hasattr(torch, 'compile') and os.environ.get('USE_TORCH_COMPILE', '0') == '1':
                print("🔥 启用 torch.compile 优化...")
                try:
                    if hasattr(unet, 'model'):
                        unet.model = torch.compile(unet.model, mode="reduce-overhead")
                        print("  ✅ UNet 已编译")
                    if hasattr(vae, 'vae') and hasattr(vae.vae, 'decoder'):
                        vae.vae.decoder = torch.compile(vae.vae.decoder, mode="reduce-overhead")
                        print("  ✅ VAE Decoder 已编译")
                except Exception as e:
                    print(f"  ⚠️ torch.compile 失败: {e}")
            
            # 保存到全局状态
            self.vae = vae
            self.unet = unet
            self.pe = pe
            
            # 恢复工作目录
            os.chdir(original_dir)
            
            # 显存统计
            if torch.cuda.is_available():
                allocated = torch.cuda.memory_allocated(self.device) / 1e9
                reserved = torch.cuda.memory_reserved(self.device) / 1e9
                print(f"\n💾 显存占用: {allocated:.2f}GB (预留: {reserved:.2f}GB)")
            
            print("=" * 60)
            print("✅ 模型加载完成!")
            print("=" * 60)
            
        except Exception as e:
            print(f"❌ 模型加载失败: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def warmup(self):
        """预热 CUDA kernel"""
        if self.is_warmed_up:
            return
        
        print("\n🔥 开始预热 CUDA kernel...")
        try:
            # 创建假数据
            dummy_latent = torch.randn(1, 8, 64, 64, device=self.device, dtype=self.dtype)
            dummy_audio = torch.randn(1, 768, device=self.device, dtype=self.dtype)
            timesteps = torch.tensor([0], device=self.device, dtype=torch.long)
            
            # 预热 PE
            with torch.no_grad():
                _ = self.pe(dummy_audio)
            
            # 预热 UNet
            if hasattr(self.unet, 'model'):
                with torch.no_grad():
                    _ = self.unet.model(dummy_latent, timesteps, encoder_hidden_states=dummy_audio)
            
            # 预热 VAE
            if hasattr(self.vae, 'decode_latents'):
                with torch.no_grad():
                    _ = self.vae.decode_latents(dummy_latent[:, :4, :, :])
            
            torch.cuda.synchronize()
            self.is_warmed_up = True
            print("✅ 预热完成!")
        except Exception as e:
            print(f"⚠️ 预热失败: {e}")
    
    def load_asset(self, asset_id: str, video_path: str, bbox_path: str):
        """
        加载资产到内存
        
        Args:
            asset_id: 资产ID（如 "idle"）
            video_path: 视频文件路径
            bbox_path: 边界框文件路径 (.pkl)
        """
        if asset_id in self.asset_cache:
            print(f"✅ 资产 {asset_id} 已在缓存中")
            return
        
        print(f"📦 加载资产: {asset_id}")
        
        # 加载视频帧
        print(f"  - 读取视频: {video_path}")
        frames = []
        cap = cv2.VideoCapture(video_path)
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            frames.append(frame)
        cap.release()
        print(f"  ✅ 加载 {len(frames)} 帧")
        
        # 加载边界框
        print(f"  - 读取边界框: {bbox_path}")
        with open(bbox_path, 'rb') as f:
            bbox_data = pickle.load(f)
        
        bboxes = bbox_data['bbox_list']
        fps = bbox_data.get('fps', 25)
        print(f"  ✅ 加载 {len(bboxes)} 个边界框")
        
        # 缓存到内存
        self.asset_cache[asset_id] = {
            'frames': frames,
            'bboxes': bboxes,
            'fps': fps,
            'frame_count': len(frames)
        }
        
        print(f"✅ 资产 {asset_id} 已驻留内存")


# 全局实例
state = GlobalState()


# ==================== FastAPI 生命周期 ====================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    print("\n" + "=" * 60)
    print("🚀 启动 MuseTalk 实时推理服务")
    print("=" * 60)
    
    # 加载模型
    state.load_models()
    
    # 预热
    state.warmup()
    
    # 🔧 加载默认资产（使用配置的路径）
    # 注意：这里需要根据实际情况调整
    default_video = os.environ.get('AVATAR_VIDEO_PATH', './data/video/idle.mp4')
    default_bbox = default_video.replace('.mp4', '_bbox.pkl')
    
    if Path(default_video).exists() and Path(default_bbox).exists():
        state.load_asset('idle', default_video, default_bbox)
    else:
        print(f"⚠️ 未找到默认资产: {default_video}")
        print("   可以通过 POST /load_asset 动态加载")
    
    print("\n✅ 服务就绪!")
    print(f"📡 API 地址: http://0.0.0.0:8000")
    
    yield
    
    # 关闭时
    print("\n👋 关闭服务...")


# ==================== FastAPI 应用 ====================
app = FastAPI(
    title="MuseTalk 实时推理服务",
    description="高性能数字人驱动引擎 - 2x RTX 4090D",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== API 路由（省略，与原版相同）====================
# ... 其余代码保持不变 ...

@app.get("/")
async def root():
    """健康检查"""
    return {
        "service": "MuseTalk 实时推理",
        "status": "running",
        "device": str(state.device),
        "dtype": str(state.dtype),
        "loaded_assets": list(state.asset_cache.keys()),
        "model_paths": {
            "unet": str(state.model_paths.UNET_PATH),
            "vae": str(state.model_paths.VAE_PATH),
            "whisper": str(state.model_paths.WHISPER_DIR)
        }
    }


# ==================== 主函数 ====================
if __name__ == "__main__":
    import uvicorn
    
    port = int(os.environ.get("PORT", 8000))
    
    print("\n" + "=" * 60)
    print(f"🚀 启动 FastAPI 服务 - 端口: {port}")
    print("=" * 60)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info",
        workers=1  # 单进程（模型在内存中）
    )
