#!/usr/bin/env python3
"""
流式处理测试客户端
用于测试WebSocket连接和伪实时处理
"""

import asyncio
import websockets
import json
import numpy as np
import time
import argparse


class StreamingTestClient:
    """流式测试客户端"""
    
    def __init__(self, server_url="ws://localhost:8766"):
        self.server_url = server_url
        self.metrics = {
            'segments_received': 0,
            'total_latency': [],
            'first_segment_time': None
        }
    
    async def test_streaming(self, template_id="default", audio_path=None):
        """测试流式处理"""
        print(f"🔗 连接到服务器: {self.server_url}/{template_id}")
        
        async with websockets.connect(f"{self.server_url}/{template_id}") as websocket:
            # 等待就绪信号
            response = await websocket.recv()
            data = json.loads(response)
            print(f"✅ 服务器响应: {data['message']}")
            
            if audio_path:
                # 测试完整音频
                await self.test_complete_audio(websocket, audio_path)
            else:
                # 测试实时音频流
                await self.test_realtime_stream(websocket)
    
    async def test_complete_audio(self, websocket, audio_path):
        """测试完整音频处理"""
        print(f"📁 发送音频文件: {audio_path}")
        
        # 发送开始信号
        await websocket.send(json.dumps({
            'command': 'start_stream',
            'template_id': 'default',
            'audio_path': audio_path
        }))
        
        start_time = time.time()
        
        # 接收处理结果
        while True:
            response = await websocket.recv()
            data = json.loads(response)
            
            if data['type'] == 'segment':
                self.metrics['segments_received'] += 1
                segment_data = data['data']
                
                # 记录第一段时间
                if self.metrics['first_segment_time'] is None:
                    self.metrics['first_segment_time'] = time.time() - start_time
                    print(f"⚡ 第一段延迟: {self.metrics['first_segment_time']*1000:.0f}ms")
                
                print(f"📹 收到视频段 {segment_data['index']}: "
                      f"处理时间={segment_data['process_time']:.2f}s")
                
            elif data['type'] == 'complete':
                total_time = time.time() - start_time
                print(f"✅ 处理完成")
                print(f"📊 统计:")
                print(f"  - 总段数: {self.metrics['segments_received']}")
                print(f"  - 总时间: {total_time:.2f}秒")
                print(f"  - 首段延迟: {self.metrics['first_segment_time']*1000:.0f}ms")
                print(f"  - 平均每段: {total_time/max(1, self.metrics['segments_received']):.2f}秒")
                break
    
    async def test_realtime_stream(self, websocket):
        """测试实时音频流"""
        print("🎤 开始实时音频流测试...")
        
        # 发送开始对话信号
        await websocket.send(json.dumps({
            'type': 'start_conversation'
        }))
        
        # 模拟发送音频块
        for i in range(10):
            # 生成模拟音频数据（0.5秒）
            audio_chunk = np.random.randn(8000).astype(np.float32)
            
            # 发送音频块
            await websocket.send(json.dumps({
                'type': 'audio_chunk',
                'audio': audio_chunk.tobytes().hex()
            }))
            
            print(f"📤 发送音频块 {i+1}/10")
            
            # 等待一段时间模拟实时
            await asyncio.sleep(0.5)
        
        # 发送结束信号
        await websocket.send(json.dumps({
            'type': 'end_audio'
        }))
        
        # 接收结果
        while True:
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(response)
                
                if data['type'] == 'video_segment':
                    segment = data['data']
                    print(f"📹 收到视频段 {segment['index']}: "
                          f"延迟={segment['latency']:.0f}ms")
                    
                elif data['type'] == 'complete':
                    print("✅ 实时流处理完成")
                    break
                    
            except asyncio.TimeoutError:
                print("⏱️ 等待超时，结束测试")
                break
        
        # 请求性能指标
        await websocket.send(json.dumps({
            'type': 'get_metrics'
        }))
        
        response = await websocket.recv()
        data = json.loads(response)
        if data['type'] == 'metrics':
            print("\n📊 性能指标:")
            metrics = data['data']
            for key, value in metrics.items():
                if isinstance(value, float):
                    print(f"  - {key}: {value:.1f}ms")
                else:
                    print(f"  - {key}: {value}")


async def benchmark_latency():
    """延迟基准测试"""
    print("🧪 开始延迟基准测试...")
    
    client = StreamingTestClient()
    
    # 测试不同长度的音频
    test_cases = [
        ("短音频", 1.0),   # 1秒
        ("中音频", 3.0),   # 3秒
        ("长音频", 10.0),  # 10秒
    ]
    
    for name, duration in test_cases:
        print(f"\n📝 测试: {name} ({duration}秒)")
        
        # 生成测试音频
        audio_data = np.random.randn(int(16000 * duration)).astype(np.float32)
        audio_path = f"/tmp/test_audio_{duration}s.wav"
        
        import soundfile as sf
        sf.write(audio_path, audio_data, 16000)
        
        # 运行测试
        await client.test_streaming(audio_path=audio_path)
        
        # 清理
        import os
        os.remove(audio_path)
        
        await asyncio.sleep(1)


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='流式处理测试客户端')
    parser.add_argument('--server', default='ws://localhost:8766', help='服务器地址')
    parser.add_argument('--template', default='default', help='模板ID')
    parser.add_argument('--audio', help='音频文件路径')
    parser.add_argument('--benchmark', action='store_true', help='运行基准测试')
    
    args = parser.parse_args()
    
    if args.benchmark:
        await benchmark_latency()
    else:
        client = StreamingTestClient(args.server)
        await client.test_streaming(args.template, args.audio)


if __name__ == "__main__":
    asyncio.run(main())