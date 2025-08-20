#!/usr/bin/env python3
"""
MuseTalk Engine 主入口
根据模式启动不同的服务
"""

import os
import sys
import argparse

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def start_offline_service():
    """启动离线批处理服务"""
    from offline.batch_inference import main as offline_main
    print("🚀 启动离线批处理服务...")
    offline_main()

def start_streaming_service():
    """启动流式处理服务"""
    from streaming.segment_processor import StreamingServer
    import asyncio
    import websockets
    
    print("🚀 启动流式处理服务...")
    server = StreamingServer()
    server.processor.initialize()
    
    # 启动WebSocket服务器
    start_server = websockets.serve(
        server.handle_connection, 
        "0.0.0.0", 
        8766
    )
    
    asyncio.get_event_loop().run_until_complete(start_server)
    print("✅ 流式服务运行在 ws://0.0.0.0:8766")
    asyncio.get_event_loop().run_forever()

def start_hybrid_service():
    """启动混合服务（默认）"""
    # 先初始化核心组件
    from core.launcher import init_templates, init_cache_dirs
    init_cache_dirs()
    init_templates()
    
    # 启动离线服务
    from offline.batch_inference import UltraFastMuseTalkService
    service = UltraFastMuseTalkService()
    service.initialize_models()
    
    print("✅ 混合服务就绪（支持离线和流式）")
    
    # 启动主循环
    from offline.batch_inference import main as offline_main
    offline_main()

def main():
    parser = argparse.ArgumentParser(description='MuseTalk Engine')
    parser.add_argument(
        '--mode', 
        choices=['offline', 'streaming', 'hybrid'],
        default='hybrid',
        help='运行模式'
    )
    
    args = parser.parse_args()
    
    if args.mode == 'offline':
        start_offline_service()
    elif args.mode == 'streaming':
        start_streaming_service()
    else:
        start_hybrid_service()

if __name__ == "__main__":
    main()