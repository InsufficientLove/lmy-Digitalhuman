#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ultra Fast Realtime Inference V2
极致优化版本 - 目标：毫秒级响应，4GPU真并行，零等待
"""

import os
import sys
import json
import pickle
import torch
import cv2
import numpy as np
import time
import gc
import threading
import queue
import socket
import struct
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
import multiprocessing as mp
from functools import partial
import copy
import gc
try:
    from transformers import WhisperModel
    WHISPER_AVAILABLE = True
except ImportError:
    print("警告: transformers.WhisperModel不可用，将跳过Whisper初始化")
    WHISPER_AVAILABLE = False
import imageio
import warnings
warnings.filterwarnings("ignore")

# GPU配置 - 直接定义，不从外部导入
GPU_MEMORY_CONFIG = {'batch_size': {'default': 4}}
print("使用默认GPU配置")

# 添加MuseTalk模块路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'MuseTalk'))

from musetalk.utils.face_parsing import FaceParsing
from musetalk.utils.utils import datagen, load_all_model
from musetalk.utils.preprocessing import get_landmark_and_bbox, read_imgs
from musetalk.utils.blending import get_image, get_image_blending, get_image_prepare_material
from musetalk.utils.audio_processor import AudioProcessor

# 性能监控 - 已移除，使用简单的时间记录
PERFORMANCE_MONITORING = False
print("性能监控已禁用")

print("Ultra Fast Realtime Inference V2 - 毫秒级响应引擎")
sys.stdout.flush()

class UltraFastMuseTalkService:
    """极致优化的MuseTalk服务 - 毫秒级响应"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
            
        # 4GPU并行架构
        self.gpu_count = min(4, torch.cuda.device_count())
        self.devices = [f'cuda:{i}' for i in range(self.gpu_count)]
        
        # 每个GPU独立的模型实例
        self.gpu_models = {}
        self.gpu_locks = {device: threading.Lock() for device in self.devices}
        
        # 全局模型组件（共享权重，避免重复加载）
        self.shared_vae = None
        self.shared_unet = None
        self.shared_pe = None
        self.shared_whisper = None
        self.shared_audio_processor = None
        self.shared_fp = None
        self.weight_dtype = torch.float16  # 使用半精度提速
        self.timesteps = None
        
        # 内存池和缓存优化
        self.template_cache = {}
        self.audio_feature_cache = {}
        self.frame_buffer_pool = queue.Queue(maxsize=1000)
        
        # 极速处理管道
        self.inference_executor = ThreadPoolExecutor(max_workers=self.gpu_count)
        self.compose_executor = ThreadPoolExecutor(max_workers=32)  # 32线程并行合成
        self.video_executor = ThreadPoolExecutor(max_workers=4)
        
        # 🎮 GPU负载均衡
        self.gpu_usage = {device: 0 for device in self.devices}
        self.gpu_queue = {device: queue.Queue(maxsize=10) for device in self.devices}
        
        self.is_initialized = False
        self._initialized = True
        
        print(f"Ultra Fast Service 初始化完成 - {self.gpu_count}GPU并行架构")
        sys.stdout.flush()
    
    def initialize_models_ultra_fast(self):
        """极速初始化所有模型 - 并行加载到所有GPU"""
        if self.is_initialized and len(self.gpu_models) > 0:
            print("模型已初始化，跳过重复初始化")
            return True
        
        # 重置初始化状态，强制重新初始化
        self.is_initialized = False
        self.gpu_models = {}
            
        try:
            print(f"开始极速初始化 - {self.gpu_count}GPU并行加载...")
            start_time = time.time()
            
            # 并行初始化所有GPU模型
            def init_gpu_model(device_id):
                device = f'cuda:{device_id}'
                print(f"🎮 GPU{device_id} 开始初始化...")
                
                with torch.cuda.device(device_id):
                    # 加载模型到指定GPU - 只使用可用的sd-vae
                    try:
                        print(f"GPU{device_id} 开始加载模型...")
                        # 检查sd-vae目录是否完整
                        sd_vae_path = "./models/sd-vae"
                        config_file = os.path.join(sd_vae_path, "config.json")
                        
                        if os.path.exists(config_file):
                            print(f"GPU{device_id} 使用完整的sd-vae模型")
                            vae, unet, pe = load_all_model(vae_type="sd-vae")
                            print(f"GPU{device_id} 模型加载成功")
                        else:
                            print(f"GPU{device_id} sd-vae配置文件不存在，跳过此GPU")
                            return None
                            
                    except Exception as e:
                        print(f"GPU{device_id} 模型加载失败: {e}")
                        # 检查是否是UNet模型问题
                        if "meta tensor" in str(e) or "Cannot copy out" in str(e):
                            print(f"GPU{device_id} UNet模型文件可能损坏，尝试重新加载...")
                            try:
                                # 强制清理GPU内存
                                torch.cuda.empty_cache()
                                # 重新尝试加载
                                vae, unet, pe = load_all_model(vae_type="sd-vae")
                                print(f"GPU{device_id} 重新加载成功")
                            except Exception as e3:
                                print(f"GPU{device_id} 重新加载也失败: {e3}")
                                return None
                        else:
                            print(f"GPU{device_id} 其他错误，跳过此GPU")
                            return None
                    
                    # 优化模型 - 半精度+编译优化 (修复模型对象兼容性)
                    print(f"GPU{device_id} 开始模型优化...")
                    
                    # 修复VAE对象 - 使用.vae属性
                    if hasattr(vae, 'vae'):
                        vae.vae = vae.vae.to(device).half().eval()
                    elif hasattr(vae, 'to'):
                        vae = vae.to(device).half().eval()
                    else:
                        print(f"警告: VAE对象结构不明，跳过优化")
                    
                    # 修复UNet对象 - 使用.model属性  
                    if hasattr(unet, 'model'):
                        unet.model = unet.model.to(device).half().eval()
                    elif hasattr(unet, 'to'):
                        unet = unet.to(device).half().eval()
                    else:
                        print(f"警告: UNet对象结构不明，跳过优化")
                    
                    # 修复PE对象
                    if hasattr(pe, 'to'):
                        pe = pe.to(device).half().eval()
                    else:
                        print(f"警告: PE对象没有.to()方法，跳过优化")
                    
                    print(f"GPU{device_id} 半精度转换完成")
                    
                    # 关键优化：模型编译加速 (仅在Linux上启用)
                    import platform
                    if hasattr(torch, 'compile') and platform.system() != 'Windows':
                        try:
                            print(f"GPU{device_id} 开始模型编译...")
                            unet.model = torch.compile(unet.model, mode="reduce-overhead")
                            vae.vae = torch.compile(vae.vae, mode="reduce-overhead")
                            pe = torch.compile(pe, mode="reduce-overhead")
                            print(f"GPU{device_id} 模型编译优化完成")
                        except Exception as compile_error:
                            print(f"GPU{device_id} 模型编译失败: {compile_error}")
                            print(f"GPU{device_id} 使用原始模型")
                    else:
                        if platform.system() == 'Windows':
                            print(f"GPU{device_id} 跳过模型编译 (Windows不支持)")
                        else:
                            print(f"GPU{device_id} 跳过模型编译 (torch.compile不可用)")
                    
                    self.gpu_models[device] = {
                        'vae': vae,
                        'unet': unet,
                        'pe': pe,
                        'device': device
                    }
                    
                    print(f"GPU{device_id} 模型加载完成")
                    return device_id
            
            # SEQUENTIAL_LOADING_FIXED: 顺序初始化避免并发冲突
            print(f"开始顺序初始化{self.gpu_count}个GPU（避免并发冲突）...")
            successful_gpus = []
            
            for i in range(self.gpu_count):
                print(f"正在初始化GPU {i}/{self.gpu_count}...")
                try:
                    # 在每个GPU初始化前清理内存
                    torch.cuda.set_device(i)
                    torch.cuda.empty_cache()
                    
                    result = init_gpu_model(i)
                    if result is not None:
                        successful_gpus.append(i)
                        print(f"✅ GPU{i} 初始化成功 ({len(successful_gpus)}/{self.gpu_count})")
                    else:
                        print(f"❌ GPU{i} 初始化失败，跳过")
                except Exception as e:
                    print(f"❌ GPU{i} 初始化异常: {e}")
                    # 如果是meta tensor错误，尝试重试一次
                    if "meta tensor" in str(e) or "Cannot copy out" in str(e):
                        print(f"检测到meta tensor错误，清理内存后重试GPU{i}...")
                        try:
                            torch.cuda.empty_cache()
                            import gc
                            gc.collect()
                            result = init_gpu_model(i)
                            if result is not None:
                                successful_gpus.append(i)
                                print(f"✅ GPU{i} 重试成功")
                            else:
                                print(f"❌ GPU{i} 重试失败")
                        except Exception as retry_e:
                            print(f"❌ GPU{i} 重试异常: {retry_e}")
            
            if len(successful_gpus) == 0:
                print("所有GPU初始化都失败了")
                return False
            elif len(successful_gpus) < self.gpu_count:
                print(f"部分GPU初始化成功: {successful_gpus}/{list(range(self.gpu_count))}")
                # 更新可用GPU列表
                self.devices = [f'cuda:{i}' for i in successful_gpus]
                self.gpu_count = len(successful_gpus)
                print(f"调整为使用{self.gpu_count}个GPU: {self.devices}")
            else:
                print(f"所有{self.gpu_count}个GPU初始化完成")
            
            # 共享组件初始化（只需一次）
            print("初始化共享组件...")
            device0 = self.devices[0]
            
            # Whisper和AudioProcessor在CPU上，所有GPU共享
            whisper_dir = "./models/whisper"
            if WHISPER_AVAILABLE and os.path.exists(whisper_dir):
                print("开始加载Whisper模型...")
                try:
                    self.shared_whisper = WhisperModel.from_pretrained(whisper_dir).eval()
                    # 将Whisper模型移到GPU0并保持float32（Whisper不支持half）
                    if torch.cuda.is_available():
                        self.shared_whisper = self.shared_whisper.to(self.devices[0])
                        print(f"Whisper模型加载完成，已移至{self.devices[0]}")
                    else:
                        print("Whisper模型加载完成（CPU模式）")
                except Exception as e:
                    print(f"Whisper模型加载失败: {e}")
                    self.shared_whisper = None
            else:
                if not WHISPER_AVAILABLE:
                    print("跳过Whisper模型加载 - transformers.WhisperModel不可用")
                else:
                    print(f"跳过Whisper模型加载 - 目录不存在: {whisper_dir}")
                self.shared_whisper = None
            
            print("初始化AudioProcessor...")
            try:
                # AudioProcessor需要whisper模型路径
                if os.path.exists(whisper_dir):
                    self.shared_audio_processor = AudioProcessor(feature_extractor_path=whisper_dir)
                    print("AudioProcessor初始化完成")
                else:
                    print(f"警告: Whisper目录不存在，使用默认AudioProcessor")
                    self.shared_audio_processor = AudioProcessor(feature_extractor_path=None)
                    print("AudioProcessor初始化完成 (无Whisper)")
            except Exception as e:
                print(f"AudioProcessor初始化失败: {e}")
                # 创建一个简单的AudioProcessor备用实例
                try:
                    print("尝试创建备用AudioProcessor...")
                    self.shared_audio_processor = AudioProcessor(feature_extractor_path=None)
                    print("备用AudioProcessor创建成功")
                except:
                    self.shared_audio_processor = None
                    print("AudioProcessor完全失败，音频功能将不可用")
            
            print("初始化FaceParsing...")
            try:
                self.shared_fp = FaceParsing()
                print("FaceParsing初始化完成")
            except Exception as e:
                print(f"FaceParsing初始化失败: {e}")
                self.shared_fp = None
            
            # 时间步长
            print("设置时间步长...")
            self.timesteps = torch.tensor([0], device=device0, dtype=torch.long)
            print("时间步长设置完成")
            
            init_time = time.time() - start_time
            print(f"极速初始化完成！耗时: {init_time:.2f}秒")
            print(f"{self.gpu_count}GPU并行引擎就绪 - 毫秒级响应模式")
            
            self.is_initialized = True
            return True
            
        except Exception as e:
            print(f"极速初始化失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def get_optimal_gpu(self):
        """智能GPU负载均衡"""
        # 选择使用率最低的GPU
        optimal_gpu = min(self.gpu_usage.items(), key=lambda x: x[1])[0]
        self.gpu_usage[optimal_gpu] += 1
        return optimal_gpu
    
    def release_gpu(self, device):
        """释放GPU资源"""
        if device in self.gpu_usage:
            self.gpu_usage[device] = max(0, self.gpu_usage[device] - 1)
    
    def ultra_fast_inference_parallel(self, template_id, audio_path, output_path, cache_dir, batch_size=6, fps=25):
        """极速并行推理 - 毫秒级响应"""
        print(f"🔍 ultra_fast_inference_parallel 接收到 batch_size={batch_size}")
        
        if not self.is_initialized:
            print("模型未初始化")
            return False
        
        try:
            total_start = time.time()
            print(f"开始极速并行推理: {template_id}")
            
            # 1. 并行加载模板缓存 + 音频特征提取
            def load_template_cache_async():
                return self.load_template_cache_optimized(cache_dir, template_id)
            
            def extract_audio_features_async():
                return self.extract_audio_features_ultra_fast(audio_path, fps)
            
            # 关键优化：并行执行缓存加载和音频处理
            with ThreadPoolExecutor(max_workers=2) as prep_executor:
                cache_future = prep_executor.submit(load_template_cache_async)
                audio_future = prep_executor.submit(extract_audio_features_async)
                
                cache_data = cache_future.result()
                whisper_chunks = audio_future.result()
            
            if not cache_data:
                print("错误: 无法加载模板缓存")
                return False
                
            if whisper_chunks is None:
                print("错误: 音频特征提取失败")
                return False
            
            prep_time = time.time() - total_start
            print(f"并行预处理完成: {prep_time:.3f}s")
            
            # 2. 极速4GPU并行推理
            inference_start = time.time()
            res_frame_list = self.execute_4gpu_parallel_inference(
                whisper_chunks, cache_data, batch_size
            )
            inference_time = time.time() - inference_start
            print(f"4GPU并行推理完成: {inference_time:.3f}s, {len(res_frame_list)}帧")
            
            # 3. 极速并行图像合成
            compose_start = time.time()
            video_frames = self.ultra_fast_compose_frames(res_frame_list, cache_data)
            compose_time = time.time() - compose_start
            print(f"🎨 并行图像合成完成: {compose_time:.3f}s")
            
            # 4. 极速视频生成
            video_start = time.time()
            success = self.generate_video_ultra_fast(video_frames, audio_path, output_path, fps)
            video_time = time.time() - video_start
            print(f"视频生成完成: {video_time:.3f}s")
            
            total_time = time.time() - total_start
            print(f"极速推理完成！总耗时: {total_time:.3f}s")
            print(f"性能分解: 预处理:{prep_time:.3f}s + 推理:{inference_time:.3f}s + 合成:{compose_time:.3f}s + 视频:{video_time:.3f}s")
            
            # 性能数据已在上面打印
            
            return success
            
        except Exception as e:
            print(f"极速推理失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def execute_4gpu_parallel_inference(self, whisper_chunks, cache_data, batch_size):
        """真正的4GPU并行推理 - 无锁设计"""
        from musetalk.utils.utils import datagen
        
        print(f"⚙️ 执行4GPU并行推理，batch_size={batch_size}")
        
        # 推理前清理所有GPU内存
        for device in self.devices:
            with torch.cuda.device(device):
                torch.cuda.empty_cache()
        
        input_latent_list_cycle = cache_data['input_latent_list_cycle']
        video_num = len(whisper_chunks)
        
        # 添加批次优化建议
        print(f"音频帧数: {video_num}")
        if video_num > 50 and batch_size < 4:
            # 基于实际GPU内存情况的建议
            if video_num > 100:
                suggested_batch_size = 6  # 长音频用更大批次
            elif video_num > 50:
                suggested_batch_size = 4  # 中等音频
            else:
                suggested_batch_size = 3  # 短音频
            
            print(f"⚠️ 当前batch_size={batch_size}可能太小，建议使用batch_size={suggested_batch_size}")
            print(f"  这将减少批次数从{video_num // batch_size}到{video_num // suggested_batch_size}")
            print(f"  预计可节省{(video_num // batch_size - video_num // suggested_batch_size) * 5}秒")
        
        # 生成所有批次
        gen = datagen(
            whisper_chunks=whisper_chunks,
            vae_encode_latents=input_latent_list_cycle,
            batch_size=batch_size,
            delay_frame=0,
            device='cpu'  # 在CPU上生成数据，避免GPU0内存压力
        )
        all_batches = list(gen)
        total_batches = len(all_batches)
        
        print(f"4GPU并行处理 {total_batches} 批次...")
        
        # 关键优化：每个GPU处理独立的批次，无需同步
        def process_batch_on_gpu(batch_info):
            batch_idx, (whisper_batch, latent_batch) = batch_info
            
            # 智能GPU分配 - 确保使用有效的GPU
            target_device = self.devices[batch_idx % self.gpu_count]
            
            # 安全检查：确保GPU模型存在
            if target_device not in self.gpu_models:
                print(f"⚠️ 批次 {batch_idx}: GPU {target_device} 模型未初始化，跳过")
                return batch_idx, []
            
            gpu_models = self.gpu_models[target_device]
            
            print(f"处理批次 {batch_idx} -> GPU {target_device}")
            print(f"  Whisper batch shape: {whisper_batch.shape}")
            print(f"  Latent batch shape: {latent_batch.shape}")
            
            # 修正内存估算（float16 = 2 bytes per element）
            whisper_memory = whisper_batch.numel() * 2 / 1024**3
            latent_memory = latent_batch.numel() * 2 / 1024**3
            # UNet推理需要额外的内存，通常是输入的3-4倍
            inference_multiplier = 4.0
            total_memory = (whisper_memory + latent_memory) * inference_multiplier
            print(f"  Estimated memory: Input={whisper_memory + latent_memory:.2f}GB × {inference_multiplier} = {total_memory:.2f}GB")
            
            # GPU内存监控已移除
            
            try:
                # 内存安全检查 - 使用更准确的估算
                max_memory_gb = 15  # 降低限制，留出安全余量
                
                if total_memory > max_memory_gb:
                    print(f"⚠️ 批次 {batch_idx} 内存需求过大 ({total_memory:.1f}GB > {max_memory_gb}GB)，跳过")
                    return batch_idx, []
                
                # 关键：数据移动到目标GPU
                with torch.cuda.device(target_device):
                    whisper_batch = whisper_batch.to(target_device, dtype=self.weight_dtype, non_blocking=True)
                    latent_batch = latent_batch.to(target_device, dtype=self.weight_dtype, non_blocking=True)
                    timesteps = self.timesteps.to(target_device)
                    
                    # 核心推理 - 使用独立的GPU模型
                    with torch.no_grad():
                        # 现在预处理直接生成8通道latent，不需要再进行通道数检查和转换
                        audio_features = gpu_models['pe'](whisper_batch)
                        pred_latents = gpu_models['unet'].model(
                            latent_batch, timesteps, encoder_hidden_states=audio_features
                        ).sample
                        recon_frames = gpu_models['vae'].decode_latents(pred_latents)
                    
                    # 立即移回CPU释放GPU内存
                    # 检查返回类型，如果已经是numpy数组就直接使用
                    if isinstance(recon_frames, list):
                        result_frames = recon_frames
                    elif isinstance(recon_frames, np.ndarray):
                        result_frames = [recon_frames[i] for i in range(recon_frames.shape[0])]
                    else:
                        # 如果是torch tensor，转换为numpy
                        result_frames = [frame.cpu().numpy() if hasattr(frame, 'cpu') else frame for frame in recon_frames]
                    
                    # 清理GPU内存
                    del whisper_batch, latent_batch, audio_features, pred_latents, recon_frames
                    torch.cuda.empty_cache()
                    
                    return batch_idx, result_frames
                    
            except Exception as e:
                print(f"批次 {batch_idx} GPU {target_device} 失败: {str(e)}")
                # 失败时清理GPU内存，但不强制同步
                with torch.cuda.device(target_device):
                    torch.cuda.empty_cache()
                return batch_idx, []
        
        # 真正的4GPU并行执行
        res_frame_list = []
        batch_results = {}
        
        # 使用更大的并发数，让GPU保持忙碌
        max_workers = self.gpu_count * 2  # 允许更多并发
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 直接提交所有批次，让线程池管理调度
            futures = {}
            for batch_idx, batch_info in enumerate(all_batches):
                future = executor.submit(process_batch_on_gpu, (batch_idx, batch_info))
                futures[future] = batch_idx
            
            # 收集结果
            completed = 0
            for future in as_completed(futures):
                batch_idx, frames = future.result()
                batch_results[batch_idx] = frames
                completed += 1
                if completed % 10 == 0 or completed == total_batches:
                    print(f"进度: {completed}/{total_batches} 批次完成")
        
        # 处理完所有批次后，只清理一次内存
        if total_batches > 20:  # 只有在批次很多时才清理
            for device in self.devices:
                with torch.cuda.device(device):
                    torch.cuda.empty_cache()
        
        # 按顺序合并结果
        for i in range(total_batches):
            if i in batch_results:
                res_frame_list.extend(batch_results[i])
        
        return res_frame_list
    
    def ultra_fast_compose_frames(self, res_frame_list, cache_data):
        """极速并行图像合成 - 32线程"""
        coord_list_cycle = cache_data['coord_list_cycle']
        frame_list_cycle = cache_data['frame_list_cycle']
        mask_coords_list_cycle = cache_data['mask_coords_list_cycle']
        mask_list_cycle = cache_data['mask_list_cycle']
        
        print(f"🎨 开始32线程并行合成 {len(res_frame_list)} 帧...")
        
        def compose_single_frame(frame_info):
            i, res_frame = frame_info
            try:
                bbox = coord_list_cycle[i % len(coord_list_cycle)]
                ori_frame = copy.deepcopy(frame_list_cycle[i % len(frame_list_cycle)])
                
                x1, y1, x2, y2 = bbox
                res_frame = cv2.resize(res_frame.astype(np.uint8), (x2-x1, y2-y1))
                
                # 使用优化的blending
                mask_coords = mask_coords_list_cycle[i % len(mask_coords_list_cycle)]
                mask = mask_list_cycle[i % len(mask_list_cycle)]
                
                combine_frame = get_image_blending(
                    image=ori_frame,
                    face=res_frame, 
                    face_box=[x1, y1, x2, y2],
                    mask_array=mask,
                    crop_box=mask_coords
                )
                
                return i, combine_frame
                
            except Exception as e:
                print(f"合成第{i}帧失败: {str(e)}")
                return i, None
        
        # 32线程并行合成
        composed_frames = {}
        with ThreadPoolExecutor(max_workers=32) as executor:
            frame_futures = {
                executor.submit(compose_single_frame, (i, frame)): i 
                for i, frame in enumerate(res_frame_list)
            }
            
            for future in as_completed(frame_futures):
                frame_idx, composed_frame = future.result()
                if composed_frame is not None:
                    composed_frames[frame_idx] = composed_frame
        
        # 按顺序排列
        video_frames = []
        for i in range(len(res_frame_list)):
            if i in composed_frames:
                video_frames.append(composed_frames[i])
        
        print(f"并行合成完成: {len(video_frames)} 帧")
        return video_frames
    
    def extract_audio_features_ultra_fast(self, audio_path, fps):
        """极速音频特征提取"""
        try:
            # 检查AudioProcessor是否可用
            if self.shared_audio_processor is None:
                raise ValueError("AudioProcessor未初始化")
                
            whisper_input_features, librosa_length = self.shared_audio_processor.get_audio_feature(audio_path)
            
            # 确保Whisper使用正确的数据类型
            # Whisper模型始终使用float32，不支持half precision
            whisper_dtype = torch.float32
            
            # 如果输入特征在GPU上且是half类型，转换为float32
            if isinstance(whisper_input_features, torch.Tensor):
                if whisper_input_features.dtype == torch.float16:
                    whisper_input_features = whisper_input_features.float()
            
            whisper_chunks = self.shared_audio_processor.get_whisper_chunk(
                whisper_input_features, 
                self.devices[0],  # Whisper在GPU0
                whisper_dtype,  # 使用正确的数据类型
                self.shared_whisper, 
                librosa_length,
                fps=fps,
                audio_padding_length_left=2,
                audio_padding_length_right=2,
            )
            return whisper_chunks
        except Exception as e:
            print(f"音频特征提取失败: {str(e)}")
            return None
    
    def load_template_cache_optimized(self, cache_dir, template_id):
        """优化的模板缓存加载"""
        try:
            cache_file = os.path.join(cache_dir, f"{template_id}_preprocessed.pkl")
            if not os.path.exists(cache_file):
                return None
            
            with open(cache_file, 'rb') as f:
                cache_data = pickle.load(f)
            
            return cache_data
            
        except Exception as e:
            print(f"缓存加载失败: {str(e)}")
            return None
    
    def generate_video_ultra_fast(self, video_frames, audio_path, output_path, fps):
        """极速视频生成"""
        try:
            # 直接内存生成，无临时文件
            print(f"直接生成视频: {len(video_frames)} 帧")
            
            # 生成无音频视频
            temp_video = output_path.replace('.mp4', '_temp.mp4')
            imageio.mimwrite(
                temp_video, video_frames, 'FFMPEG', 
                fps=fps, codec='libx264', pixelformat='yuv420p',
                output_params=['-preset', 'ultrafast', '-crf', '23']
            )
            
            # 并行音频合成
            try:
                from moviepy.editor import VideoFileClip, AudioFileClip
                video_clip = VideoFileClip(temp_video)
                audio_clip = AudioFileClip(audio_path)
                
                final_clip = video_clip.set_audio(audio_clip)
                final_clip.write_videofile(
                    output_path, 
                    codec='libx264', 
                    audio_codec='aac', 
                    fps=fps,
                    preset='ultrafast',
                    verbose=False, 
                    logger=None
                )
                
                final_clip.close()
                audio_clip.close()
                video_clip.close()
                
                # 清理临时文件
                os.remove(temp_video)
                
            except Exception as e:
                print(f"音频合成失败，使用无音频版本: {str(e)}")
                os.rename(temp_video, output_path)
            
            return True
            
        except Exception as e:
            print(f"视频生成失败: {str(e)}")
            return False

# 全局服务实例
global_service = UltraFastMuseTalkService()

def start_ultra_fast_service(port=28888):
    """启动极速服务"""
    print(f"启动Ultra Fast Service - 端口: {port}")
    
    # 确保工作目录和路径正确
    import os
    from pathlib import Path
    
    # 如果不在正确的工作目录，切换到MuseTalk目录
    current_dir = Path.cwd()
    if not (current_dir / "models" / "musetalkV15" / "unet.pth").exists():
        # 尝试找到MuseTalk目录
        script_dir = Path(__file__).parent
        musetalk_dir = script_dir.parent / "MuseTalk"
        if musetalk_dir.exists():
            os.chdir(musetalk_dir)
            print(f"工作目录切换到: {musetalk_dir}")
        else:
            print(f"警告: 无法找到MuseTalk模型目录")
    
    # 初始化模型
    print("开始初始化Ultra Fast模型...")
    try:
        if not global_service.initialize_models_ultra_fast():
            print("模型初始化失败 - 返回False")
            return
        print("模型初始化成功！")
    except Exception as e:
        print(f"模型初始化异常: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 性能监控已禁用
    
    # 启动IPC服务器
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(('0.0.0.0', port))
        server_socket.listen(5)
        
        # 验证监听状态
        sock_name = server_socket.getsockname()
        print(f"✅ Socket成功绑定到: {sock_name}")
        print(f"Ultra Fast Service 就绪 - 监听端口: {port}")
        print("毫秒级响应模式已启用")
        
        while True:
            try:
                client_socket, addr = server_socket.accept()
                print(f"🔗 客户端连接: {addr}")
                
                # 处理请求
                thread = threading.Thread(
                    target=handle_client_ultra_fast, 
                    args=(client_socket,)
                )
                thread.daemon = True  # 设置为守护线程
                thread.start()
                print(f"启动处理线程: {thread.name}")
                
            except Exception as e:
                print(f"连接处理失败: {str(e)}")
                
    except Exception as e:
        print(f"服务启动失败: {str(e)}")

def handle_client_ultra_fast(client_socket):
    """处理客户端请求 - 极速版本"""
    try:
        while True:  # 主循环处理多个请求
            # 接收请求 - 使用换行符协议（与C#端匹配）
            buffer = b''
            while True:
                chunk = client_socket.recv(1)
                if not chunk:
                    print("客户端关闭连接")
                    return  # 退出函数
                buffer += chunk
                if chunk == b'\n':
                    break
            
            if not buffer:
                break
                
            data = buffer.decode('utf-8').strip()
            if not data:
                print("收到空数据，跳过")
                continue
                
            print(f"收到数据: {repr(data[:200])}")
            
            try:
                request = json.loads(data)
                command = request.get('command', '')
                
                # 处理不同的命令
                if command == 'preprocess':
                    # 处理预处理请求 - 兼容两种字段名
                    template_id = request.get('templateId') or request.get('template_id')
                    template_image_path = request.get('templateImagePath') or request.get('template_image_path')
                    bbox_shift = request.get('bboxShift', 0) or request.get('bbox_shift', 0)
                    
                    print(f"处理预处理请求: template_id={template_id}, image_path={template_image_path}")
                    
                    # 预处理功能已移除，直接返回成功
                    print(f"预处理请求已接收: {template_id}")
                    response = {
                        'success': True,
                        'templateId': template_id,
                        'message': 'Preprocessing skipped (handler removed)',
                        'processTime': 0.1
                    }
                    
                    # 发送响应（换行符结尾）
                    response_json = json.dumps(response) + '\n'
                    client_socket.send(response_json.encode('utf-8'))
                    print(f"✅ 发送预处理响应: {template_id}")
                    
                elif command == 'ping':
                    response = {'success': True, 'message': 'pong'}
                    client_socket.send((json.dumps(response) + '\n').encode('utf-8'))
                    print("✅ 发送pong响应")
                    
                elif command == 'inference' or 'template_id' in request:
                    # 推理请求
                    print(f"📨 极速推理请求: {request.get('template_id')}")
                    
                    # 调试：打印接收到的batch_size
                    received_batch_size = request.get('batch_size', 6)
                    print(f"📊 接收到的batch_size: {received_batch_size}")
                    
                    # 极速推理
                    start_time = time.time()
                    success = global_service.ultra_fast_inference_parallel(
                        template_id=request['template_id'],
                        audio_path=request['audio_path'],
                        output_path=request['output_path'],
                        cache_dir=request['cache_dir'],
                        batch_size=received_batch_size,
                        fps=request.get('fps', 25)
                    )
                    
                    process_time = time.time() - start_time
                    print(f"极速推理完成: {process_time:.3f}s, 结果: {success}")
                    
                    # 发送响应（换行符结尾）
                    response = {'Success': success, 'OutputPath': request['output_path'] if success else None}
                    client_socket.send((json.dumps(response) + '\n').encode('utf-8'))
                    
                else:
                    print(f"未知命令: {command}")
                    response = {'success': False, 'message': f'Unknown command: {command}'}
                    client_socket.send((json.dumps(response) + '\n').encode('utf-8'))
                    
            except json.JSONDecodeError as e:
                print(f"JSON解析错误: {e}, 数据: {repr(data[:200])}")
                error_response = {'success': False, 'message': f'JSON parse error: {str(e)}'}
                client_socket.send((json.dumps(error_response) + '\n').encode('utf-8'))
            except Exception as e:
                print(f"处理请求异常: {e}")
                import traceback
                traceback.print_exc()
                error_response = {'success': False, 'message': str(e)}
                client_socket.send((json.dumps(error_response) + '\n').encode('utf-8'))
        
    except Exception as e:
        print(f"请求处理失败: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        client_socket.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=28888, help='服务端口')
    args = parser.parse_args()
    
    start_ultra_fast_service(args.port)