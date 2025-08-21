#!/usr/bin/env python3
"""
流式推理API服务
为C#端提供高性能的MuseTalk推理服务
"""

import os
import sys
import time
import json
import asyncio
import numpy as np
from pathlib import Path
from typing import Dict, Optional, List
from concurrent.futures import ThreadPoolExecutor
import threading
import queue

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from offline.batch_inference import UltraFastMuseTalkService
from streaming.frame_interpolation import FrameInterpolator


class StreamingMuseTalkAPI:
    """流式MuseTalk API服务 - 供C#调用"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
            
        # 核心服务
        self.musetalk_service = UltraFastMuseTalkService()
        self.interpolator = FrameInterpolator(method='optical_flow')
        
        # 模板缓存
        self.template_cache = {}
        self.template_cache_dir = os.environ.get('MUSE_TEMPLATE_CACHE_DIR', '/opt/musetalk/template_cache')
        
        # 配置参数
        self.segment_duration = float(os.environ.get('SEGMENT_DURATION', '1.0'))
        self.skip_frames = int(os.environ.get('SKIP_FRAMES', '2'))
        self.batch_size_config = {
            'ultra_fast': 6,   # 0.5秒以内
            'fast': 12,        # 1秒以内
            'normal': 16,      # 1-2秒
            'quality': 20      # 2秒以上
        }
        
        # 线程池
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # 会话管理
        self.active_sessions = {}
        
        self._initialized = True
        print("✅ StreamingMuseTalkAPI 初始化完成")
    
    def initialize(self) -> bool:
        """初始化服务（由C#调用）"""
        try:
            print("🚀 初始化MuseTalk推理服务...")
            
            # 初始化模型
            success = self.musetalk_service.initialize_models()
            if not success:
                print("❌ 模型初始化失败")
                return False
            
            # 预热模型
            self._warmup_models()
            
            print("✅ MuseTalk推理服务就绪")
            return True
            
        except Exception as e:
            print(f"❌ 初始化失败: {e}")
            return False
    
    def _warmup_models(self):
        """预热模型，减少首次推理延迟"""
        try:
            print("🔥 预热模型...")
            
            # 创建测试音频
            import soundfile as sf
            dummy_audio = np.zeros(16000, dtype=np.float32)
            dummy_path = "/tmp/warmup_audio.wav"
            sf.write(dummy_path, dummy_audio, 16000)
            
            # 执行一次空推理
            if hasattr(self.musetalk_service, 'extract_audio_features_ultra_fast'):
                self.musetalk_service.extract_audio_features_ultra_fast(dummy_path, 25)
            
            # 清理
            os.remove(dummy_path)
            print("✅ 模型预热完成")
            
        except Exception as e:
            print(f"⚠️ 模型预热失败: {e}")
    
    def preprocess_template(self, template_id: str, image_path: str) -> Dict:
        """
        预处理模板（由C#调用）
        返回关键推理信息用于持久化
        """
        try:
            print(f"📋 预处理模板: {template_id}")
            
            # 检查缓存
            cache_path = os.path.join(self.template_cache_dir, template_id)
            pkl_file = os.path.join(cache_path, f"{template_id}_preprocessed.pkl")
            
            if os.path.exists(pkl_file):
                print(f"✅ 模板已存在: {template_id}")
                return {
                    'success': True,
                    'template_id': template_id,
                    'cache_path': cache_path,
                    'message': '模板已预处理'
                }
            
            # 创建缓存目录
            os.makedirs(cache_path, exist_ok=True)
            
            # 调用预处理
            from core.preprocessing import preprocess_template_ultra_fast
            success = preprocess_template_ultra_fast(
                template_id=template_id,
                image_path=image_path,
                output_dir=self.template_cache_dir
            )
            
            if success:
                # 加载到内存缓存
                self.template_cache[template_id] = {
                    'path': cache_path,
                    'loaded_at': time.time()
                }
                
                return {
                    'success': True,
                    'template_id': template_id,
                    'cache_path': cache_path,
                    'message': '模板预处理成功'
                }
            else:
                return {
                    'success': False,
                    'message': '模板预处理失败'
                }
                
        except Exception as e:
            print(f"❌ 模板预处理错误: {e}")
            return {
                'success': False,
                'message': str(e)
            }
    
    def start_session(self, session_id: str, template_id: str) -> Dict:
        """
        开始对话会话（由C#调用）
        """
        try:
            print(f"🎬 开始会话: {session_id}, 模板: {template_id}")
            
            # 检查模板是否存在
            cache_path = os.path.join(self.template_cache_dir, template_id)
            if not os.path.exists(cache_path):
                return {
                    'success': False,
                    'message': f'模板不存在: {template_id}'
                }
            
            # 创建会话
            self.active_sessions[session_id] = {
                'template_id': template_id,
                'created_at': time.time(),
                'segments_processed': 0,
                'total_latency': 0
            }
            
            return {
                'success': True,
                'session_id': session_id,
                'message': '会话创建成功'
            }
            
        except Exception as e:
            print(f"❌ 创建会话失败: {e}")
            return {
                'success': False,
                'message': str(e)
            }
    
    def process_audio_segment(
        self, 
        session_id: str,
        audio_path: str,
        segment_index: int = 0,
        is_final: bool = False
    ) -> Dict:
        """
        处理音频段（由C#调用）
        这是核心的流式推理接口
        
        Args:
            session_id: 会话ID
            audio_path: 音频文件路径
            segment_index: 段索引
            is_final: 是否是最后一段
            
        Returns:
            处理结果，包含视频路径和延迟信息
        """
        try:
            start_time = time.time()
            
            # 获取会话信息
            if session_id not in self.active_sessions:
                return {
                    'success': False,
                    'message': f'会话不存在: {session_id}'
                }
            
            session = self.active_sessions[session_id]
            template_id = session['template_id']
            
            # 分析音频长度，动态调整参数
            import librosa
            audio_data, sr = librosa.load(audio_path, sr=16000)
            duration = len(audio_data) / sr
            num_frames = int(duration * 25)  # 25fps
            
            # 智能选择批处理大小和跳帧策略
            if duration <= 0.5:
                batch_size = min(num_frames, self.batch_size_config['ultra_fast'])
                skip_frames = 1
                mode = 'ultra_fast'
            elif duration <= 1.0:
                batch_size = min(num_frames, self.batch_size_config['fast'])
                skip_frames = 2
                mode = 'fast'
            elif duration <= 2.0:
                batch_size = self.batch_size_config['normal']
                skip_frames = 2
                mode = 'normal'
            else:
                batch_size = self.batch_size_config['quality']
                skip_frames = 3
                mode = 'quality'
            
            print(f"⚡ 处理音频段 {segment_index}: {duration:.2f}秒, {num_frames}帧, 模式={mode}")
            
            # 生成输出路径
            output_path = f"/tmp/segment_{session_id}_{segment_index}_{int(time.time()*1000)}.mp4"
            
            # 调用推理
            success = self.musetalk_service.ultra_fast_inference_parallel(
                template_id=template_id,
                audio_path=audio_path,
                output_path=output_path,
                cache_dir=self.template_cache_dir,
                batch_size=batch_size,
                skip_frames=skip_frames,
                streaming=True,
                auto_adjust=True
            )
            
            process_time = time.time() - start_time
            
            # 更新会话统计
            session['segments_processed'] += 1
            session['total_latency'] += process_time
            
            if success:
                result = {
                    'success': True,
                    'session_id': session_id,
                    'segment_index': segment_index,
                    'video_path': output_path,
                    'duration': duration,
                    'frames': num_frames,
                    'process_time': process_time,
                    'latency_ms': process_time * 1000,
                    'mode': mode,
                    'is_final': is_final
                }
                
                # 性能日志
                if process_time <= 1.0:
                    print(f"✅ 段 {segment_index} 极速完成: {process_time:.2f}秒")
                elif process_time <= 2.0:
                    print(f"⚡ 段 {segment_index} 快速完成: {process_time:.2f}秒")
                else:
                    print(f"⚠️ 段 {segment_index} 处理较慢: {process_time:.2f}秒")
                
                return result
            else:
                return {
                    'success': False,
                    'session_id': session_id,
                    'segment_index': segment_index,
                    'message': '推理失败'
                }
                
        except Exception as e:
            print(f"❌ 处理音频段失败: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'session_id': session_id,
                'segment_index': segment_index,
                'message': str(e)
            }
    
    def end_session(self, session_id: str) -> Dict:
        """
        结束会话（由C#调用）
        """
        try:
            if session_id not in self.active_sessions:
                return {
                    'success': False,
                    'message': f'会话不存在: {session_id}'
                }
            
            session = self.active_sessions[session_id]
            
            # 计算统计信息
            avg_latency = session['total_latency'] / max(1, session['segments_processed'])
            
            result = {
                'success': True,
                'session_id': session_id,
                'segments_processed': session['segments_processed'],
                'total_latency': session['total_latency'],
                'average_latency': avg_latency,
                'message': '会话结束'
            }
            
            # 清理会话
            del self.active_sessions[session_id]
            
            # 清理临时文件
            self._cleanup_session_files(session_id)
            
            print(f"👋 会话结束: {session_id}, 处理{session['segments_processed']}段, 平均延迟{avg_latency:.2f}秒")
            
            return result
            
        except Exception as e:
            print(f"❌ 结束会话失败: {e}")
            return {
                'success': False,
                'message': str(e)
            }
    
    def _cleanup_session_files(self, session_id: str):
        """清理会话相关的临时文件"""
        try:
            import glob
            pattern = f"/tmp/segment_{session_id}_*.mp4"
            for file in glob.glob(pattern):
                try:
                    os.remove(file)
                except:
                    pass
            print(f"🧹 清理会话文件: {session_id}")
        except Exception as e:
            print(f"⚠️ 清理失败: {e}")
    
    def get_status(self) -> Dict:
        """
        获取服务状态（由C#调用）
        """
        return {
            'status': 'ready',
            'active_sessions': len(self.active_sessions),
            'templates_cached': len(self.template_cache),
            'gpu_count': self.musetalk_service.gpu_count if hasattr(self.musetalk_service, 'gpu_count') else 0,
            'config': {
                'segment_duration': self.segment_duration,
                'skip_frames': self.skip_frames,
                'batch_sizes': self.batch_size_config
            }
        }


# 全局服务实例
_api_service = None


def get_api_service() -> StreamingMuseTalkAPI:
    """获取API服务实例"""
    global _api_service
    if _api_service is None:
        _api_service = StreamingMuseTalkAPI()
    return _api_service


# HTTP API接口（供C#调用）
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="MuseTalk Streaming API")


class PreprocessRequest(BaseModel):
    template_id: str
    image_path: str


class SessionRequest(BaseModel):
    session_id: str
    template_id: str


class ProcessRequest(BaseModel):
    session_id: str
    audio_path: str
    segment_index: int = 0
    is_final: bool = False


@app.on_event("startup")
async def startup_event():
    """启动时初始化服务"""
    service = get_api_service()
    service.initialize()


@app.post("/api/initialize")
async def initialize():
    """初始化服务"""
    service = get_api_service()
    success = service.initialize()
    if success:
        return {"success": True, "message": "服务初始化成功"}
    else:
        raise HTTPException(status_code=500, detail="服务初始化失败")


@app.post("/api/preprocess_template")
async def preprocess_template(request: PreprocessRequest):
    """预处理模板"""
    service = get_api_service()
    result = service.preprocess_template(request.template_id, request.image_path)
    if result['success']:
        return result
    else:
        raise HTTPException(status_code=400, detail=result['message'])


@app.post("/api/start_session")
async def start_session(request: SessionRequest):
    """开始会话"""
    service = get_api_service()
    result = service.start_session(request.session_id, request.template_id)
    if result['success']:
        return result
    else:
        raise HTTPException(status_code=400, detail=result['message'])


@app.post("/api/process_segment")
async def process_segment(request: ProcessRequest):
    """处理音频段"""
    service = get_api_service()
    result = service.process_audio_segment(
        request.session_id,
        request.audio_path,
        request.segment_index,
        request.is_final
    )
    if result['success']:
        return result
    else:
        raise HTTPException(status_code=400, detail=result.get('message', '处理失败'))


@app.post("/api/end_session/{session_id}")
async def end_session(session_id: str):
    """结束会话"""
    service = get_api_service()
    result = service.end_session(session_id)
    if result['success']:
        return result
    else:
        raise HTTPException(status_code=400, detail=result['message'])


@app.get("/api/status")
async def get_status():
    """获取服务状态"""
    service = get_api_service()
    return service.get_status()


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "timestamp": time.time()}


def start_api_server(host='0.0.0.0', port=28888):
    """启动API服务器"""
    print(f"🌐 启动MuseTalk API服务: http://{host}:{port}")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    start_api_server()