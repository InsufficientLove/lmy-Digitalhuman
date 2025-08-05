#!/usr/bin/env python3
"""
Enhanced MuseTalk Inference V4
增强版MuseTalk推理 V4

完全兼容原有C#服务接口，内部使用新的预处理和超高速推理系统
自动检测是否有预处理缓存，没有则先创建缓存再推理

作者: Claude Sonnet  
版本: 4.0
兼容: C# MuseTalk服务
"""

import os
import sys
import argparse
import time
import traceback
from pathlib import Path

# 导入新的增强系统
try:
    from enhanced_musetalk_preprocessing import EnhancedMuseTalkPreprocessor
    from ultra_fast_realtime_inference import UltraFastRealtimeInference
    NEW_SYSTEM_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ 新系统导入失败，回退到传统模式: {e}")
    NEW_SYSTEM_AVAILABLE = False

# 回退导入（兼容性）
if not NEW_SYSTEM_AVAILABLE:
    try:
        # 这里可以导入原有的推理系统作为回退
        from optimized_musetalk_inference_v3 import TrueParallelMuseTalkInference
    except ImportError:
        print("❌ 无法导入任何推理系统")
        sys.exit(1)


class EnhancedMuseTalkInferenceV4:
    """
    增强版MuseTalk推理 V4
    
    特点：
    - 完全兼容C#服务参数接口
    - 自动预处理缓存管理
    - 超高速实时推理
    - 智能回退机制
    """
    
    def __init__(self, 
                 unet_config="../MuseTalk/models/musetalk/musetalk.json",
                 unet_model_path="../MuseTalk/models/musetalk/pytorch_model.bin",
                 vae_type="sd-vae",
                 whisper_dir="../MuseTalk/models/whisper",
                 device="cuda:0",
                 cache_dir="./model_states",
                 batch_size=32,
                 fp16=True):
        """
        初始化V4推理器
        
        Args:
            unet_config: UNet配置路径
            unet_model_path: UNet模型路径
            vae_type: VAE类型
            whisper_dir: Whisper目录
            device: 计算设备
            cache_dir: 缓存目录
            batch_size: 批处理大小
            fp16: 半精度
        """
        self.device = device
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"🚀 初始化增强MuseTalk推理器 V4")
        print(f"📱 设备: {device}")
        print(f"💾 缓存目录: {cache_dir}")
        print(f"🔧 新系统可用: {NEW_SYSTEM_AVAILABLE}")
        
        if NEW_SYSTEM_AVAILABLE:
            # 使用新的增强系统
            try:
                self.preprocessor = EnhancedMuseTalkPreprocessor(
                    model_config_path=unet_config,
                    model_weights_path=unet_model_path,
                    vae_type=vae_type,
                    device=device,
                    cache_dir=cache_dir
                )
                
                self.inference_system = UltraFastRealtimeInference(
                    model_config_path=unet_config,
                    model_weights_path=unet_model_path,
                    vae_type=vae_type,
                    whisper_dir=whisper_dir,
                    device=device,
                    cache_dir=cache_dir,
                    batch_size=batch_size,
                    fp16=fp16
                )
                
                self.use_enhanced_system = True
                print(f"✅ 增强系统初始化完成")
                
            except Exception as e:
                print(f"❌ 增强系统初始化失败，回退到传统模式: {e}")
                self.use_enhanced_system = False
                self._init_legacy_system(unet_config, unet_model_path, vae_type, device, batch_size)
        else:
            self.use_enhanced_system = False
            self._init_legacy_system(unet_config, unet_model_path, vae_type, device, batch_size)
    
    def _init_legacy_system(self, unet_config, unet_model_path, vae_type, device, batch_size):
        """初始化传统系统（回退模式）"""
        print(f"🔄 初始化传统推理系统...")
        # 这里可以初始化原有的推理系统
        self.legacy_inference = None  # 实际项目中替换为真实的传统推理器
        print(f"✅ 传统系统初始化完成")
    
    def ensure_template_preprocessed(self, template_id, template_image_path, bbox_shift=0, parsing_mode="jaw"):
        """
        确保模板已预处理
        
        Args:
            template_id: 模板ID
            template_image_path: 模板图片路径
            bbox_shift: 边界框偏移
            parsing_mode: 解析模式
            
        Returns:
            bool: 是否成功
        """
        if not self.use_enhanced_system:
            return True  # 传统系统不需要预处理
        
        try:
            # 检查缓存是否存在
            cache_path = self.cache_dir / f"{template_id}_preprocessed.pkl"
            metadata_path = self.cache_dir / f"{template_id}_metadata.json"
            
            if cache_path.exists() and metadata_path.exists():
                print(f"📦 发现预处理缓存: {template_id}")
                return True
            
            # 缓存不存在，执行预处理
            print(f"🎯 开始预处理模板: {template_id}")
            
            # 查找模板图片路径
            if not template_image_path or not os.path.exists(template_image_path):
                # 尝试自动查找
                template_image_path = self._find_template_image(template_id)
                if not template_image_path:
                    raise FileNotFoundError(f"模板图片未找到: {template_id}")
            
            # 执行预处理
            metadata = self.preprocessor.preprocess_template(
                template_id=template_id,
                template_image_path=template_image_path,
                bbox_shift=bbox_shift,
                parsing_mode=parsing_mode,
                force_refresh=False
            )
            
            print(f"✅ 模板预处理完成: {template_id}")
            return True
            
        except Exception as e:
            print(f"❌ 模板预处理失败: {template_id}, 错误: {e}")
            traceback.print_exc()
            return False
    
    def _find_template_image(self, template_id):
        """自动查找模板图片"""
        possible_dirs = [
            "./wwwroot/templates",
            "./templates", 
            f"./model_states/{template_id}",
            "."
        ]
        
        possible_extensions = [".jpg", ".jpeg", ".png", ".bmp"]
        
        for directory in possible_dirs:
            if not os.path.exists(directory):
                continue
                
            for ext in possible_extensions:
                image_path = os.path.join(directory, f"{template_id}{ext}")
                if os.path.exists(image_path):
                    print(f"🔍 找到模板图片: {image_path}")
                    return image_path
        
        return None
    
    def generate_video(self, 
                      template_id, 
                      audio_path, 
                      output_path,
                      template_dir="./wwwroot/templates",
                      fps=25,
                      batch_size=None,
                      bbox_shift=0,
                      parsing_mode="jaw"):
        """
        生成数字人视频（主入口，兼容C#服务接口）
        
        Args:
            template_id: 模板ID
            audio_path: 音频路径
            output_path: 输出路径
            template_dir: 模板目录
            fps: 帧率
            batch_size: 批处理大小（可选）
            bbox_shift: 边界框偏移
            parsing_mode: 解析模式
            
        Returns:
            str: 输出视频路径
        """
        print(f"🎬 开始生成数字人视频")
        print(f"🎭 模板: {template_id}")
        print(f"🎵 音频: {audio_path}")
        print(f"📹 输出: {output_path}")
        print(f"⚡ 使用增强系统: {self.use_enhanced_system}")
        
        total_start_time = time.time()
        
        try:
            # 构造模板图片路径
            template_image_path = self._find_template_in_dir(template_id, template_dir)
            
            if self.use_enhanced_system:
                # 使用增强系统
                return self._generate_with_enhanced_system(
                    template_id, template_image_path, audio_path, output_path, 
                    fps, bbox_shift, parsing_mode
                )
            else:
                # 使用传统系统
                return self._generate_with_legacy_system(
                    template_id, template_image_path, audio_path, output_path, fps
                )
                
        except Exception as e:
            print(f"❌ 视频生成失败: {e}")
            traceback.print_exc()
            raise
        
        finally:
            total_time = time.time() - total_start_time
            print(f"⏱️ 总耗时: {total_time:.2f}秒")
    
    def _find_template_in_dir(self, template_id, template_dir):
        """在指定目录查找模板图片"""
        extensions = ['.jpg', '.jpeg', '.png', '.bmp']
        
        for ext in extensions:
            path = os.path.join(template_dir, f"{template_id}{ext}")
            if os.path.exists(path):
                return path
        
        raise FileNotFoundError(f"模板图片未找到: {template_id} in {template_dir}")
    
    def _generate_with_enhanced_system(self, template_id, template_image_path, audio_path, output_path, fps, bbox_shift, parsing_mode):
        """使用增强系统生成视频"""
        print(f"⚡ 使用增强系统生成视频")
        
        # 1. 确保模板已预处理
        if not self.ensure_template_preprocessed(template_id, template_image_path, bbox_shift, parsing_mode):
            raise RuntimeError(f"模板预处理失败: {template_id}")
        
        # 2. 执行超高速推理
        result_path = self.inference_system.ultra_fast_inference(
            template_id=template_id,
            audio_path=audio_path,
            output_path=output_path,
            fps=fps,
            save_frames=True
        )
        
        return result_path
    
    def _generate_with_legacy_system(self, template_id, template_image_path, audio_path, output_path, fps):
        """使用传统系统生成视频"""
        print(f"🔄 使用传统系统生成视频")
        
        # 这里调用原有的推理逻辑
        # 实际项目中替换为真实的传统推理调用
        print(f"⚠️ 传统系统暂未实现，请使用增强系统")
        raise NotImplementedError("传统系统推理暂未实现")


def main():
    """主入口函数，完全兼容C#服务参数"""
    parser = argparse.ArgumentParser(description="Enhanced MuseTalk Inference V4")
    
    # 核心参数（兼容C#服务）
    parser.add_argument("--template_id", required=True, help="模板ID")
    parser.add_argument("--audio_path", required=True, help="音频文件路径")
    parser.add_argument("--output_path", required=True, help="输出视频路径")
    parser.add_argument("--template_dir", default="./wwwroot/templates", help="模板目录")
    parser.add_argument("--fps", type=int, default=25, help="视频帧率")
    parser.add_argument("--batch_size", type=int, default=32, help="批处理大小")
    
    # 模型参数
    parser.add_argument("--unet_config", default="../MuseTalk/models/musetalk/musetalk.json", help="UNet配置路径")
    parser.add_argument("--unet_model_path", default="../MuseTalk/models/musetalk/pytorch_model.bin", help="UNet模型路径")
    parser.add_argument("--vae_type", default="sd-vae", help="VAE类型")
    parser.add_argument("--whisper_dir", default="../MuseTalk/models/whisper", help="Whisper目录")
    
    # 高级参数
    parser.add_argument("--device", default="cuda:0", help="计算设备")
    parser.add_argument("--cache_dir", default="./model_states", help="缓存目录")
    parser.add_argument("--bbox_shift", type=int, default=0, help="边界框偏移")
    parser.add_argument("--parsing_mode", default="jaw", help="面部解析模式")
    parser.add_argument("--fp16", action="store_true", default=True, help="使用半精度")
    
    # 兼容性参数（忽略但不报错）
    parser.add_argument("--version", default="v4", help="版本（兼容参数）")
    
    args = parser.parse_args()
    
    try:
        # 初始化推理器
        inference_system = EnhancedMuseTalkInferenceV4(
            unet_config=args.unet_config,
            unet_model_path=args.unet_model_path,
            vae_type=args.vae_type,
            whisper_dir=args.whisper_dir,
            device=args.device,
            cache_dir=args.cache_dir,
            batch_size=args.batch_size,
            fp16=args.fp16
        )
        
        # 生成视频
        result_path = inference_system.generate_video(
            template_id=args.template_id,
            audio_path=args.audio_path,
            output_path=args.output_path,
            template_dir=args.template_dir,
            fps=args.fps,
            batch_size=args.batch_size,
            bbox_shift=args.bbox_shift,
            parsing_mode=args.parsing_mode
        )
        
        print(f"🎉 视频生成成功: {result_path}")
        
    except Exception as e:
        print(f"❌ 程序执行失败: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()