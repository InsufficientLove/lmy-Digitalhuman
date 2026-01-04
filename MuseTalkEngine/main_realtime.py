#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实时推理服务 - 高性能 FastAPI + PyTorch FP16
Author: 数字人后端团队
Hardware: 2x RTX 4090D (24GB VRAM)
Architecture: .NET 中控 -> MuseTalk 视觉推理 -> MJPEG 流输出
Performance Target: 实时驱动，极低延迟
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

# 添加 MuseTalk 路径
MUSETALK_PATH = os.environ.get('MUSE_TALK_DIR', '/opt/musetalk/repo/MuseTalk')
sys.path.insert(0, MUSETALK_PATH)

try:
    from musetalk.utils.utils import load_all_model, datagen
    from musetalk.utils.blending import get_image_blending
    from musetalk.utils.audio_processor import AudioProcessor
    print("✅ 成功导入 MuseTalk 核心模块")
except ImportError as e:
    print(f"❌ 无法导入 MuseTalk 模块: {e}")
    sys.exit(1)


# ==================== 全局状态管理 ====================
class GlobalState:
    """全局状态 - 模型和资产缓存"""
    
    def __init__(self):
        # GPU 配置（使用环境变量或默认 cuda:1）
        gpu_id = int(os.environ.get("GPU_ID", "1"))  # 默认使用 GPU 1
        self.device = torch.device(f"cuda:{gpu_id}" if torch.cuda.is_available() else "cpu")
        self.dtype = torch.float16  # 强制 FP16
        
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
            # 切换到 MuseTalk 工作目录
            original_dir = os.getcwd()
            musetalk_dir = Path(MUSETALK_PATH)
            if musetalk_dir.exists():
                os.chdir(musetalk_dir)
                print(f"📂 工作目录: {musetalk_dir}")
            
            # 加载模型
            print("⚙️ 加载 VAE、UNet、PE...")
            # load_all_model 返回 3 个值：vae, unet, pe
            vae, unet, pe = load_all_model(device=self.device)
            
            # AudioProcessor 需要单独初始化
            print("⚙️ 初始化 AudioProcessor...")
            # 使用本地 Whisper 模型路径（避免网络下载）
            whisper_path = os.environ.get('WHISPER_MODEL_PATH', '/opt/musetalk/models/whisper')
            audio_processor = AudioProcessor(feature_extractor_path=whisper_path)
            
            # 转换为 FP16 并移动到 GPU
            print("⚡ 转换为 FP16 并移动到 GPU...")
            
            # VAE - 必须保持 Float32，避免 cuDNN 错误
            if hasattr(vae, 'vae'):
                vae.vae = vae.vae.to(self.device, dtype=torch.float32).eval()
                print("  ✅ VAE -> Float32 (避免cuDNN错误)")
            elif hasattr(vae, 'to'):
                vae = vae.to(self.device, dtype=torch.float32).eval()
                print("  ✅ VAE -> Float32 (避免cuDNN错误)")
            
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
            allocated = torch.cuda.memory_allocated(self.device) / 1e9
            reserved = torch.cuda.memory_reserved(self.device) / 1e9
            print(f"\n💾 显存占用: {allocated:.2f}GB (预留: {reserved:.2f}GB)")
            
            print("=" * 60)
            print("✅ 模型加载完成!")
            print("=" * 60)
            
        except Exception as e:
            print(f"❌ 模型加载失败: {e}")
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
            _ = self.pe(dummy_audio)
            
            # 预热 UNet
            if hasattr(self.unet, 'model'):
                _ = self.unet.model(dummy_latent, timesteps, encoder_hidden_states=dummy_audio)
            
            # 预热 VAE
            if hasattr(self.vae, 'decode_latents'):
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
            # 关键修复 Bug 1：cv2.VideoCapture 读取的是 BGR 格式，转换为 RGB 供模型使用
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frames.append(frame)
        cap.release()
        print(f"  ✅ 加载 {len(frames)} 帧 (已转换为 RGB)")
        
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
    
    # 加载默认资产
    default_video = os.environ.get('AVATAR_VIDEO_PATH', './data/video/idle.mp4')
    default_bbox = default_video.replace('.mp4', '_bbox.pkl')
    
    if Path(default_video).exists() and Path(default_bbox).exists():
        state.load_asset('idle', default_video, default_bbox)
    else:
        print(f"⚠️ 未找到默认资产: {default_video}")
    
    print("\n✅ 服务就绪!")
    
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


# ==================== 工具函数 ====================
def extract_audio_features(audio_bytes: bytes, fps: int = 25) -> torch.Tensor:
    """
    提取音频特征（Whisper）
    
    Args:
        audio_bytes: 音频数据（WAV/PCM）
        fps: 目标帧率
    
    Returns:
        whisper_chunks: 音频特征张量
    """
    # 保存临时文件
    import tempfile
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name
    
    try:
        # 提取特征
        whisper_input, librosa_length = state.audio_processor.get_audio_feature(tmp_path)
        
        # 获取 Whisper chunks
        whisper_chunks = state.audio_processor.get_whisper_chunk(
            whisper_input,
            state.device,
            torch.float32,  # Whisper 使用 float32
            state.whisper,
            librosa_length,
            fps=fps,
            audio_padding_length_left=2,
            audio_padding_length_right=2
        )
        
        return whisper_chunks
    
    finally:
        # 清理临时文件
        os.unlink(tmp_path)


def inference_frame_batch(
    whisper_chunks: torch.Tensor,
    asset_id: str,
    batch_size: int = 8
) -> List[np.ndarray]:
    """
    批量推理生成帧
    
    Args:
        whisper_chunks: 音频特征
        asset_id: 资产ID
        batch_size: 批大小
    
    Returns:
        generated_frames: 生成的人脸帧列表
    """
    asset = state.asset_cache.get(asset_id)
    if not asset:
        raise ValueError(f"资产 {asset_id} 未加载")
    
    frames = asset['frames']
    bboxes = asset['bboxes']
    
    # 循环取帧
    num_chunks = whisper_chunks.shape[0]
    generated_frames = []
    
    # 批处理推理
    for i in range(0, num_chunks, batch_size):
        batch_end = min(i + batch_size, num_chunks)
        audio_batch = whisper_chunks[i:batch_end].to(state.device, dtype=state.dtype)
        
        # 获取对应的底图
        batch_frames = []
        batch_bboxes = []
        for j in range(i, batch_end):
            frame_idx = j % len(frames)
            batch_frames.append(frames[frame_idx])
            batch_bboxes.append(bboxes[frame_idx])
        
        # 推理
        with torch.no_grad():
            # PE 编码音频
            audio_features = state.pe(audio_batch)
            
            # 创建 latent（这里简化，实际需要 VAE 编码底图）
            # 假设我们有预处理好的 latent
            latent_batch = torch.randn(
                batch_end - i, 8, 64, 64,
                device=state.device, dtype=state.dtype
            )
            
            # UNet 推理
            timesteps = torch.tensor([0], device=state.device, dtype=torch.long)
            if hasattr(state.unet, 'model'):
                pred_latents = state.unet.model(
                    latent_batch, timesteps, encoder_hidden_states=audio_features
                ).sample
            else:
                pred_latents = state.unet(
                    latent_batch, timesteps, encoder_hidden_states=audio_features
                )
            
            # VAE 解码 - 转换为 Float32 避免 cuDNN 错误
            pred_latents_fp32 = pred_latents[:, :4, :, :].to(dtype=torch.float32)
            if hasattr(state.vae, 'decode_latents'):
                recon_frames = state.vae.decode_latents(pred_latents_fp32)
            else:
                recon_frames = state.vae.decode(pred_latents_fp32).sample
        
        # 转换为 numpy
        if isinstance(recon_frames, torch.Tensor):
            recon_frames = recon_frames.cpu().numpy()
        
        # 合成到原图
        for k, (recon, orig_frame, bbox) in enumerate(zip(recon_frames, batch_frames, batch_bboxes)):
            if bbox == (0, 0, 0, 0):
                # 无效 bbox，使用原图
                generated_frames.append(orig_frame)
                continue
            
            x1, y1, x2, y2 = bbox
            
            # Resize 生成的脸
            recon = (recon * 255).astype(np.uint8)
            if recon.shape[0] == 3:  # CHW -> HWC
                recon = recon.transpose(1, 2, 0)
            
            # 关键修复 Bug 1：MuseTalk 模型输出是 RGB，需要转换为 BGR（OpenCV 格式）
            if len(recon.shape) == 3 and recon.shape[2] == 3:
                recon = cv2.cvtColor(recon, cv2.COLOR_RGB2BGR)
            
            # 关键修复 Bug 2：强制 resize 到目标尺寸（避免尺寸不匹配导致 blending 失败）
            target_w, target_h = x2 - x1, y2 - y1
            if target_w > 0 and target_h > 0:
                recon_resized = cv2.resize(recon, (target_w, target_h), interpolation=cv2.INTER_LINEAR)
            else:
                print(f"警告: bbox尺寸异常 ({target_w}x{target_h})，使用原图")
                generated_frames.append(orig_frame)
                continue
            
            # 贴回原图
            result = orig_frame.copy()
            try:
                # 简单粘贴（可以使用 get_image_blending 做融合）
                result[y1:y2, x1:x2] = recon_resized
            except:
                pass
            
            generated_frames.append(result)
    
    return generated_frames


# ==================== API 路由 ====================
@app.get("/")
async def root():
    """健康检查"""
    return {
        "service": "MuseTalk 实时推理",
        "status": "running",
        "device": str(state.device),
        "dtype": str(state.dtype),
        "loaded_assets": list(state.asset_cache.keys())
    }


@app.get("/health")
async def health():
    """健康检查"""
    return {
        "status": "healthy",
        "gpu_available": torch.cuda.is_available(),
        "gpu_count": torch.cuda.device_count() if torch.cuda.is_available() else 0,
        "models_loaded": state.vae is not None and state.unet is not None,
        "device": str(state.device)
    }


@app.post("/stream")
async def stream_inference(
    audio: UploadFile = File(...),
    asset_id: str = "idle",
    fps: int = 25,
    batch_size: int = 8
):
    """
    实时推理接口 - MJPEG 流输出
    
    Args:
        audio: 音频文件（WAV/PCM）
        asset_id: 资产ID（默认 idle）
        fps: 输出帧率
        batch_size: 推理批大小
    
    Returns:
        StreamingResponse: MJPEG 视频流
    """
    try:
        # 验证资产
        if asset_id not in state.asset_cache:
            raise HTTPException(status_code=404, detail=f"资产 {asset_id} 未加载")
        
        # 读取音频
        audio_bytes = await audio.read()
        print(f"📥 收到音频: {len(audio_bytes)} bytes")
        
        # 提取音频特征
        start_time = time.time()
        whisper_chunks = extract_audio_features(audio_bytes, fps)
        audio_time = time.time() - start_time
        print(f"⚡ 音频特征提取: {audio_time:.3f}s")
        
        # 推理生成帧
        start_time = time.time()
        generated_frames = inference_frame_batch(whisper_chunks, asset_id, batch_size)
        inference_time = time.time() - start_time
        print(f"⚡ 推理完成: {inference_time:.3f}s, {len(generated_frames)} 帧")
        
        # MJPEG 流生成器
        async def mjpeg_generator():
            for frame in generated_frames:
                # 编码为 JPEG
                _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                jpeg_bytes = buffer.tobytes()
                
                # MJPEG 格式
                yield (
                    b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + jpeg_bytes + b'\r\n'
                )
                
                # 控制帧率
                await asyncio.sleep(1.0 / fps)
        
        return StreamingResponse(
            mjpeg_generator(),
            media_type="multipart/x-mixed-replace; boundary=frame"
        )
    
    except Exception as e:
        print(f"❌ 推理失败: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/load_asset")
async def load_asset_endpoint(
    asset_id: str,
    video_path: str,
    bbox_path: str
):
    """
    加载新资产到内存
    
    Args:
        asset_id: 资产ID
        video_path: 视频路径
        bbox_path: 边界框路径
    """
    try:
        state.load_asset(asset_id, video_path, bbox_path)
        return {"success": True, "asset_id": asset_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/assets")
async def list_assets():
    """列出已加载的资产"""
    return {
        "assets": [
            {
                "id": asset_id,
                "frame_count": info['frame_count'],
                "fps": info['fps']
            }
            for asset_id, info in state.asset_cache.items()
        ]
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
