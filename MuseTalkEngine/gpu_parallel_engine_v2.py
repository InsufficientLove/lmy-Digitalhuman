"""
MuseTalk GPU并行处理引擎 V2
支持精确GPU指定和优化的批处理策略
"""

import os
import torch
import torch.nn as nn
import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Optional, Union, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import psutil
import pynvml
from threading import Lock
import logging
import json

# 初始化NVML
pynvml.nvmlInit()

@dataclass
class GPUConfig:
    """GPU配置类"""
    # GPU选择模式
    mode: str = "manual"  # manual: 手动指定, auto: 自动检测空闲GPU
    
    # 手动指定的GPU配置
    gpu_ids: List[int] = None  # 指定使用的GPU ID列表
    gpu_memory_fraction: float = 0.9  # 每个GPU的显存使用比例
    
    # 批处理配置
    batch_size_per_gpu: int = 8  # 每个GPU的批处理大小
    max_batch_size: int = 32  # 最大批处理大小
    
    # 性能优化
    enable_amp: bool = True  # 是否启用自动混合精度
    enable_cudnn_benchmark: bool = True  # 是否启用CuDNN自动优化
    enable_model_compilation: bool = False  # 是否编译模型（需要PyTorch 2.0+）
    
    # 预加载配置
    preload_frames: int = 100  # 预加载帧数
    preload_latents: bool = True  # 是否预加载latents
    
    # 内存管理
    memory_cleanup_interval: int = 50  # 内存清理间隔（批次数）
    memory_threshold: float = 0.85  # 内存使用阈值
    
    @classmethod
    def from_preset(cls, preset: str) -> 'GPUConfig':
        """从预设配置创建"""
        presets = {
            "single_4090d_48gb": {
                "mode": "manual",
                "gpu_ids": [0],
                "batch_size_per_gpu": 20,
                "max_batch_size": 20,
                "gpu_memory_fraction": 0.95,
                "preload_frames": 200,
            },
            "quad_4090_24gb": {
                "mode": "manual", 
                "gpu_ids": [0, 1, 2, 3],
                "batch_size_per_gpu": 8,
                "max_batch_size": 32,
                "gpu_memory_fraction": 0.9,
                "preload_frames": 100,
            },
            "dual_4090_24gb": {
                "mode": "manual",
                "gpu_ids": [0, 1],
                "batch_size_per_gpu": 10,
                "max_batch_size": 20,
                "gpu_memory_fraction": 0.9,
                "preload_frames": 150,
            },
            "auto": {
                "mode": "auto",
                "batch_size_per_gpu": 8,
                "gpu_memory_fraction": 0.8,
            }
        }
        
        if preset not in presets:
            raise ValueError(f"Unknown preset: {preset}. Available: {list(presets.keys())}")
        
        config = cls()
        for key, value in presets[preset].items():
            setattr(config, key, value)
        return config


class GPUManager:
    """GPU管理器，负责GPU选择和监控"""
    
    def __init__(self, config: GPUConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # 获取可用GPU
        self.available_gpus = self._detect_available_gpus()
        
        # 确定使用的GPU
        if config.mode == "manual":
            if config.gpu_ids is None:
                raise ValueError("gpu_ids must be specified in manual mode")
            self.gpu_ids = [gpu_id for gpu_id in config.gpu_ids if gpu_id in self.available_gpus]
            if not self.gpu_ids:
                raise ValueError(f"No valid GPU IDs. Requested: {config.gpu_ids}, Available: {self.available_gpus}")
        else:  # auto mode
            self.gpu_ids = self._select_idle_gpus()
        
        self.logger.info(f"Using GPUs: {self.gpu_ids}")
        
        # 设置CUDA设备
        os.environ['CUDA_VISIBLE_DEVICES'] = ','.join(map(str, self.gpu_ids))
        
        # GPU状态跟踪
        self.gpu_states = {gpu_id: {"memory_used": 0, "utilization": 0} for gpu_id in self.gpu_ids}
        self.lock = Lock()
    
    def _detect_available_gpus(self) -> List[int]:
        """检测可用的GPU"""
        gpu_count = pynvml.nvmlDeviceGetCount()
        available = []
        
        for i in range(gpu_count):
            try:
                handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                # 检查GPU是否可用
                mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                if mem_info.total > 0:
                    available.append(i)
                    
                    # 打印GPU信息
                    name = pynvml.nvmlDeviceGetName(handle).decode('utf-8')
                    total_mem = mem_info.total / (1024**3)
                    used_mem = mem_info.used / (1024**3)
                    free_mem = mem_info.free / (1024**3)
                    
                    self.logger.info(f"GPU {i}: {name}, Total: {total_mem:.1f}GB, Used: {used_mem:.1f}GB, Free: {free_mem:.1f}GB")
            except Exception as e:
                self.logger.warning(f"Failed to get info for GPU {i}: {e}")
        
        return available
    
    def _select_idle_gpus(self) -> List[int]:
        """自动选择空闲的GPU"""
        idle_gpus = []
        
        for gpu_id in self.available_gpus:
            handle = pynvml.nvmlDeviceGetHandleByIndex(gpu_id)
            
            # 获取GPU利用率
            utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)
            mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
            mem_usage = mem_info.used / mem_info.total
            
            # 选择利用率低的GPU
            if utilization.gpu < 30 and mem_usage < 0.3:
                idle_gpus.append(gpu_id)
                self.logger.info(f"Selected idle GPU {gpu_id}: Util={utilization.gpu}%, Mem={mem_usage*100:.1f}%")
        
        if not idle_gpus:
            self.logger.warning("No idle GPUs found, using all available GPUs")
            idle_gpus = self.available_gpus
        
        return idle_gpus
    
    def get_gpu_memory_info(self, gpu_id: int) -> Dict:
        """获取GPU内存信息"""
        try:
            handle = pynvml.nvmlDeviceGetHandleByIndex(gpu_id)
            mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
            return {
                "total": mem_info.total / (1024**3),
                "used": mem_info.used / (1024**3),
                "free": mem_info.free / (1024**3),
                "usage_percent": (mem_info.used / mem_info.total) * 100
            }
        except Exception as e:
            self.logger.error(f"Failed to get memory info for GPU {gpu_id}: {e}")
            return {}
    
    def should_cleanup_memory(self, gpu_id: int) -> bool:
        """检查是否需要清理内存"""
        mem_info = self.get_gpu_memory_info(gpu_id)
        if mem_info:
            return mem_info["usage_percent"] > (self.config.memory_threshold * 100)
        return False


class OptimizedBatchProcessor:
    """优化的批处理器，基于MuseTalk的处理逻辑"""
    
    def __init__(self, config: GPUConfig, gpu_manager: GPUManager):
        self.config = config
        self.gpu_manager = gpu_manager
        self.logger = logging.getLogger(__name__)
        
        # 设置设备
        self.devices = [torch.device(f'cuda:{i}') for i in range(len(gpu_manager.gpu_ids))]
        self.num_gpus = len(self.devices)
        
        # 批处理队列
        self.batch_queue = []
        self.result_queue = []
        
        # 预加载缓存
        self.latent_cache = {}
        self.frame_cache = {}
        
        # 处理统计
        self.stats = {
            "total_batches": 0,
            "total_frames": 0,
            "processing_time": 0,
            "gpu_utilization": {i: [] for i in range(self.num_gpus)}
        }
        
        # 线程池
        self.executor = ThreadPoolExecutor(max_workers=self.num_gpus * 2)
        
    def preload_data(self, frames: List, coords: List, vae_model) -> Dict:
        """预加载数据到GPU内存"""
        self.logger.info(f"Preloading {len(frames)} frames...")
        
        preload_count = min(self.config.preload_frames, len(frames))
        
        with torch.no_grad():
            for i in range(preload_count):
                if coords[i] == (0.0, 0.0, 0.0, 0.0):  # placeholder
                    continue
                    
                x1, y1, x2, y2 = coords[i]
                frame = frames[i]
                
                # 裁剪和调整大小
                crop_frame = frame[y1:y2, x1:x2]
                crop_frame = cv2.resize(crop_frame, (256, 256), interpolation=cv2.INTER_LANCZOS4)
                
                # 计算latents
                if self.config.preload_latents:
                    latents = vae_model.get_latents_for_unet(crop_frame)
                    self.latent_cache[i] = latents
                
                # 缓存帧
                self.frame_cache[i] = frame
        
        self.logger.info(f"Preloaded {len(self.latent_cache)} latents and {len(self.frame_cache)} frames")
        return {"latents": len(self.latent_cache), "frames": len(self.frame_cache)}
    
    def create_batches(self, whisper_chunks: List, latent_list: List) -> List[Tuple]:
        """创建优化的批次"""
        batches = []
        total_items = len(whisper_chunks)
        
        # 计算每个GPU的批次大小
        batch_size = min(
            self.config.batch_size_per_gpu * self.num_gpus,
            self.config.max_batch_size
        )
        
        # 创建批次
        for i in range(0, total_items, batch_size):
            end_idx = min(i + batch_size, total_items)
            
            whisper_batch = whisper_chunks[i:end_idx]
            latent_batch = latent_list[i:end_idx]
            
            # 分配到GPU
            gpu_assignments = []
            chunk_size = len(whisper_batch) // self.num_gpus
            
            for gpu_idx in range(self.num_gpus):
                start = gpu_idx * chunk_size
                if gpu_idx == self.num_gpus - 1:
                    # 最后一个GPU处理剩余的
                    end = len(whisper_batch)
                else:
                    end = start + chunk_size
                
                if start < end:
                    gpu_assignments.append({
                        "gpu_idx": gpu_idx,
                        "whisper": whisper_batch[start:end],
                        "latents": latent_batch[start:end],
                        "indices": list(range(i + start, i + end))
                    })
            
            batches.append(gpu_assignments)
        
        self.logger.info(f"Created {len(batches)} batches for {total_items} items")
        return batches
    
    def process_batch_on_gpu(self, gpu_idx: int, whisper_batch: torch.Tensor, 
                            latent_batch: torch.Tensor, unet_model, pe_model) -> torch.Tensor:
        """在指定GPU上处理批次"""
        device = self.devices[gpu_idx]
        
        try:
            # 移动数据到GPU
            whisper_batch = whisper_batch.to(device)
            latent_batch = latent_batch.to(device)
            
            # 设置模型到对应GPU
            if hasattr(unet_model, 'to'):
                unet_model = unet_model.to(device)
            if hasattr(pe_model, 'to'):
                pe_model = pe_model.to(device)
            
            # 启用AMP
            if self.config.enable_amp:
                with torch.cuda.amp.autocast():
                    audio_feature = pe_model(whisper_batch)
                    timesteps = torch.tensor([0], device=device)
                    pred_latents = unet_model.model(
                        latent_batch, 
                        timesteps, 
                        encoder_hidden_states=audio_feature
                    ).sample
            else:
                audio_feature = pe_model(whisper_batch)
                timesteps = torch.tensor([0], device=device)
                pred_latents = unet_model.model(
                    latent_batch,
                    timesteps,
                    encoder_hidden_states=audio_feature
                ).sample
            
            # 检查是否需要清理内存
            if self.gpu_manager.should_cleanup_memory(gpu_idx):
                torch.cuda.empty_cache()
                self.logger.debug(f"Cleaned GPU {gpu_idx} memory")
            
            return pred_latents.cpu()
            
        except Exception as e:
            self.logger.error(f"Error processing batch on GPU {gpu_idx}: {e}")
            raise
    
    def process_parallel(self, batches: List, unet_model, pe_model, vae_model) -> List:
        """并行处理批次"""
        results = []
        
        for batch_idx, gpu_assignments in enumerate(batches):
            batch_start = time.time()
            
            # 提交任务到线程池
            futures = []
            for assignment in gpu_assignments:
                gpu_idx = assignment["gpu_idx"]
                
                # 准备批次数据
                whisper_batch = torch.stack(assignment["whisper"])
                latent_batch = torch.cat(assignment["latents"], dim=0)
                
                # 提交任务
                future = self.executor.submit(
                    self.process_batch_on_gpu,
                    gpu_idx, whisper_batch, latent_batch,
                    unet_model, pe_model
                )
                futures.append((future, assignment["indices"]))
            
            # 收集结果
            batch_results = {}
            for future, indices in futures:
                try:
                    pred_latents = future.result(timeout=30)
                    
                    # 解码结果
                    with torch.no_grad():
                        recon = vae_model.decode_latents(pred_latents)
                    
                    # 保存结果
                    for i, idx in enumerate(indices):
                        batch_results[idx] = recon[i]
                        
                except Exception as e:
                    self.logger.error(f"Failed to get result: {e}")
            
            # 按顺序整理结果
            for idx in sorted(batch_results.keys()):
                results.append(batch_results[idx])
            
            # 更新统计
            batch_time = time.time() - batch_start
            self.stats["total_batches"] += 1
            self.stats["processing_time"] += batch_time
            
            self.logger.info(f"Batch {batch_idx + 1}/{len(batches)} processed in {batch_time:.2f}s")
        
        self.stats["total_frames"] = len(results)
        return results
    
    def get_statistics(self) -> Dict:
        """获取处理统计信息"""
        stats = self.stats.copy()
        
        if stats["total_batches"] > 0:
            stats["avg_batch_time"] = stats["processing_time"] / stats["total_batches"]
        
        if stats["total_frames"] > 0:
            stats["avg_frame_time"] = stats["processing_time"] / stats["total_frames"]
            stats["fps"] = stats["total_frames"] / stats["processing_time"] if stats["processing_time"] > 0 else 0
        
        # GPU内存信息
        stats["gpu_memory"] = {}
        for gpu_id in self.gpu_manager.gpu_ids:
            stats["gpu_memory"][gpu_id] = self.gpu_manager.get_gpu_memory_info(gpu_id)
        
        return stats


class MuseTalkGPUEngine:
    """MuseTalk GPU推理引擎"""
    
    def __init__(self, config: Union[GPUConfig, str, Dict]):
        """
        初始化引擎
        
        Args:
            config: GPU配置，可以是：
                - GPUConfig对象
                - 预设名称字符串 ("single_4090d_48gb", "quad_4090_24gb", etc.)
                - 配置字典
        """
        # 处理配置
        if isinstance(config, str):
            self.config = GPUConfig.from_preset(config)
        elif isinstance(config, dict):
            self.config = GPUConfig(**config)
        else:
            self.config = config
        
        # 初始化日志
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # 初始化GPU管理器
        self.gpu_manager = GPUManager(self.config)
        
        # 初始化批处理器
        self.batch_processor = OptimizedBatchProcessor(self.config, self.gpu_manager)
        
        # 设置PyTorch优化
        if self.config.enable_cudnn_benchmark:
            torch.backends.cudnn.benchmark = True
            self.logger.info("Enabled CuDNN benchmark")
        
        self.logger.info(f"MuseTalk GPU Engine initialized with config: {self.config.mode}")
    
    def inference(self, video_path: str, audio_path: str, 
                 models: Dict, args: Dict) -> Dict:
        """
        执行推理
        
        Args:
            video_path: 视频路径
            audio_path: 音频路径
            models: 模型字典 {"vae": vae, "unet": unet, "pe": pe, "whisper": whisper}
            args: 其他参数
        
        Returns:
            推理结果和统计信息
        """
        import cv2
        from musetalk.utils.utils import datagen
        
        # 提取模型
        vae = models["vae"]
        unet = models["unet"]
        pe = models["pe"]
        whisper = models.get("whisper")
        audio_processor = models.get("audio_processor")
        
        # 预处理视频帧
        self.logger.info("Preprocessing video frames...")
        frames, coords = self._preprocess_video(video_path, args)
        
        # 预加载数据
        if self.config.preload_latents:
            self.batch_processor.preload_data(frames, coords, vae)
        
        # 提取音频特征
        self.logger.info("Extracting audio features...")
        whisper_chunks = self._extract_audio_features(audio_path, whisper, audio_processor, args)
        
        # 准备latents
        self.logger.info("Preparing latents...")
        input_latent_list = []
        for i, (frame, coord) in enumerate(zip(frames, coords)):
            if i in self.batch_processor.latent_cache:
                input_latent_list.append(self.batch_processor.latent_cache[i])
            else:
                if coord == (0.0, 0.0, 0.0, 0.0):
                    continue
                x1, y1, x2, y2 = coord
                crop_frame = frame[y1:y2, x1:x2]
                crop_frame = cv2.resize(crop_frame, (256, 256), interpolation=cv2.INTER_LANCZOS4)
                latents = vae.get_latents_for_unet(crop_frame)
                input_latent_list.append(latents)
        
        # 循环处理（前向+反向）
        input_latent_list_cycle = input_latent_list + input_latent_list[::-1]
        
        # 创建批次
        batches = self.batch_processor.create_batches(whisper_chunks, input_latent_list_cycle)
        
        # 并行处理
        self.logger.info("Starting parallel inference...")
        results = self.batch_processor.process_parallel(batches, unet, pe, vae)
        
        # 获取统计信息
        stats = self.batch_processor.get_statistics()
        
        self.logger.info(f"Inference completed: {stats['total_frames']} frames in {stats['processing_time']:.2f}s")
        self.logger.info(f"Average FPS: {stats.get('fps', 0):.2f}")
        
        return {
            "results": results,
            "frames": frames,
            "coords": coords,
            "statistics": stats
        }
    
    def _preprocess_video(self, video_path: str, args: Dict) -> Tuple[List, List]:
        """预处理视频"""
        # 这里简化处理，实际应该调用MuseTalk的预处理函数
        frames = []
        coords = []
        
        # TODO: 实现视频预处理
        
        return frames, coords
    
    def _extract_audio_features(self, audio_path: str, whisper, audio_processor, args: Dict) -> List:
        """提取音频特征"""
        # 这里简化处理，实际应该调用MuseTalk的音频处理函数
        whisper_chunks = []
        
        # TODO: 实现音频特征提取
        
        return whisper_chunks
    
    def cleanup(self):
        """清理资源"""
        self.batch_processor.executor.shutdown(wait=True)
        torch.cuda.empty_cache()
        self.logger.info("Resources cleaned up")


# 使用示例
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str, default="auto",
                       choices=["single_4090d_48gb", "quad_4090_24gb", "dual_4090_24gb", "auto"],
                       help="GPU configuration preset")
    parser.add_argument("--gpu_ids", type=int, nargs="+", help="Manual GPU IDs")
    parser.add_argument("--batch_size", type=int, default=8, help="Batch size per GPU")
    args = parser.parse_args()
    
    # 创建配置
    if args.gpu_ids:
        # 手动指定GPU
        config = GPUConfig(
            mode="manual",
            gpu_ids=args.gpu_ids,
            batch_size_per_gpu=args.batch_size
        )
    else:
        # 使用预设
        config = args.config
    
    # 初始化引擎
    engine = MuseTalkGPUEngine(config)
    
    # 打印配置信息
    print(f"Engine initialized with GPUs: {engine.gpu_manager.gpu_ids}")
    print(f"Batch size per GPU: {engine.config.batch_size_per_gpu}")
    print(f"Total batch size: {engine.config.batch_size_per_gpu * len(engine.gpu_manager.gpu_ids)}")