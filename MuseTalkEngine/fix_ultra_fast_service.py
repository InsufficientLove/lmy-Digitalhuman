#!/usr/bin/env python3
"""
修复ultra_fast_realtime_inference_v2.py的通信问题
"""

import re
import sys
from pathlib import Path

def apply_fixes():
    """应用所有修复"""
    
    file_path = Path('ultra_fast_realtime_inference_v2.py')
    if not file_path.exists():
        print(f"❌ 文件不存在: {file_path}")
        return False
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    print("📝 应用修复...")
    
    # 1. 添加导入
    if 'from preprocess_handler import' not in content:
        # 在文件开头的导入部分添加
        import_section = "import json\nimport socket\nimport threading"
        new_import = "from preprocess_handler import handle_preprocess_request"
        content = content.replace(import_section, f"{import_section}\n{new_import}")
        print("✅ 添加预处理导入")
    
    # 2. 修复handle_client_ultra_fast函数的数据接收
    # 查找并替换数据接收部分
    old_recv_pattern = r'while True:\s+data = client_socket\.recv\(4096\)\.decode\(\'utf-8\'\)\s+if not data:\s+break\s+request = json\.loads\(data\)'
    
    new_recv_code = '''while True:
            # 改进的数据接收：读取直到换行符
            buffer = b''
            while True:
                chunk = client_socket.recv(1)
                if not chunk:
                    break
                buffer += chunk
                if chunk == b'\\n':
                    break
            
            if not buffer:
                break
            
            # 解析请求
            try:
                data = buffer.decode('utf-8').strip()
                if not data:
                    continue
                    
                print(f"收到请求数据: {data[:200]}")
                request = json.loads(data)
            except json.JSONDecodeError as e:
                print(f"JSON解析错误: {e}, 数据: {repr(buffer[:100])}")
                continue
            except Exception as e:
                print(f"处理错误: {e}")
                continue'''
    
    content = re.sub(old_recv_pattern, new_recv_code, content, flags=re.DOTALL)
    print("✅ 修复数据接收逻辑")
    
    # 3. 添加命令处理
    if 'if command == \'preprocess\':' not in content:
        # 在获取command后添加处理
        command_pattern = r'(command = request\.get\([\'"]command[\'"].*?\))'
        
        command_handling = r'''\1
            print(f"处理命令: {command}")
            
            # 处理预处理请求
            if command == 'preprocess':
                handle_preprocess_request(request, client_socket)
                continue
            
            # 处理ping请求
            elif command == 'ping':
                response = {'success': True, 'message': 'pong'}
                response_json = json.dumps(response) + '\n'
                client_socket.send(response_json.encode('utf-8'))
                print("响应ping请求")
                continue'''
        
        content = re.sub(command_pattern, command_handling, content)
        print("✅ 添加命令处理逻辑")
    
    # 4. 确保有异常处理
    if 'except Exception as ex:' not in content:
        # 在handle_client_ultra_fast函数末尾添加异常处理
        content = content.replace(
            'finally:\n        client_socket.close()',
            '''except Exception as ex:
        print(f"客户端处理异常: {ex}")
        import traceback
        traceback.print_exc()
    finally:
        client_socket.close()'''
        )
        print("✅ 添加异常处理")
    
    # 保存修复后的文件
    backup_path = file_path.with_suffix('.py.bak_fixed')
    with open(backup_path, 'w') as f:
        f.write(content)
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"✅ 所有修复已应用，备份保存为: {backup_path}")
    return True

if __name__ == '__main__':
    success = apply_fixes()
    sys.exit(0 if success else 1)