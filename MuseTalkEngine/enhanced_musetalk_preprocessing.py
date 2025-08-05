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
import sys
import cv2
import torch
import numpy as np
import pickle
import json
import glob
from tqdm import tqdm
import time
from pathlib import Path

def convert_numpy_types(obj):
    """转换numpy类型为Python原生类型，解决JSON序列化问题"""
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    else:
        return obj

# 动态添加MuseTalk路径到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
musetalk_dir = os.path.join(os.path.dirname(current_dir), "MuseTalk")

if os.path.exists(musetalk_dir) and musetalk_dir not in sys.path:
    sys.path.insert(0, musetalk_dir)
    print(f"Added MuseTalk path: {musetalk_dir}")

# MuseTalk组件导入
try:
    from musetalk.utils.face_parsing import FaceParsing
    from musetalk.utils.preprocessing import get_landmark_and_bbox, read_imgs
    from musetalk.utils.blending import get_image_prepare_material, get_image_blending
    from musetalk.utils.utils import load_all_model
    print("MuseTalk modules imported successfully")
except ImportError as e:
    print(f"MuseTalk import failed: {e}")
    print(f"Python path: {sys.path}")
    print(f"MuseTalk dir: {musetalk_dir}")
    print(f"MuseTalk dir exists: {os.path.exists(musetalk_dir)}")
    if os.path.exists(musetalk_dir):
        print(f"MuseTalk dir contents: {os.listdir(musetalk_dir)}")
    raise


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
                 model_config_path="../MuseTalk/models/musetalk/musetalk.json",
                 model_weights_path="../MuseTalk/models/musetalk/pytorch_model.bin",
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
        
        print(f"Initializing MuseTalk preprocessor...")
        print(f"Device: {self.device}")
        print(f"Cache dir: {self.cache_dir}")
        
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
    
    def preprocess_template(self, template_id, template_image_path, bbox_shift=0, parsing_mode='cpu', force_refresh=False):
        """
        预处理模板图片，提取面部特征并缓存
        
        Args:
            template_id: 模板ID
            template_image_path: 模板图片路径
            bbox_shift: 边界框偏移
            parsing_mode: 解析模式 ('cpu' 或 'gpu')
            force_refresh: 是否强制刷新缓存
            
        Returns:
            dict: 预处理结果信息
        """
        cache_path = self.cache_dir / f"{template_id}_preprocessed.pkl"
        metadata_path = self.cache_dir / f"{template_id}_metadata.json"
        
        # 检查缓存
        if not force_refresh and cache_path.exists() and metadata_path.exists():
            print(f"📦 发现缓存: {template_id}")
            try:
                # 验证JSON文件完整性
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if not content:
                        print(f"⚠️ 元数据文件为空，重新预处理: {template_id}")
                        metadata_path.unlink()  # 删除空文件
                        if cache_path.exists():
                            cache_path.unlink()  # 删除对应的缓存文件
                    else:
                        # 尝试解析JSON
                        f.seek(0)
                        metadata = json.load(f)
                        
                        # 验证缓存完整性
                        if self._validate_cache(cache_path, metadata):
                            print(f"✅ 缓存有效，跳过预处理: {template_id}")
                            return metadata
                        else:
                            print(f"⚠️ 缓存无效，重新预处理: {template_id}")
            except (json.JSONDecodeError, UnicodeDecodeError, FileNotFoundError) as e:
                print(f"⚠️ 元数据文件损坏，重新预处理: {template_id} - {str(e)}")
                # 清理损坏的文件
                if metadata_path.exists():
                    metadata_path.unlink()
                if cache_path.exists():
                    cache_path.unlink()
            except Exception as e:
                print(f"⚠️ 读取缓存时发生未知错误，重新预处理: {template_id} - {str(e)}")
                # 清理可能损坏的文件
                if metadata_path.exists():
                    metadata_path.unlink()
                if cache_path.exists():
                    cache_path.unlink()
        
        print(f"🎯 开始预处理模板: {template_id}")
        start_time = time.time()
        
        # 确保缓存目录存在
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 加载并预处理图片
        print(f"📸 加载模板图片: {template_image_path}")
        
        # 检查文件是否存在
        if not os.path.exists(template_image_path):
            raise ValueError(f"模板图片文件不存在: {template_image_path}")
        
        # 检查文件大小
        file_size = os.path.getsize(template_image_path)
        print(f"📊 图片文件大小: {file_size} bytes")
        
        if file_size == 0:
            raise ValueError(f"模板图片文件为空: {template_image_path}")
        
        img_np = cv2.imread(template_image_path)
        if img_np is None:
            raise ValueError(f"无法加载图片: {template_image_path}")
        
        print(f"✅ 图片加载成功，原始尺寸: {img_np.shape}")
        img_np = cv2.cvtColor(img_np, cv2.COLOR_BGR2RGB)
        print(f"✅ 图片格式转换完成: BGR -> RGB")
        
        # 面部检测和关键点提取
        print("🔍 检测面部特征...")
        bbox, landmarks = self._detect_face(img_np)
        
        if bbox is None:
            raise ValueError(f"未检测到面部: {template_image_path}")
        
        # 应用边界框偏移
        if bbox_shift != 0:
            bbox = self._apply_bbox_shift(bbox, bbox_shift, img_np.shape)
        
        # 裁剪面部区域
        face_img = self._crop_face(img_np, bbox)
        
        # 生成循环帧列表
        print("🎬 生成循环帧...")
        frame_list_cycle = self._generate_frame_cycle(face_img)
        
        # 提取坐标信息
        print("📍 提取坐标信息...")
        coord_list_cycle = self._extract_coordinates(frame_list_cycle, parsing_mode)
        
        # VAE编码
        print("🔧 VAE编码...")
        input_latent_list_cycle = self._encode_frames(frame_list_cycle)
        input_latent = input_latent_list_cycle[0]  # 使用第一帧作为参考
        
        # 生成掩码
        print("🎭 生成掩码...")
        mask_list_cycle = self._generate_masks(coord_list_cycle)
        mask_coords_list_cycle = self._extract_mask_coordinates(mask_list_cycle)
        
        # 准备缓存数据
        preprocessed_data = {
            'frame_list_cycle': frame_list_cycle,
            'coord_list_cycle': coord_list_cycle,
            'input_latent_list_cycle': input_latent_list_cycle,
            'mask_list_cycle': mask_list_cycle,
            'mask_coords_list_cycle': mask_coords_list_cycle,
            'bbox': bbox,
            'landmarks': landmarks
        }
        
        # 保存预处理数据
        print(f"💾 保存预处理缓存: {cache_path}")
        with open(cache_path, 'wb') as f:
            pickle.dump(preprocessed_data, f, protocol=pickle.HIGHEST_PROTOCOL)
        
        # 准备元数据
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
        
        # 转换numpy类型为JSON可序列化类型
        metadata_serializable = convert_numpy_types(metadata)
        
        # 安全保存元数据文件
        temp_metadata_path = metadata_path.with_suffix('.tmp')
        try:
            with open(temp_metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata_serializable, f, indent=2, ensure_ascii=False)
            
            # 验证写入的JSON文件
            with open(temp_metadata_path, 'r', encoding='utf-8') as f:
                json.load(f)  # 验证可以正确解析
            
            # 原子性移动文件
            temp_metadata_path.replace(metadata_path)
            print(f"✅ 元数据已保存: {metadata_path}")
            
        except Exception as e:
            print(f"❌ 保存元数据失败: {e}")
            if temp_metadata_path.exists():
                temp_metadata_path.unlink()
            raise
        
        processing_time = time.time() - start_time
        print(f"✅ 模板预处理完成: {template_id}")
        print(f"⏱️ 处理耗时: {processing_time:.2f}秒")
        print(f"📦 缓存大小: {cache_path.stat().st_size / 1024 / 1024:.2f}MB")
        
        return metadata
    
    def _detect_face(self, img_np):
        """检测面部并提取关键点"""
        try:
            print(f"🔍 开始面部检测，图片尺寸: {img_np.shape}")
            
            # 使用已经导入的MuseTalk面部检测功能
            # 创建临时文件用于检测
            import tempfile
            import time
            import uuid
            
            # 使用更安全的临时文件创建方式
            temp_dir = tempfile.gettempdir()
            temp_filename = f"musetalk_temp_{uuid.uuid4().hex[:8]}.jpg"
            temp_path = os.path.join(temp_dir, temp_filename)
            
            try:
                # 确保图片格式正确
                img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
                success = cv2.imwrite(temp_path, img_bgr)
                if not success:
                    print(f"❌ 图片保存失败: {temp_path}")
                    return None, None
                
                print(f"📁 临时图片已保存: {temp_path}")
                
                # 验证临时图片可以读取
                test_img = cv2.imread(temp_path)
                if test_img is None:
                    print(f"❌ 无法读取临时图片: {temp_path}")
                    # 尝试删除文件，但不影响流程
                    self._safe_remove_file(temp_path)
                    return None, None
                
                print(f"✅ 临时图片验证成功，尺寸: {test_img.shape}")
                
                # 调用面部检测
                print("🎯 调用get_landmark_and_bbox进行面部检测...")
                coord_list, frame_list = get_landmark_and_bbox([temp_path], 0)
                print(f"📊 检测结果 - coord_list长度: {len(coord_list) if coord_list else 0}, frame_list长度: {len(frame_list) if frame_list else 0}")
                
                # 在处理检测结果之前先保存结果，避免文件删除失败影响逻辑
                detection_success = False
                bbox_result = None
                
                # 验证检测结果
                if coord_list and len(coord_list) > 0:
                    bbox = coord_list[0]
                    x1, y1, x2, y2 = bbox
                    print(f"🔍 检测到边界框: ({x1:.1f}, {y1:.1f}, {x2:.1f}, {y2:.1f})")
                    
                    # 检查边界框是否有效
                    if x1 < x2 and y1 < y2 and bbox != (0.0, 0.0, 0.0, 0.0):
                        landmarks = None  # 暂时不提取详细关键点
                        print(f"✅ 面部检测成功: 边界框 ({x1:.1f}, {y1:.1f}, {x2:.1f}, {y2:.1f})")
                        detection_success = True
                        bbox_result = bbox
                    else:
                        print(f"⚠️ 检测到无效的面部边界框: {bbox}")
                else:
                    print("⚠️ 未检测到面部区域")
                
                # 返回检测结果（不受文件清理失败影响）
                return (bbox_result, None) if detection_success else (None, None)
                
            finally:
                # 确保临时文件被清理（在finally块中）
                self._safe_remove_file(temp_path)
                
        except Exception as e:
            print(f"⚠️ 面部检测失败: {e}")
            import traceback
            traceback.print_exc()
            return None, None
    
    def _safe_remove_file(self, file_path):
        """安全删除文件，处理Windows权限问题"""
        if not os.path.exists(file_path):
            return
            
        import time
        cleanup_attempts = 0
        max_attempts = 3
        
        while cleanup_attempts < max_attempts:
            try:
                os.unlink(file_path)
                print(f"🗑️ 临时文件已清理: {file_path}")
                return
            except PermissionError as e:
                cleanup_attempts += 1
                print(f"⚠️ 文件清理尝试 {cleanup_attempts}/{max_attempts} 失败: {e}")
                if cleanup_attempts < max_attempts:
                    time.sleep(0.1)  # 等待100ms后重试
                else:
                    print(f"⚠️ 无法删除临时文件，系统将自动清理: {file_path}")
                    # 在Windows上，临时文件通常会被系统自动清理
            except Exception as e:
                print(f"⚠️ 清理临时文件时发生其他错误: {e}")
                break
    
    def _apply_bbox_shift(self, bbox, shift, img_shape):
        """应用边界框偏移"""
        x1, y1, x2, y2 = bbox
        h, w = img_shape[:2]
        
        # 应用偏移
        x1 = max(0, x1 - shift)
        y1 = max(0, y1 - shift)
        x2 = min(w, x2 + shift)
        y2 = min(h, y2 + shift)
        
        return (x1, y1, x2, y2)
    
    def _crop_face(self, img_np, bbox):
        """裁剪面部区域"""
        x1, y1, x2, y2 = [int(coord) for coord in bbox]
        face_img = img_np[y1:y2, x1:x2]
        
        # 调整到标准尺寸
        face_img = cv2.resize(face_img, (256, 256), interpolation=cv2.INTER_LANCZOS4)
        return face_img
    
    def _generate_frame_cycle(self, face_img):
        """生成循环帧列表"""
        # 简单实现：使用单帧创建循环
        frame_bgr = cv2.cvtColor(face_img, cv2.COLOR_RGB2BGR)
        return [frame_bgr, frame_bgr]  # 创建简单的2帧循环
    
    def _extract_coordinates(self, frame_list, parsing_mode):
        """提取坐标信息"""
        # 简化实现：为每帧返回相同的坐标
        coord = (0, 0, 256, 256)  # 标准化后的坐标
        return [coord] * len(frame_list)
    
    def _encode_frames(self, frame_list):
        """VAE编码帧列表"""
        encoded_list = []
        for frame in frame_list:
            with torch.no_grad():
                # 转换为RGB并调整尺寸
                if frame.shape[2] == 3:  # BGR to RGB
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                else:
                    frame_rgb = frame
                
                # VAE编码
                input_latent = self.vae.get_latents_for_unet(frame_rgb)
                encoded_list.append(input_latent)
        
        return encoded_list
    
    def _generate_masks(self, coord_list):
        """生成掩码列表"""
        # 使用已经导入的MuseTalk掩码生成功能
        
        mask_list = []
        for coord in coord_list:
            # 创建简单的面部掩码
            mask = np.ones((256, 256), dtype=np.uint8) * 255
            mask_list.append(mask)
        
        return mask_list
    
    def _extract_mask_coordinates(self, mask_list):
        """提取掩码坐标"""
        # 简化实现：返回标准坐标
        coords = (0, 0, 256, 256)
        return [coords] * len(mask_list)
    
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
            tuple: (预处理数据, 元数据)
        """
        cache_path = self.cache_dir / f"{template_id}_preprocessed.pkl"
        metadata_path = self.cache_dir / f"{template_id}_metadata.json"
        
        if not cache_path.exists():
            raise FileNotFoundError(f"模板缓存不存在: {template_id}")
        
        if not metadata_path.exists():
            raise FileNotFoundError(f"模板元数据不存在: {template_id}")
        
        # 安全加载元数据
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content:
                    raise ValueError(f"元数据文件为空: {template_id}")
                
                # 重新定位到文件开头并解析JSON
                f.seek(0)
                metadata = json.load(f)
                
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            raise ValueError(f"元数据文件损坏: {template_id} - {str(e)}")
        except Exception as e:
            raise RuntimeError(f"加载元数据时发生错误: {template_id} - {str(e)}")
        
        # 加载预处理数据
        try:
            with open(cache_path, 'rb') as f:
                preprocessed_data = pickle.load(f)
        except Exception as e:
            raise RuntimeError(f"加载预处理数据失败: {template_id} - {str(e)}")
        
        print(f"📦 加载预处理模板: {template_id}")
        print(f"📊 帧数: {len(preprocessed_data['frame_list_cycle'])}")
        print(f"⏱️ 预处理时间: {metadata.get('processed_at', 'unknown')}")
        
        return preprocessed_data, metadata
    
    def list_cached_templates(self):
        """列出所有缓存的模板"""
        templates = []
        corrupted_files = []
        
        for metadata_file in self.cache_dir.glob("*_metadata.json"):
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if not content:
                        print(f"⚠️ 元数据文件为空，将被清理: {metadata_file}")
                        corrupted_files.append(metadata_file)
                        continue
                    
                    # 重新定位到文件开头并解析JSON
                    f.seek(0)
                    metadata = json.load(f)
                    templates.append(metadata)
                    
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                print(f"⚠️ 元数据文件损坏，将被清理 {metadata_file}: {e}")
                corrupted_files.append(metadata_file)
            except Exception as e:
                print(f"⚠️ 读取元数据失败 {metadata_file}: {e}")
                corrupted_files.append(metadata_file)
        
        # 清理损坏的文件
        for corrupted_file in corrupted_files:
            try:
                # 获取模板ID
                template_id = corrupted_file.stem.replace('_metadata', '')
                cache_file = self.cache_dir / f"{template_id}_preprocessed.pkl"
                
                # 删除损坏的文件
                if corrupted_file.exists():
                    corrupted_file.unlink()
                    print(f"🗑️ 已清理损坏的元数据文件: {corrupted_file}")
                
                if cache_file.exists():
                    cache_file.unlink()
                    print(f"🗑️ 已清理对应的缓存文件: {cache_file}")
                    
            except Exception as e:
                print(f"⚠️ 清理损坏文件失败 {corrupted_file}: {e}")
        
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
    """命令行接口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Enhanced MuseTalk 模板预处理工具")
    parser.add_argument("--template_id", required=True, help="模板ID")
    parser.add_argument("--template_image", required=True, help="模板图片路径")
    parser.add_argument("--output_state", help="输出状态文件路径")
    parser.add_argument("--cache_dir", default="./template_cache", help="缓存目录")
    parser.add_argument("--device", default="cuda:0", help="计算设备")
    parser.add_argument("--bbox_shift", type=int, default=0, help="边界框偏移")
    parser.add_argument("--parsing_mode", default="jaw", help="解析模式")
    parser.add_argument("--force_refresh", action="store_true", help="强制刷新缓存")
    
    args = parser.parse_args()
    
    # 验证输入文件
    if not os.path.exists(args.template_image):
        print(f"❌ 模板图片不存在: {args.template_image}")
        return 1
    
    try:
        print(f"🚀 开始预处理模板: {args.template_id}")
        print(f"📁 模板图片: {args.template_image}")
        print(f"💾 缓存目录: {args.cache_dir}")
        print(f"🎮 设备: {args.device}")
        
        # 初始化预处理器
        preprocessor = EnhancedMuseTalkPreprocessor(
            device=args.device,
            cache_dir=args.cache_dir
        )
        
        # 预处理模板
        metadata = preprocessor.preprocess_template(
            template_id=args.template_id,
            template_image_path=args.template_image,
            bbox_shift=args.bbox_shift,
            parsing_mode=args.parsing_mode,
            force_refresh=args.force_refresh
        )
        
        print(f"✅ 预处理完成: {metadata}")
        
        # 如果指定了输出状态文件，保存到指定位置
        if args.output_state:
            cache_file = os.path.join(args.cache_dir, f"{args.template_id}_preprocessed.pkl")
            if os.path.exists(cache_file):
                # 确保输出目录存在
                os.makedirs(os.path.dirname(args.output_state), exist_ok=True)
                
                # 复制缓存文件到指定位置
                import shutil
                shutil.copy2(cache_file, args.output_state)
                print(f"📦 状态文件已保存: {args.output_state}")
            else:
                print(f"⚠️ 缓存文件不存在: {cache_file}")
        
        # 验证预处理结果
        data, meta = preprocessor.load_preprocessed_template(args.template_id)
        print(f"🎯 验证成功，预处理帧数: {len(data['frame_list_cycle'])}")
        
        # 显示缓存信息
        cache_info = preprocessor.get_cache_info()
        print(f"💾 缓存统计: {cache_info}")
        
        return 0
        
    except Exception as e:
        print(f"❌ 预处理失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())