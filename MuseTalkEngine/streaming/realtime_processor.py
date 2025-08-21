#!/usr/bin/env python3
"""
真·伪实时处理器 - 核心实现
目标：1-2秒延迟的流畅对话体验
"""

import os
import sys
import time
import json
import asyncio
import threading
import queue
import librosa
import numpy as np
import soundfile as sf
from pathlib import Path
from typing import Dict, List, Optional, Tuple, AsyncGenerator
from concurrent.futures import ThreadPoolExecutor
from collections import deque

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class RealtimeSegmentProcessor:
    """真实时分段处理器 - 优化版"""
    
    def __init__(self):
        self.service = None
        self.template_cache = {}
        
        # 优化的分段参数
        self.optimal_segment_duration = 1.0  # 最优1秒分段（平衡延迟和质量）
        self.max_segment_duration = 1.5      # 最长1.5秒
        self.min_segment_duration = 0.3      # 最短0.3秒（避免太碎片化）
        
        # 预处理缓冲区
        self.audio_buffer = deque(maxlen=100)  # 音频缓冲
        self.result_queue = asyncio.Queue()    # 结果队列
        
        # 并行处理线程池
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # 性能监控
        self.metrics = {
            'segment_count': 0,
            'total_process_time': 0,
            'average_latency': 0
        }
        
    def initialize(self):
        """初始化服务 - 预加载模型"""
        from offline.batch_inference import UltraFastMuseTalkService
        
        print("🚀 初始化实时处理器...")
        self.service = UltraFastMuseTalkService()
        self.service.initialize_models()
        
        # 预热模型（减少首次推理延迟）
        self._warmup_models()
        print("✅ 实时处理器初始化完成")
    
    def _warmup_models(self):
        """预热模型 - 减少首次推理延迟"""
        try:
            print("🔥 预热模型...")
            # 创建一个短音频进行预热
            dummy_audio = np.zeros(16000)  # 1秒静音
            dummy_path = "/tmp/warmup.wav"
            sf.write(dummy_path, dummy_audio, 16000)
            
            # 执行一次推理预热GPU
            if hasattr(self.service, 'extract_audio_features_ultra_fast'):
                self.service.extract_audio_features_ultra_fast(dummy_path, 25)
            
            os.remove(dummy_path)
            print("✅ 模型预热完成")
        except Exception as e:
            print(f"⚠️ 模型预热失败: {e}")
    
    def smart_segment_audio(self, audio_data: np.ndarray, sr: int = 16000) -> List[Dict]:
        """智能音频分段 - 基于语音活动检测"""
        segments = []
        
        # 使用librosa的onset detection找到语音段落
        onset_frames = librosa.onset.onset_detect(
            y=audio_data, 
            sr=sr, 
            units='samples',
            backtrack=True
        )
        
        # 如果没有检测到onset，使用固定分段
        if len(onset_frames) == 0:
            return self._fixed_segment_audio(audio_data, sr)
        
        # 基于onset智能分段
        current_start = 0
        segment_index = 0
        
        for i, onset in enumerate(onset_frames):
            segment_duration = (onset - current_start) / sr
            
            # 检查是否需要分段
            if segment_duration >= self.optimal_segment_duration:
                # 创建段
                segment_data = audio_data[current_start:onset]
                if len(segment_data) > int(self.min_segment_duration * sr):
                    segments.append(self._create_segment(
                        segment_data, sr, segment_index, current_start / sr
                    ))
                    segment_index += 1
                    current_start = onset
            elif segment_duration >= self.max_segment_duration:
                # 强制分段（避免太长）
                end_pos = current_start + int(self.max_segment_duration * sr)
                segment_data = audio_data[current_start:end_pos]
                segments.append(self._create_segment(
                    segment_data, sr, segment_index, current_start / sr
                ))
                segment_index += 1
                current_start = end_pos
        
        # 处理最后一段
        if current_start < len(audio_data):
            segment_data = audio_data[current_start:]
            if len(segment_data) > int(self.min_segment_duration * sr):
                segments.append(self._create_segment(
                    segment_data, sr, segment_index, current_start / sr
                ))
        
        return segments
    
    def _fixed_segment_audio(self, audio_data: np.ndarray, sr: int) -> List[Dict]:
        """固定长度分段（后备方案）"""
        segments = []
        segment_samples = int(self.optimal_segment_duration * sr)
        segment_index = 0
        
        for i in range(0, len(audio_data), segment_samples):
            segment_data = audio_data[i:i + segment_samples]
            if len(segment_data) > int(self.min_segment_duration * sr):
                segments.append(self._create_segment(
                    segment_data, sr, segment_index, i / sr
                ))
                segment_index += 1
        
        return segments
    
    def _create_segment(self, audio_data: np.ndarray, sr: int, index: int, start_time: float) -> Dict:
        """创建音频段信息"""
        # 保存临时文件
        segment_path = f"/tmp/rt_segment_{index}_{int(time.time()*1000)}.wav"
        sf.write(segment_path, audio_data, sr)
        
        duration = len(audio_data) / sr
        frames = int(duration * 25)  # 25fps
        
        return {
            'index': index,
            'path': segment_path,
            'start_time': start_time,
            'duration': duration,
            'frames': frames,
            'audio_data': audio_data  # 保留原始数据用于快速处理
        }
    
    async def process_segment_async(
        self,
        template_id: str,
        segment_info: Dict,
        priority: int = 0
    ) -> Dict:
        """异步处理单个音频片段 - 优化版"""
        start_time = time.time()
        
        try:
            # 动态调整推理参数
            num_frames = segment_info['frames']
            
            # 极速模式：短段用小batch，长段跳帧
            if num_frames <= 12:  # 0.5秒以内
                batch_size = num_frames
                skip_frames = 1
            elif num_frames <= 25:  # 1秒以内
                batch_size = 12
                skip_frames = 2
            else:  # 1秒以上
                batch_size = 8
                skip_frames = 3
            
            # 生成输出路径
            output_path = f"/tmp/rt_video_{template_id}_{segment_info['index']}_{int(time.time()*1000)}.mp4"
            
            # 获取缓存目录
            cache_dir = os.environ.get('MUSE_TEMPLATE_CACHE_DIR', '/opt/musetalk/template_cache')
            
            # 异步执行推理
            loop = asyncio.get_event_loop()
            success = await loop.run_in_executor(
                self.executor,
                self._run_inference,
                template_id,
                segment_info['path'],
                output_path,
                cache_dir,
                batch_size,
                skip_frames
            )
            
            process_time = time.time() - start_time
            
            # 更新性能指标
            self.metrics['segment_count'] += 1
            self.metrics['total_process_time'] += process_time
            self.metrics['average_latency'] = self.metrics['total_process_time'] / self.metrics['segment_count']
            
            result = {
                'success': success,
                'index': segment_info['index'],
                'path': output_path if success else None,
                'duration': segment_info['duration'],
                'frames': num_frames,
                'process_time': process_time,
                'start_time': segment_info['start_time'],
                'latency': process_time * 1000  # 毫秒
            }
            
            # 性能日志
            if process_time > 1.5:
                print(f"⚠️ 段 {segment_info['index']} 处理较慢: {process_time:.2f}秒")
            else:
                print(f"⚡ 段 {segment_info['index']} 快速完成: {process_time:.2f}秒")
            
            return result
            
        except Exception as e:
            print(f"❌ 段处理异常: {e}")
            return {
                'success': False,
                'index': segment_info['index'],
                'error': str(e),
                'process_time': time.time() - start_time
            }
    
    def _run_inference(self, template_id, audio_path, output_path, cache_dir, batch_size, skip_frames):
        """运行推理（在线程池中执行）"""
        return self.service.ultra_fast_inference_parallel(
            template_id=template_id,
            audio_path=audio_path,
            output_path=output_path,
            cache_dir=cache_dir,
            batch_size=batch_size,
            skip_frames=skip_frames,
            streaming=True,
            auto_adjust=True  # 自动调整batch_size避免OOM
        )
    
    async def process_audio_stream(
        self,
        template_id: str,
        audio_stream: AsyncGenerator,
        callback=None
    ):
        """处理实时音频流"""
        print("🎙️ 开始处理实时音频流...")
        
        # 音频缓冲区
        audio_buffer = []
        buffer_duration = 0
        segment_tasks = []
        
        async for audio_chunk in audio_stream:
            # 累积音频
            audio_buffer.append(audio_chunk)
            buffer_duration += len(audio_chunk) / 16000  # 假设16kHz
            
            # 当缓冲区达到最优长度时处理
            if buffer_duration >= self.optimal_segment_duration:
                # 合并音频
                audio_data = np.concatenate(audio_buffer)
                
                # 创建段
                segment = self._create_segment(
                    audio_data, 
                    16000, 
                    len(segment_tasks),
                    len(segment_tasks) * self.optimal_segment_duration
                )
                
                # 异步处理（不阻塞）
                task = asyncio.create_task(
                    self.process_segment_async(template_id, segment)
                )
                segment_tasks.append(task)
                
                # 清空缓冲区
                audio_buffer = []
                buffer_duration = 0
                
                # 检查完成的任务
                for task in segment_tasks:
                    if task.done():
                        result = await task
                        if callback and result['success']:
                            await callback(result)
        
        # 处理剩余音频
        if audio_buffer:
            audio_data = np.concatenate(audio_buffer)
            if len(audio_data) > int(self.min_segment_duration * 16000):
                segment = self._create_segment(
                    audio_data, 16000, len(segment_tasks), 
                    len(segment_tasks) * self.optimal_segment_duration
                )
                result = await self.process_segment_async(template_id, segment)
                if callback and result['success']:
                    await callback(result)
        
        # 等待所有任务完成
        if segment_tasks:
            results = await asyncio.gather(*segment_tasks)
            print(f"✅ 处理完成: {len(results)}段, 平均延迟: {self.metrics['average_latency']:.1f}ms")
    
    def cleanup(self):
        """清理资源"""
        try:
            # 清理临时文件
            import glob
            for pattern in ["/tmp/rt_segment_*.wav", "/tmp/rt_video_*.mp4"]:
                for file in glob.glob(pattern):
                    try:
                        os.remove(file)
                    except:
                        pass
            
            # 关闭线程池
            self.executor.shutdown(wait=False)
            
            print("🧹 资源清理完成")
        except Exception as e:
            print(f"⚠️ 清理失败: {e}")


class StreamingPipeline:
    """完整的流式处理管道"""
    
    def __init__(self):
        self.processor = RealtimeSegmentProcessor()
        self.whisper_service = None  # WhisperNet服务
        self.websocket_clients = {}
        
    async def initialize(self):
        """初始化管道"""
        print("🚀 初始化流式管道...")
        self.processor.initialize()
        # TODO: 初始化WhisperNet
        print("✅ 流式管道就绪")
    
    async def handle_realtime_conversation(
        self,
        websocket,
        template_id: str
    ):
        """处理实时对话"""
        client_id = id(websocket)
        self.websocket_clients[client_id] = websocket
        
        try:
            print(f"👤 客户端 {client_id} 连接")
            
            # 发送就绪信号
            await websocket.send(json.dumps({
                'type': 'ready',
                'message': '系统就绪，请开始说话'
            }))
            
            # 处理消息
            async for message in websocket:
                data = json.loads(message)
                
                if data['type'] == 'audio_chunk':
                    # 处理音频块
                    audio_data = np.frombuffer(
                        bytes.fromhex(data['audio']), 
                        dtype=np.float32
                    )
                    
                    # 创建音频流生成器
                    async def audio_generator():
                        yield audio_data
                    
                    # 处理并发送结果
                    await self.processor.process_audio_stream(
                        template_id,
                        audio_generator(),
                        callback=lambda r: self._send_result(websocket, r)
                    )
                    
                elif data['type'] == 'complete_audio':
                    # 处理完整音频
                    audio_path = data['audio_path']
                    await self._process_complete_audio(
                        websocket, template_id, audio_path
                    )
                    
        except Exception as e:
            print(f"❌ 客户端 {client_id} 错误: {e}")
        finally:
            del self.websocket_clients[client_id]
            print(f"👋 客户端 {client_id} 断开")
    
    async def _send_result(self, websocket, result):
        """发送处理结果"""
        await websocket.send(json.dumps({
            'type': 'video_segment',
            'data': {
                'index': result['index'],
                'video_url': f"/videos/{Path(result['path']).name}",
                'duration': result['duration'],
                'latency': result['latency'],
                'timestamp': time.time()
            }
        }))
    
    async def _process_complete_audio(self, websocket, template_id, audio_path):
        """处理完整音频文件"""
        # 加载音频
        audio_data, sr = librosa.load(audio_path, sr=16000)
        
        # 智能分段
        segments = self.processor.smart_segment_audio(audio_data, sr)
        
        # 并行处理所有段
        tasks = []
        for segment in segments:
            task = asyncio.create_task(
                self.processor.process_segment_async(template_id, segment)
            )
            tasks.append(task)
        
        # 逐个发送结果（保持顺序）
        for task in tasks:
            result = await task
            if result['success']:
                await self._send_result(websocket, result)
        
        # 发送完成信号
        await websocket.send(json.dumps({
            'type': 'complete',
            'message': '处理完成',
            'metrics': self.processor.metrics
        }))


# WebSocket服务器入口
async def start_websocket_server(host='0.0.0.0', port=8766):
    """启动WebSocket服务器"""
    import websockets
    
    pipeline = StreamingPipeline()
    await pipeline.initialize()
    
    async def handler(websocket, path):
        # 从路径获取template_id
        template_id = path.strip('/') or 'default'
        await pipeline.handle_realtime_conversation(websocket, template_id)
    
    print(f"🌐 WebSocket服务器启动: ws://{host}:{port}")
    async with websockets.serve(handler, host, port):
        await asyncio.Future()  # 永远运行


if __name__ == "__main__":
    # 测试入口
    asyncio.run(start_websocket_server())