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
    
    def initialize_models_once(self, gpu_id=0):
        """全局初始化所有模型（整个程序生命周期只执行一次）"""
        if self.is_initialized:
            print("✅ 模型已全局初始化，直接复用")
            return True
            
        try:
            print(f"🔧 全局初始化MuseTalk模型 (GPU:{gpu_id})...")
            start_time = time.time()
            
            # 设置设备
            self.device = torch.device(f"cuda:{gpu_id}" if torch.cuda.is_available() else "cpu")
            print(f"🎮 使用设备: {self.device}")
            
            # 🚀 基于官方MuseTalk架构加载模型
            print("📦 加载VAE, UNet, PE模型...")
            self.vae, self.unet, self.pe = load_all_model(
                unet_model_path=self.unet_model_path,
                vae_type=self.vae_type,
                unet_config=self.unet_config,
                device=self.device
            )
            
            # 🔧 官方优化：使用half精度提升性能
            self.weight_dtype = torch.float16
            self.pe = self.pe.half().to(self.device)
            self.vae.vae = self.vae.vae.half().to(self.device)
            self.unet.model = self.unet.model.half().to(self.device)
            
            self.timesteps = torch.tensor([0], device=self.device)
            
            # 加载Whisper模型
            print("🎵 加载Whisper模型...")
            self.audio_processor = AudioProcessor(feature_extractor_path=self.whisper_dir)
            self.whisper = WhisperModel.from_pretrained(self.whisper_dir)
            self.whisper = self.whisper.to(device=self.device, dtype=self.weight_dtype).eval()
            self.whisper.requires_grad_(False)
            
            # 初始化面部解析器
            print("👤 初始化面部解析器...")
            self.fp = FaceParsing()
            
            self.is_initialized = True
            init_time = time.time() - start_time
            print(f"✅ 全局模型初始化完成，耗时: {init_time:.2f}秒")
            print("🎉 模型已加载到GPU内存，后续推理将极速执行")
            return True
            
        except Exception as e:
            print(f"❌ 全局模型初始化失败: {str(e)}")
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
                for i, (whisper_batch, latent_batch) in enumerate(tqdm(gen, total=int(np.ceil(float(video_num)/batch_size)), desc="推理进度")):
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
                
                for i, res_frame in enumerate(tqdm(res_frame_list, desc="合成图像")):
                    bbox = coord_list_cycle[i % len(coord_list_cycle)]
                    ori_frame = copy.deepcopy(frame_list_cycle[i % len(frame_list_cycle)])
                    
                    x1, y1, x2, y2 = bbox
                    try:
                        res_frame = cv2.resize(res_frame.astype(np.uint8), (x2-x1, y2-y1))
                    except:
                        continue
                    
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
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(('localhost', port))
            self.server_socket.listen(5)
            self.is_server_running = True
            
            print(f"🌐 IPC服务器启动成功，监听端口: {port}")
            print("📡 等待C#客户端连接...")
            
            while self.is_server_running:
                try:
                    client_socket, addr = self.server_socket.accept()
                    print(f"🔗 客户端连接: {addr}")
                    
                    # 处理客户端请求
                    threading.Thread(target=self._handle_client, args=(client_socket,)).start()
                    
                except Exception as e:
                    if self.is_server_running:
                        print(f"❌ 接受连接失败: {str(e)}")
                    
        except Exception as e:
            print(f"❌ IPC服务器启动失败: {str(e)}")
    
    def _handle_client(self, client_socket):
        """处理客户端请求"""
        try:
            # 接收请求数据
            data_length = struct.unpack('I', client_socket.recv(4))[0]
            data = client_socket.recv(data_length).decode('utf-8')
            request = json.loads(data)
            
            print(f"📨 收到推理请求: {request['template_id']}")
            
            # 执行推理
            success = self.ultra_fast_inference(
                template_id=request['template_id'],
                audio_path=request['audio_path'],
                output_path=request['output_path'],
                cache_dir=request['cache_dir'],
                batch_size=request.get('batch_size', 8),
                fps=request.get('fps', 25)
            )
            
            # 发送响应
            response = {'success': success, 'output_path': request['output_path'] if success else None}
            response_data = json.dumps(response).encode('utf-8')
            client_socket.send(struct.pack('I', len(response_data)))
            client_socket.send(response_data)
            
            print(f"📤 推理响应已发送: {'成功' if success else '失败'}")
            
        except Exception as e:
            print(f"❌ 处理客户端请求失败: {str(e)}")
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
    parser = argparse.ArgumentParser(description='全局持久化MuseTalk服务')
    parser.add_argument('--mode', choices=['server', 'client'], default='server', help='运行模式')
    parser.add_argument('--port', type=int, default=9999, help='IPC端口')
    parser.add_argument('--gpu_id', type=int, default=0, help='GPU ID')
    
    # 客户端模式参数
    parser.add_argument('--template_id', type=str, help='模板ID')
    parser.add_argument('--audio_path', type=str, help='音频文件路径')
    parser.add_argument('--output_path', type=str, help='输出视频路径')
    parser.add_argument('--cache_dir', type=str, help='缓存目录')
    parser.add_argument('--batch_size', type=int, default=8, help='批处理大小')
    parser.add_argument('--fps', type=int, default=25, help='视频帧率')
    
    args = parser.parse_args()
    
    if args.mode == 'server':
        # 服务器模式：启动时初始化所有模型，然后监听请求
        print("🚀 启动全局MuseTalk服务器...")
        
        # 全局初始化模型（只执行一次）
        if not global_service.initialize_models_once(args.gpu_id):
            print("❌ 模型初始化失败")
            sys.exit(1)
        
        # 启动IPC服务器
        try:
            global_service.start_ipc_server(args.port)
        except KeyboardInterrupt:
            print("\n🛑 收到停止信号")
            global_service.stop_server()
            
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