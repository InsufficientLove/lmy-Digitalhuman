#!/usr/bin/env python3
"""
临时修复MuseTalk通信协议的脚本
直接在musetalk-python容器内运行，无需重建镜像
"""

import socket
import json
import threading
import time
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ProtocolFixProxy:
    """协议修复代理，在28889端口监听，转发到28888端口"""
    
    def __init__(self, listen_port=28889, target_port=28888):
        self.listen_port = listen_port
        self.target_port = target_port
        self.running = False
        
    def handle_client(self, client_socket, client_address):
        """处理客户端连接"""
        logger.info(f"新连接来自: {client_address}")
        
        try:
            # 连接到真实的MuseTalk服务
            target_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            target_socket.connect(('localhost', self.target_port))
            
            # 创建双向转发线程
            client_to_target = threading.Thread(
                target=self.forward_data,
                args=(client_socket, target_socket, "C->S", True)
            )
            target_to_client = threading.Thread(
                target=self.forward_data,
                args=(target_socket, client_socket, "S->C", False)
            )
            
            client_to_target.start()
            target_to_client.start()
            
            client_to_target.join()
            target_to_client.join()
            
        except Exception as e:
            logger.error(f"处理连接错误: {e}")
        finally:
            client_socket.close()
            target_socket.close()
            logger.info(f"连接关闭: {client_address}")
    
    def forward_data(self, source, destination, direction, fix_protocol=False):
        """转发数据，可选择修复协议"""
        buffer = b""
        
        try:
            while True:
                data = source.recv(4096)
                if not data:
                    break
                
                if fix_protocol:
                    # 从客户端到服务器：确保消息以换行符结尾
                    buffer += data
                    
                    # 尝试找到完整的JSON消息
                    while buffer:
                        try:
                            # 尝试解析JSON
                            decoded = buffer.decode('utf-8')
                            json_obj = json.loads(decoded)
                            
                            # 成功解析，添加换行符并发送
                            fixed_data = (json.dumps(json_obj) + '\n').encode('utf-8')
                            destination.send(fixed_data)
                            logger.debug(f"{direction} 修复并转发: {len(fixed_data)} bytes")
                            buffer = b""
                            break
                            
                        except (json.JSONDecodeError, UnicodeDecodeError):
                            # JSON不完整，继续接收
                            if len(buffer) > 65536:  # 防止缓冲区过大
                                # 可能不是JSON，直接转发
                                destination.send(buffer)
                                logger.debug(f"{direction} 直接转发: {len(buffer)} bytes")
                                buffer = b""
                            break
                else:
                    # 从服务器到客户端：直接转发
                    destination.send(data)
                    logger.debug(f"{direction} 转发: {len(data)} bytes")
                    
        except Exception as e:
            logger.error(f"{direction} 转发错误: {e}")
    
    def start(self):
        """启动代理服务器"""
        self.running = True
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(('0.0.0.0', self.listen_port))
        server_socket.listen(5)
        
        logger.info(f"协议修复代理启动在端口 {self.listen_port}，转发到 {self.target_port}")
        
        try:
            while self.running:
                client_socket, client_address = server_socket.accept()
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, client_address)
                )
                client_thread.daemon = True
                client_thread.start()
        except KeyboardInterrupt:
            logger.info("代理服务器停止")
        finally:
            server_socket.close()

if __name__ == "__main__":
    # 启动协议修复代理
    proxy = ProtocolFixProxy()
    proxy.start()