#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数字人系统 - MuseTalk服务完整版
支持多种人脸检测库的智能回退机制
版本: 2025-01-28 终极版
"""

import os
import sys
import logging
import traceback
from typing import Optional, Union, List, Tuple
import numpy as np
import cv2
from flask import Flask, request, jsonify, send_file
import torch
import warnings

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('musetalk_service.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# 抑制警告
warnings.filterwarnings('ignore')

class FaceDetectorManager:
    """人脸检测器管理器 - 支持多种库的智能回退"""
    
    def __init__(self):
        self.detector = None
        self.detector_type = None
        self.initialize_detector()
    
    def initialize_detector(self):
        """按优先级初始化人脸检测器"""
        
        # 优先级1: dlib (最佳质量)
        try:
            import dlib
            self.detector = dlib.get_frontal_face_detector()
            self.detector_type = 'dlib'
            logger.info("✅ 使用dlib人脸检测器 (最佳质量)")
            return
        except ImportError as e:
            logger.warning(f"dlib不可用: {e}")
        except Exception as e:
            logger.warning(f"dlib初始化失败: {e}")
        
        # 优先级2: MediaPipe (良好质量)
        try:
            import mediapipe as mp
            self.mp_face_detection = mp.solutions.face_detection
            self.mp_drawing = mp.solutions.drawing_utils
            self.detector = self.mp_face_detection.FaceDetection(
                model_selection=1, min_detection_confidence=0.5
            )
            self.detector_type = 'mediapipe'
            logger.info("✅ 使用MediaPipe人脸检测器 (良好质量)")
            return
        except ImportError as e:
            logger.warning(f"MediaPipe不可用: {e}")
        except Exception as e:
            logger.warning(f"MediaPipe初始化失败: {e}")
        
        # 优先级3: OpenCV Haar Cascades (基础质量)
        try:
            cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            if os.path.exists(cascade_path):
                self.detector = cv2.CascadeClassifier(cascade_path)
                self.detector_type = 'opencv'
                logger.info("✅ 使用OpenCV Haar人脸检测器 (基础质量)")
                return
        except Exception as e:
            logger.warning(f"OpenCV Haar初始化失败: {e}")
        
        # 优先级4: OpenCV DNN (需要模型文件)
        try:
            # 这里可以添加DNN模型的初始化
            pass
        except Exception as e:
            logger.warning(f"OpenCV DNN初始化失败: {e}")
        
        logger.error("❌ 无法初始化任何人脸检测器！")
        raise RuntimeError("没有可用的人脸检测器")
    
    def detect_faces(self, image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        检测人脸
        返回: [(x, y, w, h), ...] 格式的边界框列表
        """
        if self.detector is None:
            return []
        
        try:
            if self.detector_type == 'dlib':
                return self._detect_faces_dlib(image)
            elif self.detector_type == 'mediapipe':
                return self._detect_faces_mediapipe(image)
            elif self.detector_type == 'opencv':
                return self._detect_faces_opencv(image)
            else:
                return []
        except Exception as e:
            logger.error(f"人脸检测失败: {e}")
            return []
    
    def _detect_faces_dlib(self, image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """使用dlib检测人脸"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = self.detector(gray)
        
        results = []
        for face in faces:
            x, y, w, h = face.left(), face.top(), face.width(), face.height()
            results.append((x, y, w, h))
        
        return results
    
    def _detect_faces_mediapipe(self, image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """使用MediaPipe检测人脸"""
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = self.detector.process(rgb_image)
        
        faces = []
        if results.detections:
            h, w, _ = image.shape
            for detection in results.detections:
                bbox = detection.location_data.relative_bounding_box
                x = int(bbox.xmin * w)
                y = int(bbox.ymin * h)
                width = int(bbox.width * w)
                height = int(bbox.height * h)
                faces.append((x, y, width, height))
        
        return faces
    
    def _detect_faces_opencv(self, image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """使用OpenCV检测人脸"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = self.detector.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30)
        )
        
        return [(x, y, w, h) for x, y, w, h in faces]

class MuseTalkService:
    """MuseTalk数字人服务"""
    
    def __init__(self):
        self.face_detector = FaceDetectorManager()
        self.device = self._get_device()
        logger.info(f"使用设备: {self.device}")
    
    def _get_device(self) -> str:
        """获取计算设备"""
        if torch.cuda.is_available():
            return "cuda"
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            return "mps"
        else:
            return "cpu"
    
    def process_image(self, image_path: str) -> dict:
        """处理单张图片"""
        try:
            # 读取图片
            image = cv2.imread(image_path)
            if image is None:
                return {"error": "无法读取图片"}
            
            # 检测人脸
            faces = self.face_detector.detect_faces(image)
            
            result = {
                "success": True,
                "detector_type": self.face_detector.detector_type,
                "faces_count": len(faces),
                "faces": faces,
                "image_shape": image.shape
            }
            
            logger.info(f"处理图片 {image_path}: 检测到 {len(faces)} 个人脸")
            return result
            
        except Exception as e:
            error_msg = f"处理图片失败: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            return {"error": error_msg}
    
    def process_video(self, video_path: str, audio_path: str, output_path: str) -> dict:
        """处理视频和音频生成数字人"""
        try:
            # 这里添加MuseTalk的核心逻辑
            # 由于MuseTalk需要特定的模型文件，这里提供框架
            
            logger.info(f"开始处理视频: {video_path}")
            logger.info(f"音频文件: {audio_path}")
            logger.info(f"输出路径: {output_path}")
            
            # 检测视频中的人脸
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return {"error": "无法打开视频文件"}
            
            frame_count = 0
            total_faces = 0
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                faces = self.face_detector.detect_faces(frame)
                total_faces += len(faces)
                frame_count += 1
                
                # 处理前几帧就够了，用于验证
                if frame_count >= 10:
                    break
            
            cap.release()
            
            result = {
                "success": True,
                "detector_type": self.face_detector.detector_type,
                "processed_frames": frame_count,
                "average_faces_per_frame": total_faces / frame_count if frame_count > 0 else 0,
                "message": "视频分析完成，MuseTalk处理需要加载完整模型"
            }
            
            return result
            
        except Exception as e:
            error_msg = f"处理视频失败: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            return {"error": error_msg}

# Flask应用
app = Flask(__name__)
musetalk_service = MuseTalkService()

@app.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        "status": "healthy",
        "detector_type": musetalk_service.face_detector.detector_type,
        "device": musetalk_service.device
    })

@app.route('/detect_faces', methods=['POST'])
def detect_faces():
    """人脸检测API"""
    if 'image' not in request.files:
        return jsonify({"error": "没有上传图片"}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({"error": "没有选择文件"}), 400
    
    # 保存临时文件
    temp_path = f"temp_{file.filename}"
    file.save(temp_path)
    
    try:
        result = musetalk_service.process_image(temp_path)
        return jsonify(result)
    finally:
        # 清理临时文件
        if os.path.exists(temp_path):
            os.remove(temp_path)

@app.route('/generate', methods=['POST'])
def generate_digital_human():
    """生成数字人视频"""
    data = request.json
    
    if not data or 'video_path' not in data or 'audio_path' not in data:
        return jsonify({"error": "缺少必要参数"}), 400
    
    video_path = data['video_path']
    audio_path = data['audio_path']
    output_path = data.get('output_path', 'output.mp4')
    
    result = musetalk_service.process_video(video_path, audio_path, output_path)
    return jsonify(result)

@app.route('/info', methods=['GET'])
def get_info():
    """获取系统信息"""
    info = {
        "service": "MuseTalk数字人系统",
        "version": "2025-01-28 终极版",
        "detector_type": musetalk_service.face_detector.detector_type,
        "device": musetalk_service.device,
        "available_detectors": []
    }
    
    # 检查可用的检测器
    try:
        import dlib
        info["available_detectors"].append("dlib")
    except ImportError:
        pass
    
    try:
        import mediapipe
        info["available_detectors"].append("mediapipe")
    except ImportError:
        pass
    
    try:
        import cv2
        info["available_detectors"].append("opencv")
    except ImportError:
        pass
    
    return jsonify(info)

def main():
    """主函数"""
    try:
        logger.info("🚀 启动MuseTalk数字人服务...")
        logger.info(f"人脸检测器: {musetalk_service.face_detector.detector_type}")
        logger.info(f"计算设备: {musetalk_service.device}")
        
        # 启动Flask服务
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=False,
            threaded=True
        )
        
    except Exception as e:
        logger.error(f"服务启动失败: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()