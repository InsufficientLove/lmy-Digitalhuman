#!/usr/bin/env python3
"""
最简单的导入测试脚本
"""
import sys
import os

print("🚀 Python导入测试开始...")
print(f"🐍 Python版本: {sys.version}")
print(f"🐍 工作目录: {os.getcwd()}")

# 测试基础模块
try:
    import torch
    print(f"✅ torch导入成功: {torch.__version__}")
except Exception as e:
    print(f"❌ torch导入失败: {str(e)}")
    sys.exit(1)

try:
    import cv2
    print(f"✅ cv2导入成功")
except Exception as e:
    print(f"❌ cv2导入失败: {str(e)}")

try:
    import numpy as np
    print(f"✅ numpy导入成功: {np.__version__}")
except Exception as e:
    print(f"❌ numpy导入失败: {str(e)}")

# 测试MuseTalk路径
musetalk_path = os.path.join(os.path.dirname(__file__), '..', 'MuseTalk')
print(f"📁 MuseTalk路径: {musetalk_path}")
print(f"📁 MuseTalk存在: {os.path.exists(musetalk_path)}")

sys.path.append(musetalk_path)

# 测试MuseTalk模块导入
try:
    from musetalk.utils.face_parsing import FaceParsing
    print("✅ FaceParsing导入成功")
except Exception as e:
    print(f"❌ FaceParsing导入失败: {str(e)}")

try:
    from musetalk.utils.utils import load_all_model
    print("✅ load_all_model导入成功")
except Exception as e:
    print(f"❌ load_all_model导入失败: {str(e)}")

try:
    from transformers import WhisperModel
    print("✅ WhisperModel导入成功")
except Exception as e:
    print(f"❌ WhisperModel导入失败: {str(e)}")

print("✅ 导入测试完成")

# 测试socket监听
import socket
import time

try:
    test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    test_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    test_socket.bind(('localhost', 9999))
    test_socket.listen(1)
    print("✅ 端口9999监听测试成功")
    
    # 保持监听5秒让C#能连接测试
    test_socket.settimeout(5.0)
    try:
        print("📡 等待连接测试...")
        client, addr = test_socket.accept()
        print(f"🔗 收到连接: {addr}")
        client.close()
    except socket.timeout:
        print("⏰ 连接测试超时")
    
    test_socket.close()
    
except Exception as e:
    print(f"❌ 端口测试失败: {str(e)}")

print("🎉 所有测试完成")