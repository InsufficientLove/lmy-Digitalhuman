#!/usr/bin/env python3
"""
Integrated MuseTalk Service
集成的MuseTalk服务

提供两个主要功能：
1. 模板预处理服务 - 创建和缓存面部特征
2. 超高速实时推理服务 - 基于缓存的极速推理

与C#服务完全兼容，支持原有的API接口

作者: Claude Sonnet
版本: 2.0
"""

import os
import sys
import argparse
import json
import time
from pathlib import Path

# 导入新的组件
from enhanced_musetalk_preprocessing import EnhancedMuseTalkPreprocessor
from ultra_fast_realtime_inference import UltraFastRealtimeInference


class IntegratedMuseTalkService:
    """
    集成的MuseTalk服务
    
    结合预处理和实时推理功能，提供完整的数字人视频生成服务
    """
    
    def __init__(self, 
                 model_config_path="models/musetalk/musetalk.json",
                 model_weights_path="models/musetalk/pytorch_model.bin",
                 vae_type="sd-vae",
                 whisper_dir="models/whisper",
                 device="cuda:0",
                 cache_dir="./template_cache",
                 batch_size=32,
                 fp16=True):
        """
        初始化集成服务
        
        Args:
            model_config_path: UNet配置路径
            model_weights_path: UNet权重路径
            vae_type: VAE类型
            whisper_dir: Whisper模型目录
            device: 计算设备
            cache_dir: 缓存目录
            batch_size: 批处理大小
            fp16: 是否使用半精度
        """
        self.device = device
        self.cache_dir = Path(cache_dir)
        self.batch_size = batch_size
        
        print(f"🚀 初始化集成MuseTalk服务...")
        print(f"📱 设备: {device}")
        print(f"💾 缓存目录: {cache_dir}")
        
        # 初始化预处理器
        self.preprocessor = EnhancedMuseTalkPreprocessor(
            model_config_path=model_config_path,
            model_weights_path=model_weights_path,
            vae_type=vae_type,
            device=device,
            cache_dir=cache_dir
        )
        
        # 初始化实时推理系统
        self.inference_system = UltraFastRealtimeInference(
            model_config_path=model_config_path,
            model_weights_path=model_weights_path,
            vae_type=vae_type,
            whisper_dir=whisper_dir,
            device=device,
            cache_dir=cache_dir,
            batch_size=batch_size,
            fp16=fp16
        )
        
        print(f"✅ 集成服务初始化完成")
    
    def preprocess_template(self, 
                          template_id, 
                          template_image_path, 
                          bbox_shift=0,
                          parsing_mode="jaw",
                          force_refresh=False):
        """
        预处理模板服务
        
        Args:
            template_id: 模板唯一ID
            template_image_path: 模板图片路径
            bbox_shift: 边界框偏移
            parsing_mode: 面部解析模式
            force_refresh: 是否强制刷新缓存
            
        Returns:
            dict: 预处理结果
        """
        print(f"🎯 模板预处理服务")
        print(f"📋 模板ID: {template_id}")
        print(f"📸 图片路径: {template_image_path}")
        
        try:
            # 执行预处理
            metadata = self.preprocessor.preprocess_template(
                template_id=template_id,
                template_image_path=template_image_path,
                bbox_shift=bbox_shift,
                parsing_mode=parsing_mode,
                force_refresh=force_refresh
            )
            
            result = {
                'success': True,
                'template_id': template_id,
                'metadata': metadata,
                'message': f'模板 {template_id} 预处理完成'
            }
            
            print(f"✅ 预处理成功: {template_id}")
            return result
            
        except Exception as e:
            error_msg = f"预处理失败: {str(e)}"
            print(f"❌ {error_msg}")
            
            result = {
                'success': False,
                'template_id': template_id,
                'error': error_msg,
                'message': f'模板 {template_id} 预处理失败'
            }
            return result
    
    def realtime_inference(self, 
                         template_id, 
                         audio_path, 
                         output_path,
                         fps=25):
        """
        实时推理服务
        
        Args:
            template_id: 模板ID
            audio_path: 音频文件路径
            output_path: 输出视频路径
            fps: 帧率
            
        Returns:
            dict: 推理结果
        """
        print(f"⚡ 实时推理服务")
        print(f"🎭 模板ID: {template_id}")
        print(f"🎵 音频文件: {audio_path}")
        print(f"📹 输出路径: {output_path}")
        
        start_time = time.time()
        
        try:
            # 执行超高速推理
            result_path = self.inference_system.ultra_fast_inference(
                template_id=template_id,
                audio_path=audio_path,
                output_path=output_path,
                fps=fps,
                save_frames=True
            )
            
            total_time = time.time() - start_time
            
            result = {
                'success': True,
                'template_id': template_id,
                'audio_path': audio_path,
                'output_path': result_path,
                'processing_time': total_time,
                'fps': fps,
                'message': f'推理完成，耗时 {total_time:.2f}秒'
            }
            
            print(f"✅ 推理成功: {result_path}")
            return result
            
        except Exception as e:
            error_msg = f"推理失败: {str(e)}"
            print(f"❌ {error_msg}")
            
            result = {
                'success': False,
                'template_id': template_id,
                'audio_path': audio_path,
                'error': error_msg,
                'processing_time': time.time() - start_time,
                'message': f'推理失败'
            }
            return result
    
    def check_template_cache(self, template_id):
        """
        检查模板缓存状态
        
        Args:
            template_id: 模板ID
            
        Returns:
            dict: 缓存状态信息
        """
        cache_path = self.cache_dir / f"{template_id}_preprocessed.pkl"
        metadata_path = self.cache_dir / f"{template_id}_metadata.json"
        
        exists = cache_path.exists() and metadata_path.exists()
        
        if exists:
            try:
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                
                return {
                    'exists': True,
                    'template_id': template_id,
                    'metadata': metadata,
                    'cache_size_mb': cache_path.stat().st_size / 1024 / 1024,
                    'message': f'缓存存在: {template_id}'
                }
            except Exception as e:
                return {
                    'exists': False,
                    'template_id': template_id,
                    'error': str(e),
                    'message': f'缓存损坏: {template_id}'
                }
        else:
            return {
                'exists': False,
                'template_id': template_id,
                'message': f'缓存不存在: {template_id}'
            }
    
    def get_service_info(self):
        """获取服务信息"""
        cache_info = self.preprocessor.get_cache_info()
        
        return {
            'service_name': 'IntegratedMuseTalkService',
            'version': '2.0',
            'device': str(self.device),
            'cache_dir': str(self.cache_dir),
            'batch_size': self.batch_size,
            'cache_info': cache_info,
            'capabilities': [
                'template_preprocessing',
                'realtime_inference', 
                'cache_management',
                'performance_optimization'
            ]
        }


def main():
    """命令行界面"""
    parser = argparse.ArgumentParser(description="集成MuseTalk服务")
    
    # 服务类型
    service_group = parser.add_mutually_exclusive_group(required=True)
    service_group.add_argument("--preprocess", action="store_true", help="预处理模式")
    service_group.add_argument("--inference", action="store_true", help="推理模式")
    service_group.add_argument("--check_cache", action="store_true", help="检查缓存模式")
    service_group.add_argument("--service_info", action="store_true", help="服务信息模式")
    
    # 共同参数
    parser.add_argument("--template_id", help="模板ID")
    parser.add_argument("--device", default="cuda:0", help="计算设备")
    parser.add_argument("--cache_dir", default="./template_cache", help="缓存目录")
    parser.add_argument("--batch_size", type=int, default=32, help="批处理大小")
    parser.add_argument("--fp16", action="store_true", default=True, help="使用半精度")
    
    # 预处理参数
    parser.add_argument("--template_image_path", help="模板图片路径")
    parser.add_argument("--bbox_shift", type=int, default=0, help="边界框偏移")
    parser.add_argument("--parsing_mode", default="jaw", help="面部解析模式")
    parser.add_argument("--force_refresh", action="store_true", help="强制刷新缓存")
    
    # 推理参数
    parser.add_argument("--audio_path", help="音频文件路径")
    parser.add_argument("--output_path", help="输出视频路径")
    parser.add_argument("--fps", type=int, default=25, help="视频帧率")
    
    # 模型参数
    parser.add_argument("--unet_config", default="models/musetalk/musetalk.json", help="UNet配置路径")
    parser.add_argument("--unet_model_path", default="models/musetalk/pytorch_model.bin", help="UNet权重路径")
    parser.add_argument("--vae_type", default="sd-vae", help="VAE类型")
    parser.add_argument("--whisper_dir", default="models/whisper", help="Whisper模型目录")
    
    args = parser.parse_args()
    
    # 初始化服务
    service = IntegratedMuseTalkService(
        model_config_path=args.unet_config,
        model_weights_path=args.unet_model_path,
        vae_type=args.vae_type,
        whisper_dir=args.whisper_dir,
        device=args.device,
        cache_dir=args.cache_dir,
        batch_size=args.batch_size,
        fp16=args.fp16
    )
    
    # 执行对应服务
    if args.preprocess:
        if not args.template_id or not args.template_image_path:
            print("❌ 预处理模式需要指定 --template_id 和 --template_image_path")
            sys.exit(1)
        
        result = service.preprocess_template(
            template_id=args.template_id,
            template_image_path=args.template_image_path,
            bbox_shift=args.bbox_shift,
            parsing_mode=args.parsing_mode,
            force_refresh=args.force_refresh
        )
        
    elif args.inference:
        if not args.template_id or not args.audio_path or not args.output_path:
            print("❌ 推理模式需要指定 --template_id, --audio_path 和 --output_path")
            sys.exit(1)
        
        result = service.realtime_inference(
            template_id=args.template_id,
            audio_path=args.audio_path,
            output_path=args.output_path,
            fps=args.fps
        )
        
    elif args.check_cache:
        if not args.template_id:
            print("❌ 检查缓存模式需要指定 --template_id")
            sys.exit(1)
        
        result = service.check_template_cache(args.template_id)
        
    elif args.service_info:
        result = service.get_service_info()
    
    # 输出结果
    print("\n" + "="*50)
    print("📊 服务执行结果:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # 退出状态码
    if 'success' in result:
        sys.exit(0 if result['success'] else 1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()