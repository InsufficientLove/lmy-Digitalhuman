#!/usr/bin/env python3
import json
import os
import time
from pathlib import Path

def handle_preprocess_request(request, client_socket):
    """处理预处理请求"""
    try:
        # 兼容两种字段名格式
        template_id = request.get('templateId') or request.get('template_id')
        template_path = request.get('templateImagePath') or request.get('template_image_path')
        bbox_shift = request.get('bboxShift', 0) or request.get('bbox_shift', 0)
        
        print(f"开始预处理: template_id={template_id}, path={template_path}")
        
        start_time = time.time()
        
        # 创建输出目录
        output_dir = Path(f'/opt/musetalk/models/templates/{template_id}')
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 模拟预处理
        time.sleep(0.5)
        (output_dir / 'preprocessed.flag').touch()
        
        process_time = time.time() - start_time
        
        response = {
            'success': True,
            'templateId': template_id,
            'message': 'Preprocessing completed',
            'processTime': process_time
        }
        
        # 发送响应
        response_json = json.dumps(response) + '\n'
        client_socket.send(response_json.encode('utf-8'))
        print(f"发送响应: {response}")
        
        return None
        
    except Exception as e:
        print(f"预处理异常: {e}")
        error_response = {
            'success': False,
            'templateId': request.get('templateId') or request.get('template_id', ''),
            'message': str(e),
            'processTime': 0
        }
        client_socket.send((json.dumps(error_response) + '\n').encode('utf-8'))
        return None
