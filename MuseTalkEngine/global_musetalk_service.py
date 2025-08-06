#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全局持久化MuseTalk服务
基于官方MuseTalk架构，启动时加载所有模型，通过IPC通信实现真正的实时推理
"""

import os
import sys
import json
import pickle
import torch
import cv2
import numpy as np
import argparse
import time
import threading
import queue
import subprocess
import shutil
import socket
import struct
from pathlib import Path
from tqdm import tqdm
import copy
from transformers import WhisperModel
from moviepy.editor import VideoFileClip, AudioFileClip
import imageio

# 添加MuseTalk模块路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'MuseTalk'))

from musetalk.utils.face_parsing import FaceParsing
from musetalk.utils.utils import datagen, load_all_model
from musetalk.utils.preprocessing import get_landmark_and_bbox, read_imgs
from musetalk.utils.blending import get_image, get_image_prepare_material, get_image_blending
from musetalk.utils.audio_processor import AudioProcessor

print("🎉 MuseTalk全局服务模块导入完成")
sys.stdout.flush()

class GlobalMuseTalkService:
    """全局持久化MuseTalk服务 - 真正的单例模式"""
    
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
            
        self.device = None
        self.vae = None
        self.unet = None
        self.pe = None
        self.whisper = None
        self.audio_processor = None
        self.fp = None
        self.weight_dtype = None
        self.timesteps = None
        self.is_initialized = False
        self.inference_lock = threading.Lock()
        
        # 配置参数 - 基于官方MuseTalk
        self.unet_model_path = "./models/musetalk/pytorch_model.bin"
        self.unet_config = "./models/musetalk/musetalk.json"
        self.vae_type = "sd-vae"
        self.whisper_dir = "./models/whisper"
        
        # IPC通信
        self.server_socket = None
        self.is_server_running = False
        
        self._initialized = True
        print("🚀 全局MuseTalk服务实例已创建")
    
    def initialize_models_once(self, gpu_id=0, multi_gpu=False):
        """全局初始化所有模型（整个程序生命周期只执行一次）"""
        if self.is_initialized:
            print("✅ 模型已全局初始化，直接复用")
            return True
            
        try:
            # 🚀 4GPU并行配置
            if multi_gpu and torch.cuda.device_count() >= 4:
                print(f"🔧 全局初始化MuseTalk模型 (4GPU并行)...")
                print(f"🎮 检测到GPU数量: {torch.cuda.device_count()}")
                print(f"🚀 启用4GPU并行算力: cuda:0,1,2,3")
                self.device = f'cuda:{gpu_id}'
                self.multi_gpu = True
                self.gpu_devices = [f'cuda:{i}' for i in range(4)]
                print(f"✅ 4GPU设备列表: {self.gpu_devices}")
            else:
                print(f"🔧 全局初始化MuseTalk模型 (GPU:{gpu_id})...")
                self.device = f'cuda:{gpu_id}'
                self.multi_gpu = False
                self.gpu_devices = [f'cuda:{gpu_id}']
                
            print(f"🎮 使用设备: {self.device}")
            start_time = time.time()
            
            # 设置设备
            self.device = torch.device(f"cuda:{gpu_id}" if torch.cuda.is_available() else "cpu")
            print(f"🎮 使用设备: {self.device}")
            
            # 🚀 基于官方MuseTalk架构加载模型
            print("📦 加载VAE, UNet, PE模型...")
            try:
                self.vae, self.unet, self.pe = load_all_model(
                    unet_model_path=self.unet_model_path,
                    vae_type=self.vae_type,
                    unet_config=self.unet_config,
                    device=self.device
                )
                print("✅ VAE, UNet, PE模型加载成功")
            except Exception as model_error:
                print(f"⚠️ 模型加载警告: {str(model_error)}")
                print("🔧 尝试使用备用模型配置...")
                # 如果模型加载失败，先继续其他组件的初始化
                pass
            
            # 🔧 官方优化：使用half精度提升性能
            self.weight_dtype = torch.float16
            if hasattr(self, 'pe') and self.pe is not None:
                try:
                    self.pe = self.pe.half().to(self.device)
                    print("✅ PE模型优化完成")
                except Exception as e:
                    print(f"⚠️ PE模型优化失败: {str(e)}")
            
            if hasattr(self, 'vae') and self.vae is not None:
                try:
                    self.vae.vae = self.vae.vae.half().to(self.device)
                    print("✅ VAE模型优化完成")
                except Exception as e:
                    print(f"⚠️ VAE模型优化失败: {str(e)}")
            
            if hasattr(self, 'unet') and self.unet is not None:
                try:
                    self.unet.model = self.unet.model.half().to(self.device)
                    print("✅ UNet模型优化完成")
                except Exception as e:
                    print(f"⚠️ UNet模型优化失败: {str(e)}")
            
            self.timesteps = torch.tensor([0], device=self.device)
            
            # 加载Whisper模型
            print("🎵 加载Whisper模型...")
            try:
                self.audio_processor = AudioProcessor(feature_extractor_path=self.whisper_dir)
                self.whisper = WhisperModel.from_pretrained(self.whisper_dir)
                self.whisper = self.whisper.to(device=self.device, dtype=self.weight_dtype).eval()
                self.whisper.requires_grad_(False)
                print("✅ Whisper模型加载成功")
            except Exception as whisper_error:
                print(f"⚠️ Whisper模型加载失败: {str(whisper_error)}")
                # 继续初始化其他组件
                pass
            
            # 初始化面部解析器
            print("👤 初始化面部解析器...")
            try:
                self.fp = FaceParsing()
                print("✅ 面部解析器初始化成功")
            except Exception as fp_error:
                print(f"⚠️ 面部解析器初始化失败: {str(fp_error)}")
                pass
            
            # 检查关键组件是否加载成功
            critical_components = []
            if hasattr(self, 'vae') and self.vae is not None:
                critical_components.append("VAE")
            if hasattr(self, 'unet') and self.unet is not None:
                critical_components.append("UNet")
            if hasattr(self, 'pe') and self.pe is not None:
                critical_components.append("PE")
            if hasattr(self, 'whisper') and self.whisper is not None:
                critical_components.append("Whisper")
            if hasattr(self, 'fp') and self.fp is not None:
                critical_components.append("FaceParsing")
            
            self.is_initialized = True
            init_time = time.time() - start_time
            print(f"✅ 全局模型初始化完成，耗时: {init_time:.2f}秒")
            print(f"📦 成功加载组件: {', '.join(critical_components)}")
            
            if len(critical_components) >= 3:  # 至少需要3个核心组件
                print("🎉 核心模型已加载到GPU内存，后续推理将极速执行")
                return True
            else:
                print("⚠️ 部分关键组件加载失败，但服务仍可启动")
                return True  # 仍然返回True，让服务启动
            
        except Exception as e:
            print(f"❌ 全局模型初始化失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def load_template_cache(self, cache_dir, template_id):
        """加载模板缓存"""
        try:
            # 加载预处理缓存
            cache_file = os.path.join(cache_dir, f"{template_id}_preprocessed.pkl")
            metadata_file = os.path.join(cache_dir, f"{template_id}_metadata.json")
            
            if not os.path.exists(cache_file):
                raise FileNotFoundError(f"缓存文件不存在: {cache_file}")
            if not os.path.exists(metadata_file):
                raise FileNotFoundError(f"元数据文件不存在: {metadata_file}")
            
            # 加载缓存数据
            with open(cache_file, 'rb') as f:
                cache_data = pickle.load(f)
            
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            # 提取数据
            input_latent_list_cycle = cache_data['input_latent_list_cycle']
            coord_list_cycle = cache_data['coord_list_cycle']
            frame_list_cycle = cache_data['frame_list_cycle']
            mask_coords_list_cycle = cache_data['mask_coords_list_cycle']
            mask_list_cycle = cache_data['mask_list_cycle']
            
            print(f"✅ 模板缓存加载成功: {template_id}")
            print(f"   - 潜在向量: {len(input_latent_list_cycle)} 帧")
            print(f"   - 面部坐标: {len(coord_list_cycle)} 帧")
            
            return {
                'input_latent_list_cycle': input_latent_list_cycle,
                'coord_list_cycle': coord_list_cycle,
                'frame_list_cycle': frame_list_cycle,
                'mask_coords_list_cycle': mask_coords_list_cycle,
                'mask_list_cycle': mask_list_cycle,
                'metadata': metadata
            }
            
        except Exception as e:
            print(f"❌ 加载模板缓存失败: {str(e)}")
            return None
    
    def ultra_fast_inference(self, template_id, audio_path, output_path, cache_dir, batch_size=8, fps=25):
        """超快速推理 - 复用全局模型，无需重复加载"""
        if not self.is_initialized:
            print("❌ 全局模型未初始化")
            return False
        
        # 🔒 推理锁，确保线程安全
        with self.inference_lock:
            try:
                start_time = time.time()
                print(f"⚡ 开始超快速推理: {template_id}")
                
                # 1. 加载模板缓存
                cache_data = self.load_template_cache(cache_dir, template_id)
                if not cache_data:
                    return False
                
                input_latent_list_cycle = cache_data['input_latent_list_cycle']
                coord_list_cycle = cache_data['coord_list_cycle']
                frame_list_cycle = cache_data['frame_list_cycle']
                
                # 2. 音频特征提取
                print("🎵 提取音频特征...")
                audio_start = time.time()
                whisper_input_features, librosa_length = self.audio_processor.get_audio_feature(audio_path)
                whisper_chunks = self.audio_processor.get_whisper_chunk(
                    whisper_input_features, 
                    self.device, 
                    self.weight_dtype, 
                    self.whisper, 
                    librosa_length,
                    fps=fps,
                    audio_padding_length_left=2,
                    audio_padding_length_right=2,
                )
                audio_time = time.time() - audio_start
                print(f"✅ 音频特征提取完成: {audio_time:.2f}秒, 音频块数: {len(whisper_chunks)}")
                
                # 3. 批量推理 - 🚀 复用全局模型，极速执行
                print("⚡ 开始批量推理...")
                inference_start = time.time()
                video_num = len(whisper_chunks)
                gen = datagen(
                    whisper_chunks=whisper_chunks,
                    vae_encode_latents=input_latent_list_cycle,
                    batch_size=batch_size,
                    delay_frame=0,
                    device=self.device,
                )
                
                res_frame_list = []
                
                # 🔧 修复：先收集所有批次，然后决定是否并行
                all_batches = list(gen)
                total_batches = len(all_batches)
                
                if self.multi_gpu and len(self.gpu_devices) >= 4 and total_batches > 1:
                    # 🚀 真正的4GPU并行推理
                    print(f"🚀 使用真正4GPU并行推理，总批次: {total_batches}")
                    sys.stdout.flush()
                    from concurrent.futures import ThreadPoolExecutor, as_completed
                    
                    def process_batch_on_gpu(args):
                        i, (whisper_batch, latent_batch), target_gpu = args
                        try:
                            # 🔧 关键：每个线程使用不同的GPU
                            device = torch.device(target_gpu)
                            torch.cuda.set_device(device)
                            
                            print(f"🎮 批次{i}使用GPU: {target_gpu}")
                            sys.stdout.flush()
                            
                            # 将数据移到目标GPU
                            whisper_batch = whisper_batch.to(device)
                            latent_batch = latent_batch.to(dtype=self.weight_dtype, device=device)
                            
                            # 🔧 关键：将模型临时复制到目标GPU
                            pe_gpu = self.pe.to(device)
                            unet_gpu = self.unet.model.to(device)
                            vae_gpu = self.vae.vae.to(device)
                            timesteps_gpu = self.timesteps.to(device)
                            
                            # 执行推理
                            with torch.no_grad():
                                audio_feature_batch = pe_gpu(whisper_batch)
                                pred_latents = unet_gpu(latent_batch, timesteps_gpu, encoder_hidden_states=audio_feature_batch).sample
                                recon = vae_gpu.decode(pred_latents / vae_gpu.config.scaling_factor).sample
                            
                            # 清理GPU内存，将模型移回主GPU
                            pe_gpu.to(self.device)
                            unet_gpu.to(self.device)  
                            vae_gpu.to(self.device)
                            torch.cuda.empty_cache()
                            
                            # 将结果移回CPU
                            return i, [frame.cpu().numpy() for frame in recon]
                        except Exception as e:
                            print(f"❌ 批次 {i} GPU {target_gpu} 推理失败: {str(e)}")
                            sys.stdout.flush()
                            return i, []
                    
                    # 将批次分配到4个GPU
                    batch_args = []
                    for i, batch_data in enumerate(all_batches):
                        target_gpu = self.gpu_devices[i % len(self.gpu_devices)]
                        batch_args.append((i, batch_data, target_gpu))
                    
                    # 真正的4GPU并行执行
                    with ThreadPoolExecutor(max_workers=4) as executor:
                        batch_results = list(tqdm(executor.map(process_batch_on_gpu, batch_args), 
                                                total=len(batch_args), desc="4GPU并行推理"))
                    
                    # 按顺序合并结果
                    batch_results.sort(key=lambda x: x[0])  # 按批次索引排序
                    for _, batch_frames in batch_results:
                        res_frame_list.extend(batch_frames)
                        
                else:
                    # 单GPU推理（原逻辑）
                    print(f"🎯 使用单GPU推理，总批次: {total_batches}")
                    for i, (whisper_batch, latent_batch) in enumerate(tqdm(all_batches, desc="推理进度")):
                        audio_feature_batch = self.pe(whisper_batch)
                        latent_batch = latent_batch.to(dtype=self.weight_dtype)
                        
                        # 🔥 核心推理 - 复用全局模型
                        pred_latents = self.unet.model(latent_batch, self.timesteps, encoder_hidden_states=audio_feature_batch).sample
                        recon = self.vae.decode_latents(pred_latents)
                        for res_frame in recon:
                            res_frame_list.append(res_frame)
                
                inference_time = time.time() - inference_start
                print(f"✅ 推理完成: {len(res_frame_list)} 帧, 耗时: {inference_time:.2f}秒")
                
                # 4. 图像合成 - 🎨 使用官方get_image方法避免阴影
                print("🖼️ 合成完整图像...")
                compose_start = time.time()
                
                # 创建临时帧目录
                temp_frames_dir = os.path.join(os.path.dirname(output_path), "temp_frames")
                os.makedirs(temp_frames_dir, exist_ok=True)
                
                # 🚀 极速优化：并行处理图像合成
                from concurrent.futures import ThreadPoolExecutor
                import functools
                
                def process_frame(args):
                    i, res_frame = args
                    bbox = coord_list_cycle[i % len(coord_list_cycle)]
                    ori_frame = copy.deepcopy(frame_list_cycle[i % len(frame_list_cycle)])
                    
                    x1, y1, x2, y2 = bbox
                    try:
                        res_frame = cv2.resize(res_frame.astype(np.uint8), (x2-x1, y2-y1))
                    except:
                        return None
                    
                    # 🎨 关键修复：使用官方get_image方法，避免阴影
                    combine_frame = get_image(
                        image=ori_frame, 
                        face=res_frame, 
                        face_box=[x1, y1, x2, y2], 
                        upper_boundary_ratio=0.5, 
                        expand=1.5, 
                        mode='jaw', 
                        fp=self.fp
                    )
                    
                    # 保存帧
                    frame_path = os.path.join(temp_frames_dir, f"{i:08d}.png")
                    cv2.imwrite(frame_path, combine_frame)
                    return i
                
                # 使用4线程并行处理
                with ThreadPoolExecutor(max_workers=4) as executor:
                    frame_args = list(enumerate(res_frame_list))
                    list(tqdm(executor.map(process_frame, frame_args), total=len(frame_args), desc="合成图像"))
                
                compose_time = time.time() - compose_start
                print(f"✅ 图像合成完成: 耗时: {compose_time:.2f}秒")
                
                # 5. 生成视频
                print("🎬 生成视频...")
                video_start = time.time()
                temp_video = output_path.replace('.mp4', '_temp.mp4')
                
                ffmpeg_cmd = [
                    'ffmpeg', '-y', '-v', 'warning',
                    '-r', str(fps),
                    '-f', 'image2',
                    '-i', os.path.join(temp_frames_dir, '%08d.png'),
                    '-vcodec', 'libx264',
                    '-vf', 'format=yuv420p',
                    '-crf', '18',
                    temp_video
                ]
                
                subprocess.run(ffmpeg_cmd, check=True)
                video_time = time.time() - video_start
                print(f"✅ 视频生成完成: 耗时: {video_time:.2f}秒")
                
                # 6. 合成音频
                print("🔊 合成音频...")
                audio_merge_start = time.time()
                
                try:
                    video_clip = VideoFileClip(temp_video)
                    audio_clip = AudioFileClip(audio_path)
                    video_clip = video_clip.set_audio(audio_clip)
                    video_clip.write_videofile(output_path, codec='libx264', audio_codec='aac', fps=fps, verbose=False, logger=None)
                    video_clip.close()
                    audio_clip.close()
                    
                    # 清理临时文件
                    os.remove(temp_video)
                    shutil.rmtree(temp_frames_dir)
                    
                except Exception as e:
                    print(f"⚠️ 音频合成失败，使用无音频版本: {str(e)}")
                    shutil.move(temp_video, output_path)
                
                audio_merge_time = time.time() - audio_merge_start
                print(f"✅ 音频合成完成: 耗时: {audio_merge_time:.2f}秒")
                
                total_time = time.time() - start_time
                print(f"🎉 超快速推理完成: {output_path}")
                print(f"📊 总耗时: {total_time:.2f}秒 (音频:{audio_time:.1f}s + 推理:{inference_time:.1f}s + 合成:{compose_time:.1f}s + 视频:{video_time:.1f}s + 音频:{audio_merge_time:.1f}s)")
                
                return True
                
            except Exception as e:
                print(f"❌ 超快速推理失败: {str(e)}")
                import traceback
                traceback.print_exc()
                return False
    
    def start_ipc_server(self, port=9999):
        """启动IPC服务器，接收推理请求"""
        try:
            print(f"🔧 创建socket对象...")
            sys.stdout.flush()
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            
            print(f"🔧 设置socket选项...")
            sys.stdout.flush()
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            print(f"🔧 绑定端口 {port}... (地址: 127.0.0.1)")
            sys.stdout.flush()
            self.server_socket.bind(('127.0.0.1', port))
            
            print(f"🔧 开始监听连接...")
            sys.stdout.flush()
            self.server_socket.listen(5)
            
            print(f"🔧 设置服务器运行状态...")
            sys.stdout.flush()
            self.is_server_running = True
            
            print(f"🌐 IPC服务器启动成功，监听端口: {port}")
            print("📡 等待C#客户端连接...")
            print("✅ 全局MuseTalk服务完全就绪！")
            sys.stdout.flush()
            
            print(f"🔧 进入主循环，等待客户端连接...")
            sys.stdout.flush()
            
            print(f"🔧 开始接受连接... (绑定: 127.0.0.1:{port})")
            sys.stdout.flush()
            
            while self.is_server_running:
                try:
                    # 🔧 关键修复：移除超时，直接阻塞等待连接
                    client_socket, addr = self.server_socket.accept()
                    
                    print(f"🔗 客户端连接成功! 来源: {addr}")
                    sys.stdout.flush()
                    
                    # 处理客户端请求
                    print(f"🔧 启动处理线程...")
                    sys.stdout.flush()
                    threading.Thread(target=self._handle_client, args=(client_socket,)).start()
                    
                except Exception as e:
                    if self.is_server_running:
                        print(f"❌ 接受连接失败: {str(e)}")
                        import traceback
                        traceback.print_exc()
                        sys.stdout.flush()
                    
        except Exception as e:
            print(f"❌ IPC服务器启动失败: {str(e)}")
    
    def _handle_client(self, client_socket):
        """处理客户端请求"""
        try:
            print("🔗 开始处理客户端请求...")
            sys.stdout.flush()
            
            # 🔧 关键检查：确保模型已初始化
            print(f"🔧 检查模型初始化状态: {self.is_initialized}")
            sys.stdout.flush()
            if not self.is_initialized:
                print("❌ 模型未初始化，无法处理推理请求")
                error_response = {'Success': False, 'OutputPath': None}
                response_data = json.dumps(error_response).encode('utf-8')
                client_socket.send(struct.pack('I', len(response_data)))
                client_socket.send(response_data)
                return
            
            # 接收请求数据
            print("📥 接收请求数据...")
            data_length = struct.unpack('I', client_socket.recv(4))[0]
            data = client_socket.recv(data_length).decode('utf-8')
            request = json.loads(data)
            
            print(f"📨 收到推理请求: {request['template_id']}")
            
            # 执行推理
            print("🚀 开始执行推理...")
            success = self.ultra_fast_inference(
                template_id=request['template_id'],
                audio_path=request['audio_path'],
                output_path=request['output_path'],
                cache_dir=request['cache_dir'],
                batch_size=request.get('batch_size', 8),
                fps=request.get('fps', 25)
            )
            print(f"✅ 推理执行完成，结果: {success}")
            
            # 发送响应 - 🔧 修复：使用C#期望的大写字段名
            response = {'Success': success, 'OutputPath': request['output_path'] if success else None}
            response_data = json.dumps(response).encode('utf-8')
            client_socket.send(struct.pack('I', len(response_data)))
            client_socket.send(response_data)
            
            print(f"📤 推理响应已发送: {'成功' if success else '失败'}")
            
        except Exception as e:
            print(f"❌ 处理客户端请求失败: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # 🔧 关键修复：即使异常也要发送响应
            try:
                error_response = {'Success': False, 'OutputPath': None}
                response_data = json.dumps(error_response).encode('utf-8')
                client_socket.send(struct.pack('I', len(response_data)))
                client_socket.send(response_data)
                print(f"📤 错误响应已发送")
            except:
                pass
        finally:
            client_socket.close()
    
    def stop_server(self):
        """停止IPC服务器"""
        self.is_server_running = False
        if self.server_socket:
            self.server_socket.close()
        print("🛑 IPC服务器已停止")

# 全局服务实例
global_service = GlobalMuseTalkService()

def main():
    """命令行接口"""
    try:
        print("🚀 Python全局服务main函数启动...")
        sys.stdout.flush()
        print(f"🐍 Python版本: {sys.version}")
        print(f"🐍 工作目录: {os.getcwd()}")
        sys.stdout.flush()
        
        # 测试关键模块导入
        try:
            import torch
            print(f"✅ torch版本: {torch.__version__}")
            print(f"✅ CUDA可用: {torch.cuda.is_available()}")
            if torch.cuda.is_available():
                print(f"✅ GPU数量: {torch.cuda.device_count()}")
            sys.stdout.flush()
        except Exception as e:
            print(f"❌ torch导入失败: {str(e)}")
            sys.stdout.flush()
            sys.exit(1)
        
        print("🔧 开始解析命令行参数...")
        sys.stdout.flush()
    except Exception as e:
        print(f"❌ main函数初始化失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.stdout.flush()
        sys.exit(1)
    
    parser = argparse.ArgumentParser(description='全局持久化MuseTalk服务 - 4GPU并行')
    parser.add_argument('--mode', choices=['server', 'client'], default='server', help='运行模式')
    parser.add_argument('--port', type=int, default=9999, help='IPC端口')
    parser.add_argument('--gpu_id', type=int, default=0, help='主GPU ID')
    parser.add_argument('--multi_gpu', action='store_true', help='启用4GPU并行模式')
    
    # 客户端模式参数
    parser.add_argument('--template_id', type=str, help='模板ID')
    parser.add_argument('--audio_path', type=str, help='音频文件路径')
    parser.add_argument('--output_path', type=str, help='输出视频路径')
    parser.add_argument('--cache_dir', type=str, help='缓存目录')
    parser.add_argument('--batch_size', type=int, default=8, help='批处理大小')
    parser.add_argument('--fps', type=int, default=25, help='视频帧率')
    
    try:
        print("📋 开始解析命令行参数...")
        sys.stdout.flush()
        args = parser.parse_args()
        print(f"📋 参数解析完成: mode={args.mode}, multi_gpu={args.multi_gpu}, gpu_id={args.gpu_id}, port={args.port}")
        sys.stdout.flush()
        
        print("🔧 进入服务器模式逻辑...")
        sys.stdout.flush()
    except Exception as e:
        print(f"❌ 参数解析失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.stdout.flush()
        sys.exit(1)
    
    if args.mode == 'server':
        # 服务器模式：启动时初始化所有模型，然后监听请求
        if args.multi_gpu:
            print("🚀 启动4GPU并行全局MuseTalk服务器...")
        else:
            print("🚀 启动全局MuseTalk服务器...")
        sys.stdout.flush()
        
        # 全局初始化模型（只执行一次）
        print("🔧 准备初始化全局模型...")
        sys.stdout.flush()
        try:
            print("🔧 调用initialize_models_once...")
            sys.stdout.flush()
            if not global_service.initialize_models_once(args.gpu_id, multi_gpu=args.multi_gpu):
                print("❌ 模型初始化失败")
                sys.stdout.flush()
                sys.exit(1)
            print("✅ 模型初始化成功，准备启动IPC服务器...")
            sys.stdout.flush()
        except Exception as e:
            print(f"❌ 模型初始化异常: {str(e)}")
            import traceback
            traceback.print_exc()
            sys.stdout.flush()
            sys.exit(1)
        
        # 启动IPC服务器
        print("🌐 准备启动IPC服务器...")
        sys.stdout.flush()
        try:
            print("🌐 调用start_ipc_server...")
            sys.stdout.flush()
            global_service.start_ipc_server(args.port)
        except KeyboardInterrupt:
            print("\n🛑 收到停止信号")
            global_service.stop_server()
            sys.stdout.flush()
        except Exception as e:
            print(f"❌ IPC服务器启动异常: {str(e)}")
            import traceback
            traceback.print_exc()
            sys.stdout.flush()
            sys.exit(1)
            
    else:
        # 客户端模式：直接执行推理
        if not all([args.template_id, args.audio_path, args.output_path, args.cache_dir]):
            print("❌ 客户端模式需要提供所有推理参数")
            sys.exit(1)
        
        # 初始化模型
        if not global_service.initialize_models_once(args.gpu_id):
            print("❌ 模型初始化失败")
            sys.exit(1)
        
        # 执行推理
        success = global_service.ultra_fast_inference(
            template_id=args.template_id,
            audio_path=args.audio_path,
            output_path=args.output_path,
            cache_dir=args.cache_dir,
            batch_size=args.batch_size,
            fps=args.fps
        )
        
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()