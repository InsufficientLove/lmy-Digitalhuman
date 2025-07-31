#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
集成官方MuseTalk的调用脚本
使用真正的MuseTalk官方API和模型
"""

import os
import sys
import argparse
import json
import time
import logging
import subprocess
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('official_musetalk.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class OfficialMuseTalkService:
    def __init__(self):
        self.musetalk_root = self.find_musetalk_installation()
        self.setup_environment()
        
    def find_musetalk_installation(self):
        """查找MuseTalk安装目录"""
        possible_paths = [
            "Models/musetalk/MuseTalk",
            "../Models/musetalk/MuseTalk", 
            "../../Models/musetalk/MuseTalk",
            "C:/Users/Administrator/Desktop/digitalhuman/lmy-Digitalhuman/Models/musetalk/MuseTalk"
        ]
        
        for path in possible_paths:
            if os.path.exists(path) and os.path.exists(os.path.join(path, "app.py")):
                logger.info(f"找到MuseTalk安装目录: {path}")
                return os.path.abspath(path)
        
        raise FileNotFoundError("未找到MuseTalk安装目录，请确保已正确下载MuseTalk")
    
    def setup_environment(self):
        """设置环境"""
        # 切换到MuseTalk目录
        os.chdir(self.musetalk_root)
        logger.info(f"切换到MuseTalk目录: {self.musetalk_root}")
        
        # 检查必要文件
        required_files = [
            "app.py",
            "scripts/inference.py", 
            "configs/inference/test.yaml"
        ]
        
        missing_files = []
        for file in required_files:
            if not os.path.exists(file):
                missing_files.append(file)
        
        if missing_files:
            logger.error(f"缺少MuseTalk文件: {missing_files}")
            raise FileNotFoundError(f"MuseTalk安装不完整，缺少文件: {missing_files}")
        
        logger.info("MuseTalk环境检查完成")
    
    def create_inference_config(self, avatar_path, audio_path, output_path, **kwargs):
        """创建推理配置文件"""
        config = {
            "inference": {
                "avatar_id": "custom",
                "avatar_path": avatar_path,
                "audio_path": audio_path,
                "output_path": output_path,
                "batch_size": kwargs.get('batch_size', 4),
                "fps": kwargs.get('fps', 25),
                "bbox_shift": kwargs.get('bbox_shift', 0),
                "use_float16": True,  # 4x GPU优化
                "device": "cuda"
            }
        }
        
        # 保存临时配置文件
        config_path = "configs/inference/temp_inference.yaml"
        import yaml
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
        
        return config_path
    
    def run_official_inference(self, avatar_path, audio_path, output_path, **kwargs):
        """运行官方MuseTalk推理"""
        try:
            start_time = time.time()
            
            # 验证输入文件
            if not os.path.exists(avatar_path):
                raise FileNotFoundError(f"头像文件不存在: {avatar_path}")
            if not os.path.exists(audio_path):
                raise FileNotFoundError(f"音频文件不存在: {audio_path}")
            
            # 确保输出目录存在
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # 创建配置文件
            config_path = self.create_inference_config(avatar_path, audio_path, output_path, **kwargs)
            
            # 构建官方推理命令
            cmd = [
                sys.executable, "-m", "scripts.inference",
                "--inference_config", config_path
            ]
            
            # 添加可选参数
            if kwargs.get('bbox_shift', 0) != 0:
                cmd.extend(["--bbox_shift", str(kwargs['bbox_shift'])])
            
            if kwargs.get('use_float16', True):
                cmd.append("--use_float16")
            
            logger.info(f"执行官方MuseTalk推理命令: {' '.join(cmd)}")
            
            # 执行推理
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.musetalk_root,
                timeout=kwargs.get('timeout', 600)  # 10分钟超时
            )
            
            processing_time = time.time() - start_time
            
            if result.returncode == 0:
                logger.info(f"MuseTalk推理成功，耗时: {processing_time:.2f}秒")
                
                # 检查输出文件
                if os.path.exists(output_path):
                    file_size = os.path.getsize(output_path)
                    logger.info(f"生成视频: {output_path}, 大小: {file_size} bytes")
                    
                    return {
                        'success': True,
                        'video_path': output_path,
                        'processing_time': processing_time,
                        'file_size': file_size,
                        'stdout': result.stdout,
                        'method': 'official_musetalk'
                    }
                else:
                    logger.error(f"推理完成但输出文件不存在: {output_path}")
                    return {
                        'success': False,
                        'error': f"输出文件不存在: {output_path}",
                        'stdout': result.stdout,
                        'stderr': result.stderr,
                        'processing_time': processing_time
                    }
            else:
                logger.error(f"MuseTalk推理失败: {result.stderr}")
                return {
                    'success': False,
                    'error': result.stderr,
                    'stdout': result.stdout,
                    'processing_time': processing_time
                }
                
        except subprocess.TimeoutExpired:
            logger.error("MuseTalk推理超时")
            return {
                'success': False,
                'error': "推理超时",
                'processing_time': time.time() - start_time
            }
        except Exception as e:
            logger.error(f"MuseTalk推理异常: {e}")
            return {
                'success': False,
                'error': str(e),
                'processing_time': time.time() - start_time
            }
    
    def run_gradio_app_inference(self, avatar_path, audio_path, output_path, **kwargs):
        """使用Gradio应用进行推理（备用方案）"""
        try:
            # 这里可以实现通过调用app.py的方式进行推理
            # 或者直接导入app.py中的推理函数
            logger.info("使用Gradio应用推理模式")
            
            # 导入MuseTalk的核心模块
            sys.path.insert(0, self.musetalk_root)
            
            # 这里需要根据实际的MuseTalk代码结构来调用
            # 由于我们没有完整的MuseTalk源码，这里提供框架
            
            return {
                'success': False,
                'error': "Gradio应用推理模式需要完整的MuseTalk源码支持",
                'processing_time': 0
            }
            
        except Exception as e:
            logger.error(f"Gradio应用推理失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'processing_time': 0
            }

def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(description='官方MuseTalk集成服务')
    
    # 必需参数
    parser.add_argument('--avatar', required=True, help='头像图片路径')
    parser.add_argument('--audio', required=True, help='音频文件路径') 
    parser.add_argument('--output', required=True, help='输出视频路径')
    
    # 可选参数
    parser.add_argument('--fps', type=int, default=25, help='视频帧率')
    parser.add_argument('--batch_size', type=int, default=4, help='批处理大小')
    parser.add_argument('--bbox_shift', type=int, default=0, help='边界框偏移')
    parser.add_argument('--timeout', type=int, default=600, help='超时时间(秒)')
    parser.add_argument('--use_gradio', action='store_true', help='使用Gradio应用模式')
    parser.add_argument('--verbose', '-v', action='store_true', help='详细输出')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # 创建官方MuseTalk服务
        service = OfficialMuseTalkService()
        
        # 选择推理方式
        if args.use_gradio:
            result = service.run_gradio_app_inference(
                args.avatar, args.audio, args.output,
                fps=args.fps, batch_size=args.batch_size,
                bbox_shift=args.bbox_shift, timeout=args.timeout
            )
        else:
            result = service.run_official_inference(
                args.avatar, args.audio, args.output,
                fps=args.fps, batch_size=args.batch_size, 
                bbox_shift=args.bbox_shift, timeout=args.timeout
            )
        
        # 输出结果
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(0 if result['success'] else 1)
        
    except Exception as e:
        logger.error(f"服务初始化失败: {e}")
        print(json.dumps({
            'success': False,
            'error': str(e),
            'processing_time': 0
        }, ensure_ascii=False, indent=2))
        sys.exit(1)

if __name__ == '__main__':
    main()