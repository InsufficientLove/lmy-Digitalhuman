#!/usr/bin/env python3
"""
Enhanced MuseTalk Preprocessing System
基于MuseTalk官方实时推理机制的优化预处理系统

核心功能：
1. 面部特征预提取（VAE编码、坐标、掩码等）
2. 持久化缓存机制
3. 真正的实时推理支持

作者: Claude Sonnet
版本: 1.0
"""

import os
import cv2
import torch
import numpy as np
import pickle
import json
import glob
from tqdm import tqdm
import time
from pathlib import Path

# MuseTalk组件导入
from musetalk.utils.face_parsing import FaceParsing
from musetalk.utils.preprocessing import get_landmark_and_bbox, read_imgs
from musetalk.utils.blending import get_image_prepare_material, get_image_blending
from musetalk.utils.utils import load_all_model


class EnhancedMuseTalkPreprocessor:
    """
    增强的MuseTalk预处理器
    
    实现真正的面部特征预提取，包括：
    - VAE潜在编码预计算
    - 面部坐标和掩码预提取  
    - 持久化缓存机制
    - 实时推理优化
    """
    
    def __init__(self, 
                 model_config_path="models/musetalk/musetalk.json",
                 model_weights_path="models/musetalk/pytorch_model.bin",
                 vae_type="sd-vae",
                 device="cuda:0",
                 cache_dir="./template_cache"):
        """
        初始化增强预处理器
        
        Args:
            model_config_path: UNet模型配置路径
            model_weights_path: UNet模型权重路径  
            vae_type: VAE类型
            device: 计算设备
            cache_dir: 缓存目录
        """
        self.device = torch.device(device)
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"🚀 初始化增强MuseTalk预处理器...")
        print(f"📱 设备: {self.device}")
        print(f"💾 缓存目录: {self.cache_dir}")
        
        # 加载模型组件
        self._load_models(model_weights_path, vae_type, model_config_path)
        
        # 初始化面部解析器
        self.face_parser = FaceParsing()
        
        print(f"✅ 预处理器初始化完成")
    
    def _load_models(self, model_weights_path, vae_type, model_config_path):
        """加载模型组件"""
        print(f"🔧 加载模型组件...")
        
        # 加载VAE, UNet, PE等组件
        self.vae, self.unet, self.pe = load_all_model(
            unet_model_path=model_weights_path,
            vae_type=vae_type,
            unet_config=model_config_path,
            device=self.device
        )
        
        print(f"✅ 模型组件加载完成")
    
    def preprocess_template(self, 
                          template_id, 
                          template_image_path, 
                          bbox_shift=0,
                          parsing_mode="jaw",
                          force_refresh=False):
        """
        预处理模板，提取并缓存所有面部特征
        
        Args:
            template_id: 模板唯一ID
            template_image_path: 模板图片路径
            bbox_shift: 边界框偏移
            parsing_mode: 面部解析模式  
            force_refresh: 是否强制刷新缓存
            
        Returns:
            dict: 预处理结果信息
        """
        cache_path = self.cache_dir / f"{template_id}_preprocessed.pkl"
        metadata_path = self.cache_dir / f"{template_id}_metadata.json"
        
        # 检查缓存
        if not force_refresh and cache_path.exists() and metadata_path.exists():
            print(f"📦 发现缓存: {template_id}")
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            # 验证缓存完整性
            if self._validate_cache(cache_path, metadata):
                print(f"✅ 缓存有效，跳过预处理: {template_id}")
                return metadata
            else:
                print(f"⚠️ 缓存无效，重新预处理: {template_id}")
        
        print(f"🎯 开始预处理模板: {template_id}")
        start_time = time.time()
        
        # 读取模板图片
        if not os.path.exists(template_image_path):
            raise FileNotFoundError(f"模板图片不存在: {template_image_path}")
        
        template_img = cv2.imread(template_image_path)
        if template_img is None:
            raise ValueError(f"无法读取图片: {template_image_path}")
        
        print(f"📸 模板图片: {template_image_path}, 尺寸: {template_img.shape}")
        
        # 1. 面部检测和坐标提取
        print(f"🔍 提取面部坐标...")
        coord_list, frame_list = get_landmark_and_bbox([template_image_path], bbox_shift)
        
        if not coord_list or coord_list[0] == (0.0, 0.0, 0.0, 0.0):
            raise ValueError(f"未检测到有效面部: {template_image_path}")
        
        bbox = coord_list[0]
        frame = frame_list[0]
        x1, y1, x2, y2 = bbox
        
        print(f"📍 面部坐标: ({x1}, {y1}, {x2}, {y2})")
        
        # 2. VAE潜在编码预计算
        print(f"🧠 计算VAE潜在编码...")
        crop_frame = frame[y1:y2, x1:x2]
        resized_crop_frame = cv2.resize(crop_frame, (256, 256), interpolation=cv2.INTER_LANCZOS4)
        
        with torch.no_grad():
            input_latent = self.vae.get_latents_for_unet(resized_crop_frame)
        
        print(f"💾 VAE编码尺寸: {input_latent.shape}")
        
        # 3. 面部掩码和融合区域预计算
        print(f"🎭 计算面部掩码...")
        mask, mask_crop_box = get_image_prepare_material(
            frame, [x1, y1, x2, y2], 
            fp=self.face_parser, 
            mode=parsing_mode
        )
        
        print(f"🎭 掩码尺寸: {mask.shape}, 融合区域: {mask_crop_box}")
        
        # 4. 创建循环数据（正向+反向，符合MuseTalk官方实现）
        frame_list_cycle = [frame] + [frame][::-1] if len([frame]) > 1 else [frame] * 2
        coord_list_cycle = [bbox] + [bbox][::-1] if len([bbox]) > 1 else [bbox] * 2
        input_latent_list_cycle = [input_latent] + [input_latent][::-1] if len([input_latent]) > 1 else [input_latent] * 2
        mask_list_cycle = [mask] + [mask][::-1] if len([mask]) > 1 else [mask] * 2
        mask_coords_list_cycle = [mask_crop_box] + [mask_crop_box][::-1] if len([mask_crop_box]) > 1 else [mask_crop_box] * 2
        
        # 5. 准备缓存数据
        preprocessed_data = {
            'frame_list_cycle': frame_list_cycle,
            'coord_list_cycle': coord_list_cycle,
            'input_latent_list_cycle': input_latent_list_cycle,
            'mask_list_cycle': mask_list_cycle,
            'mask_coords_list_cycle': mask_coords_list_cycle,
            'original_bbox': bbox,
            'processed_at': time.time()
        }
        
        # 6. 保存缓存
        print(f"💾 保存预处理缓存...")
        with open(cache_path, 'wb') as f:
            pickle.dump(preprocessed_data, f, protocol=pickle.HIGHEST_PROTOCOL)
        
        # 7. 保存元数据
        metadata = {
            'template_id': template_id,
            'template_image_path': template_image_path,
            'bbox_shift': bbox_shift,
            'parsing_mode': parsing_mode,
            'bbox': bbox,
            'processing_time': time.time() - start_time,
            'processed_at': time.time(),
            'cache_path': str(cache_path),
            'frame_count': len(frame_list_cycle),
            'input_latent_shape': list(input_latent.shape),
            'version': '1.0'
        }
        
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        processing_time = time.time() - start_time
        print(f"✅ 模板预处理完成: {template_id}")
        print(f"⏱️ 处理耗时: {processing_time:.2f}秒")
        print(f"📦 缓存大小: {cache_path.stat().st_size / 1024 / 1024:.2f}MB")
        
        return metadata
    
    def _validate_cache(self, cache_path, metadata):
        """验证缓存完整性"""
        try:
            # 检查缓存文件存在且非空
            if not cache_path.exists() or cache_path.stat().st_size == 0:
                return False
            
            # 尝试加载缓存数据
            with open(cache_path, 'rb') as f:
                data = pickle.load(f)
            
            # 检查必要字段
            required_fields = [
                'frame_list_cycle', 'coord_list_cycle', 'input_latent_list_cycle',
                'mask_list_cycle', 'mask_coords_list_cycle'
            ]
            
            for field in required_fields:
                if field not in data:
                    return False
                if not data[field]:  # 检查非空
                    return False
            
            return True
            
        except Exception as e:
            print(f"❌ 缓存验证失败: {e}")
            return False
    
    def load_preprocessed_template(self, template_id):
        """
        加载预处理的模板数据
        
        Args:
            template_id: 模板ID
            
        Returns:
            dict: 预处理数据
        """
        cache_path = self.cache_dir / f"{template_id}_preprocessed.pkl"
        metadata_path = self.cache_dir / f"{template_id}_metadata.json"
        
        if not cache_path.exists():
            raise FileNotFoundError(f"模板缓存不存在: {template_id}")
        
        if not metadata_path.exists():
            raise FileNotFoundError(f"模板元数据不存在: {template_id}")
        
        # 加载元数据
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        # 加载预处理数据
        with open(cache_path, 'rb') as f:
            preprocessed_data = pickle.load(f)
        
        print(f"📦 加载预处理模板: {template_id}")
        print(f"📊 帧数: {len(preprocessed_data['frame_list_cycle'])}")
        print(f"⏱️ 预处理时间: {metadata['processed_at']}")
        
        return preprocessed_data, metadata
    
    def list_cached_templates(self):
        """列出所有缓存的模板"""
        templates = []
        for metadata_file in self.cache_dir.glob("*_metadata.json"):
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                templates.append(metadata)
            except Exception as e:
                print(f"⚠️ 读取元数据失败 {metadata_file}: {e}")
        
        return templates
    
    def clean_cache(self, template_id=None):
        """清理缓存"""
        if template_id:
            # 清理指定模板
            cache_path = self.cache_dir / f"{template_id}_preprocessed.pkl"
            metadata_path = self.cache_dir / f"{template_id}_metadata.json"
            
            for path in [cache_path, metadata_path]:
                if path.exists():
                    path.unlink()
                    print(f"🗑️ 已删除: {path}")
        else:
            # 清理所有缓存
            for file_path in self.cache_dir.glob("*"):
                file_path.unlink()
                print(f"🗑️ 已删除: {file_path}")
    
    def get_cache_info(self):
        """获取缓存信息"""
        templates = self.list_cached_templates()
        total_size = sum(f.stat().st_size for f in self.cache_dir.glob("*"))
        
        return {
            'cache_dir': str(self.cache_dir),
            'template_count': len(templates),
            'total_size_mb': total_size / 1024 / 1024,
            'templates': templates
        }


def main():
    """示例使用"""
    # 初始化预处理器
    preprocessor = EnhancedMuseTalkPreprocessor(
        device="cuda:0",
        cache_dir="./template_cache"
    )
    
    # 示例：预处理模板
    template_id = "xiaoha"
    template_image = "./wwwroot/templates/xiaoha.jpg"
    
    try:
        # 预处理模板
        metadata = preprocessor.preprocess_template(
            template_id=template_id,
            template_image_path=template_image,
            bbox_shift=0,
            parsing_mode="jaw",
            force_refresh=False  # 使用缓存
        )
        
        print(f"✅ 预处理完成: {metadata}")
        
        # 加载预处理数据
        data, meta = preprocessor.load_preprocessed_template(template_id)
        print(f"📦 加载数据成功，帧数: {len(data['frame_list_cycle'])}")
        
        # 显示缓存信息
        cache_info = preprocessor.get_cache_info()
        print(f"💾 缓存信息: {cache_info}")
        
    except Exception as e:
        print(f"❌ 处理失败: {e}")


if __name__ == "__main__":
    main()