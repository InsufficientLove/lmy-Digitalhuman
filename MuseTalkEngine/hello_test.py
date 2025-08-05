#!/usr/bin/env python3
print("🎉 Hello from Python! Script is working!")
print("🐍 Python executable:", __import__('sys').executable)
print("🐍 Working directory:", __import__('os').getcwd())
print("🐍 Script path:", __file__)

import socket
import time

# 简单的socket服务器
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(('localhost', 9999))
server.listen(1)
print("🌐 Socket server started on port 9999")

# 保持运行
while True:
    try:
        client, addr = server.accept()
        print(f"🔗 Client connected: {addr}")
        client.send(b'Hello from Python!')
        client.close()
    except Exception as e:
        print(f"❌ Error: {e}")
        break