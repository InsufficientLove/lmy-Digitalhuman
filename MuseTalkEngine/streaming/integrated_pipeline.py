#!/usr/bin/env python3
"""
集成化流式处理管道
整合WhisperNet ASR + LLM + TTS + MuseTalk
实现端到端的伪实时对话
"""

import os
import sys
import time
import json
import asyncio
import numpy as np
import websockets
from typing import Dict, Optional, AsyncGenerator
from concurrent.futures import ThreadPoolExecutor
import queue
import threading

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from streaming.realtime_processor import RealtimeSegmentProcessor


class IntegratedRealtimePipeline:
    """集成的实时处理管道"""
    
    def __init__(self):
        # 核心组件
        self.musetalk_processor = RealtimeSegmentProcessor()
        
        # 连接配置
        self.csharp_api_url = "http://lmy-digitalhuman:5000"  # C#服务地址
        self.whisper_endpoint = f"{self.csharp_api_url}/api/whisper/stream"
        self.llm_endpoint = f"{self.csharp_api_url}/api/llm/stream"
        self.tts_endpoint = f"{self.csharp_api_url}/api/tts/stream"
        
        # 处理队列
        self.audio_queue = asyncio.Queue(maxsize=10)
        self.text_queue = asyncio.Queue(maxsize=10)
        self.tts_queue = asyncio.Queue(maxsize=10)
        self.video_queue = asyncio.Queue(maxsize=10)
        
        # 线程池
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # 性能监控
        self.metrics = {
            'asr_latency': [],
            'llm_latency': [],
            'tts_latency': [],
            'musetalk_latency': [],
            'total_latency': []
        }
        
        # 当前会话状态
        self.current_session = None
        self.template_id = None
        
    async def initialize(self, template_id: str):
        """初始化管道"""
        print("🚀 初始化集成管道...")
        self.template_id = template_id
        
        # 初始化MuseTalk
        await asyncio.get_event_loop().run_in_executor(
            self.executor,
            self.musetalk_processor.initialize
        )
        
        print("✅ 集成管道初始化完成")
    
    async def process_user_audio_stream(
        self,
        audio_stream: AsyncGenerator,
        websocket=None
    ):
        """处理用户音频流 - 完整的对话流程"""
        print("🎙️ 开始处理用户音频...")
        
        # 启动并行处理任务
        tasks = [
            asyncio.create_task(self._asr_task(audio_stream)),
            asyncio.create_task(self._llm_task()),
            asyncio.create_task(self._tts_task()),
            asyncio.create_task(self._musetalk_task()),
            asyncio.create_task(self._output_task(websocket))
        ]
        
        try:
            # 等待所有任务
            await asyncio.gather(*tasks)
        except Exception as e:
            print(f"❌ 管道处理错误: {e}")
            # 取消所有任务
            for task in tasks:
                task.cancel()
    
    async def _asr_task(self, audio_stream: AsyncGenerator):
        """ASR任务 - 语音识别"""
        print("🎤 ASR任务启动")
        
        # 音频缓冲
        audio_buffer = []
        buffer_duration = 0
        
        async for audio_chunk in audio_stream:
            start_time = time.time()
            
            # 累积音频
            audio_buffer.append(audio_chunk)
            buffer_duration += len(audio_chunk) / 16000
            
            # 每0.5秒识别一次（平衡实时性和准确性）
            if buffer_duration >= 0.5:
                # 合并音频
                audio_data = np.concatenate(audio_buffer)
                
                # 调用WhisperNet（通过C#服务）
                text = await self._call_whisper(audio_data)
                
                if text:
                    # 放入文本队列
                    await self.text_queue.put({
                        'text': text,
                        'timestamp': time.time()
                    })
                    
                    # 记录延迟
                    latency = (time.time() - start_time) * 1000
                    self.metrics['asr_latency'].append(latency)
                    print(f"📝 识别: {text} (延迟: {latency:.0f}ms)")
                
                # 清空缓冲
                audio_buffer = []
                buffer_duration = 0
    
    async def _llm_task(self):
        """LLM任务 - 生成回复"""
        print("🤖 LLM任务启动")
        
        sentence_buffer = []
        
        while True:
            try:
                # 获取识别文本
                text_data = await self.text_queue.get()
                start_time = time.time()
                
                # 累积成句子
                sentence_buffer.append(text_data['text'])
                
                # 检测句子结束（简单规则）
                if any(punct in text_data['text'] for punct in ['。', '？', '！', '.', '?', '!']):
                    sentence = ''.join(sentence_buffer)
                    sentence_buffer = []
                    
                    # 调用LLM生成回复（流式）
                    async for response_chunk in self._call_llm_stream(sentence):
                        # 放入TTS队列
                        await self.tts_queue.put({
                            'text': response_chunk,
                            'timestamp': time.time()
                        })
                        
                        # 记录首字延迟
                        if len(self.metrics['llm_latency']) == 0:
                            latency = (time.time() - start_time) * 1000
                            self.metrics['llm_latency'].append(latency)
                            print(f"💬 LLM首字: {latency:.0f}ms")
                            
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"❌ LLM错误: {e}")
    
    async def _tts_task(self):
        """TTS任务 - 语音合成"""
        print("🔊 TTS任务启动")
        
        text_buffer = []
        buffer_chars = 0
        
        while True:
            try:
                # 获取文本
                text_data = await self.tts_queue.get()
                start_time = time.time()
                
                # 累积文本
                text_buffer.append(text_data['text'])
                buffer_chars += len(text_data['text'])
                
                # 每10个字或遇到标点就合成
                if buffer_chars >= 10 or any(p in text_data['text'] for p in ['，', '。', '！', '？']):
                    text_to_synthesize = ''.join(text_buffer)
                    text_buffer = []
                    buffer_chars = 0
                    
                    # 调用TTS
                    audio_path = await self._call_tts(text_to_synthesize)
                    
                    if audio_path:
                        # 放入视频生成队列
                        await self.video_queue.put({
                            'audio_path': audio_path,
                            'text': text_to_synthesize,
                            'timestamp': time.time()
                        })
                        
                        # 记录延迟
                        latency = (time.time() - start_time) * 1000
                        self.metrics['tts_latency'].append(latency)
                        print(f"🎵 TTS完成: {latency:.0f}ms")
                        
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"❌ TTS错误: {e}")
    
    async def _musetalk_task(self):
        """MuseTalk任务 - 生成数字人视频"""
        print("🎭 MuseTalk任务启动")
        
        segment_index = 0
        
        while True:
            try:
                # 获取音频
                audio_data = await self.video_queue.get()
                start_time = time.time()
                
                # 创建段信息
                segment_info = {
                    'index': segment_index,
                    'path': audio_data['audio_path'],
                    'start_time': segment_index,
                    'duration': 1.0,  # 估算
                    'frames': 25  # 估算
                }
                
                # 处理视频
                result = await self.musetalk_processor.process_segment_async(
                    self.template_id,
                    segment_info,
                    priority=segment_index
                )
                
                if result['success']:
                    # 记录延迟
                    latency = (time.time() - start_time) * 1000
                    self.metrics['musetalk_latency'].append(latency)
                    print(f"🎬 视频生成: {latency:.0f}ms")
                    
                    # 添加到输出
                    result['text'] = audio_data['text']
                    await self.video_queue.put(result)
                
                segment_index += 1
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"❌ MuseTalk错误: {e}")
    
    async def _output_task(self, websocket):
        """输出任务 - 发送结果到客户端"""
        print("📤 输出任务启动")
        
        if not websocket:
            return
        
        while True:
            try:
                # 获取视频结果
                result = await self.video_queue.get()
                
                # 发送到客户端
                await websocket.send(json.dumps({
                    'type': 'video_segment',
                    'data': {
                        'index': result['index'],
                        'video_path': result['path'],
                        'text': result.get('text', ''),
                        'latency': result.get('latency', 0),
                        'timestamp': time.time()
                    }
                }))
                
                # 计算总延迟
                total_latency = sum([
                    np.mean(self.metrics['asr_latency']) if self.metrics['asr_latency'] else 0,
                    np.mean(self.metrics['llm_latency']) if self.metrics['llm_latency'] else 0,
                    np.mean(self.metrics['tts_latency']) if self.metrics['tts_latency'] else 0,
                    np.mean(self.metrics['musetalk_latency']) if self.metrics['musetalk_latency'] else 0
                ])
                
                print(f"⏱️ 端到端延迟: {total_latency:.0f}ms")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"❌ 输出错误: {e}")
    
    async def _call_whisper(self, audio_data: np.ndarray) -> Optional[str]:
        """调用WhisperNet服务"""
        # TODO: 实际调用C#的WhisperNet服务
        # 这里返回模拟数据
        await asyncio.sleep(0.2)  # 模拟200ms延迟
        return "你好，请问有什么可以帮助您的？"
    
    async def _call_llm_stream(self, text: str) -> AsyncGenerator:
        """调用LLM服务（流式）"""
        # TODO: 实际调用C#的LLM服务
        # 这里返回模拟数据
        response = "非常感谢您的提问。我是您的数字人助手，很高兴为您服务。"
        
        # 模拟流式返回
        for i in range(0, len(response), 5):
            await asyncio.sleep(0.05)  # 模拟50ms延迟
            yield response[i:i+5]
    
    async def _call_tts(self, text: str) -> Optional[str]:
        """调用TTS服务"""
        # TODO: 实际调用C#的TTS服务
        # 这里返回模拟路径
        await asyncio.sleep(0.1)  # 模拟100ms延迟
        return f"/tmp/tts_audio_{int(time.time()*1000)}.wav"
    
    def get_performance_report(self) -> Dict:
        """获取性能报告"""
        return {
            'asr_avg_latency': np.mean(self.metrics['asr_latency']) if self.metrics['asr_latency'] else 0,
            'llm_first_token_latency': self.metrics['llm_latency'][0] if self.metrics['llm_latency'] else 0,
            'tts_avg_latency': np.mean(self.metrics['tts_latency']) if self.metrics['tts_latency'] else 0,
            'musetalk_avg_latency': np.mean(self.metrics['musetalk_latency']) if self.metrics['musetalk_latency'] else 0,
            'total_segments_processed': len(self.metrics['musetalk_latency']),
            'estimated_total_latency': sum([
                np.mean(self.metrics['asr_latency']) if self.metrics['asr_latency'] else 0,
                self.metrics['llm_latency'][0] if self.metrics['llm_latency'] else 0,
                np.mean(self.metrics['tts_latency']) if self.metrics['tts_latency'] else 0,
                np.mean(self.metrics['musetalk_latency']) if self.metrics['musetalk_latency'] else 0
            ])
        }


class RealtimeWebSocketServer:
    """实时WebSocket服务器"""
    
    def __init__(self):
        self.pipeline = IntegratedRealtimePipeline()
        self.clients = {}
        
    async def handle_client(self, websocket, path):
        """处理客户端连接"""
        client_id = id(websocket)
        self.clients[client_id] = websocket
        
        try:
            print(f"👤 客户端 {client_id} 连接")
            
            # 获取template_id
            template_id = path.strip('/') or 'default'
            
            # 初始化管道
            await self.pipeline.initialize(template_id)
            
            # 发送就绪信号
            await websocket.send(json.dumps({
                'type': 'ready',
                'message': '系统就绪',
                'template_id': template_id
            }))
            
            # 处理消息
            async for message in websocket:
                data = json.loads(message)
                
                if data['type'] == 'start_conversation':
                    # 开始对话
                    print("🎬 开始实时对话")
                    
                    # 创建音频流生成器
                    async def audio_generator():
                        while True:
                            msg = await websocket.recv()
                            msg_data = json.loads(msg)
                            if msg_data['type'] == 'audio_chunk':
                                audio_bytes = bytes.fromhex(msg_data['audio'])
                                audio_data = np.frombuffer(audio_bytes, dtype=np.float32)
                                yield audio_data
                            elif msg_data['type'] == 'end_audio':
                                break
                    
                    # 处理音频流
                    await self.pipeline.process_user_audio_stream(
                        audio_generator(),
                        websocket
                    )
                    
                elif data['type'] == 'get_metrics':
                    # 返回性能指标
                    metrics = self.pipeline.get_performance_report()
                    await websocket.send(json.dumps({
                        'type': 'metrics',
                        'data': metrics
                    }))
                    
        except websockets.ConnectionClosed:
            print(f"👋 客户端 {client_id} 断开")
        except Exception as e:
            print(f"❌ 客户端 {client_id} 错误: {e}")
        finally:
            if client_id in self.clients:
                del self.clients[client_id]
    
    async def start(self, host='0.0.0.0', port=8766):
        """启动服务器"""
        print(f"🌐 实时WebSocket服务器启动: ws://{host}:{port}")
        async with websockets.serve(self.handle_client, host, port):
            await asyncio.Future()


# 主入口
async def main():
    """主函数"""
    server = RealtimeWebSocketServer()
    await server.start()


if __name__ == "__main__":
    asyncio.run(main())