#!/usr/bin/env python3
"""
🚀 MuseTalk极致性能优化版本
基于官方realtime_inference.py源码，针对固定模板场景的极致优化

特性:
1. 模板预处理一次，永久使用
2. 4x RTX 4090并行推理
3. 内存预加载，减少重复计算
4. 批处理优化，最大化GPU利用率
"""

import argparse
import os
import json
import time
import threading
import queue
import multiprocessing as mp
from pathlib import Path
from omegaconf import OmegaConf
import numpy as np
import cv2
import torch
import glob
import pickle
import copy
from tqdm import tqdm
from transformers import WhisperModel

from musetalk.utils.face_parsing import FaceParsing
from musetalk.utils.utils import datagen, load_all_model
from musetalk.utils.preprocessing import get_landmark_and_bbox, read_imgs
from musetalk.utils.blending import get_image_prepare_material, get_image_blending
from musetalk.utils.audio_processor import AudioProcessor

class OptimizedMuseTalkInference:
    """🚀 MuseTalk极致性能优化推理器"""
    
    def __init__(self, config):
        self.config = config
        self.device_count = torch.cuda.device_count()
        self.models = {}  # 每个GPU的模型实例
        self.templates = {}  # 预处理的模板缓存
        self.audio_processor = None
        self.fp = None
        
        print(f"🚀 初始化MuseTalk优化推理器 - 检测到 {self.device_count} 个GPU")
        
        # 初始化每个GPU的模型
        self._initialize_models()
        
        # 预处理所有模板
        self._preprocess_templates()
        
        print("✅ MuseTalk优化推理器初始化完成")
    
    def _initialize_models(self):
        """初始化每个GPU的模型实例"""
        print("🔧 初始化GPU模型...")
        
        for gpu_id in range(self.device_count):
            device = torch.device(f"cuda:{gpu_id}")
            
            print(f"🎮 初始化GPU {gpu_id} 模型...")
            
            # 加载模型
            vae, unet, pe = load_all_model(
                unet_model_path=self.config.unet_model_path,
                vae_type=self.config.vae_type,
                unet_config=self.config.unet_config,
                device=device
            )
            
            # 转换为半精度并移动到指定GPU
            pe = pe.half().to(device)
            vae.vae = vae.vae.half().to(device)
            unet.model = unet.model.half().to(device)
            
            # 初始化Whisper模型
            whisper = WhisperModel.from_pretrained(self.config.whisper_dir)
            whisper = whisper.to(device=device, dtype=unet.model.dtype).eval()
            whisper.requires_grad_(False)
            
            # 初始化时间步
            timesteps = torch.tensor([0], device=device)
            
            self.models[gpu_id] = {
                'vae': vae,
                'unet': unet,
                'pe': pe,
                'whisper': whisper,
                'timesteps': timesteps,
                'device': device
            }
            
            print(f"✅ GPU {gpu_id} 模型初始化完成")
        
        # 初始化音频处理器（共享）
        self.audio_processor = AudioProcessor(feature_extractor_path=self.config.whisper_dir)
        
        # 初始化面部解析器（共享）
        if self.config.version == "v15":
            self.fp = FaceParsing(
                left_cheek_width=self.config.left_cheek_width,
                right_cheek_width=self.config.right_cheek_width
            )
        else:
            self.fp = FaceParsing()
    
    def _preprocess_templates(self):
        """预处理所有模板"""
        print("🔄 开始预处理模板...")
        
        # 从wwwroot/templates目录读取模板列表
        template_dir = getattr(self.config, 'template_dir', './templates')
        if os.path.exists(template_dir):
            template_files = []
            # 支持常见图片格式
            for ext in ['*.jpg', '*.jpeg', '*.png', '*.bmp', '*.webp']:
                template_files.extend(glob.glob(os.path.join(template_dir, ext)))
        else:
            print(f"⚠️ 模板目录不存在: {template_dir}")
            template_files = []
        
        if not template_files:
            print("⚠️ 未找到任何模板文件，将在运行时动态预处理")
            return
        
        for template_file in template_files:
            template_id = Path(template_file).stem
            print(f"🔄 预处理模板: {template_id}")
            
            try:
                template_data = self._preprocess_single_template(template_id, template_file)
                self.templates[template_id] = template_data
                print(f"✅ 模板 {template_id} 预处理完成")
            except Exception as e:
                print(f"❌ 模板 {template_id} 预处理失败: {e}")
        
        print(f"🎉 所有模板预处理完成，共 {len(self.templates)} 个模板")
    
    def _preprocess_single_template(self, template_id, template_path):
        """预处理单个模板"""
        # 创建模板目录
        template_dir = f"./results/optimized_templates/{template_id}"
        os.makedirs(template_dir, exist_ok=True)
        
        # 检查是否已经预处理过
        cache_file = f"{template_dir}/preprocessed_cache.pkl"
        if os.path.exists(cache_file):
            print(f"📋 加载已预处理的模板缓存: {template_id}")
            with open(cache_file, 'rb') as f:
                return pickle.load(f)
        
        # 使用GPU 0进行预处理
        device = self.models[0]['device']
        vae = self.models[0]['vae']
        
        # 读取模板图片
        if os.path.isfile(template_path):
            frame_list = [cv2.imread(template_path)]
            if frame_list[0] is None:
                raise ValueError(f"无法读取模板图片: {template_path}")
        else:
            raise ValueError(f"模板文件不存在: {template_path}")
        
        # 提取面部坐标
        print(f"🔍 提取面部坐标: {template_id}")
        coord_list, frame_list = get_landmark_and_bbox([template_path], self.config.bbox_shift)
        
        # 预计算VAE编码
        print(f"🧠 预计算VAE编码: {template_id}")
        input_latent_list = []
        coord_placeholder = (0.0, 0.0, 0.0, 0.0)
        
        for bbox, frame in zip(coord_list, frame_list):
            if bbox == coord_placeholder:
                continue
            
            x1, y1, x2, y2 = bbox
            if self.config.version == "v15":
                y2 = y2 + self.config.extra_margin
                y2 = min(y2, frame.shape[0])
            
            crop_frame = frame[y1:y2, x1:x2]
            resized_crop_frame = cv2.resize(crop_frame, (256, 256), interpolation=cv2.INTER_LANCZOS4)
            
            with torch.no_grad():
                latents = vae.get_latents_for_unet(resized_crop_frame)
                input_latent_list.append(latents)
        
        # 创建循环列表（前向+反向，用于平滑）
        frame_list_cycle = frame_list + frame_list[::-1]
        coord_list_cycle = coord_list + coord_list[::-1]
        input_latent_list_cycle = input_latent_list + input_latent_list[::-1]
        
        # 预计算面部解析mask
        print(f"🎭 预计算面部解析: {template_id}")
        mask_coords_list_cycle = []
        mask_list_cycle = []
        
        for i, frame in enumerate(tqdm(frame_list_cycle, desc="预计算面部解析")):
            x1, y1, x2, y2 = coord_list_cycle[i]
            if self.config.version == "v15":
                mode = self.config.parsing_mode
            else:
                mode = "raw"
            
            mask, crop_box = get_image_prepare_material(frame, [x1, y1, x2, y2], fp=self.fp, mode=mode)
            mask_coords_list_cycle.append(crop_box)
            mask_list_cycle.append(mask)
        
        # 构建模板数据
        template_data = {
            'template_id': template_id,
            'template_path': template_path,
            'frame_list_cycle': frame_list_cycle,
            'coord_list_cycle': coord_list_cycle,
            'input_latent_list_cycle': input_latent_list_cycle,
            'mask_coords_list_cycle': mask_coords_list_cycle,
            'mask_list_cycle': mask_list_cycle,
            'preprocessed_at': time.time()
        }
        
        # 保存缓存
        with open(cache_file, 'wb') as f:
            pickle.dump(template_data, f)
        
        return template_data
    
    def inference_parallel(self, template_id, audio_path, output_path, fps=25):
        """并行推理 - 4GPU协同工作"""
        # 如果模板未预处理，动态预处理
        if template_id not in self.templates:
            print(f"🔄 模板 {template_id} 未预处理，开始动态预处理...")
            template_path = self._find_template_path(template_id)
            if not template_path:
                raise ValueError(f"模板 {template_id} 文件未找到")
            
            template_data = self._preprocess_single_template(template_id, template_path)
            self.templates[template_id] = template_data
            print(f"✅ 模板 {template_id} 动态预处理完成")
        
        template_data = self.templates[template_id]
        
        print(f"🚀 开始并行推理: 模板={template_id}, 音频={audio_path}")
        start_time = time.time()
        
        # 1. 音频特征提取（使用GPU 0）
        print("🎵 提取音频特征...")
        audio_start = time.time()
        
        device = self.models[0]['device']
        whisper = self.models[0]['whisper']
        weight_dtype = self.models[0]['unet'].model.dtype
        
        whisper_input_features, librosa_length = self.audio_processor.get_audio_feature(
            audio_path, weight_dtype=weight_dtype
        )
        
        whisper_chunks = self.audio_processor.get_whisper_chunk(
            whisper_input_features,
            device,
            weight_dtype,
            whisper,
            librosa_length,
            fps=fps,
            audio_padding_length_left=self.config.audio_padding_length_left,
            audio_padding_length_right=self.config.audio_padding_length_right,
        )
        
        audio_time = time.time() - audio_start
        print(f"✅ 音频特征提取完成: {audio_time:.2f}s, 共 {len(whisper_chunks)} 帧")
        
        # 2. 并行GPU推理
        print("🎮 开始4GPU并行推理...")
        inference_start = time.time()
        
        # 将任务分配给4个GPU
        video_num = len(whisper_chunks)
        batch_size = self.config.batch_size
        
        # 创建数据生成器
        gen = datagen(
            whisper_chunks,
            template_data['input_latent_list_cycle'],
            batch_size
        )
        
        # 使用队列进行GPU间通信
        task_queue = queue.Queue()
        result_queue = queue.Queue()
        
        # 将所有批次加入任务队列
        batch_list = list(gen)
        for i, (whisper_batch, latent_batch) in enumerate(batch_list):
            task_queue.put((i, whisper_batch, latent_batch))
        
        # 启动GPU工作线程
        gpu_threads = []
        for gpu_id in range(self.device_count):
            thread = threading.Thread(
                target=self._gpu_worker,
                args=(gpu_id, task_queue, result_queue)
            )
            thread.start()
            gpu_threads.append(thread)
        
        # 等待所有任务完成
        task_queue.join()
        
        # 收集结果
        results = {}
        for _ in range(len(batch_list)):
            batch_idx, batch_results = result_queue.get()
            results[batch_idx] = batch_results
        
        # 按顺序组装结果
        res_frame_list = []
        for i in range(len(batch_list)):
            if i in results:
                res_frame_list.extend(results[i])
        
        inference_time = time.time() - inference_start
        print(f"✅ 4GPU并行推理完成: {inference_time:.2f}s")
        
        # 3. 后处理和视频合成
        print("🎬 开始视频合成...")
        postprocess_start = time.time()
        
        self._postprocess_and_save(
            template_data, res_frame_list, audio_path, output_path, fps
        )
        
        postprocess_time = time.time() - postprocess_start
        total_time = time.time() - start_time
        
        print(f"🎉 推理完成!")
        print(f"📊 性能统计:")
        print(f"   音频处理: {audio_time:.2f}s")
        print(f"   GPU推理: {inference_time:.2f}s")
        print(f"   后处理: {postprocess_time:.2f}s")
        print(f"   总耗时: {total_time:.2f}s")
        print(f"   视频长度: {len(res_frame_list)/fps:.1f}s")
        print(f"   实时率: {(len(res_frame_list)/fps)/total_time:.2f}x")
        
        return output_path
    
    def _gpu_worker(self, gpu_id, task_queue, result_queue):
        """GPU工作线程"""
        models = self.models[gpu_id]
        device = models['device']
        
        print(f"🎮 GPU {gpu_id} 工作线程启动")
        
        while True:
            try:
                # 获取任务（超时1秒）
                batch_idx, whisper_batch, latent_batch = task_queue.get(timeout=1)
                
                # 执行推理
                with torch.no_grad():
                    # 音频特征编码
                    audio_feature_batch = models['pe'](whisper_batch.to(device))
                    latent_batch = latent_batch.to(device=device, dtype=models['unet'].model.dtype)
                    
                    # UNet推理
                    pred_latents = models['unet'].model(
                        latent_batch,
                        models['timesteps'],
                        encoder_hidden_states=audio_feature_batch
                    ).sample
                    
                    # VAE解码
                    pred_latents = pred_latents.to(device=device, dtype=models['vae'].vae.dtype)
                    recon = models['vae'].decode_latents(pred_latents)
                
                # 返回结果
                result_queue.put((batch_idx, recon))
                task_queue.task_done()
                
            except queue.Empty:
                # 队列为空，退出线程
                break
            except Exception as e:
                print(f"❌ GPU {gpu_id} 处理错误: {e}")
                task_queue.task_done()
        
        print(f"🛑 GPU {gpu_id} 工作线程结束")
    
    def _find_template_path(self, template_id):
        """查找模板文件路径"""
        template_dir = getattr(self.config, 'template_dir', './templates')
        
        # 支持的图片格式
        extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.webp']
        
        for ext in extensions:
            template_path = os.path.join(template_dir, f"{template_id}{ext}")
            if os.path.exists(template_path):
                return template_path
        
        return None
    
    def _postprocess_and_save(self, template_data, res_frame_list, audio_path, output_path, fps):
        """后处理和保存视频"""
        # 创建输出目录
        output_dir = os.path.dirname(output_path)
        os.makedirs(output_dir, exist_ok=True)
        
        temp_dir = f"{output_dir}/temp_{int(time.time())}"
        os.makedirs(temp_dir, exist_ok=True)
        
        # 合成最终帧
        print("🖼️ 合成最终帧...")
        for i, res_frame in enumerate(tqdm(res_frame_list, desc="合成帧")):
            # 获取对应的原始帧和坐标
            cycle_idx = i % len(template_data['coord_list_cycle'])
            bbox = template_data['coord_list_cycle'][cycle_idx]
            ori_frame = copy.deepcopy(template_data['frame_list_cycle'][cycle_idx])
            
            x1, y1, x2, y2 = bbox
            
            try:
                # 调整生成帧大小
                res_frame = cv2.resize(res_frame.astype(np.uint8), (x2-x1, y2-y1))
                
                # 获取mask和坐标
                mask = template_data['mask_list_cycle'][cycle_idx]
                mask_crop_box = template_data['mask_coords_list_cycle'][cycle_idx]
                
                # 混合图像
                combine_frame = get_image_blending(ori_frame, res_frame, bbox, mask, mask_crop_box)
                
                # 保存帧
                cv2.imwrite(f"{temp_dir}/{i:08d}.png", combine_frame)
                
            except Exception as e:
                print(f"⚠️ 第 {i} 帧处理失败: {e}")
                continue
        
        # 生成视频
        print("🎬 生成视频文件...")
        temp_video = f"{temp_dir}/temp_video.mp4"
        cmd_img2video = f"ffmpeg -y -v warning -r {fps} -f image2 -i {temp_dir}/%08d.png -vcodec libx264 -vf format=yuv420p -crf 18 {temp_video}"
        os.system(cmd_img2video)
        
        # 合并音频
        print("🔊 合并音频...")
        cmd_combine_audio = f"ffmpeg -y -v warning -i {audio_path} -i {temp_video} {output_path}"
        os.system(cmd_combine_audio)
        
        # 清理临时文件
        import shutil
        shutil.rmtree(temp_dir)
        
        print(f"✅ 视频保存完成: {output_path}")

def main():
    parser = argparse.ArgumentParser(description="MuseTalk极致性能优化推理")
    parser.add_argument("--config", type=str, default="configs/optimized_inference.yaml", help="配置文件路径")
    parser.add_argument("--template_id", type=str, required=True, help="模板ID")
    parser.add_argument("--audio_path", type=str, required=True, help="音频文件路径")
    parser.add_argument("--output_path", type=str, required=True, help="输出视频路径")
    parser.add_argument("--fps", type=int, default=25, help="视频帧率")
    
    # MuseTalk标准参数
    parser.add_argument("--version", type=str, default="v1", choices=["v1", "v15"])
    parser.add_argument("--unet_config", type=str, default="./models/musetalk/musetalk.json")
    parser.add_argument("--unet_model_path", type=str, default="./models/musetalk/pytorch_model.bin")
    parser.add_argument("--whisper_dir", type=str, default="./models/whisper")
    parser.add_argument("--vae_type", type=str, default="sd-vae")
    parser.add_argument("--batch_size", type=int, default=32, help="批处理大小 - 4GPU优化")
    parser.add_argument("--bbox_shift", type=int, default=0)
    parser.add_argument("--extra_margin", type=int, default=10)
    parser.add_argument("--audio_padding_length_left", type=int, default=2)
    parser.add_argument("--audio_padding_length_right", type=int, default=2)
    parser.add_argument("--parsing_mode", default='jaw')
    parser.add_argument("--left_cheek_width", type=int, default=90)
    parser.add_argument("--right_cheek_width", type=int, default=90)
    parser.add_argument("--template_dir", type=str, default="./templates", help="模板目录")
    
    args = parser.parse_args()
    
    print("🚀 启动MuseTalk极致性能优化推理器")
    print(f"📊 配置参数:")
    print(f"   模板ID: {args.template_id}")
    print(f"   音频文件: {args.audio_path}")
    print(f"   输出路径: {args.output_path}")
    print(f"   批处理大小: {args.batch_size}")
    print(f"   GPU数量: {torch.cuda.device_count()}")
    
    # 初始化推理器
    inference_engine = OptimizedMuseTalkInference(args)
    
    # 执行推理
    result_path = inference_engine.inference_parallel(
        template_id=args.template_id,
        audio_path=args.audio_path,
        output_path=args.output_path,
        fps=args.fps
    )
    
    print(f"🎉 推理完成，输出文件: {result_path}")

if __name__ == "__main__":
    main()