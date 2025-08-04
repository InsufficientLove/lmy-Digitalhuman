#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
持久化MuseTalk服务器
避免每次推理都重新启动Python进程和加载模型

使用方式：
1. 启动服务器：python persistent_musetalk_server.py --port 8888
2. C#通过HTTP调用推理
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
import concurrent.futures
from flask import Flask, request, jsonify
import traceback

from musetalk.utils.face_parsing import FaceParsing
from musetalk.utils.utils import datagen, load_all_model
from musetalk.utils.preprocessing import get_landmark_and_bbox, read_imgs
from musetalk.utils.blending import get_image_prepare_material, get_image_blending
from musetalk.utils.audio_processor import AudioProcessor

class PersistentMuseTalkServer:
    """持久化MuseTalk服务器"""
    
    def __init__(self, config_path="models/musetalk/musetalk.json"):
        self.config = OmegaConf.load(config_path)
        self.config.version = "v1"
        self.config.parsing_mode = "jaw"
        self.config.fp16 = True
        
        self.gpu_count = min(4, torch.cuda.device_count())
        self.models = {}
        self.templates = {}
        self.is_initialized = False
        
        print(f"🚀 启动持久化MuseTalk服务器 - {self.gpu_count}GPU")
        
        # 预加载所有GPU模型
        self._initialize_all_gpus()
        self.is_initialized = True
        
        print("✅ 持久化服务器初始化完成，等待推理请求...")
    
    def _initialize_all_gpus(self):
        """初始化所有GPU模型"""
        print("🎮 预加载所有GPU模型...")
        
        def init_gpu_model(gpu_id):
            device = torch.device(f"cuda:{gpu_id}")
            print(f"🎮 初始化GPU {gpu_id}...")
            
            try:
                # 尝试新版本load_all_model调用
                audio_processor, vae, unet, pe = load_all_model(
                    unet_model_path="models/musetalk/pytorch_model.bin",
                    vae_type="sd-vae",
                    unet_config="models/musetalk/musetalk.json",
                    device=device
                )
            except TypeError:
                # 回退到旧版本调用
                audio_processor, vae, unet, pe = load_all_model(
                    "v1", True, device
                )
            
            # 初始化面部解析器
            fp = FaceParsing(device=device)
            
            return {
                'gpu_id': gpu_id,
                'device': device,
                'audio_processor': audio_processor,
                'vae': vae,
                'unet': unet,
                'pe': pe,
                'fp': fp,
                'initialized_at': time.time()
            }
        
        # 并行初始化所有GPU
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.gpu_count) as executor:
            futures = [executor.submit(init_gpu_model, gpu_id) for gpu_id in range(self.gpu_count)]
            
            for future in concurrent.futures.as_completed(futures):
                model_info = future.result()
                gpu_id = model_info['gpu_id']
                self.models[gpu_id] = model_info
                print(f"✅ GPU {gpu_id} 模型预加载完成")
        
        print(f"🎉 所有{self.gpu_count}个GPU模型预加载完成!")
    
    def preprocess_template(self, template_id, template_path):
        """预处理模板"""
        cache_dir = os.path.join("model_states", template_id)
        os.makedirs(cache_dir, exist_ok=True)
        cache_file = os.path.join(cache_dir, "server_template_cache.pkl")
        
        if os.path.exists(cache_file):
            print(f"🚀 加载模板缓存: {template_id}")
            with open(cache_file, 'rb') as f:
                template_data = pickle.load(f)
            self.templates[template_id] = template_data
            return template_data
        
        print(f"🔄 预处理模板: {template_id}")
        
        # 使用GPU 0进行预处理
        gpu_0_model = self.models[0]
        device = gpu_0_model['device']
        vae = gpu_0_model['vae']
        fp = gpu_0_model['fp']
        
        # 读取图片
        img = cv2.imread(template_path)
        if img is None:
            raise ValueError(f"无法读取模板图片: {template_path}")
        
        # 获取面部坐标
        coord_list, frame_list = get_landmark_and_bbox([template_path], 0)
        
        # 预计算VAE编码
        input_latent_list = []
        for bbox, frame in zip(coord_list, frame_list):
            x1, y1, x2, y2 = bbox
            if x1 >= x2 or y1 >= y2:
                continue
                
            h, w = frame.shape[:2]
            x1, y1 = max(0, int(x1)), max(0, int(y1))
            x2, y2 = min(w, int(x2)), min(h, int(y2))
            
            crop_frame = frame[y1:y2, x1:x2]
            resized_crop_frame = cv2.resize(crop_frame, (256, 256), interpolation=cv2.INTER_LANCZOS4)
            
            with torch.no_grad():
                latents = vae.get_latents_for_unet(resized_crop_frame)
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
                # 使用jaw模式
                mask, crop_box = get_image_prepare_material(frame, [x1, y1, x2, y2], fp=fp, mode="jaw")
                mask_coords_list_cycle.append(crop_box)
                mask_list_cycle.append(mask)
            except Exception as e:
                print(f"[WARN] 面部解析失败: {e}")
                mask_coords_list_cycle.append([x1, y1, x2, y2])
                default_mask = np.zeros((256, 256), dtype=np.uint8)
                default_mask[64:192, 64:192] = 255
                mask_list_cycle.append(default_mask)
        
        # 保存模板数据
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
        
        # 永久化保存
        with open(cache_file, 'wb') as f:
            pickle.dump(template_data, f)
        
        self.templates[template_id] = template_data
        print(f"✅ 模板预处理完成: {template_id}")
        return template_data
    
    def inference(self, template_id, audio_path, output_path, fps=25):
        """4GPU并行推理"""
        if template_id not in self.templates:
            template_path = self._find_template_path(template_id)
            self.preprocess_template(template_id, template_path)
        
        template_data = self.templates[template_id]
        
        print(f"🎵 提取音频特征...")
        # 使用GPU 0的音频处理器
        audio_processor = self.models[0]['audio_processor']
        whisper_feature = audio_processor.audio2feat(audio_path)
        whisper_chunks = audio_processor.feature2chunks(feature_array=whisper_feature, fps=fps)
        
        video_num = len(whisper_chunks)
        print(f"🎮 开始{self.gpu_count}GPU并行推理: {video_num}帧")
        
        # 4GPU并行推理
        chunk_size = max(1, video_num // self.gpu_count)
        gpu_tasks = []
        
        for gpu_id in range(self.gpu_count):
            start_idx = gpu_id * chunk_size
            if gpu_id == self.gpu_count - 1:
                end_idx = video_num
            else:
                end_idx = (gpu_id + 1) * chunk_size
            
            if start_idx < video_num:
                gpu_chunks = whisper_chunks[start_idx:end_idx]
                gpu_tasks.append((gpu_id, start_idx, end_idx, gpu_chunks))
        
        # 并行执行推理
        results = [None] * video_num
        
        def gpu_inference_worker(gpu_id, start_idx, end_idx, gpu_chunks):
            model = self.models[gpu_id]
            device = model['device']
            unet = model['unet']
            vae = model['vae']
            
            gpu_results = []
            batch_size = 32
            
            for i in range(0, len(gpu_chunks), batch_size):
                batch_end = min(i + batch_size, len(gpu_chunks))
                batch_chunks = gpu_chunks[i:batch_end]
                
                batch_latents = []
                for j, chunk in enumerate(batch_chunks):
                    frame_idx = (start_idx + i + j) % len(template_data['input_latent_list_cycle'])
                    input_latent = template_data['input_latent_list_cycle'][frame_idx]
                    batch_latents.append(input_latent)
                
                with torch.no_grad():
                    batch_latents = torch.stack(batch_latents).to(device)
                    batch_chunks_tensor = torch.stack([torch.tensor(chunk).to(device) for chunk in batch_chunks])
                    
                    if self.config.fp16:
                        batch_latents = batch_latents.half()
                        batch_chunks_tensor = batch_chunks_tensor.half()
                    
                    batch_results = unet.forward_with_cfg(batch_latents, batch_chunks_tensor, 3.5)
                    batch_frames = vae.decode_latents(batch_results)
                    
                    for frame in batch_frames:
                        gpu_results.append(frame.cpu().numpy())
            
            for i, result in enumerate(gpu_results):
                results[start_idx + i] = result
        
        # 启动并行推理
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.gpu_count) as executor:
            futures = [
                executor.submit(gpu_inference_worker, gpu_id, start_idx, end_idx, gpu_chunks)
                for gpu_id, start_idx, end_idx, gpu_chunks in gpu_tasks
            ]
            concurrent.futures.wait(futures)
        
        print(f"🎬 视频合成...")
        # 视频合成
        final_frames = []
        for i, res_frame in enumerate(results):
            if res_frame is None:
                continue
                
            frame_idx = i % len(template_data['frame_list_cycle'])
            ori_frame = template_data['frame_list_cycle'][frame_idx]
            bbox = template_data['coord_list_cycle'][frame_idx]
            mask = template_data['mask_list_cycle'][frame_idx]
            mask_crop_box = template_data['mask_coords_list_cycle'][frame_idx]
            
            try:
                x1, y1, x2, y2 = bbox
                res_frame_resized = cv2.resize(res_frame.astype(np.uint8), (x2 - x1, y2 - y1))
                combine_frame = get_image_blending(ori_frame, res_frame_resized, bbox, mask, mask_crop_box)
                final_frames.append(combine_frame)
            except Exception as e:
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
        """保存视频"""
        if not frames:
            raise ValueError("没有帧可以保存")
        
        h, w, c = frames[0].shape
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        temp_video = output_path.replace('.mp4', '_temp.mp4')
        
        out = cv2.VideoWriter(temp_video, fourcc, fps, (w, h))
        for frame in frames:
            out.write(frame)
        out.release()
        
        # 合并音频
        cmd = f'ffmpeg -y -i "{temp_video}" -i "{audio_path}" -c:v copy -c:a aac -strict experimental "{output_path}" -loglevel quiet'
        os.system(cmd)
        
        if os.path.exists(temp_video):
            os.remove(temp_video)

# Flask应用
app = Flask(__name__)
musetalk_server = None

@app.route('/inference', methods=['POST'])
def inference_endpoint():
    try:
        data = request.json
        template_id = data['template_id']
        audio_path = data['audio_path']
        output_path = data['output_path']
        fps = data.get('fps', 25)
        
        # 设置模板目录
        os.environ['TEMPLATE_DIR'] = data.get('template_dir', './wwwroot/templates')
        
        start_time = time.time()
        result_path = musetalk_server.inference(template_id, audio_path, output_path, fps)
        elapsed_time = time.time() - start_time
        
        return jsonify({
            'success': True,
            'output_path': result_path,
            'processing_time': elapsed_time,
            'gpu_count': musetalk_server.gpu_count
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@app.route('/status', methods=['GET'])
def status_endpoint():
    return jsonify({
        'status': 'running',
        'gpu_count': musetalk_server.gpu_count if musetalk_server else 0,
        'templates_loaded': len(musetalk_server.templates) if musetalk_server else 0,
        'initialized': musetalk_server.is_initialized if musetalk_server else False
    })

def main():
    global musetalk_server
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8888, help="服务器端口")
    parser.add_argument("--host", default="127.0.0.1", help="服务器地址")
    parser.add_argument("--config", default="models/musetalk/musetalk.json", help="配置文件路径")
    
    args = parser.parse_args()
    
    print(f"🚀 启动持久化MuseTalk服务器: {args.host}:{args.port}")
    
    # 初始化服务器
    musetalk_server = PersistentMuseTalkServer(args.config)
    
    # 启动Flask服务
    app.run(host=args.host, port=args.port, debug=False, threaded=True)

if __name__ == "__main__":
    main()