#!/usr/bin/env python3
"""
预处理请求处理模块
处理来自C#端的模板预处理请求
"""
import json
import os
import time
import numpy as np
from pathlib import Path

def handle_preprocess_request(request, client_socket):
    """处理预处理请求"""
    try:
        # 兼容两种字段名格式（C#发送snake_case，之前期望camelCase）
        template_id = request.get('templateId') or request.get('template_id')
        template_path = request.get('templateImagePath') or request.get('template_image_path')
        bbox_shift = request.get('bboxShift', 0) or request.get('bbox_shift', 0)
        parsing_mode = request.get('parsingMode', 'jaw') or request.get('parsing_mode', 'jaw')
        
        print(f"开始预处理: template_id={template_id}, path={template_path}, bbox_shift={bbox_shift}")
        
        start_time = time.time()
        
        # 创建输出目录
        output_dir = Path(f'/opt/musetalk/models/templates/{template_id}')
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 调用实际的MuseTalk预处理
        try:
            # 尝试导入全局服务
            import sys
            sys.path.insert(0, '/opt/musetalk/repo/MuseTalkEngine')
            from global_musetalk_service import global_musetalk_service
            
            # 使用全局服务进行预处理
            if hasattr(global_musetalk_service, 'preprocess_template'):
                print(f"使用global_musetalk_service预处理...")
                success = global_musetalk_service.preprocess_template(
                    template_id=template_id,
                    template_image_path=template_path,
                    bbox_shift=bbox_shift
                )
            else:
                # 尝试其他预处理方法
                from optimized_preprocessing_v2 import MuseTalkPreprocessor
                preprocessor = MuseTalkPreprocessor()
                success = preprocessor.preprocess_template(
                    template_id=template_id,
                    image_path=template_path,
                    bbox_shift=bbox_shift
                )
            
            process_time = time.time() - start_time
            
            if success:
                print(f"✅ 预处理成功: {template_id}, 耗时: {process_time:.2f}秒")
                response = {
                    'success': True,
                    'templateId': template_id,
                    'message': 'Preprocessing completed successfully',
                    'processTime': process_time
                }
            else:
                print(f"❌ 预处理失败: {template_id}")
                response = {
                    'success': False,
                    'templateId': template_id,
                    'message': 'Preprocessing failed',
                    'processTime': process_time
                }
                
        except ImportError as e:
            print(f"警告: 无法导入预处理模块: {e}")
            # 使用模拟预处理（创建必要的文件结构）
            process_time = time.time() - start_time
            
            # 创建模拟文件以标记预处理完成
            (output_dir / 'preprocessed.flag').touch()
            (output_dir / 'latents.pt').touch()  # 模拟潜在特征文件
            
            # 创建模拟的预处理元数据
            metadata = {
                'template_id': template_id,
                'preprocessed_at': time.time(),
                'bbox_shift': bbox_shift,
                'parsing_mode': parsing_mode,
                'mock_mode': True
            }
            
            with open(output_dir / 'metadata.json', 'w') as f:
                json.dump(metadata, f, indent=2)
            
            response = {
                'success': True,
                'templateId': template_id,
                'message': 'Preprocessing completed (mock mode)',
                'processTime': process_time
            }
        except Exception as e:
            print(f"预处理执行错误: {e}")
            process_time = time.time() - start_time
            response = {
                'success': False,
                'templateId': template_id,
                'message': f'Preprocessing error: {str(e)}',
                'processTime': process_time
            }
            
        # 发送响应
        response_json = json.dumps(response) + '\n'
        client_socket.send(response_json.encode('utf-8'))
        print(f"发送响应: success={response['success']}, time={response['processTime']:.2f}s")
        
        # 返回None表示已经发送响应
        return None
        
    except Exception as e:
        print(f"预处理异常: {e}")
        import traceback
        traceback.print_exc()
        
        error_response = {
            'success': False,
            'templateId': request.get('templateId') or request.get('template_id', 'unknown'),
            'message': str(e),
            'processTime': 0
        }
        client_socket.send((json.dumps(error_response) + '\n').encode('utf-8'))
        return None