#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单GPU优化服务 - 专为RTX 4090D 48GB优化
目标：
1. 启动时预加载所有模型到GPU
2. 优化批处理大小（充分利用48GB显存）
3. 为WebRTC实时推理做准备
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
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import copy
import gc
import imageio
import warnings
warnings.filterwarnings("ignore")

# 添加MuseTalk模块路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'MuseTalk'))

from musetalk.utils.face_parsing import FaceParsing
from musetalk.utils.utils import datagen, load_all_model
from musetalk.utils.preprocessing import get_landmark_and_bbox, read_imgs
from musetalk.utils.blending import get_image_blending
from musetalk.utils.audio_processor import AudioProcessor

print("🚀 单GPU优化服务 - RTX 4090D 48GB专用版")

class SingleGPUOptimizedService:
    """单GPU优化服务 - 充分利用48GB显存"""
    
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
            
        # 单GPU配置
        self.device = 'cuda:0' if torch.cuda.is_available() else 'cpu'
        self.weight_dtype = torch.float16  # 使用半精度节省显存
        
        # 模型组件（预加载到GPU）
        self.vae = None
        self.unet = None
        self.pe = None
        self.whisper = None
        self.audio_processor = None
        self.fp = None
        self.timesteps = None
        
        # 缓存优化
        self.template_cache = {}  # 模板缓存常驻内存
        self.audio_cache = {}     # 音频特征缓存
        self.max_cache_size = 100  # 最大缓存数
        
        # 批处理优化 - 48GB显存可以处理更大批次
        self.optimal_batch_size = 12  # RTX 4090D可以处理更大批次
        self.max_batch_size = 16      # 最大批次大小
        
        # 线程池优化
        self.inference_executor = ThreadPoolExecutor(max_workers=2)
        self.compose_executor = ThreadPoolExecutor(max_workers=16)
        
        # WebRTC实时推理准备
        self.realtime_queue = queue.Queue(maxsize=10)
        self.is_realtime_mode = False
        
        self.is_initialized = False
        self._initialized = True
        
        print(f"✅ 单GPU服务初始化 - 设备: {self.device}")
    
    def initialize_and_preload(self):
        """启动时预加载所有模型到GPU"""
        if self.is_initialized:
            print("模型已加载，跳过重复初始化")
            return True
            
        try:
            print("🔄 开始预加载模型到GPU...")
            start_time = time.time()
            
            # 1. 加载主模型到GPU
            print("加载VAE, UNet, PE模型...")
            self.vae, self.unet, self.pe = load_all_model(vae_type="sd-vae")
            
            # 优化：模型转换为半精度并编译
            print("优化模型（半精度+编译）...")
            if hasattr(self.vae, 'vae'):
                self.vae.vae = self.vae.vae.to(self.device).half().eval()
                # 编译加速（Linux）
                if hasattr(torch, 'compile') and os.name != 'nt':
                    try:
                        self.vae.vae = torch.compile(self.vae.vae, mode="reduce-overhead")
                    except:
                        pass
            
            if hasattr(self.unet, 'model'):
                self.unet.model = self.unet.model.to(self.device).half().eval()
                if hasattr(torch, 'compile') and os.name != 'nt':
                    try:
                        self.unet.model = torch.compile(self.unet.model, mode="reduce-overhead")
                    except:
                        pass
            
            if hasattr(self.pe, 'to'):
                self.pe = self.pe.to(self.device).half().eval()
                if hasattr(torch, 'compile') and os.name != 'nt':
                    try:
                        self.pe = torch.compile(self.pe, mode="reduce-overhead")
                    except:
                        pass
            
            # 2. 加载Whisper（保持float32）
            whisper_dir = "./models/whisper"
            if os.path.exists(whisper_dir):
                print("加载Whisper模型...")
                try:
                    from transformers import WhisperModel
                    self.whisper = WhisperModel.from_pretrained(whisper_dir).eval()
                    self.whisper = self.whisper.to(self.device)  # Whisper需要float32
                    print("✅ Whisper加载完成")
                except Exception as e:
                    print(f"⚠️ Whisper加载失败: {e}")
                    self.whisper = None
            
            # 3. 初始化音频处理器
            print("初始化音频处理器...")
            self.audio_processor = AudioProcessor(
                feature_extractor_path=whisper_dir if os.path.exists(whisper_dir) else None
            )
            
            # 4. 初始化FaceParsing
            print("初始化FaceParsing...")
            self.fp = FaceParsing()
            
            # 5. 设置时间步
            self.timesteps = torch.tensor([0], device=self.device, dtype=torch.long)
            
            # 6. 预热GPU（可选）
            print("预热GPU...")
            self._warmup_gpu()
            
            load_time = time.time() - start_time
            print(f"✅ 模型预加载完成！耗时: {load_time:.2f}秒")
            
            # 显示GPU内存使用
            if torch.cuda.is_available():
                allocated = torch.cuda.memory_allocated(0) / 1024**3
                reserved = torch.cuda.memory_reserved(0) / 1024**3
                print(f"📊 GPU内存: 已分配 {allocated:.2f}GB / 已保留 {reserved:.2f}GB / 总计 48GB")
            
            self.is_initialized = True
            return True
            
        except Exception as e:
            print(f"❌ 模型预加载失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _warmup_gpu(self):
        """GPU预热，提高首次推理速度"""
        try:
            # 创建小批次测试数据
            dummy_whisper = torch.randn(1, 1, 384, device=self.device, dtype=self.weight_dtype)
            dummy_latent = torch.randn(1, 8, 32, 32, device=self.device, dtype=self.weight_dtype)
            
            # 执行一次推理预热
            with torch.no_grad():
                audio_features = self.pe(dummy_whisper)
                pred = self.unet.model(dummy_latent, self.timesteps, encoder_hidden_states=audio_features).sample
                # 不需要解码，只是预热
                del audio_features, pred
            
            torch.cuda.empty_cache()
            print("✅ GPU预热完成")
        except Exception as e:
            print(f"⚠️ GPU预热失败（不影响使用）: {e}")
    
    def get_optimal_batch_size(self, video_length):
        """根据视频长度动态调整批次大小"""
        # RTX 4090D 48GB的优化策略
        if video_length < 50:
            return 8  # 短视频用较小批次，减少延迟
        elif video_length < 100:
            return 12  # 中等长度视频
        elif video_length < 200:
            return 14  # 较长视频
        else:
            return 16  # 长视频用最大批次，提高吞吐量
    
    def inference_optimized(self, template_id, audio_path, output_path, cache_dir, fps=25):
        """优化的单GPU推理"""
        if not self.is_initialized:
            print("⚠️ 模型未初始化，正在加载...")
            if not self.initialize_and_preload():
                return False
        
        try:
            total_start = time.time()
            
            # 1. 加载模板缓存（可能已在内存中）
            cache_data = self.load_template_cache_fast(cache_dir, template_id)
            if not cache_data:
                print(f"❌ 无法加载模板缓存: {template_id}")
                return False
            
            # 2. 提取音频特征（检查缓存）
            audio_cache_key = f"{audio_path}_{fps}"
            if audio_cache_key in self.audio_cache:
                print("✅ 使用缓存的音频特征")
                whisper_chunks = self.audio_cache[audio_cache_key]
            else:
                print("🎵 提取音频特征...")
                whisper_chunks = self.extract_audio_features(audio_path, fps)
                if whisper_chunks is None:
                    return False
                # 缓存音频特征
                if len(self.audio_cache) < self.max_cache_size:
                    self.audio_cache[audio_cache_key] = whisper_chunks
            
            # 3. 动态确定批次大小
            video_length = len(whisper_chunks)
            batch_size = self.get_optimal_batch_size(video_length)
            print(f"📊 视频长度: {video_length}帧, 使用批次大小: {batch_size}")
            
            # 4. 单GPU批处理推理
            inference_start = time.time()
            res_frame_list = self.batch_inference_single_gpu(
                whisper_chunks, cache_data, batch_size
            )
            inference_time = time.time() - inference_start
            print(f"⚡ 推理完成: {inference_time:.2f}秒 ({len(res_frame_list)}帧, {len(res_frame_list)/inference_time:.1f} FPS)")
            
            # 5. 并行图像合成
            compose_start = time.time()
            video_frames = self.parallel_compose_frames(res_frame_list, cache_data)
            compose_time = time.time() - compose_start
            print(f"🎨 合成完成: {compose_time:.2f}秒")
            
            # 6. 生成视频
            video_start = time.time()
            success = self.generate_video_fast(video_frames, audio_path, output_path, fps)
            video_time = time.time() - video_start
            print(f"📹 视频生成: {video_time:.2f}秒")
            
            total_time = time.time() - total_start
            print(f"✅ 总耗时: {total_time:.2f}秒")
            print(f"   推理: {inference_time:.2f}s | 合成: {compose_time:.2f}s | 视频: {video_time:.2f}s")
            
            return success
            
        except Exception as e:
            print(f"❌ 推理失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def batch_inference_single_gpu(self, whisper_chunks, cache_data, batch_size):
        """单GPU批处理推理 - 优化版"""
        from musetalk.utils.utils import datagen
        
        input_latent_list_cycle = cache_data['input_latent_list_cycle']
        
        # 生成批次
        gen = datagen(
            whisper_chunks=whisper_chunks,
            vae_encode_latents=input_latent_list_cycle,
            batch_size=batch_size,
            delay_frame=0,
            device=self.device  # 直接在GPU上生成
        )
        
        res_frame_list = []
        batch_count = 0
        
        # 批处理推理
        with torch.no_grad():
            for whisper_batch, latent_batch in gen:
                batch_count += 1
                
                # 确保数据在GPU上
                whisper_batch = whisper_batch.to(self.device, dtype=self.weight_dtype, non_blocking=True)
                latent_batch = latent_batch.to(self.device, dtype=self.weight_dtype, non_blocking=True)
                
                # 推理
                audio_features = self.pe(whisper_batch)
                pred_latents = self.unet.model(
                    latent_batch, self.timesteps, 
                    encoder_hidden_states=audio_features
                ).sample
                
                # 解码
                recon_frames = self.vae.decode_latents(pred_latents)
                
                # 转换为numpy
                if isinstance(recon_frames, torch.Tensor):
                    recon_frames = recon_frames.cpu().numpy()
                
                # 添加到结果
                if isinstance(recon_frames, list):
                    res_frame_list.extend(recon_frames)
                elif isinstance(recon_frames, np.ndarray):
                    for i in range(recon_frames.shape[0]):
                        res_frame_list.append(recon_frames[i])
                
                # 定期清理显存
                if batch_count % 10 == 0:
                    torch.cuda.empty_cache()
                
                print(f"  批次 {batch_count} 完成", end='\r')
        
        print(f"\n✅ 处理了 {batch_count} 个批次")
        return res_frame_list
    
    def load_template_cache_fast(self, cache_dir, template_id):
        """快速加载模板缓存（内存缓存）"""
        # 先检查内存缓存
        if template_id in self.template_cache:
            print(f"✅ 使用内存中的模板缓存: {template_id}")
            return self.template_cache[template_id]
        
        # 从磁盘加载
        try:
            cache_file = os.path.join(cache_dir, f"{template_id}_preprocessed.pkl")
            if not os.path.exists(cache_file):
                print(f"❌ 缓存文件不存在: {cache_file}")
                return None
            
            print(f"📂 从磁盘加载模板缓存: {template_id}")
            with open(cache_file, 'rb') as f:
                cache_data = pickle.load(f)
            
            # 存入内存缓存
            if len(self.template_cache) < 10:  # 最多缓存10个模板
                self.template_cache[template_id] = cache_data
            
            return cache_data
            
        except Exception as e:
            print(f"❌ 缓存加载失败: {e}")
            return None
    
    def extract_audio_features(self, audio_path, fps):
        """提取音频特征"""
        try:
            if self.audio_processor is None:
                raise ValueError("音频处理器未初始化")
            
            whisper_input_features, librosa_length = self.audio_processor.get_audio_feature(audio_path)
            
            # Whisper需要float32
            whisper_dtype = torch.float32
            if isinstance(whisper_input_features, torch.Tensor):
                if whisper_input_features.dtype == torch.float16:
                    whisper_input_features = whisper_input_features.float()
            
            whisper_chunks = self.audio_processor.get_whisper_chunk(
                whisper_input_features,
                self.device,
                whisper_dtype,
                self.whisper,
                librosa_length,
                fps=fps,
                audio_padding_length_left=2,
                audio_padding_length_right=2,
            )
            
            return whisper_chunks
            
        except Exception as e:
            print(f"❌ 音频特征提取失败: {e}")
            return None
    
    def parallel_compose_frames(self, res_frame_list, cache_data):
        """并行图像合成"""
        coord_list_cycle = cache_data['coord_list_cycle']
        frame_list_cycle = cache_data['frame_list_cycle']
        mask_coords_list_cycle = cache_data['mask_coords_list_cycle']
        mask_list_cycle = cache_data['mask_list_cycle']
        
        def compose_single_frame(args):
            i, res_frame = args
            try:
                bbox = coord_list_cycle[i % len(coord_list_cycle)]
                ori_frame = copy.deepcopy(frame_list_cycle[i % len(frame_list_cycle)])
                
                x1, y1, x2, y2 = bbox
                res_frame = cv2.resize(res_frame.astype(np.uint8), (x2-x1, y2-y1))
                
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
                print(f"合成第{i}帧失败: {e}")
                return i, None
        
        # 并行合成
        with ThreadPoolExecutor(max_workers=16) as executor:
            results = list(executor.map(compose_single_frame, enumerate(res_frame_list)))
        
        # 按顺序排列
        video_frames = []
        for i, frame in sorted(results, key=lambda x: x[0]):
            if frame is not None:
                video_frames.append(frame)
        
        return video_frames
    
    def generate_video_fast(self, video_frames, audio_path, output_path, fps):
        """快速视频生成"""
        try:
            # 生成无音频视频
            temp_video = output_path.replace('.mp4', '_temp.mp4')
            imageio.mimwrite(
                temp_video, video_frames, 'FFMPEG',
                fps=fps, codec='libx264', pixelformat='yuv420p',
                output_params=['-preset', 'ultrafast', '-crf', '23']
            )
            
            # 合并音频
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
                
                os.remove(temp_video)
            except Exception as e:
                print(f"音频合成失败: {e}")
                os.rename(temp_video, output_path)
            
            return True
            
        except Exception as e:
            print(f"视频生成失败: {e}")
            return False
    
    def prepare_for_realtime(self):
        """为WebRTC实时推理做准备"""
        print("🎯 准备实时推理模式...")
        
        # 1. 确保模型已加载
        if not self.is_initialized:
            self.initialize_and_preload()
        
        # 2. 设置实时模式参数
        self.is_realtime_mode = True
        self.realtime_batch_size = 1  # 实时模式使用小批次
        
        # 3. 清理缓存，释放内存
        torch.cuda.empty_cache()
        
        print("✅ 实时推理模式就绪")
        return True
    
    def realtime_inference_frame(self, audio_chunk, template_cache):
        """实时推理单帧（WebRTC用）"""
        if not self.is_realtime_mode:
            self.prepare_for_realtime()
        
        try:
            with torch.no_grad():
                # 快速推理单帧
                # TODO: 实现实时推理逻辑
                pass
        except Exception as e:
            print(f"实时推理失败: {e}")
            return None

# 全局服务实例
global_service = SingleGPUOptimizedService()

def start_optimized_service(port=28888):
    """启动优化服务"""
    print(f"🚀 启动单GPU优化服务 - 端口: {port}")
    
    # 预加载模型
    print("📦 预加载模型到GPU...")
    if not global_service.initialize_and_preload():
        print("❌ 模型加载失败")
        return
    
    # 启动Socket服务器
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(('0.0.0.0', port))
        server_socket.listen(5)
        
        print(f"✅ 服务就绪 - 监听端口: {port}")
        print(f"📊 优化配置: 批次大小 8-16, 48GB显存优化")
        
        while True:
            client_socket, addr = server_socket.accept()
            print(f"🔗 客户端连接: {addr}")
            
            thread = threading.Thread(
                target=handle_client_request,
                args=(client_socket,)
            )
            thread.daemon = True
            thread.start()
            
    except Exception as e:
        print(f"❌ 服务启动失败: {e}")

def handle_client_request(client_socket):
    """处理客户端请求"""
    try:
        # 接收请求
        buffer = b''
        while True:
            chunk = client_socket.recv(1)
            if not chunk:
                break
            buffer += chunk
            if chunk == b'\n':
                break
        
        if not buffer:
            return
        
        data = buffer.decode('utf-8').strip()
        request = json.loads(data)
        
        # 处理推理请求
        if 'template_id' in request:
            print(f"📨 推理请求: {request.get('template_id')}")
            
            start_time = time.time()
            success = global_service.inference_optimized(
                template_id=request['template_id'],
                audio_path=request['audio_path'],
                output_path=request['output_path'],
                cache_dir=request.get('cache_dir', '/opt/musetalk/models/templates'),
                fps=request.get('fps', 25)
            )
            
            process_time = time.time() - start_time
            
            response = {
                'Success': success,
                'OutputPath': request['output_path'] if success else None,
                'ProcessTime': process_time
            }
            
            client_socket.send((json.dumps(response) + '\n').encode('utf-8'))
            print(f"✅ 推理完成: {process_time:.2f}秒")
        
    except Exception as e:
        print(f"❌ 请求处理失败: {e}")
        error_response = {'Success': False, 'Error': str(e)}
        client_socket.send((json.dumps(error_response) + '\n').encode('utf-8'))
    finally:
        client_socket.close()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=28888, help='服务端口')
    args = parser.parse_args()
    
    start_optimized_service(args.port)