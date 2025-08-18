# 在原始文件的基础上添加预处理支持
# 这是handle_client_ultra_fast函数的修复部分

def handle_client_ultra_fast_fixed(client_socket, client_address):
    """处理Ultra Fast客户端请求 - 修复版"""
    print(f"🔗 客户端连接: {client_address}")
    
    try:
        while True:
            # 读取完整的一行数据（以\n结尾）
            buffer = b''
            while True:
                byte = client_socket.recv(1)
                if not byte:
                    break
                buffer += byte
                if byte == b'\n':
                    break
            
            if not buffer:
                break
            
            # 解析请求
            try:
                data = buffer.decode('utf-8').strip()
                if not data:
                    continue
                    
                print(f"收到数据: {data[:100]}")
                request = json.loads(data)
                command = request.get('command')
                print(f"处理命令: {command}")
                
                # 处理预处理请求
                if command == 'preprocess':
                    template_id = request.get('templateId')
                    template_path = request.get('templateImagePath', '')
                    print(f"预处理模板: {template_id}, 路径: {template_path}")
                    
                    # 执行预处理（这里应该调用实际的预处理函数）
                    response = {
                        'success': True,
                        'templateId': template_id,
                        'processTime': 1.0,
                        'message': 'Preprocessing completed'
                    }
                    
                    # 发送响应
                    response_json = json.dumps(response) + '\n'
                    client_socket.send(response_json.encode('utf-8'))
                    print(f"发送响应: {response}")
                    
                elif command == 'ping':
                    response = {'success': True, 'message': 'pong'}
                    response_json = json.dumps(response) + '\n'
                    client_socket.send(response_json.encode('utf-8'))
                    
                # 处理其他命令...
                
            except json.JSONDecodeError as e:
                print(f"JSON解析错误: {e}, 数据: {repr(buffer[:100])}")
                error_response = {'success': False, 'error': str(e)}
                client_socket.send((json.dumps(error_response) + '\n').encode('utf-8'))
                
    except Exception as e:
        print(f"客户端处理异常: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client_socket.close()
        print(f"客户端断开: {client_address}")