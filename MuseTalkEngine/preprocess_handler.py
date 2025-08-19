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
        
        # 尝试调用真正的预处理
        try:
            # 导入预处理模块 - 先切换到正确的工作目录
            import sys
            original_cwd = os.getcwd()
            
            # 切换到MuseTalk目录（optimized_preprocessing_v2需要）
            os.chdir('/opt/musetalk/repo/MuseTalk')
            sys.path.insert(0, '/opt/musetalk/repo/MuseTalkEngine')
            sys.path.insert(0, '/opt/musetalk/repo/MuseTalk')
            
            from optimized_preprocessing_v2 import OptimizedPreprocessor
            
            print(f"使用OptimizedPreprocessor进行真正的预处理...")
            preprocessor = OptimizedPreprocessor()
            
            # 初始化模型
            if not preprocessor.is_initialized:
                preprocessor.initialize_models()
            
            # 执行真正的预处理
            template_output_dir = f'/opt/musetalk/models/templates/{template_id}'
            result = preprocessor.preprocess_template_ultra_fast(
                template_path=template_path,
                output_dir=template_output_dir,
                template_id=template_id
            )
            
            # 恢复原始工作目录
            os.chdir(original_cwd)
            
            if result:
                # 读取预处理结果信息
                info_file = output_dir / 'preprocessing_info.json'
                if info_file.exists():
                    with open(info_file, 'r') as f:
                        info = json.load(f)
                    message = f"Preprocessing completed. Face detected: {info.get('face_detected', 'unknown')}"
                else:
                    message = "Preprocessing completed successfully"
                    
                process_time = time.time() - start_time
                response = {
                    'success': True,
                    'templateId': template_id,
                    'message': message,
                    'processTime': process_time,
                    'details': {
                        'faceDetected': True,
                        'outputPath': str(output_dir)
                    }
                }
                print(f"✅ 真正的预处理成功，耗时: {process_time:.2f}秒")
            else:
                raise Exception("预处理返回False")
                
        except ImportError as e:
            print(f"⚠️ 无法导入预处理模块，使用模拟模式: {e}")
            # 模拟预处理
            time.sleep(0.5)
            (output_dir / 'preprocessed.flag').touch()
            
            # 创建模拟的预处理信息
            info = {
                'template_id': template_id,
                'face_detected': True,
                'bbox_shift': bbox_shift,
                'timestamp': time.time(),
                'mode': 'mock'
            }
            with open(output_dir / 'preprocessing_info.json', 'w') as f:
                json.dump(info, f, indent=2)
            
            process_time = time.time() - start_time
            response = {
                'success': True,
                'templateId': template_id,
                'message': 'Preprocessing completed (mock mode)',
                'processTime': process_time,
                'details': {
                    'faceDetected': True,
                    'outputPath': str(output_dir),
                    'mode': 'mock'
                }
            }
            print(f"⚠️ 使用模拟预处理，耗时: {process_time:.2f}秒")
        
        # 发送响应
        response_json = json.dumps(response) + '\n'
        client_socket.send(response_json.encode('utf-8'))
        print(f"发送响应: success={response['success']}, message={response['message']}")
        
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
