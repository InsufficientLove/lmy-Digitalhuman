#!/usr/bin/env python3
"""
最简化的MuseTalk服务 - 用于测试导入问题
"""

print("🚀 最简化服务启动...")

# 基础导入
import os
import sys
import json
import socket
import argparse

print("✅ 基础模块导入成功")

# 添加MuseTalk路径
musetalk_path = os.path.join(os.path.dirname(__file__), '..', 'MuseTalk')
sys.path.append(musetalk_path)
print(f"✅ MuseTalk路径添加: {musetalk_path}")

# 逐个测试MuseTalk模块导入
try:
    from musetalk.utils.face_parsing import FaceParsing
    print("✅ FaceParsing导入成功")
except Exception as e:
    print(f"❌ FaceParsing导入失败: {str(e)}")

try:
    from musetalk.utils.utils import datagen, load_all_model
    print("✅ utils导入成功")
except Exception as e:
    print(f"❌ utils导入失败: {str(e)}")

try:
    from musetalk.utils.preprocessing import get_landmark_and_bbox, read_imgs
    print("✅ preprocessing导入成功")
except Exception as e:
    print(f"❌ preprocessing导入失败: {str(e)}")

try:
    from musetalk.utils.blending import get_image, get_image_prepare_material, get_image_blending
    print("✅ blending导入成功")
except Exception as e:
    print(f"❌ blending导入失败: {str(e)}")

try:
    from musetalk.utils.audio_processor import AudioProcessor
    print("✅ audio_processor导入成功")
except Exception as e:
    print(f"❌ audio_processor导入失败: {str(e)}")

# 其他可能有问题的导入
try:
    from transformers import WhisperModel
    print("✅ WhisperModel导入成功")
except Exception as e:
    print(f"❌ WhisperModel导入失败: {str(e)}")

try:
    from moviepy.editor import VideoFileClip, AudioFileClip
    print("✅ moviepy导入成功")
except Exception as e:
    print(f"❌ moviepy导入失败: {str(e)}")

try:
    import imageio
    print("✅ imageio导入成功")
except Exception as e:
    print(f"❌ imageio导入失败: {str(e)}")

try:
    from tqdm import tqdm
    print("✅ tqdm导入成功")
except Exception as e:
    print(f"❌ tqdm导入失败: {str(e)}")

print("🎉 所有导入测试完成")

# 测试简单的socket服务器
def main():
    print("🚀 main函数启动...")
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=9999)
    args = parser.parse_args()
    
    print(f"📋 参数解析成功: port={args.port}")
    
    # 启动简单的socket服务器
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(('localhost', args.port))
        server_socket.listen(5)
        
        print(f"🌐 服务器启动成功，监听端口: {args.port}")
        print("📡 等待连接...")
        
        # 保持监听
        while True:
            try:
                client_socket, addr = server_socket.accept()
                print(f"🔗 客户端连接: {addr}")
                
                # 发送简单响应
                response = b'{"Success": true, "Message": "Minimal service is running"}'
                client_socket.send(response)
                client_socket.close()
                
            except Exception as e:
                print(f"❌ 处理连接失败: {str(e)}")
                
    except Exception as e:
        print(f"❌ 服务器启动失败: {str(e)}")

if __name__ == "__main__":
    main()