#!/usr/bin/env python3
"""
基于官方MuseTalk的正确实时推理实现
直接使用预处理缓存，不重复预处理

参考: https://github.com/TMElyralab/MuseTalk
作者: Claude Sonnet (基于官方实现)
"""

import argparse
import os
import numpy as np
import cv2
import torch
import glob
import pickle
import sys
from tqdm import tqdm
import copy
import json
import time
import threading
import queue
from transformers import WhisperModel

from musetalk.utils.face_parsing import FaceParsing
from musetalk.utils.utils import datagen
from musetalk.utils.preprocessing import read_imgs
from musetalk.utils.blending import get_image_blending
from musetalk.utils.utils import load_all_model
from musetalk.utils.audio_processor import AudioProcessor


@torch.no_grad()
class OfficialMuseTalkAvatar:
    """基于官方实现的MuseTalk Avatar"""
    
    def __init__(self, template_id, cache_dir, device, batch_size=8):
        self.template_id = template_id
        self.cache_dir = cache_dir
        self.device = device
        self.batch_size = batch_size
        self.idx = 0
        
        # 加载缓存数据
        self.load_cache()
    
    def load_cache(self):
        """加载预处理缓存数据"""
        print(f"🔄 加载模板缓存: {self.template_id}")
        
        # 使用现有的预处理缓存文件
        cache_file = os.path.join(self.cache_dir, f"{self.template_id}_preprocessed.pkl")
        metadata_file = os.path.join(self.cache_dir, f"{self.template_id}_metadata.json")
        
        if not os.path.exists(cache_file):
            raise FileNotFoundError(f"预处理缓存文件不存在: {cache_file}")
        if not os.path.exists(metadata_file):
            raise FileNotFoundError(f"元数据文件不存在: {metadata_file}")
        
        # 加载预处理缓存数据
        with open(cache_file, 'rb') as f:
            cache_data = pickle.load(f)
        
        # 提取数据
        self.input_latent_list_cycle = cache_data['input_latent_list_cycle']
        self.coord_list_cycle = cache_data['coord_list_cycle']
        self.frame_list_cycle = cache_data['frame_list_cycle']
        self.mask_coords_list_cycle = cache_data['mask_coords_list_cycle']
        self.mask_list_cycle = cache_data['mask_list_cycle']
        
        print(f"✅ 加载潜在向量: {len(self.input_latent_list_cycle)} 帧")
        print(f"✅ 加载面部坐标: {len(self.coord_list_cycle)} 帧")
        print(f"✅ 加载掩码坐标: {len(self.mask_coords_list_cycle)} 帧")
        
        # 加载元数据
        with open(metadata_file, 'r', encoding='utf-8') as f:
            self.metadata = json.load(f)
        
        print(f"✅ 缓存加载完成: {self.template_id}")
    
    def process_frames(self, res_frame_queue, video_len, output_dir):
        """处理生成的帧"""
        os.makedirs(output_dir, exist_ok=True)
        frame_idx = 0
        
        while frame_idx < video_len:
            try:
                res_frame = res_frame_queue.get(block=True, timeout=1)
            except queue.Empty:
                continue
            
            # 获取对应的坐标和掩码
            cycle_idx = frame_idx % len(self.coord_list_cycle)
            bbox = self.coord_list_cycle[cycle_idx]
            ori_frame = copy.deepcopy(self.frame_list_cycle[cycle_idx])
            
            x1, y1, x2, y2 = bbox
            try:
                res_frame = cv2.resize(res_frame.astype(np.uint8), (x2 - x1, y2 - y1))
            except:
                frame_idx += 1
                continue
            
            mask = self.mask_list_cycle[cycle_idx]
            mask_crop_box = self.mask_coords_list_cycle[cycle_idx]
            combine_frame = get_image_blending(ori_frame, res_frame, bbox, mask, mask_crop_box)
            
            # 保存帧
            cv2.imwrite(f"{output_dir}/{str(frame_idx).zfill(8)}.png", combine_frame)
            frame_idx += 1
    
    @torch.no_grad()
    def inference(self, audio_path, output_path, fps, models):
        """执行推理生成视频"""
        print(f"🚀 开始推理: {self.template_id}")
        
        vae, unet, pe, audio_processor, whisper = models
        weight_dtype = unet.model.dtype
        
        # 创建临时目录
        temp_dir = os.path.join(os.path.dirname(output_path), "temp_frames")
        os.makedirs(temp_dir, exist_ok=True)
        
        ############################################## 提取音频特征 ##############################################
        start_time = time.time()
        whisper_input_features, librosa_length = audio_processor.get_audio_feature(audio_path, weight_dtype=weight_dtype)
        whisper_chunks = audio_processor.get_whisper_chunk(
            whisper_input_features,
            self.device,
            weight_dtype,
            whisper,
            librosa_length,
            fps=fps,
            audio_padding_length_left=0,
            audio_padding_length_right=0,
        )
        print(f"✅ 音频特征提取完成: {(time.time() - start_time) * 1000:.1f}ms, 音频块数: {len(whisper_chunks)}")
        
        ############################################## 批量推理 ##############################################
        video_num = len(whisper_chunks)
        res_frame_queue = queue.Queue()
        self.idx = 0
        
        # 启动帧处理线程
        process_thread = threading.Thread(target=self.process_frames, args=(res_frame_queue, video_num, temp_dir))
        process_thread.start()
        
        # 批量生成数据
        gen = datagen(whisper_chunks, self.input_latent_list_cycle, self.batch_size)
        start_time = time.time()
        
        for i, (whisper_batch, latent_batch) in enumerate(tqdm(gen, total=int(np.ceil(float(video_num) / self.batch_size)))):
            audio_feature_batch = pe(whisper_batch.to(self.device))
            latent_batch = latent_batch.to(device=self.device, dtype=unet.model.dtype)
            
            # UNet推理
            pred_latents = unet.model(latent_batch,
                                    torch.tensor([0], device=self.device),
                                    encoder_hidden_states=audio_feature_batch).sample
            pred_latents = pred_latents.to(device=self.device, dtype=vae.vae.dtype)
            
            # VAE解码
            recon = vae.decode_latents(pred_latents)
            for res_frame in recon:
                res_frame_queue.put(res_frame)
        
        # 等待帧处理完成
        process_thread.join()
        
        inference_time = time.time() - start_time
        print(f'✅ 推理完成: {video_num} 帧, 耗时: {inference_time:.2f}秒')
        
        # 合成视频
        cmd_img2video = f"ffmpeg -y -v warning -r {fps} -f image2 -i {temp_dir}/%08d.png -vcodec libx264 -vf format=yuv420p -crf 18 {output_path}"
        print(f"🎬 合成视频: {cmd_img2video}")
        result = os.system(cmd_img2video)
        
        # 清理临时文件
        import shutil
        shutil.rmtree(temp_dir)
        
        if result == 0:
            print(f"✅ 视频生成成功: {output_path}")
            return output_path
        else:
            raise RuntimeError("视频合成失败")


def main():
    parser = argparse.ArgumentParser(description="官方MuseTalk实时推理")
    parser.add_argument("--template_id", required=True, help="模板ID")
    parser.add_argument("--audio_path", required=True, help="音频文件路径")
    parser.add_argument("--output_path", required=True, help="输出视频路径")
    parser.add_argument("--cache_dir", default="./model_states", help="缓存目录")
    parser.add_argument("--device", default="cuda:0", help="计算设备")
    parser.add_argument("--batch_size", type=int, default=8, help="批处理大小")
    parser.add_argument("--fps", type=int, default=25, help="视频帧率")
    parser.add_argument("--unet_model_path", default="models/musetalk/pytorch_model.bin", help="UNet模型路径")
    parser.add_argument("--unet_config", default="models/musetalk/musetalk.json", help="UNet配置路径")
    parser.add_argument("--vae_type", default="sd-vae", help="VAE类型")
    parser.add_argument("--whisper_dir", default="models/whisper", help="Whisper模型目录")
    
    args = parser.parse_args()
    
    # 设置设备
    device = torch.device(args.device if torch.cuda.is_available() else "cpu")
    print(f"🔧 使用设备: {device}")
    
    # 加载模型
    print("🔄 加载MuseTalk模型...")
    vae, unet, pe = load_all_model(
        unet_model_path=args.unet_model_path,
        vae_type=args.vae_type,
        unet_config=args.unet_config,
        device=device
    )
    
    # 设置半精度
    pe = pe.half().to(device)
    vae.vae = vae.vae.half().to(device)
    unet.model = unet.model.half().to(device)
    
    # 初始化音频处理器和Whisper模型
    audio_processor = AudioProcessor(feature_extractor_path=args.whisper_dir)
    weight_dtype = unet.model.dtype
    whisper = WhisperModel.from_pretrained(args.whisper_dir)
    whisper = whisper.to(device=device, dtype=weight_dtype).eval()
    whisper.requires_grad_(False)
    
    print("✅ 模型加载完成")
    
    # 创建Avatar并执行推理
    avatar = OfficialMuseTalkAvatar(
        template_id=args.template_id,
        cache_dir=args.cache_dir,
        device=device,
        batch_size=args.batch_size
    )
    
    models = (vae, unet, pe, audio_processor, whisper)
    result_path = avatar.inference(args.audio_path, args.output_path, args.fps, models)
    print(f"🎉 推理完成: {result_path}")


if __name__ == "__main__":
    main()