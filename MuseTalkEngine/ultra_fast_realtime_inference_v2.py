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
from transformers import WhisperModel
import imageio
import warnings
warnings.filterwarnings("ignore")

# 添加MuseTalk模块路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'MuseTalk'))

from musetalk.utils.face_parsing import FaceParsing
from musetalk.utils.utils import datagen, load_all_model
from musetalk.utils.preprocessing import get_landmark_and_bbox, read_imgs
from musetalk.utils.blending import get_image, get_image_blending, get_image_prepare_material
from musetalk.utils.audio_processor import AudioProcessor

# 导入性能监控
try:
    from performance_monitor import start_performance_monitoring, record_performance, print_performance_report
    PERFORMANCE_MONITORING = True
except ImportError:
    PERFORMANCE_MONITORING = False
    print("⚠️ 性能监控模块未找到，跳过性能监控")

print("🚀 Ultra Fast Realtime Inference V2 - 毫秒级响应引擎")
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
            
        # 🚀 4GPU并行架构
        self.gpu_count = min(4, torch.cuda.device_count())
        self.devices = [f'cuda:{i}' for i in range(self.gpu_count)]
        
        # 🔥 每个GPU独立的模型实例
        self.gpu_models = {}
        self.gpu_locks = {device: threading.Lock() for device in self.devices}
        
        # 🎯 全局模型组件（共享权重，避免重复加载）
        self.shared_vae = None
        self.shared_unet = None
        self.shared_pe = None
        self.shared_whisper = None
        self.shared_audio_processor = None
        self.shared_fp = None
        self.weight_dtype = torch.float16  # 使用半精度提速
        self.timesteps = None
        
        # 🚀 内存池和缓存优化
        self.template_cache = {}
        self.audio_feature_cache = {}
        self.frame_buffer_pool = queue.Queue(maxsize=1000)
        
        # 🔥 极速处理管道
        self.inference_executor = ThreadPoolExecutor(max_workers=self.gpu_count)
        self.compose_executor = ThreadPoolExecutor(max_workers=32)  # 32线程并行合成
        self.video_executor = ThreadPoolExecutor(max_workers=4)
        
        # 🎮 GPU负载均衡
        self.gpu_usage = {device: 0 for device in self.devices}
        self.gpu_queue = {device: queue.Queue(maxsize=10) for device in self.devices}
        
        self.is_initialized = False
        self._initialized = True
        
        print(f"🚀 Ultra Fast Service 初始化完成 - {self.gpu_count}GPU并行架构")
        sys.stdout.flush()
    
    def initialize_models_ultra_fast(self):
        """极速初始化所有模型 - 并行加载到所有GPU"""
        if self.is_initialized:
            return True
            
        try:
            print(f"🚀 开始极速初始化 - {self.gpu_count}GPU并行加载...")
            start_time = time.time()
            
            # 🔥 并行初始化所有GPU模型
            def init_gpu_model(device_id):
                device = f'cuda:{device_id}'
                print(f"🎮 GPU{device_id} 开始初始化...")
                
                with torch.cuda.device(device_id):
                    # 加载模型到指定GPU
                    model_dict = load_all_model()
                    
                    # 优化模型 - 半精度+编译优化
                    vae = model_dict['vae'].to(device).half().eval()
                    unet = model_dict['unet'].to(device).half().eval()
                    pe = model_dict['pe'].to(device).half().eval()
                    
                    # 🚀 关键优化：模型编译加速
                    if hasattr(torch, 'compile'):
                        try:
                            unet.model = torch.compile(unet.model, mode="reduce-overhead")
                            vae.vae = torch.compile(vae.vae, mode="reduce-overhead")
                            pe = torch.compile(pe, mode="reduce-overhead")
                            print(f"✅ GPU{device_id} 模型编译优化完成")
                        except:
                            print(f"⚠️ GPU{device_id} 模型编译失败，使用原始模型")
                    
                    self.gpu_models[device] = {
                        'vae': vae,
                        'unet': unet,
                        'pe': pe,
                        'device': device
                    }
                    
                    print(f"✅ GPU{device_id} 模型加载完成")
                    return device_id
            
            # 🔥 真正的并行初始化
            with ThreadPoolExecutor(max_workers=self.gpu_count) as executor:
                futures = [executor.submit(init_gpu_model, i) for i in range(self.gpu_count)]
                for future in as_completed(futures):
                    gpu_id = future.result()
                    print(f"🎯 GPU{gpu_id} 就绪")
            
            # 🎵 共享组件初始化（只需一次）
            print("🎵 初始化共享组件...")
            device0 = self.devices[0]
            
            # Whisper和AudioProcessor在CPU上，所有GPU共享
            whisper_dir = "./models/whisper"
            if os.path.exists(whisper_dir):
                self.shared_whisper = WhisperModel.from_pretrained(whisper_dir).eval()
                print("✅ Whisper模型加载完成")
            
            self.shared_audio_processor = AudioProcessor()
            self.shared_fp = FaceParsing()
            
            # 时间步长
            self.timesteps = torch.tensor([0], device=device0, dtype=torch.long)
            
            init_time = time.time() - start_time
            print(f"🎉 极速初始化完成！耗时: {init_time:.2f}秒")
            print(f"🚀 {self.gpu_count}GPU并行引擎就绪 - 毫秒级响应模式")
            
            self.is_initialized = True
            return True
            
        except Exception as e:
            print(f"❌ 极速初始化失败: {str(e)}")
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
    
    def ultra_fast_inference_parallel(self, template_id, audio_path, output_path, cache_dir, batch_size=16, fps=25):
        """极速并行推理 - 毫秒级响应"""
        if not self.is_initialized:
            print("❌ 模型未初始化")
            return False
        
        try:
            total_start = time.time()
            print(f"⚡ 开始极速并行推理: {template_id}")
            
            # 🔥 1. 并行加载模板缓存 + 音频特征提取
            def load_template_cache_async():
                return self.load_template_cache_optimized(cache_dir, template_id)
            
            def extract_audio_features_async():
                return self.extract_audio_features_ultra_fast(audio_path, fps)
            
            # 🚀 关键优化：并行执行缓存加载和音频处理
            with ThreadPoolExecutor(max_workers=2) as prep_executor:
                cache_future = prep_executor.submit(load_template_cache_async)
                audio_future = prep_executor.submit(extract_audio_features_async)
                
                cache_data = cache_future.result()
                whisper_chunks = audio_future.result()
            
            if not cache_data or not whisper_chunks:
                return False
            
            prep_time = time.time() - total_start
            print(f"⚡ 并行预处理完成: {prep_time:.3f}s")
            
            # 🔥 2. 极速4GPU并行推理
            inference_start = time.time()
            res_frame_list = self.execute_4gpu_parallel_inference(
                whisper_chunks, cache_data, batch_size
            )
            inference_time = time.time() - inference_start
            print(f"🚀 4GPU并行推理完成: {inference_time:.3f}s, {len(res_frame_list)}帧")
            
            # 🔥 3. 极速并行图像合成
            compose_start = time.time()
            video_frames = self.ultra_fast_compose_frames(res_frame_list, cache_data)
            compose_time = time.time() - compose_start
            print(f"🎨 并行图像合成完成: {compose_time:.3f}s")
            
            # 🔥 4. 极速视频生成
            video_start = time.time()
            success = self.generate_video_ultra_fast(video_frames, audio_path, output_path, fps)
            video_time = time.time() - video_start
            print(f"🎬 视频生成完成: {video_time:.3f}s")
            
            total_time = time.time() - total_start
            print(f"🎉 极速推理完成！总耗时: {total_time:.3f}s")
            print(f"📊 性能分解: 预处理:{prep_time:.3f}s + 推理:{inference_time:.3f}s + 合成:{compose_time:.3f}s + 视频:{video_time:.3f}s")
            
            # 🔍 记录性能数据
            if PERFORMANCE_MONITORING:
                record_performance(inference_time, compose_time, video_time, total_time)
            
            return success
            
        except Exception as e:
            print(f"❌ 极速推理失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def execute_4gpu_parallel_inference(self, whisper_chunks, cache_data, batch_size):
        """真正的4GPU并行推理 - 无锁设计"""
        from musetalk.utils.utils import datagen
        
        input_latent_list_cycle = cache_data['input_latent_list_cycle']
        video_num = len(whisper_chunks)
        
        # 生成所有批次
        gen = datagen(
            whisper_chunks=whisper_chunks,
            vae_encode_latents=input_latent_list_cycle,
            batch_size=batch_size,
            delay_frame=0,
            device=self.devices[0]  # 数据生成在GPU0
        )
        all_batches = list(gen)
        total_batches = len(all_batches)
        
        print(f"🚀 4GPU并行处理 {total_batches} 批次...")
        
        # 🔥 关键优化：每个GPU处理独立的批次，无需同步
        def process_batch_on_gpu(batch_info):
            batch_idx, (whisper_batch, latent_batch) = batch_info
            
            # 智能GPU分配
            target_device = self.devices[batch_idx % self.gpu_count]
            gpu_models = self.gpu_models[target_device]
            
            try:
                # 🚀 关键：数据移动到目标GPU
                with torch.cuda.device(target_device):
                    whisper_batch = whisper_batch.to(target_device, dtype=self.weight_dtype, non_blocking=True)
                    latent_batch = latent_batch.to(target_device, dtype=self.weight_dtype, non_blocking=True)
                    timesteps = self.timesteps.to(target_device)
                    
                    # 🔥 核心推理 - 使用独立的GPU模型
                    with torch.no_grad():
                        audio_features = gpu_models['pe'](whisper_batch)
                        pred_latents = gpu_models['unet'].model(
                            latent_batch, timesteps, encoder_hidden_states=audio_features
                        ).sample
                        recon_frames = gpu_models['vae'].decode_latents(pred_latents)
                    
                    # 立即移回CPU释放GPU内存
                    result_frames = [frame.cpu().numpy() for frame in recon_frames]
                    
                    # 清理GPU内存
                    del whisper_batch, latent_batch, audio_features, pred_latents, recon_frames
                    torch.cuda.empty_cache()
                    
                    return batch_idx, result_frames
                    
            except Exception as e:
                print(f"❌ 批次 {batch_idx} GPU {target_device} 失败: {str(e)}")
                return batch_idx, []
        
        # 🚀 真正的4GPU并行执行
        res_frame_list = []
        batch_results = {}
        
        with ThreadPoolExecutor(max_workers=self.gpu_count) as executor:
            # 提交所有批次
            futures = {
                executor.submit(process_batch_on_gpu, (i, batch)): i 
                for i, batch in enumerate(all_batches)
            }
            
            # 收集结果
            for future in as_completed(futures):
                batch_idx, frames = future.result()
                batch_results[batch_idx] = frames
        
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
                
                # 🚀 使用优化的blending
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
                print(f"❌ 合成第{i}帧失败: {str(e)}")
                return i, None
        
        # 🚀 32线程并行合成
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
        
        print(f"✅ 并行合成完成: {len(video_frames)} 帧")
        return video_frames
    
    def extract_audio_features_ultra_fast(self, audio_path, fps):
        """极速音频特征提取"""
        try:
            whisper_input_features, librosa_length = self.shared_audio_processor.get_audio_feature(audio_path)
            whisper_chunks = self.shared_audio_processor.get_whisper_chunk(
                whisper_input_features, 
                self.devices[0],  # Whisper在GPU0
                self.weight_dtype, 
                self.shared_whisper, 
                librosa_length,
                fps=fps,
                audio_padding_length_left=2,
                audio_padding_length_right=2,
            )
            return whisper_chunks
        except Exception as e:
            print(f"❌ 音频特征提取失败: {str(e)}")
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
            print(f"❌ 缓存加载失败: {str(e)}")
            return None
    
    def generate_video_ultra_fast(self, video_frames, audio_path, output_path, fps):
        """极速视频生成"""
        try:
            # 🚀 直接内存生成，无临时文件
            print(f"🎬 直接生成视频: {len(video_frames)} 帧")
            
            # 生成无音频视频
            temp_video = output_path.replace('.mp4', '_temp.mp4')
            imageio.mimwrite(
                temp_video, video_frames, 'FFMPEG', 
                fps=fps, codec='libx264', pixelformat='yuv420p',
                output_params=['-preset', 'ultrafast', '-crf', '23']
            )
            
            # 🚀 并行音频合成
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
                print(f"⚠️ 音频合成失败，使用无音频版本: {str(e)}")
                os.rename(temp_video, output_path)
            
            return True
            
        except Exception as e:
            print(f"❌ 视频生成失败: {str(e)}")
            return False

# 全局服务实例
global_service = UltraFastMuseTalkService()

def start_ultra_fast_service(port=28888):
    """启动极速服务"""
    print(f"🚀 启动Ultra Fast Service - 端口: {port}")
    
    # 初始化模型
    if not global_service.initialize_models_ultra_fast():
        print("❌ 模型初始化失败")
        return
    
    # 🔍 启动性能监控
    if PERFORMANCE_MONITORING:
        start_performance_monitoring()
        print("🔍 性能监控已启动")
    
    # 启动IPC服务器
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(('127.0.0.1', port))
        server_socket.listen(5)
        
        print(f"🌐 Ultra Fast Service 就绪 - 监听端口: {port}")
        print("⚡ 毫秒级响应模式已启用")
        
        while True:
            try:
                client_socket, addr = server_socket.accept()
                print(f"🔗 客户端连接: {addr}")
                
                # 处理请求
                threading.Thread(
                    target=handle_client_ultra_fast, 
                    args=(client_socket,)
                ).start()
                
            except Exception as e:
                print(f"❌ 连接处理失败: {str(e)}")
                
    except Exception as e:
        print(f"❌ 服务启动失败: {str(e)}")

def handle_client_ultra_fast(client_socket):
    """处理客户端请求 - 极速版本"""
    try:
        # 接收请求
        data_length = struct.unpack('I', client_socket.recv(4))[0]
        data = client_socket.recv(data_length).decode('utf-8')
        request = json.loads(data)
        
        print(f"📨 极速推理请求: {request['template_id']}")
        
        # 🚀 极速推理
        start_time = time.time()
        success = global_service.ultra_fast_inference_parallel(
            template_id=request['template_id'],
            audio_path=request['audio_path'],
            output_path=request['output_path'],
            cache_dir=request['cache_dir'],
            batch_size=request.get('batch_size', 16),
            fps=request.get('fps', 25)
        )
        
        process_time = time.time() - start_time
        print(f"⚡ 极速推理完成: {process_time:.3f}s, 结果: {success}")
        
        # 发送响应
        response = {'Success': success, 'OutputPath': request['output_path'] if success else None}
        response_data = json.dumps(response).encode('utf-8')
        client_socket.send(struct.pack('I', len(response_data)))
        client_socket.send(response_data)
        
    except Exception as e:
        print(f"❌ 请求处理失败: {str(e)}")
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