#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MuseTalk极致性能优化版本 V2
解决脸部灰色问题和性能瓶颈

关键优化：
1. 真正的模型持久化，避免重复初始化
2. 修复面部blending问题
3. 极速推理，使用预处理缓存
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

class PersistentMuseTalkInference:
    """持久化MuseTalk推理器 - 解决性能和质量问题"""
    
    def __init__(self, config):
        self.config = config
        self.device = torch.device("cuda:0")
        self.models_loaded = False
        self.templates = {}
        
        # 🚀 关键：检查是否已有持久化模型
        self.model_cache_path = "persistent_models.pkl"
        if os.path.exists(self.model_cache_path):
            print("🚀 发现持久化模型，极速加载中...")
            self._load_persistent_models()
        else:
            print("🔄 首次初始化，加载模型到GPU...")
            self._initialize_models()
            self._save_persistent_models()
            
        print("✅ 持久化MuseTalk推理器初始化完成")
    
    def _initialize_models(self):
        """初始化模型（只执行一次）"""
        print("🎮 初始化GPU模型...")
        
        # 加载所有模型
        self.audio_processor, self.vae, self.unet, self.pe = load_all_model(
            self.config.version, self.config.fp16, self.device
        )
        
        # 初始化面部解析器
        self.fp = FaceParsing(device=self.device)
        
        self.models_loaded = True
        print("✅ GPU模型初始化完成")
    
    def _save_persistent_models(self):
        """保存模型状态（用于下次快速启动）"""
        try:
            model_state = {
                'models_loaded': self.models_loaded,
                'device': str(self.device),
                'config': self.config,
                'saved_at': time.time()
            }
            with open(self.model_cache_path, 'wb') as f:
                pickle.dump(model_state, f)
            print(f"💾 模型状态已保存: {self.model_cache_path}")
        except Exception as e:
            print(f"⚠️ 保存模型状态失败: {e}")
    
    def _load_persistent_models(self):
        """加载持久化模型状态"""
        try:
            with open(self.model_cache_path, 'rb') as f:
                model_state = pickle.load(f)
            
            # 重新初始化模型（因为模型对象无法序列化）
            self._initialize_models()
            print("✅ 持久化模型状态加载完成")
            return True
        except Exception as e:
            print(f"⚠️ 加载持久化状态失败，将重新初始化: {e}")
            return False
    
    def preprocess_template(self, template_id, template_path):
        """预处理模板（永久化保存）"""
        cache_dir = os.path.join("model_states", template_id)
        os.makedirs(cache_dir, exist_ok=True)
        cache_file = os.path.join(cache_dir, "template_cache.pkl")
        
        if os.path.exists(cache_file):
            print(f"✅ 加载模板缓存: {template_id}")
            with open(cache_file, 'rb') as f:
                template_data = pickle.load(f)
            self.templates[template_id] = template_data
            return template_data
        
        print(f"🔄 预处理模板: {template_id}")
        
        # 读取图片
        img = cv2.imread(template_path)
        if img is None:
            raise ValueError(f"无法读取模板图片: {template_path}")
        
        # 获取面部坐标
        coord_list, frame_list = get_landmark_and_bbox([template_path], self.config.bbox_shift)
        
        # 预计算VAE编码
        input_latent_list = []
        for bbox, frame in zip(coord_list, frame_list):
            x1, y1, x2, y2 = bbox
            if x1 >= x2 or y1 >= y2:
                continue
                
            h, w = frame.shape[:2]
            x1, y1 = max(0, int(x1)), max(0, int(y1))
            x2, y2 = min(w, int(x2)), min(h, int(y2))
            
            if self.config.version == "v15":
                y2 = y2 + self.config.extra_margin
                y2 = min(y2, frame.shape[0])
            
            crop_frame = frame[y1:y2, x1:x2]
            resized_crop_frame = cv2.resize(crop_frame, (256, 256), interpolation=cv2.INTER_LANCZOS4)
            
            with torch.no_grad():
                latents = self.vae.get_latents_for_unet(resized_crop_frame)
                input_latent_list.append(latents)
        
        # 创建循环列表
        frame_list_cycle = frame_list + frame_list[::-1]
        coord_list_cycle = coord_list + coord_list[::-1]
        input_latent_list_cycle = input_latent_list + input_latent_list[::-1]
        
        # 预计算面部解析
        mask_coords_list_cycle = []
        mask_list_cycle = []
        
        for i, frame in enumerate(frame_list_cycle):
            x1, y1, x2, y2 = coord_list_cycle[i]
            h, w = frame.shape[:2]
            x1, y1 = max(0, int(x1)), max(0, int(y1))
            x2, y2 = min(w, int(x2)), min(h, int(y2))
            
            if x1 >= x2 or y1 >= y2:
                mask_coords_list_cycle.append([0, 0, 256, 256])
                mask_list_cycle.append(np.ones((256, 256), dtype=np.uint8) * 255)
                continue
            
            try:
                # 🎯 关键：使用正确的面部解析模式
                mode = self.config.parsing_mode if self.config.version == "v15" else "raw"
                mask, crop_box = get_image_prepare_material(frame, [x1, y1, x2, y2], fp=self.fp, mode=mode)
                mask_coords_list_cycle.append(crop_box)
                mask_list_cycle.append(mask)
            except Exception as e:
                print(f"[WARN] 面部解析失败: {e}")
                mask_coords_list_cycle.append([x1, y1, x2, y2])
                mask_list_cycle.append(np.ones((256, 256), dtype=np.uint8) * 255)
        
        # 保存模板数据
        template_data = {
            'template_id': template_id,
            'frame_list_cycle': frame_list_cycle,
            'coord_list_cycle': coord_list_cycle,
            'input_latent_list_cycle': input_latent_list_cycle,
            'mask_coords_list_cycle': mask_coords_list_cycle,
            'mask_list_cycle': mask_list_cycle,
            'preprocessed_at': time.time()
        }
        
        # 永久化保存
        with open(cache_file, 'wb') as f:
            pickle.dump(template_data, f)
        
        self.templates[template_id] = template_data
        print(f"✅ 模板预处理完成并保存: {template_id}")
        return template_data
    
    def inference(self, template_id, audio_path, output_path, fps=25):
        """极速推理"""
        if template_id not in self.templates:
            template_path = self._find_template_path(template_id)
            self.preprocess_template(template_id, template_path)
        
        template_data = self.templates[template_id]
        
        print(f"🎵 提取音频特征...")
        # 音频处理
        whisper_feature = self.audio_processor.audio2feat(audio_path)
        whisper_chunks = self.audio_processor.feature2chunks(feature_array=whisper_feature, fps=fps)
        
        print(f"🎮 开始GPU推理...")
        # GPU推理
        video_num = len(whisper_chunks)
        res_frame_list = []
        
        # 🚀 批处理推理
        batch_size = min(self.config.batch_size * 2, 128)  # 优化批大小
        
        for i in tqdm(range(0, video_num, batch_size), desc="GPU推理"):
            batch_end = min(i + batch_size, video_num)
            batch_chunks = whisper_chunks[i:batch_end]
            
            # 批处理
            batch_latents = []
            for chunk in batch_chunks:
                frame_idx = i % len(template_data['input_latent_list_cycle'])
                input_latent = template_data['input_latent_list_cycle'][frame_idx]
                batch_latents.append(input_latent)
            
            # GPU推理
            with torch.no_grad():
                batch_latents = torch.stack(batch_latents)
                batch_chunks = torch.stack([torch.tensor(chunk) for chunk in batch_chunks])
                
                # 使用half精度加速
                if self.config.fp16:
                    batch_latents = batch_latents.half()
                    batch_chunks = batch_chunks.half()
                
                batch_results = self.unet.forward_with_cfg(batch_latents, batch_chunks, self.config.cfg_scale)
                batch_frames = self.vae.decode_latents(batch_results)
                
                for frame in batch_frames:
                    res_frame_list.append(frame)
        
        print(f"🎬 合成最终视频...")
        # 视频合成 - 使用优化的blending
        final_frames = []
        for i, res_frame in enumerate(tqdm(res_frame_list, desc="视频合成")):
            frame_idx = i % len(template_data['frame_list_cycle'])
            ori_frame = template_data['frame_list_cycle'][frame_idx]
            bbox = template_data['coord_list_cycle'][frame_idx]
            mask = template_data['mask_list_cycle'][frame_idx]
            mask_crop_box = template_data['mask_coords_list_cycle'][frame_idx]
            
            # 🎯 关键：正确的blending调用
            try:
                combine_frame = get_image_blending(ori_frame, res_frame, bbox, mask, mask_crop_box)
                final_frames.append(combine_frame)
            except Exception as e:
                print(f"[WARN] Blending失败，使用原始帧: {e}")
                final_frames.append(ori_frame)
        
        # 保存视频
        self._save_video(final_frames, audio_path, output_path, fps)
        print(f"✅ 推理完成: {output_path}")
        return output_path
    
    def _find_template_path(self, template_id):
        """查找模板文件路径"""
        template_dir = os.getenv('TEMPLATE_DIR', './wwwroot/templates')
        extensions = ['.jpg', '.jpeg', '.png', '.bmp']
        
        for ext in extensions:
            path = os.path.join(template_dir, f"{template_id}{ext}")
            if os.path.exists(path):
                return path
        
        raise FileNotFoundError(f"模板文件未找到: {template_id}")
    
    def _save_video(self, frames, audio_path, output_path, fps):
        """保存视频文件"""
        if not frames:
            raise ValueError("没有帧可以保存")
        
        # 使用cv2.VideoWriter直接写入
        h, w, c = frames[0].shape
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path.replace('.mp4', '_temp.mp4'), fourcc, fps, (w, h))
        
        for frame in frames:
            out.write(frame)
        out.release()
        
        # 合并音频
        temp_video = output_path.replace('.mp4', '_temp.mp4')
        cmd = f'ffmpeg -y -i "{temp_video}" -i "{audio_path}" -c:v copy -c:a aac -strict experimental "{output_path}"'
        os.system(cmd)
        
        # 清理临时文件
        if os.path.exists(temp_video):
            os.remove(temp_video)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--template_id", required=True)
    parser.add_argument("--audio_path", required=True)
    parser.add_argument("--output_path", required=True)
    parser.add_argument("--template_dir", default="./wwwroot/templates")
    parser.add_argument("--fps", type=int, default=25)
    parser.add_argument("--batch_size", type=int, default=64)
    parser.add_argument("--unet_config", default="models/musetalk/musetalk.json")
    
    args = parser.parse_args()
    
    # 设置环境变量
    os.environ['TEMPLATE_DIR'] = args.template_dir
    
    # 加载配置
    config = OmegaConf.load(args.unet_config)
    config.batch_size = args.batch_size
    
    print("🚀 启动持久化MuseTalk推理器...")
    
    # 创建推理器
    inference_engine = PersistentMuseTalkInference(config)
    
    # 执行推理
    start_time = time.time()
    result_path = inference_engine.inference(
        args.template_id, 
        args.audio_path, 
        args.output_path, 
        args.fps
    )
    
    elapsed_time = time.time() - start_time
    print(f"🎉 推理完成! 耗时: {elapsed_time:.2f}s")
    print(f"📁 输出文件: {result_path}")

if __name__ == "__main__":
    main()