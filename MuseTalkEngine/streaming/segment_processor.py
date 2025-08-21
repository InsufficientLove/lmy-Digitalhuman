#!/usr/bin/env python3
"""
分段处理器 - 伪实时流式处理
将音频分成1-2秒片段进行快速处理
"""

import os
import sys
import time
import json
import asyncio
import librosa
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class SegmentProcessor:
    """分段处理器 - 复用离线推理优化"""
    
    def __init__(self):
        self.service = None
        self.template_cache = {}
        # 优化的分段参数 - 更短的段以降低延迟
        self.segment_duration = 1.0  # 每段标准1秒（平衡延迟和效率）
        self.max_segment_duration = 1.5  # 最长1.5秒
        self.min_segment_duration = 0.3  # 最短0.3秒（避免太碎片化）
        
    def initialize(self):
        """初始化服务"""
        from offline.batch_inference import UltraFastMuseTalkService
        
        print("🚀 初始化分段处理器...")
        self.service = UltraFastMuseTalkService()
        self.service.initialize_models()
        print("✅ 分段处理器初始化完成")
        
    def split_audio_to_segments(self, audio_path: str) -> List[Dict]:
        """将音频分割成小段"""
        try:
            # 加载音频
            audio, sr = librosa.load(audio_path, sr=16000)
            total_duration = len(audio) / sr
            
            segments = []
            current_pos = 0
            segment_index = 0
            
            while current_pos < len(audio):
                # 计算段长度
                segment_samples = int(self.segment_duration * sr)
                end_pos = min(current_pos + segment_samples, len(audio))
                
                # 提取段
                segment_audio = audio[current_pos:end_pos]
                segment_duration = len(segment_audio) / sr
                
                # 跳过太短的段
                if segment_duration < self.min_segment_duration:
                    break
                
                # 保存临时音频文件
                segment_path = f"/tmp/segment_{segment_index}.wav"
                import soundfile as sf
                sf.write(segment_path, segment_audio, sr)
                
                segments.append({
                    'index': segment_index,
                    'path': segment_path,
                    'start_time': current_pos / sr,
                    'duration': segment_duration,
                    'frames': int(segment_duration * 25)  # 25fps
                })
                
                current_pos = end_pos
                segment_index += 1
            
            print(f"📊 音频分割: {total_duration:.1f}秒 -> {len(segments)}段")
            return segments
            
        except Exception as e:
            print(f"❌ 音频分割失败: {e}")
            return []
    
    def process_segment(
        self, 
        template_id: str,
        segment_info: Dict,
        skip_frames: int = 1
    ) -> Dict:
        """处理单个音频片段 - 优化版"""
        try:
            start_time = time.time()
            
            # 优化的批次大小策略
            num_frames = segment_info['frames']
            if num_frames <= 12:  # 0.5秒以内 - 极速模式
                batch_size = min(num_frames, 6)
                skip_frames = 1
            elif num_frames <= 25:  # 1秒以内 - 快速模式
                batch_size = min(num_frames, 12)
                skip_frames = 2
            elif num_frames <= 50:  # 2秒以内 - 标准模式
                batch_size = 16
                skip_frames = 2
            else:  # 2秒以上 - 跳帧模式
                batch_size = 20
                skip_frames = 3
            
            # 生成输出路径
            output_path = f"/tmp/segment_{template_id}_{segment_info['index']}.mp4"
            
            # 获取缓存目录
            cache_dir = os.environ.get('MUSE_TEMPLATE_CACHE_DIR', '/opt/musetalk/template_cache')
            
            # 调用离线推理（复用所有优化）
            success = self.service.ultra_fast_inference_parallel(
                template_id=template_id,
                audio_path=segment_info['path'],
                output_path=output_path,
                cache_dir=cache_dir,
                batch_size=batch_size,
                skip_frames=skip_frames,
                streaming=True,  # 标记为流式模式
                auto_adjust=True  # 自动调整避免OOM
            )
            
            process_time = time.time() - start_time
            
            return {
                'success': success,
                'index': segment_info['index'],
                'path': output_path if success else None,
                'duration': segment_info['duration'],
                'frames': num_frames,
                'process_time': process_time,
                'start_time': segment_info['start_time']
            }
            
        except Exception as e:
            print(f"❌ 段处理失败: {e}")
            return {
                'success': False,
                'index': segment_info['index'],
                'error': str(e)
            }
    
    async def process_stream(
        self,
        template_id: str,
        audio_path: str,
        callback=None
    ):
        """流式处理音频"""
        try:
            # 分割音频
            segments = self.split_audio_to_segments(audio_path)
            if not segments:
                print("❌ 音频分割失败")
                return
            
            # 逐段处理
            for segment in segments:
                print(f"⚡ 处理段 {segment['index']+1}/{len(segments)}")
                
                result = self.process_segment(template_id, segment)
                
                if result['success']:
                    print(f"✅ 段 {result['index']} 完成: {result['process_time']:.1f}秒")
                    
                    # 回调通知
                    if callback:
                        await callback(result)
                else:
                    print(f"❌ 段 {result['index']} 失败")
                    
        except Exception as e:
            print(f"❌ 流式处理失败: {e}")

    def cleanup_segments(self, prefix: str = "segment_"):
        """清理临时文件"""
        try:
            import glob
            for file in glob.glob(f"/tmp/{prefix}*.wav"):
                os.remove(file)
            for file in glob.glob(f"/tmp/{prefix}*.mp4"):
                os.remove(file)
            print("🧹 清理临时文件完成")
        except Exception as e:
            print(f"⚠️ 清理失败: {e}")


class StreamingServer:
    """流式服务器 - 处理WebSocket连接"""
    
    def __init__(self):
        self.processor = SegmentProcessor()
        self.connections = {}
        
    async def handle_connection(self, websocket, path):
        """处理WebSocket连接"""
        connection_id = id(websocket)
        self.connections[connection_id] = websocket
        
        try:
            async for message in websocket:
                data = json.loads(message)
                
                if data['command'] == 'start_stream':
                    await self.start_streaming(
                        websocket,
                        data['template_id'],
                        data['audio_path']
                    )
                    
        except Exception as e:
            print(f"❌ 连接错误: {e}")
        finally:
            del self.connections[connection_id]
    
    async def start_streaming(self, websocket, template_id, audio_path):
        """开始流式处理"""
        
        async def send_segment(result):
            """发送视频段到客户端"""
            await websocket.send(json.dumps({
                'type': 'segment',
                'data': result
            }))
        
        # 处理流
        await self.processor.process_stream(
            template_id,
            audio_path,
            callback=send_segment
        )
        
        # 发送完成信号
        await websocket.send(json.dumps({
            'type': 'complete'
        }))


def main():
    """测试入口"""
    import argparse
    parser = argparse.ArgumentParser(description='分段处理器')
    parser.add_argument('--template_id', required=True, help='模板ID')
    parser.add_argument('--audio_path', required=True, help='音频路径')
    parser.add_argument('--test', action='store_true', help='测试模式')
    
    args = parser.parse_args()
    
    processor = SegmentProcessor()
    processor.initialize()
    
    if args.test:
        # 测试分割
        segments = processor.split_audio_to_segments(args.audio_path)
        print(f"分割结果: {len(segments)}段")
        
        # 测试处理第一段
        if segments:
            result = processor.process_segment(args.template_id, segments[0])
            print(f"处理结果: {result}")
    else:
        # 运行流式处理
        asyncio.run(processor.process_stream(
            args.template_id,
            args.audio_path
        ))
    
    processor.cleanup_segments()


if __name__ == "__main__":
    main()