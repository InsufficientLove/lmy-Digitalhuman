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
        
        # 现在通过Docker卷共享，C#的/app/wwwroot直接映射到Python容器
        # 不需要路径转换
        
        print(f"开始预处理: template_id={template_id}, path={template_path}")
        
        # 验证文件是否存在
        if not os.path.exists(template_path):
            error_msg = f"图片文件不存在: {template_path}"
            print(f"❌ {error_msg}")
            error_response = {
                'success': False,
                'templateId': template_id,
                'message': error_msg,
                'processTime': 0
            }
            client_socket.send((json.dumps(error_response) + '\n').encode('utf-8'))
            return None
        
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
                # 预处理失败，不要使用模拟模式
                error_msg = "预处理失败：模型返回False"
                print(f"❌ {error_msg}")
                error_response = {
                    'success': False,
                    'templateId': template_id,
                    'message': error_msg,
                    'processTime': time.time() - start_time
                }
                client_socket.send((json.dumps(error_response) + '\n').encode('utf-8'))
                os.chdir(original_cwd)  # 恢复工作目录
                return None
                
        except ImportError as e:
            print(f"❌ 无法导入预处理模块: {e}")
            # 不使用模拟模式，直接返回失败
            error_response = {
                'success': False,
                'templateId': template_id,
                'message': f"预处理模块导入失败: {str(e)}",
                'processTime': time.time() - start_time
            }
            client_socket.send((json.dumps(error_response) + '\n').encode('utf-8'))
            return None
        
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
