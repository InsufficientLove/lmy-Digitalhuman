#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MuseTalk Real-time Inference Engine with Multi-GPU Support
基于官方MuseTalk代码的实时推理引擎，支持多GPU并行和预处理加速
"""

import os
import sys
import torch
import numpy as np
import cv2
import time
import threading
import queue
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
import gc

# 添加MuseTalk路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'MuseTalk'))

# 导入MuseTalk官方模块
from musetalk.utils.utils import load_all_model, datagen, get_file_type
from musetalk.utils.preprocessing import get_landmark_and_bbox, read_imgs, coord_placeholder
from musetalk.utils.blending import get_image, get_image_blending, get_image_prepare_material
from musetalk.utils.face_parsing import FaceParsing
from musetalk.whisper.audio2feature import Audio2Feature

# 导入我们的多GPU引擎
from multi_gpu_parallel_engine import MultiGPUParallelEngine, GPUConfig, create_gpu_config


@dataclass
class RealtimeConfig:
    """实时推理配置"""
    fps: int = 25
    batch_size: int = 8
    bbox_shift: int = 0
    use_float16: bool = True
    cache_frames: bool = True
    preprocess_workers: int = 4
    inference_mode: str = 'parallel'  # 'serial' or 'parallel'


class MuseTalkRealtimeEngine:
    """MuseTalk实时推理引擎"""
    
    def __init__(self, config: RealtimeConfig, gpu_config: Optional[GPUConfig] = None):
        self.config = config
        self.gpu_config = gpu_config or self._auto_detect_gpu_config()
        
        # 初始化组件
        self.models = {}
        self.preprocessors = {}
        self.frame_cache = {}
        self.audio_cache = {}
        
        # 队列
        self.input_queue = queue.Queue(maxsize=100)
        self.output_queue = queue.Queue(maxsize=100)
        
        # 线程控制
        self.processing = False
        self.threads = []
        
        # 性能统计
        self.stats = {
            'frames_processed': 0,
            'total_time': 0,
            'preprocessing_time': 0,
            'inference_time': 0,
            'postprocessing_time': 0
        }
        
        # 初始化
        self._initialize()
    
    def _auto_detect_gpu_config(self) -> GPUConfig:
        """自动检测GPU配置"""
        if not torch.cuda.is_available():
            raise RuntimeError("CUDA is not available")
        
        num_gpus = torch.cuda.device_count()
        
        # 检测GPU内存
        gpu_memory = []
        for i in range(num_gpus):
            props = torch.cuda.get_device_properties(i)
            memory_gb = props.total_memory / (1024**3)
            gpu_memory.append(memory_gb)
        
        # 根据内存决定批次大小
        min_memory = min(gpu_memory)
        if min_memory >= 40:  # 48GB GPU
            batch_size_per_gpu = 16
        elif min_memory >= 20:  # 24GB GPU
            batch_size_per_gpu = 8
        else:
            batch_size_per_gpu = 4
        
        return create_gpu_config(
            gpu_ids=list(range(num_gpus)),
            batch_size_per_gpu=batch_size_per_gpu,
            memory_fraction=0.9,
            enable_amp=self.config.use_float16
        )
    
    def _initialize(self):
        """初始化引擎"""
        print("Initializing MuseTalk Realtime Engine...")
        
        # 1. 加载模型
        self._load_models()
        
        # 2. 初始化预处理器
        self._init_preprocessors()
        
        # 3. 如果使用并行模式，初始化多GPU引擎
        if self.config.inference_mode == 'parallel':
            self.parallel_engine = MultiGPUParallelEngine(self.gpu_config)
            # 将模型传递给并行引擎
            self.parallel_engine.models = self.models
        
        print("Initialization complete")
    
    def _load_models(self):
        """加载MuseTalk模型"""
        print("Loading MuseTalk models...")
        
        # 模型路径
        model_paths = {
            'vae': 'models/sd-vae',
            'unet': 'models/musetalkV15/unet.pth',
            'unet_config': 'models/musetalkV15/musetalk.json',
            'whisper': 'models/whisper',
            'face_parsing': 'models/face-parse-bisent',
            'dwpose': 'models/dwpose'
        }
        
        # 检查模型文件
        for name, path in model_paths.items():
            if not os.path.exists(path):
                raise FileNotFoundError(f"Model not found: {path}")
        
        # 加载VAE, UNet, PE
        vae, unet, pe = load_all_model(
            unet_model_path=model_paths['unet'],
            vae_type='sd-vae',
            unet_config=model_paths['unet_config']
        )
        
        # 移到GPU并优化
        device = f'cuda:{self.gpu_config.gpu_ids[0]}'
        
        # VAE优化
        vae.vae = vae.vae.to(device)
        if self.config.use_float16:
            vae.vae = vae.vae.half()
        vae.vae.eval()
        
        # UNet优化
        unet.model = unet.model.to(device)
        if self.config.use_float16:
            unet.model = unet.model.half()
        unet.model.eval()
        
        # PE优化
        pe = pe.to(device)
        if self.config.use_float16:
            pe = pe.half()
        pe.eval()
        
        # 保存模型
        self.models['vae'] = vae
        self.models['unet'] = unet
        self.models['pe'] = pe
        
        # 加载Audio2Feature
        audio_processor = Audio2Feature(
            model_path=model_paths['whisper'],
            device=device
        )
        self.models['audio_processor'] = audio_processor
        
        # 加载Face Parsing
        face_parsing = FaceParsing(model_path=model_paths['face_parsing'])
        face_parsing.to(device)
        face_parsing.eval()
        self.models['face_parsing'] = face_parsing
        
        print(f"Models loaded to {device}")
    
    def _init_preprocessors(self):
        """初始化预处理器"""
        print("Initializing preprocessors...")
        
        # 创建预处理线程池
        from concurrent.futures import ThreadPoolExecutor
        self.preprocess_executor = ThreadPoolExecutor(
            max_workers=self.config.preprocess_workers
        )
        
        print(f"Preprocessors initialized with {self.config.preprocess_workers} workers")
    
    def preprocess_video(self, video_path: str) -> Dict:
        """预处理视频"""
        print(f"Preprocessing video: {video_path}")
        
        start_time = time.time()
        
        # 检查缓存
        if self.config.cache_frames and video_path in self.frame_cache:
            print("Using cached frames")
            return self.frame_cache[video_path]
        
        # 读取视频信息
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # 读取所有帧
        frames = []
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            frames.append(frame)
        cap.release()
        
        print(f"Read {len(frames)} frames")
        
        # 并行处理帧
        if len(frames) > 0:
            # 获取第一帧的landmark和bbox
            frame_landmark_list = []
            coord_list = []
            frame_list = []
            
            # 使用线程池并行处理
            futures = []
            for i, frame in enumerate(frames):
                future = self.preprocess_executor.submit(
                    self._process_single_frame, frame, i
                )
                futures.append(future)
            
            # 收集结果
            for future in futures:
                result = future.result()
                if result:
                    frame_list.append(result['frame'])
                    frame_landmark_list.append(result['landmark'])
                    coord_list.append(result['coord'])
        
        # 准备材料
        input_latent_list = []
        for frame in frame_list[:5]:  # 只处理前5帧用于准备
            material = get_image_prepare_material(
                frame, 
                self.config.bbox_shift
            )
            input_latent_list.append(material)
        
        # 缓存结果
        result = {
            'frames': frame_list,
            'landmarks': frame_landmark_list,
            'coords': coord_list,
            'latents': input_latent_list,
            'fps': fps,
            'frame_count': frame_count
        }
        
        if self.config.cache_frames:
            self.frame_cache[video_path] = result
        
        elapsed = time.time() - start_time
        self.stats['preprocessing_time'] += elapsed
        print(f"Preprocessing completed in {elapsed:.2f}s")
        
        return result
    
    def _process_single_frame(self, frame, index):
        """处理单帧"""
        try:
            # 获取landmark和bbox
            landmark, bbox = get_landmark_and_bbox(frame, self.config.bbox_shift)
            
            # 获取坐标
            coord = coord_placeholder(bbox)
            
            return {
                'frame': frame,
                'landmark': landmark,
                'coord': coord,
                'index': index
            }
        except Exception as e:
            print(f"Error processing frame {index}: {e}")
            return None
    
    def preprocess_audio(self, audio_path: str) -> np.ndarray:
        """预处理音频"""
        print(f"Preprocessing audio: {audio_path}")
        
        # 检查缓存
        if audio_path in self.audio_cache:
            print("Using cached audio features")
            return self.audio_cache[audio_path]
        
        # 提取音频特征
        audio_processor = self.models['audio_processor']
        whisper_features = audio_processor.audio2feat(audio_path)
        
        # 缓存
        self.audio_cache[audio_path] = whisper_features
        
        return whisper_features
    
    def generate_batch(self, video_data: Dict, audio_features: np.ndarray, 
                      start_frame: int, batch_size: int) -> List[np.ndarray]:
        """生成一批帧"""
        
        # 准备批次数据
        batch_data = []
        for i in range(batch_size):
            frame_idx = start_frame + i
            if frame_idx >= len(video_data['frames']):
                break
            
            # 准备输入
            latent = video_data['latents'][min(frame_idx, len(video_data['latents'])-1)]
            audio_feat = audio_features[frame_idx] if frame_idx < len(audio_features) else audio_features[-1]
            
            batch_data.append({
                'latent': latent,
                'audio': audio_feat,
                'frame_idx': frame_idx
            })
        
        if not batch_data:
            return []
        
        # 推理
        if self.config.inference_mode == 'parallel':
            # 使用多GPU并行
            results = self.parallel_engine.process_batch_parallel(
                batch_data, 
                strategy='data_parallel'
            )
        else:
            # 串行处理
            results = self._process_batch_serial(batch_data)
        
        return results
    
    def _process_batch_serial(self, batch_data: List[Dict]) -> List[np.ndarray]:
        """串行处理批次"""
        results = []
        
        device = f'cuda:{self.gpu_config.gpu_ids[0]}'
        vae = self.models['vae']
        unet = self.models['unet']
        pe = self.models['pe']
        
        with torch.no_grad():
            for data in batch_data:
                # 准备输入
                latent = torch.tensor(data['latent']).to(device)
                audio = torch.tensor(data['audio']).to(device)
                
                if self.config.use_float16:
                    latent = latent.half()
                    audio = audio.half()
                
                # UNet推理
                pred = unet.model(latent, audio, pe)
                
                # VAE解码
                frame = vae.decode(pred)
                
                # 转换为numpy
                frame_np = frame.cpu().numpy()
                results.append(frame_np)
        
        return results
    
    def run_realtime(self, video_path: str, audio_path: str, output_path: str):
        """实时推理主函数"""
        print("Starting real-time inference...")
        
        # 1. 预处理
        video_data = self.preprocess_video(video_path)
        audio_features = self.preprocess_audio(audio_path)
        
        # 2. 准备输出
        fps = video_data['fps']
        frame_count = video_data['frame_count']
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (256, 256))
        
        # 3. 批量生成
        total_batches = (frame_count + self.config.batch_size - 1) // self.config.batch_size
        
        print(f"Generating {frame_count} frames in {total_batches} batches...")
        start_time = time.time()
        
        for batch_idx in range(total_batches):
            batch_start = batch_idx * self.config.batch_size
            
            # 生成批次
            batch_frames = self.generate_batch(
                video_data, 
                audio_features,
                batch_start,
                self.config.batch_size
            )
            
            # 写入视频
            for frame in batch_frames:
                out.write(frame)
                self.stats['frames_processed'] += 1
            
            # 打印进度
            if (batch_idx + 1) % 10 == 0:
                elapsed = time.time() - start_time
                fps_actual = self.stats['frames_processed'] / elapsed
                print(f"Batch {batch_idx + 1}/{total_batches}, "
                      f"FPS: {fps_actual:.2f}, "
                      f"Frames: {self.stats['frames_processed']}/{frame_count}")
        
        # 4. 完成
        out.release()
        
        total_time = time.time() - start_time
        self.stats['total_time'] = total_time
        
        print(f"\nInference completed!")
        print(f"Total frames: {self.stats['frames_processed']}")
        print(f"Total time: {total_time:.2f}s")
        print(f"Average FPS: {self.stats['frames_processed'] / total_time:.2f}")
        print(f"Output saved to: {output_path}")
        
        return self.stats
    
    def cleanup(self):
        """清理资源"""
        print("Cleaning up...")
        
        # 清理缓存
        self.frame_cache.clear()
        self.audio_cache.clear()
        
        # 清理GPU内存
        torch.cuda.empty_cache()
        gc.collect()
        
        # 关闭线程池
        if hasattr(self, 'preprocess_executor'):
            self.preprocess_executor.shutdown(wait=True)
        
        # 清理并行引擎
        if hasattr(self, 'parallel_engine'):
            self.parallel_engine.cleanup()
        
        print("Cleanup completed")


def main():
    """测试函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='MuseTalk Realtime Inference')
    parser.add_argument('--video', type=str, required=True, help='Input video path')
    parser.add_argument('--audio', type=str, required=True, help='Input audio path')
    parser.add_argument('--output', type=str, default='output.mp4', help='Output video path')
    parser.add_argument('--fps', type=int, default=25, help='Output FPS')
    parser.add_argument('--batch_size', type=int, default=8, help='Batch size')
    parser.add_argument('--mode', type=str, default='parallel', 
                       choices=['serial', 'parallel'], help='Inference mode')
    parser.add_argument('--gpus', type=str, default='auto', 
                       help='GPU IDs to use (e.g., "0,1,2,3" or "auto")')
    
    args = parser.parse_args()
    
    # 配置
    config = RealtimeConfig(
        fps=args.fps,
        batch_size=args.batch_size,
        inference_mode=args.mode,
        use_float16=True,
        cache_frames=True
    )
    
    # GPU配置
    if args.gpus == 'auto':
        gpu_config = None  # 自动检测
    else:
        gpu_ids = [int(x) for x in args.gpus.split(',')]
        gpu_config = create_gpu_config(
            gpu_ids=gpu_ids,
            batch_size_per_gpu=args.batch_size // len(gpu_ids)
        )
    
    # 创建引擎
    engine = MuseTalkRealtimeEngine(config, gpu_config)
    
    try:
        # 运行推理
        stats = engine.run_realtime(args.video, args.audio, args.output)
        
        # 打印统计
        print("\n=== Performance Statistics ===")
        for key, value in stats.items():
            print(f"{key}: {value}")
        
    finally:
        # 清理
        engine.cleanup()


if __name__ == "__main__":
    main()