#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
持久化MuseTalk服务
基于官方MuseTalk架构，避免重复加载模型，实现真正的快速推理
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
from musetalk.utils.blending import get_image_prepare_material, get_image_blending
from musetalk.utils.audio_processor import AudioProcessor

class PersistentMuseTalkService:
    """持久化MuseTalk服务 - 避免重复加载模型"""
    
    def __init__(self):
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
        self.lock = threading.Lock()
        
        # 配置参数
        self.unet_model_path = "./models/musetalk/pytorch_model.bin"
        self.unet_config = "./models/musetalk/musetalk.json"
        self.vae_type = "sd-vae"
        self.whisper_dir = "./models/whisper"
        
        print("🚀 持久化MuseTalk服务已创建")
    
    def initialize_models(self, gpu_id=0):
        """初始化所有模型（只执行一次）"""
        if self.is_initialized:
            print("✅ 模型已初始化，跳过重复加载")
            return True
            
        with self.lock:
            if self.is_initialized:  # 双重检查
                return True
                
            try:
                print(f"🔧 初始化MuseTalk模型 (GPU:{gpu_id})...")
                start_time = time.time()
                
                # 设置设备
                self.device = torch.device(f"cuda:{gpu_id}" if torch.cuda.is_available() else "cpu")
                print(f"🎮 使用设备: {self.device}")
                
                # 加载核心模型
                print("📦 加载VAE, UNet, PE模型...")
                self.vae, self.unet, self.pe = load_all_model(
                    unet_model_path=self.unet_model_path,
                    vae_type=self.vae_type,
                    unet_config=self.unet_config,
                    device=self.device
                )
                
                # 设置数据类型和设备
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
                print(f"✅ 模型初始化完成，耗时: {init_time:.2f}秒")
                return True
                
            except Exception as e:
                print(f"❌ 模型初始化失败: {str(e)}")
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
            print(f"   - 掩码坐标: {len(mask_coords_list_cycle)} 帧")
            
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
    
    def inference_with_cache(self, template_id, audio_path, output_path, cache_dir, batch_size=8, fps=25):
        """使用缓存进行快速推理"""
        if not self.is_initialized:
            print("❌ 模型未初始化")
            return False
            
        try:
            start_time = time.time()
            print(f"🚀 开始快速推理: {template_id}")
            
            # 1. 加载模板缓存
            cache_data = self.load_template_cache(cache_dir, template_id)
            if not cache_data:
                return False
            
            input_latent_list_cycle = cache_data['input_latent_list_cycle']
            coord_list_cycle = cache_data['coord_list_cycle']
            frame_list_cycle = cache_data['frame_list_cycle']
            mask_coords_list_cycle = cache_data['mask_coords_list_cycle']
            mask_list_cycle = cache_data['mask_list_cycle']
            
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
            
            # 3. 批量推理
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
                
                pred_latents = self.unet.model(latent_batch, self.timesteps, encoder_hidden_states=audio_feature_batch).sample
                recon = self.vae.decode_latents(pred_latents)
                for res_frame in recon:
                    res_frame_list.append(res_frame)
            
            inference_time = time.time() - inference_start
            print(f"✅ 推理完成: {len(res_frame_list)} 帧, 耗时: {inference_time:.2f}秒")
            
            # 4. 合成完整图像
            print("🖼️ 合成完整图像...")
            compose_start = time.time()
            
            # 创建临时帧目录
            temp_frames_dir = os.path.join(os.path.dirname(output_path), "temp_frames")
            os.makedirs(temp_frames_dir, exist_ok=True)
            
            for i, res_frame in enumerate(tqdm(res_frame_list, desc="合成图像")):
                bbox = coord_list_cycle[i % len(coord_list_cycle)]
                ori_frame = copy.deepcopy(frame_list_cycle[i % len(frame_list_cycle)])
                mask_coords = mask_coords_list_cycle[i % len(mask_coords_list_cycle)]
                mask = mask_list_cycle[i % len(mask_list_cycle)]
                
                x1, y1, x2, y2 = bbox
                try:
                    res_frame = cv2.resize(res_frame.astype(np.uint8), (x2-x1, y2-y1))
                except:
                    continue
                
                # 使用官方的图像合成方法
                combine_frame = get_image_blending(
                    image=ori_frame, 
                    face=res_frame, 
                    face_box=bbox, 
                    mask_array=mask, 
                    crop_box=mask_coords
                )
                
                # 保存帧
                frame_path = os.path.join(temp_frames_dir, f"{i:08d}.png")
                cv2.imwrite(frame_path, combine_frame)
            
            compose_time = time.time() - compose_start
            print(f"✅ 图像合成完成: 耗时: {compose_time:.2f}秒")
            
            # 5. 生成视频（无音频版本）
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
            print(f"🎉 推理完成: {output_path}")
            print(f"📊 总耗时: {total_time:.2f}秒 (音频:{audio_time:.1f}s + 推理:{inference_time:.1f}s + 合成:{compose_time:.1f}s + 视频:{video_time:.1f}s + 音频:{audio_merge_time:.1f}s)")
            
            return True
            
        except Exception as e:
            print(f"❌ 推理失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

# 全局服务实例
musetalk_service = PersistentMuseTalkService()

def main():
    """命令行接口"""
    parser = argparse.ArgumentParser(description='持久化MuseTalk推理服务')
    parser.add_argument('--template_id', type=str, required=True, help='模板ID')
    parser.add_argument('--audio_path', type=str, required=True, help='音频文件路径')
    parser.add_argument('--output_path', type=str, required=True, help='输出视频路径')
    parser.add_argument('--cache_dir', type=str, required=True, help='缓存目录')
    parser.add_argument('--device', type=str, default='cuda:0', help='GPU设备')
    parser.add_argument('--batch_size', type=int, default=8, help='批处理大小')
    parser.add_argument('--fps', type=int, default=25, help='视频帧率')
    
    args = parser.parse_args()
    
    # 解析GPU ID
    gpu_id = 0
    if args.device.startswith('cuda:'):
        gpu_id = int(args.device.split(':')[1])
    
    # 初始化模型（只执行一次）
    if not musetalk_service.initialize_models(gpu_id):
        print("❌ 模型初始化失败")
        sys.exit(1)
    
    # 执行推理
    success = musetalk_service.inference_with_cache(
        template_id=args.template_id,
        audio_path=args.audio_path,
        output_path=args.output_path,
        cache_dir=args.cache_dir,
        batch_size=args.batch_size,
        fps=args.fps
    )
    
    if success:
        print("✅ 推理成功完成")
        sys.exit(0)
    else:
        print("❌ 推理失败")
        sys.exit(1)

if __name__ == "__main__":
    main()