#!/usr/bin/env python3
"""
预处理请求处理模块
处理来自C#客户端的模板预处理请求
"""

import json
import os
import cv2
import numpy as np
from pathlib import Path

def handle_preprocess_request(request, client_socket):
    """
    处理预处理请求
    """
    try:
        template_id = request.get('templateId')
        template_path = request.get('templateImagePath', '')
        bbox_shift = request.get('bboxShift', 0)
        parsing_mode = request.get('parsingMode', 'default')
        
        print(f"🎯 处理预处理请求: templateId={template_id}, path={template_path}")
        
        # 检查图片文件
        if not os.path.exists(template_path):
            response = {
                'success': False,
                'templateId': template_id,
                'message': f'Image file not found: {template_path}',
                'processTime': 0
            }
        else:
            # 执行预处理
            result = preprocess_template(template_id, template_path, bbox_shift, parsing_mode)
            response = result
        
        # 发送响应
        response_json = json.dumps(response) + '\n'
        client_socket.send(response_json.encode('utf-8'))
        print(f"✅ 发送预处理响应: success={response.get('success')}")
        
    except Exception as e:
        print(f"❌ 预处理请求处理失败: {e}")
        error_response = {
            'success': False,
            'templateId': request.get('templateId', 'unknown'),
            'message': str(e),
            'processTime': 0
        }
        client_socket.send((json.dumps(error_response) + '\n').encode('utf-8'))


def preprocess_template(template_id, image_path, bbox_shift=0, parsing_mode='default'):
    """
    执行实际的模板预处理
    """
    try:
        print(f"开始预处理模板: {template_id}")
        
        # 读取图片
        img = cv2.imread(image_path)
        if img is None:
            return {
                'success': False,
                'templateId': template_id,
                'message': 'Failed to read image',
                'processTime': 0
            }
        
        # 创建输出目录
        output_dir = Path(f'/opt/musetalk/models/templates/{template_id}')
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # TODO: 这里应该调用MuseTalk的实际预处理函数
        # 包括：
        # 1. 人脸检测 (face detection)
        # 2. 关键点提取 (landmark extraction)
        # 3. 人脸解析 (face parsing)
        # 4. 3DMM拟合 (3DMM fitting)
        
        # 临时：保存一些模拟数据
        # 实际应该调用 MuseTalk 的预处理函数
        height, width = img.shape[:2]
        
        # 模拟人脸边界框
        face_bbox = [width//4, height//4, width*3//4, height*3//4]
        
        # 模拟68个关键点
        landmarks = np.random.rand(68, 2) * [width, height]
        
        # 保存预处理结果
        np.save(str(output_dir / 'face_bbox.npy'), face_bbox)
        np.save(str(output_dir / 'landmarks.npy'), landmarks)
        cv2.imwrite(str(output_dir / 'original.jpg'), img)
        
        # 创建元数据文件
        metadata = {
            'template_id': template_id,
            'image_size': [width, height],
            'face_bbox': face_bbox,
            'bbox_shift': bbox_shift,
            'parsing_mode': parsing_mode,
            'preprocessed': True
        }
        
        with open(output_dir / 'metadata.json', 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"✅ 预处理完成: {template_id}")
        
        return {
            'success': True,
            'templateId': template_id,
            'message': 'Preprocessing completed successfully',
            'processTime': 0.5,
            'outputDir': str(output_dir)
        }
        
    except Exception as e:
        print(f"❌ 预处理失败: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            'success': False,
            'templateId': template_id,
            'message': f'Preprocessing failed: {str(e)}',
            'processTime': 0
        }