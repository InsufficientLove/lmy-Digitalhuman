#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
便携式MuseTalk HTTP服务
支持动态GPU配置和多机器部署
将此文件复制到 F:\AI\DigitalHuman_Portable\MuseTalk\musetalk_service.py
"""

import os
import sys
import json
import logging
import time
from pathlib import Path
from flask import Flask, request, jsonify
from flask_cors import CORS

# 获取脚本所在目录
SCRIPT_DIR = Path(__file__).parent.absolute()
BASE_DIR = SCRIPT_DIR.parent
CONFIG_DIR = BASE_DIR / "config"
LOGS_DIR = BASE_DIR / "logs"

# 确保日志目录存在
LOGS_DIR.mkdir(exist_ok=True)

# 加载GPU配置
def load_gpu_config():
    """加载GPU配置"""
    gpu_config_file = CONFIG_DIR / "gpu_config.env"
    if gpu_config_file.exists():
        with open(gpu_config_file, 'r') as f:
            for line in f:
                if '=' in line:
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value
                    print(f"✅ 加载环境变量: {key}={value}")

# 加载服务配置
def load_service_config():
    """加载服务配置"""
    config_file = CONFIG_DIR / "service_config.json"
    default_config = {
        "host": "0.0.0.0",
        "port": 8000,
        "debug": False,
        "model_config": {
            "batch_size": 4,
            "fps": 25,
            "quality": "medium",
            "enable_emotion": True
        }
    }
    
    if config_file.exists():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                print(f"✅ 加载服务配置: {config_file}")
                return {**default_config, **config}
        except Exception as e:
            print(f"⚠️ 配置文件加载失败，使用默认配置: {e}")
    
    return default_config

# 早期加载配置
load_gpu_config()
service_config = load_service_config()

# 添加MuseTalk路径
sys.path.append(str(SCRIPT_DIR))

app = Flask(__name__)
CORS(app)

# 配置日志
log_file = LOGS_DIR / "musetalk_service.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# 全局变量
musetalk_model = None
gpu_info = {}

def detect_gpu_info():
    """检测GPU信息"""
    global gpu_info
    try:
        import torch
        gpu_info = {
            "torch_version": torch.__version__,
            "cuda_available": torch.cuda.is_available(),
            "gpu_count": torch.cuda.device_count() if torch.cuda.is_available() else 0,
            "current_device": torch.cuda.current_device() if torch.cuda.is_available() else None,
            "gpu_names": []
        }
        
        if torch.cuda.is_available():
            for i in range(torch.cuda.device_count()):
                gpu_name = torch.cuda.get_device_name(i)
                gpu_info["gpu_names"].append(f"GPU {i}: {gpu_name}")
                
        logger.info(f"GPU信息: {gpu_info}")
        
        # 设置GPU设备
        cuda_devices = os.environ.get('CUDA_VISIBLE_DEVICES', '0')
        if torch.cuda.is_available():
            logger.info(f"使用GPU设备: {cuda_devices}")
        else:
            logger.warning("CUDA不可用，将使用CPU模式")
            
    except Exception as e:
        logger.error(f"GPU检测失败: {e}")
        gpu_info = {"error": str(e)}

def initialize_musetalk():
    """初始化MuseTalk模型"""
    global musetalk_model
    try:
        logger.info("正在初始化MuseTalk模型...")
        
        # 检测GPU
        detect_gpu_info()
        
        # TODO: 这里需要根据实际的MuseTalk API进行实现
        # 示例代码结构:
        """
        from musetalk.models import MuseTalkModel
        from musetalk.utils.preprocess import AudioProcessor, ImageProcessor
        
        # 初始化模型
        musetalk_model = {
            'model': MuseTalkModel.from_pretrained(model_path),
            'audio_processor': AudioProcessor(),
            'image_processor': ImageProcessor(),
            'config': service_config['model_config']
        }
        """
        
        # 临时模拟初始化
        musetalk_model = {
            'initialized': True,
            'config': service_config['model_config'],
            'gpu_info': gpu_info
        }
        
        logger.info("MuseTalk模型初始化成功")
        return True
        
    except Exception as e:
        logger.error(f"MuseTalk模型初始化失败: {e}")
        return False

@app.route('/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({
        "status": "healthy",
        "service": "MuseTalk Portable",
        "model_loaded": musetalk_model is not None,
        "gpu_info": gpu_info,
        "environment": {
            "cuda_visible_devices": os.environ.get('CUDA_VISIBLE_DEVICES', 'N/A'),
            "base_dir": str(BASE_DIR),
            "script_dir": str(SCRIPT_DIR),
            "python_version": sys.version
        },
        "config": service_config
    })

@app.route('/generate', methods=['POST'])
def generate_video():
    """生成数字人视频接口"""
    try:
        if musetalk_model is None:
            return jsonify({
                "success": False,
                "message": "MuseTalk模型未初始化"
            }), 500
            
        data = request.json
        logger.info(f"收到生成请求: {data}")
        
        # 提取参数
        avatar_image = data.get('avatar_image')
        audio_path = data.get('audio_path')
        result_dir = data.get('result_dir')
        output_filename = data.get('output_filename', f'musetalk_{int(time.time())}.mp4')
        
        # 使用服务配置的默认值
        model_config = service_config['model_config']
        fps = data.get('fps', model_config['fps'])
        batch_size = data.get('batch_size', model_config['batch_size'])
        quality = data.get('quality', model_config['quality'])
        enable_emotion = data.get('enable_emotion', model_config['enable_emotion'])
        
        # 验证输入文件
        if not os.path.exists(avatar_image):
            return jsonify({
                "success": False,
                "message": f"头像图片不存在: {avatar_image}"
            }), 400
            
        if not os.path.exists(audio_path):
            return jsonify({
                "success": False,
                "message": f"音频文件不存在: {audio_path}"
            }), 400
        
        # 确保输出目录存在
        os.makedirs(result_dir, exist_ok=True)
        output_path = os.path.join(result_dir, output_filename)
        
        # 记录开始时间
        start_time = time.time()
        
        logger.info(f"开始生成视频:")
        logger.info(f"  头像: {avatar_image}")
        logger.info(f"  音频: {audio_path}")
        logger.info(f"  输出: {output_path}")
        logger.info(f"  参数: fps={fps}, batch_size={batch_size}, quality={quality}")
        
        # TODO: 调用实际的MuseTalk生成逻辑
        """
        # 实际实现示例:
        result = musetalk_model['model'].generate(
            avatar_image=avatar_image,
            audio_path=audio_path,
            output_path=output_path,
            fps=fps,
            batch_size=batch_size,
            quality=quality,
            enable_emotion=enable_emotion,
            device=f"cuda:{os.environ.get('CUDA_VISIBLE_DEVICES', '0').split(',')[0]}" if gpu_info.get('cuda_available') else "cpu"
        )
        """
        
        # 临时模拟生成过程
        logger.info("正在生成数字人视频...")
        
        # 根据GPU数量调整处理时间模拟
        gpu_count = gpu_info.get('gpu_count', 1)
        base_time = 3.0  # 基础处理时间
        processing_time_sim = base_time / max(1, gpu_count)  # GPU并行加速
        
        time.sleep(processing_time_sim)  # 模拟处理时间
        
        # 创建临时输出文件
        with open(output_path, 'w') as f:
            f.write(f"# MuseTalk生成的视频文件\n# 参数: fps={fps}, quality={quality}\n# GPU: {gpu_info}")
        
        processing_time = (time.time() - start_time) * 1000
        file_size = os.path.getsize(output_path)
        
        logger.info(f"视频生成完成: {output_path}")
        logger.info(f"处理时间: {processing_time:.0f}ms")
        logger.info(f"文件大小: {file_size} bytes")
        
        return jsonify({
            "success": True,
            "video_path": output_path,
            "message": "视频生成成功",
            "duration": 10.0,
            "processing_time": int(processing_time),
            "file_size": file_size,
            "metadata": {
                "fps": fps,
                "quality": quality,
                "resolution": "1280x720" if quality == "medium" else "1920x1080",
                "gpu_used": gpu_info.get('gpu_names', ['CPU']),
                "batch_size": batch_size
            }
        })
        
    except Exception as e:
        logger.error(f"生成视频失败: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "message": f"生成失败: {str(e)}"
        }), 500

@app.route('/config', methods=['GET'])
def get_config():
    """获取当前配置"""
    return jsonify({
        "service_config": service_config,
        "gpu_config": {
            "cuda_visible_devices": os.environ.get('CUDA_VISIBLE_DEVICES'),
            "pytorch_cuda_alloc_conf": os.environ.get('PYTORCH_CUDA_ALLOC_CONF')
        },
        "paths": {
            "base_dir": str(BASE_DIR),
            "script_dir": str(SCRIPT_DIR),
            "config_dir": str(CONFIG_DIR),
            "logs_dir": str(LOGS_DIR)
        }
    })

@app.route('/config', methods=['POST'])
def update_config():
    """更新配置"""
    try:
        new_config = request.json
        
        # 更新服务配置
        config_file = CONFIG_DIR / "service_config.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(new_config, f, indent=2, ensure_ascii=False)
        
        logger.info(f"配置已更新: {new_config}")
        
        return jsonify({
            "success": True,
            "message": "配置更新成功，重启服务后生效"
        })
        
    except Exception as e:
        logger.error(f"配置更新失败: {e}")
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

if __name__ == '__main__':
    logger.info("="*50)
    logger.info("🚀 启动便携式MuseTalk服务")
    logger.info("="*50)
    logger.info(f"📁 基础目录: {BASE_DIR}")
    logger.info(f"📁 脚本目录: {SCRIPT_DIR}")
    logger.info(f"📁 配置目录: {CONFIG_DIR}")
    logger.info(f"📁 日志目录: {LOGS_DIR}")
    logger.info(f"🔧 服务配置: {service_config}")
    
    # 初始化模型
    if initialize_musetalk():
        host = service_config['host']
        port = service_config['port']
        debug = service_config['debug']
        
        logger.info(f"✅ 服务启动成功")
        logger.info(f"🌐 监听地址: http://{host}:{port}")
        logger.info(f"🏥 健康检查: http://{host}:{port}/health")
        logger.info(f"⚙️ 配置接口: http://{host}:{port}/config")
        
        app.run(host=host, port=port, debug=debug, threaded=True)
    else:
        logger.error("❌ 模型初始化失败，服务无法启动")
        sys.exit(1)