#!/usr/bin/env python3
import sys
import os
import socket
import time
import traceback

try:
    print("🎉 Hello from Python! Script is working!")
    print("🐍 Python executable:", sys.executable)
    print("🐍 Working directory:", os.getcwd())
    print("🐍 Script path:", __file__)
    print("🐍 Python version:", sys.version)
    print("🐍 Arguments:", sys.argv)
    
    # 强制刷新输出
    sys.stdout.flush()
    sys.stderr.flush()
    
    print("🔧 Starting socket server...")
    sys.stdout.flush()
    
    # 简单的socket服务器
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('localhost', 9999))
    server.listen(1)
    print("🌐 Socket server started on port 9999")
    sys.stdout.flush()
    
    # 保持运行
    connection_count = 0
    while connection_count < 10:  # 限制连接数，避免无限循环
        try:
            print(f"📡 Waiting for connection #{connection_count + 1}...")
            sys.stdout.flush()
            
            server.settimeout(30.0)  # 30秒超时
            client, addr = server.accept()
            connection_count += 1
            
            print(f"🔗 Client connected: {addr} (#{connection_count})")
            client.send(b'Hello from Python!')
            client.close()
            sys.stdout.flush()
            
        except socket.timeout:
            print("⏰ Socket timeout, continuing...")
            sys.stdout.flush()
        except Exception as e:
            print(f"❌ Socket error: {e}")
            traceback.print_exc()
            sys.stdout.flush()
            break
    
    print("🎯 Closing server after handling connections")
    server.close()
    
except Exception as e:
    print(f"❌ Fatal error: {e}")
    traceback.print_exc()
    sys.stdout.flush()
    sys.stderr.flush()
finally:
    print("🏁 Script finished")
    sys.stdout.flush()