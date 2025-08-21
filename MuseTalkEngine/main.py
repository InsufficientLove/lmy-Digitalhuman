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
    """启动流式处理服务 - 增强版"""
    import asyncio
    
    print("🚀 启动流式处理服务...")
    
    # 根据环境变量选择服务模式
    streaming_mode = os.environ.get('STREAMING_MODE', 'integrated')
    
    if streaming_mode == 'integrated':
        # 使用集成管道（推荐）
        from streaming.integrated_pipeline import RealtimeWebSocketServer
        server = RealtimeWebSocketServer()
        asyncio.run(server.start("0.0.0.0", 8766))
    elif streaming_mode == 'realtime':
        # 使用实时处理器
        from streaming.realtime_processor import start_websocket_server
        asyncio.run(start_websocket_server("0.0.0.0", 8766))
    else:
        # 使用基础分段处理器
        from streaming.segment_processor import StreamingServer
        import websockets
        server = StreamingServer()
        server.processor.initialize()
        
        start_server = websockets.serve(
            server.handle_connection, 
            "0.0.0.0", 
            8766
        )
        
        asyncio.get_event_loop().run_until_complete(start_server)
        print("✅ 流式服务运行在 ws://0.0.0.0:8766")
        asyncio.get_event_loop().run_forever()

def start_hybrid_service():
    """启动混合服务（默认） - API模式"""
    # 先初始化核心组件
    from core.launcher import init_templates, init_cache_dirs
    init_cache_dirs()
    init_templates()
    
    # 启动API服务（供C#调用）
    from streaming.api_service import start_api_server
    print("🚀 启动MuseTalk API服务（供C#调用）...")
    start_api_server(host='0.0.0.0', port=28888)

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