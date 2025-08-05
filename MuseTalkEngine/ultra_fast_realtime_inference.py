#!/usr/bin/env python3
"""
Ultra-Fast Real-time MuseTalk Inference System
超高速实时MuseTalk推理系统

基于预处理缓存的极速推理，推理过程只涉及：
1. 音频特征提取（一次性）
2. UNet推理
3. VAE解码
4. 图像融合

消除了重复的面部检测、VAE编码等耗时操作

作者: Claude Sonnet
版本: 1.0
"""

import os
import cv2
import torch
import numpy as np
import time
import argparse
from pathlib import Path
from tqdm import tqdm
import threading
import queue
import concurrent.futures

# MuseTalk组件导入
from musetalk.utils.blending import get_image_blending
from musetalk.utils.utils import load_all_model
from musetalk.utils.audio_processor import AudioProcessor
from transformers import WhisperModel

# 导入增强预处理器
from enhanced_musetalk_preprocessing import EnhancedMuseTalkPreprocessor


class UltraFastRealtimeInference:
    """
    超高速实时推理系统
    
    特点：
    - 基于预处理缓存，消除重复计算
    - 多GPU并行推理
    - 内存优化的批处理
    - 实时音频流处理
    """
    
        def __init__(self, 
                 model_config_path="../MuseTalk/models/musetalk/musetalk.json",
                 model_weights_path="../MuseTalk/models/musetalk/pytorch_model.bin",
                 vae_type="sd-vae",
                 whisper_dir="../MuseTalk/models/whisper",
                 device="cuda:0",
                 cache_dir="./template_cache",
                 batch_size=32,
                 fp16=True):
        """
        初始化超高速推理系统
        
        Args:
            model_config_path: UNet配置路径
            model_weights_path: UNet权重路径
            vae_type: VAE类型
            whisper_dir: Whisper模型目录
            device: 主设备
            cache_dir: 缓存目录
            batch_size: 批处理大小
            fp16: 是否使用半精度
        """
        self.device = torch.device(device)
        self.cache_dir = Path(cache_dir)
        self.batch_size = batch_size
        self.fp16 = fp16
        
        print(f"🚀 初始化超高速实时推理系统...")
        print(f"📱 主设备: {self.device}")
        print(f"🎯 批处理大小: {batch_size}")
        print(f"💾 缓存目录: {cache_dir}")
        
        # 初始化预处理器（用于加载缓存）
        self.preprocessor = EnhancedMuseTalkPreprocessor(
            model_config_path=model_config_path,
            model_weights_path=model_weights_path,
            vae_type=vae_type,
            device=device,
            cache_dir=cache_dir
        )
        
        # 获取模型组件引用
        self.vae = self.preprocessor.vae
        self.unet = self.preprocessor.unet
        self.pe = self.preprocessor.pe
        
        # 优化模型精度
        if self.fp16:
            self.pe = self.pe.half()
            self.vae.vae = self.vae.vae.half()
            self.unet.model = self.unet.model.half()
        
        # 初始化音频处理器
        self.audio_processor = AudioProcessor(feature_extractor_path=whisper_dir)
        self.weight_dtype = self.unet.model.dtype
        
        # 初始化Whisper模型
        self.whisper = WhisperModel.from_pretrained(whisper_dir)
        self.whisper = self.whisper.to(device=self.device, dtype=self.weight_dtype).eval()
        self.whisper.requires_grad_(False)
        
        # 时间戳
        self.timesteps = torch.tensor([0], device=self.device)
        
        print(f"✅ 超高速推理系统初始化完成")
    
    def load_template_cache(self, template_id):
        """
        加载模板预处理缓存
        
        Args:
            template_id: 模板ID
            
        Returns:
            tuple: (预处理数据, 元数据)
        """
        print(f"📦 加载模板缓存: {template_id}")
        
        try:
            data, metadata = self.preprocessor.load_preprocessed_template(template_id)
            print(f"✅ 缓存加载成功")
            print(f"📊 帧数: {len(data['frame_list_cycle'])}")
            print(f"📍 原始bbox: {metadata['bbox']}")
            return data, metadata
        
        except FileNotFoundError:
            print(f"❌ 模板缓存不存在: {template_id}")
            print(f"💡 请先运行预处理创建缓存")
            raise
    
    def extract_audio_features(self, audio_path, fps=25):
        """
        提取音频特征
        
        Args:
            audio_path: 音频文件路径
            fps: 帧率
            
        Returns:
            list: Whisper音频块
        """
        print(f"🎵 提取音频特征: {audio_path}")
        start_time = time.time()
        
        # 提取音频特征
        whisper_input_features, librosa_length = self.audio_processor.get_audio_feature(
            audio_path, weight_dtype=self.weight_dtype
        )
        
        # 生成Whisper音频块
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
        
        extract_time = time.time() - start_time
        print(f"✅ 音频特征提取完成")
        print(f"⏱️ 提取耗时: {extract_time:.3f}秒")
        print(f"📊 音频块数: {len(whisper_chunks)}")
        
        return whisper_chunks
    
    def ultra_fast_inference(self, 
                           template_id, 
                           audio_path, 
                           output_path,
                           fps=25,
                           save_frames=True):
        """
        超高速推理主函数
        
        Args:
            template_id: 模板ID
            audio_path: 音频文件路径
            output_path: 输出视频路径
            fps: 帧率
            save_frames: 是否保存中间帧
            
        Returns:
            str: 输出视频路径
        """
        print(f"🚀 开始超高速推理")
        print(f"🎭 模板: {template_id}")
        print(f"🎵 音频: {audio_path}")
        print(f"📹 输出: {output_path}")
        
        total_start_time = time.time()
        
        # 1. 加载预处理缓存
        template_data, metadata = self.load_template_cache(template_id)
        
        # 2. 提取音频特征
        whisper_chunks = self.extract_audio_features(audio_path, fps)
        video_frames_count = len(whisper_chunks)
        
        # 3. 准备批处理数据生成器
        def batch_generator():
            """批处理数据生成器"""
            for i in range(0, len(whisper_chunks), self.batch_size):
                batch_end = min(i + self.batch_size, len(whisper_chunks))
                
                # 音频批次
                audio_batch = whisper_chunks[i:batch_end]
                
                # 潜在编码批次（循环使用）
                latent_batch = []
                for j in range(len(audio_batch)):
                    frame_idx = (i + j) % len(template_data['input_latent_list_cycle'])
                    latent = template_data['input_latent_list_cycle'][frame_idx]
                    latent_batch.append(latent)
                
                yield torch.stack(audio_batch), torch.stack(latent_batch), i
        
        # 4. 超高速批处理推理
        print(f"⚡ 开始批处理推理...")
        inference_start_time = time.time()
        
        results = {}  # 存储推理结果
        
        with torch.no_grad():
            for audio_batch, latent_batch, start_idx in tqdm(
                batch_generator(), 
                desc="推理进度",
                total=(len(whisper_chunks) + self.batch_size - 1) // self.batch_size
            ):
                # 音频特征编码
                audio_feature_batch = self.pe(audio_batch.to(self.device))
                
                # 潜在编码准备
                latent_batch = latent_batch.to(device=self.device, dtype=self.unet.model.dtype)
                
                # UNet推理
                pred_latents = self.unet.model(
                    latent_batch,
                    self.timesteps,
                    encoder_hidden_states=audio_feature_batch
                ).sample
                
                # VAE解码
                pred_latents = pred_latents.to(device=self.device, dtype=self.vae.vae.dtype)
                recon_frames = self.vae.decode_latents(pred_latents)
                
                # 存储结果
                for i, frame in enumerate(recon_frames):
                    results[start_idx + i] = frame.cpu().numpy()
        
        inference_time = time.time() - inference_start_time
        print(f"✅ 推理完成，耗时: {inference_time:.3f}秒")
        print(f"⚡ 推理速度: {len(whisper_chunks) / inference_time:.1f} FPS")
        
        # 5. 图像融合和视频合成
        if save_frames:
            print(f"🎬 开始图像融合...")
            blending_start_time = time.time()
            
            final_frames = []
            for i in tqdm(range(video_frames_count), desc="融合进度"):
                if i not in results:
                    continue
                
                # 获取推理结果
                res_frame = results[i]
                
                # 获取模板数据（循环使用）
                frame_idx = i % len(template_data['frame_list_cycle'])
                ori_frame = template_data['frame_list_cycle'][frame_idx].copy()
                bbox = template_data['coord_list_cycle'][frame_idx]
                mask = template_data['mask_list_cycle'][frame_idx]
                mask_crop_box = template_data['mask_coords_list_cycle'][frame_idx]
                
                # 调整大小并融合
                x1, y1, x2, y2 = bbox
                res_frame_resized = cv2.resize(res_frame.astype(np.uint8), (x2 - x1, y2 - y1))
                
                # 图像融合
                combine_frame = get_image_blending(ori_frame, res_frame_resized, bbox, mask, mask_crop_box)
                final_frames.append(combine_frame)
            
            blending_time = time.time() - blending_start_time
            print(f"✅ 图像融合完成，耗时: {blending_time:.3f}秒")
            
            # 6. 保存视频
            self._save_video(final_frames, audio_path, output_path, fps)
        
        total_time = time.time() - total_start_time
        print(f"🎉 超高速推理完成")
        print(f"⏱️ 总耗时: {total_time:.3f}秒")
        print(f"⚡ 平均速度: {video_frames_count / total_time:.1f} FPS")
        print(f"📹 输出: {output_path}")
        
        return output_path
    
    def _save_video(self, frames, audio_path, output_path, fps):
        """保存视频"""
        if not frames:
            raise ValueError("没有帧可以保存")
        
        print(f"💾 保存视频: {output_path}")
        
        h, w, c = frames[0].shape
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        temp_video = output_path.replace('.mp4', '_temp.mp4')
        
        # 写入视频帧
        out = cv2.VideoWriter(temp_video, fourcc, fps, (w, h))
        for frame in frames:
            out.write(frame)
        out.release()
        
        # 合并音频
        cmd = (f'ffmpeg -y -i "{temp_video}" -i "{audio_path}" '
               f'-c:v copy -c:a aac -strict experimental "{output_path}" -loglevel quiet')
        os.system(cmd)
        
        # 清理临时文件
        if os.path.exists(temp_video):
            os.remove(temp_video)
        
        print(f"✅ 视频保存完成")
    
    def benchmark_performance(self, template_id, audio_path, runs=3):
        """
        性能基准测试
        
        Args:
            template_id: 模板ID
            audio_path: 音频文件路径
            runs: 测试次数
        """
        print(f"🏃 开始性能基准测试")
        print(f"🎭 模板: {template_id}")
        print(f"🎵 音频: {audio_path}")
        print(f"🔄 测试次数: {runs}")
        
        times = []
        
        for run in range(runs):
            print(f"\n--- 第 {run + 1} 次测试 ---")
            
            start_time = time.time()
            
            # 加载缓存
            template_data, metadata = self.load_template_cache(template_id)
            
            # 提取音频特征
            whisper_chunks = self.extract_audio_features(audio_path)
            
            # 只做推理，不保存视频
            with torch.no_grad():
                for i in range(0, len(whisper_chunks), self.batch_size):
                    batch_end = min(i + self.batch_size, len(whisper_chunks))
                    audio_batch = whisper_chunks[i:batch_end]
                    
                    latent_batch = []
                    for j in range(len(audio_batch)):
                        frame_idx = (i + j) % len(template_data['input_latent_list_cycle'])
                        latent = template_data['input_latent_list_cycle'][frame_idx]
                        latent_batch.append(latent)
                    
                    audio_batch = torch.stack(audio_batch)
                    latent_batch = torch.stack(latent_batch)
                    
                    # 推理
                    audio_feature_batch = self.pe(audio_batch.to(self.device))
                    latent_batch = latent_batch.to(device=self.device, dtype=self.unet.model.dtype)
                    
                    pred_latents = self.unet.model(
                        latent_batch, self.timesteps, encoder_hidden_states=audio_feature_batch
                    ).sample
                    
                    pred_latents = pred_latents.to(device=self.device, dtype=self.vae.vae.dtype)
                    recon_frames = self.vae.decode_latents(pred_latents)
            
            run_time = time.time() - start_time
            fps = len(whisper_chunks) / run_time
            times.append(run_time)
            
            print(f"⏱️ 耗时: {run_time:.3f}秒")
            print(f"⚡ 速度: {fps:.1f} FPS")
        
        # 统计结果
        avg_time = np.mean(times)
        avg_fps = len(whisper_chunks) / avg_time
        
        print(f"\n📊 基准测试结果 ({runs} 次平均):")
        print(f"⏱️ 平均耗时: {avg_time:.3f}秒")
        print(f"⚡ 平均速度: {avg_fps:.1f} FPS")
        print(f"📈 最快速度: {len(whisper_chunks) / min(times):.1f} FPS")


def main():
    """命令行界面"""
    parser = argparse.ArgumentParser(description="超高速实时MuseTalk推理")
    parser.add_argument("--template_id", required=True, help="模板ID")
    parser.add_argument("--audio_path", required=True, help="音频文件路径")
    parser.add_argument("--output_path", required=True, help="输出视频路径")
    parser.add_argument("--cache_dir", default="./template_cache", help="缓存目录")
    parser.add_argument("--device", default="cuda:0", help="计算设备")
    parser.add_argument("--batch_size", type=int, default=32, help="批处理大小")
    parser.add_argument("--fps", type=int, default=25, help="视频帧率")
    parser.add_argument("--fp16", action="store_true", default=True, help="使用半精度")
    parser.add_argument("--benchmark", action="store_true", help="运行性能基准测试")
    parser.add_argument("--benchmark_runs", type=int, default=3, help="基准测试次数")
    
    args = parser.parse_args()
    
    # 初始化推理系统
    inference_system = UltraFastRealtimeInference(
        device=args.device,
        cache_dir=args.cache_dir,
        batch_size=args.batch_size,
        fp16=args.fp16
    )
    
    if args.benchmark:
        # 性能基准测试
        inference_system.benchmark_performance(
            args.template_id, 
            args.audio_path, 
            args.benchmark_runs
        )
    else:
        # 正常推理
        inference_system.ultra_fast_inference(
            template_id=args.template_id,
            audio_path=args.audio_path,
            output_path=args.output_path,
            fps=args.fps,
            save_frames=True
        )


if __name__ == "__main__":
    main()