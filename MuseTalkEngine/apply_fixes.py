#!/usr/bin/env python3
"""
应用修复补丁到ultra_fast_realtime_inference_v2.py
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
        imports = "from preprocess_handler import handle_preprocess_request\n"
        # 在其他import语句后添加
        content = content.replace('import json', 'import json\n' + imports)
        print("✅ 添加预处理导入")
    
    # 2. 修复handle_client_ultra_fast函数
    # 查找函数定义
    func_pattern = r'(def handle_client_ultra_fast\(client_socket, client_address\):.*?)\n(\s+)""".*?"""\n(.*?)while True:(.*?)request = json\.loads\(data\)'
    
    def replacer(match):
        func_def = match.group(1)
        indent = match.group(2)
        doc = match.group(2) + '"""处理Ultra Fast客户端请求"""'
        pre_while = match.group(3)
        
        new_code = f'''{func_def}
{doc}
{indent}print(f"🔗 客户端连接: {{client_address}}")
{indent}
{indent}try:
{indent}    while True:
{indent}        # 改进的数据接收：读取直到换行符
{indent}        buffer = b''
{indent}        while True:
{indent}            chunk = client_socket.recv(1)
{indent}            if not chunk:
{indent}                break
{indent}            buffer += chunk
{indent}            if chunk == b'\\n':
{indent}                break
{indent}        
{indent}        if not buffer:
{indent}            break
{indent}        
{indent}        # 解析请求
{indent}        try:
{indent}            data = buffer.decode('utf-8').strip()
{indent}            if not data:
{indent}                continue
{indent}                
{indent}            print(f"收到请求数据: {{data[:200]}}")
{indent}            request = json.loads(data)'''
        
        return new_code
    
    new_content = re.sub(func_pattern, replacer, content, flags=re.DOTALL)
    
    if new_content != content:
        content = new_content
        print("✅ 修复数据接收逻辑")
    
    # 3. 添加预处理命令处理
    if 'if command == \'preprocess\':' not in content:
        # 在获取command后添加处理
        command_pattern = r'(command = request\.get\([\'"]command[\'"].*?\))'
        replacement = r'''\1
            print(f"处理命令: {command}")
            
            # 处理预处理请求
            if command == 'preprocess':
                handle_preprocess_request(request, client_socket)
                continue'''
        
        content = re.sub(command_pattern, replacement, content)
        print("✅ 添加预处理命令处理")
    
    # 4. 添加ping命令支持
    if 'if command == \'ping\':' not in content:
        # 在preprocess后添加ping
        content = content.replace(
            'if command == \'preprocess\':',
            '''if command == 'preprocess':
                handle_preprocess_request(request, client_socket)
                continue
            elif command == 'ping':
                response = {'success': True, 'message': 'pong'}
                client_socket.send((json.dumps(response) + '\\n').encode('utf-8'))
                print("响应ping请求")
                continue
            elif command == 'preprocess':'''
        )
    
    # 保存修复后的文件
    with open(file_path, 'w') as f:
        f.write(content)
    
    print("✅ 所有修复已应用")
    return True

if __name__ == '__main__':
    success = apply_fixes()
    sys.exit(0 if success else 1)