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
        
        # 立即初始化模型，避免首次调用时的延迟
        print("🚀 自动初始化MuseTalk模型...")
        try:
            success = self.musetalk_service.initialize_models_ultra_fast()
            if success:
                print("✅ 模型自动初始化成功")
            else:
                print("⚠️ 模型自动初始化失败，将在首次调用时重试")
        except Exception as e:
            print(f"⚠️ 模型自动初始化异常: {e}")
        
        # 模板缓存
        self.template_cache = {}
        self.template_cache_dir = os.environ.get('MUSE_TEMPLATE_CACHE_DIR', '/opt/musetalk/template_cache')
        
        # 配置参数
        self.segment_duration = float(os.environ.get('SEGMENT_DURATION', '1.0'))
        self.skip_frames = int(os.environ.get('SKIP_FRAMES', '2'))
        self.batch_size_config = {
            'ultra_fast': 1,   # 0.5秒以内 - 单帧处理最稳定
            'fast': 1,         # 1秒以内 - 也用单帧
            'normal': 2,       # 1-2秒 - 最多2帧
            'quality': 2       # 2秒以上 - 降到2避免OOM
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
            
            # 检查是否已经初始化
            if self.musetalk_service.is_initialized:
                print("✅ 模型已经初始化，跳过重复初始化")
                return True
            
            # 初始化模型 - 使用正确的方法名
            success = self.musetalk_service.initialize_models_ultra_fast()
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
    
    def preprocess_template(self, template_id: str, image_path: str, force: bool = False) -> Dict:
        """
        预处理图片模板（由C#调用）
        返回关键推理信息用于持久化
        
        Args:
            template_id: 模板ID
            image_path: 图片路径
            force: 是否强制重新处理（清除缓存）
        """
        try:
            print(f"📋 预处理图片模板: {template_id} (force={force})")
            
            # 检查缓存
            cache_path = os.path.join(self.template_cache_dir, template_id)
            pkl_file = os.path.join(cache_path, f"{template_id}_preprocessed.pkl")
            
            # 如果不是强制重处理，且缓存存在，返回缓存
            if not force and os.path.exists(pkl_file):
                print(f"✅ 使用缓存模板: {template_id}")
                return {
                    'success': True,
                    'template_id': template_id,
                    'cache_path': cache_path,
                    'template_type': 'image',
                    'message': '模板已预处理（使用缓存）'
                }
            
            # 如果是强制重处理，清理旧缓存
            if force and os.path.exists(cache_path):
                print(f"🗑️ 清理旧缓存: {template_id}")
                import shutil
                shutil.rmtree(cache_path, ignore_errors=True)
            
            # 创建缓存目录
            os.makedirs(cache_path, exist_ok=True)
            
            # 调用预处理
            from core.preprocessing import OptimizedPreprocessor
            preprocessor = OptimizedPreprocessor()
            success = preprocessor.preprocess_template_ultra_fast(
                template_path=image_path,
                output_dir=self.template_cache_dir,
                template_id=template_id
            )
            
            if success:
                # 加载到内存缓存
                self.template_cache[template_id] = {
                    'path': cache_path,
                    'type': 'image',
                    'loaded_at': time.time()
                }
                
                return {
                    'success': True,
                    'template_id': template_id,
                    'cache_path': cache_path,
                    'template_type': 'image',
                    'message': '图片模板预处理成功'
                }
            else:
                # 预处理失败，清理缓存目录
                print(f"❌ 预处理失败，清理缓存: {template_id}")
                import shutil
                if os.path.exists(cache_path):
                    shutil.rmtree(cache_path, ignore_errors=True)
                
                return {
                    'success': False,
                    'message': '图片模板预处理失败'
                }
                
        except Exception as e:
            print(f"❌ 图片模板预处理错误: {e}")
            return {
                'success': False,
                'message': str(e)
            }
    
    def preprocess_video(self, template_id: str, video_path: str, force: bool = False) -> Dict:
        """
        预处理视频模板（由C#调用）
        提取视频的人脸边界框信息
        
        Args:
            template_id: 模板ID
            video_path: 视频路径
            force: 是否强制重新处理
        """
        try:
            print(f"🎬 预处理视频模板: {template_id} (force={force})")
            
            # 检查缓存
            preprocessed_dir = "/opt/musetalk/preprocessed"
            os.makedirs(preprocessed_dir, exist_ok=True)
            bbox_file = os.path.join(preprocessed_dir, f"{template_id}_bbox.pkl")
            
            # 如果不是强制重处理，且缓存存在，返回缓存
            if not force and os.path.exists(bbox_file):
                print(f"✅ 使用缓存视频: {template_id}")
                return {
                    'success': True,
                    'template_id': template_id,
                    'bbox_path': bbox_file,
                    'video_path': video_path,
                    'template_type': 'video',
                    'message': '视频已预处理（使用缓存）'
                }
            
            # 如果是强制重处理，删除旧缓存
            if force and os.path.exists(bbox_file):
                print(f"🗑️ 清理旧缓存: {template_id}")
                os.remove(bbox_file)
            
            # 调用视频预处理脚本
            import subprocess
            import sys
            
            preprocess_script = "/opt/musetalk/repo/MuseTalkEngine/preprocess_assets.py"
            
            print(f"⚙️ 开始预处理视频: {video_path}")
            
            result = subprocess.run(
                [sys.executable, preprocess_script, 
                 "--video", video_path,
                 "--output", preprocessed_dir],
                capture_output=True,
                text=True,
                timeout=600  # 10分钟超时
            )
            
            if result.returncode != 0:
                print(f"❌ 视频预处理失败: {result.stderr}")
                return {
                    'success': False,
                    'message': f'视频预处理失败: {result.stderr}'
                }
            
            # 检查bbox文件是否生成
            # 预处理脚本使用视频文件名作为输出
            import os.path as osp
            video_name = osp.splitext(osp.basename(video_path))[0]
            generated_bbox = os.path.join(preprocessed_dir, f"{video_name}_bbox.pkl")
            
            if os.path.exists(generated_bbox):
                # 重命名为template_id格式
                if generated_bbox != bbox_file:
                    import shutil
                    shutil.move(generated_bbox, bbox_file)
                
                print(f"✅ 视频预处理成功: {bbox_file}")
                
                # 加载到内存缓存
                self.template_cache[template_id] = {
                    'bbox_path': bbox_file,
                    'video_path': video_path,
                    'type': 'video',
                    'loaded_at': time.time()
                }
                
                return {
                    'success': True,
                    'template_id': template_id,
                    'bbox_path': bbox_file,
                    'video_path': video_path,
                    'template_type': 'video',
                    'message': '视频模板预处理成功'
                }
            else:
                print(f"❌ 未找到生成的bbox文件: {generated_bbox}")
                return {
                    'success': False,
                    'message': '视频预处理失败：未生成bbox文件'
                }
                
        except subprocess.TimeoutExpired:
            print(f"❌ 视频预处理超时: {template_id}")
            return {
                'success': False,
                'message': '视频预处理超时（超过10分钟）'
            }
        except Exception as e:
            print(f"❌ 视频预处理错误: {e}")
            import traceback
            traceback.print_exc()
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
            
            # 根据音频长度选择处理策略
            num_frames = int(duration * 25)  # 25fps
            
            # 优化策略：针对 RTX 4090D 优化 batch_size
            # RTX 4090D 24GB 显存，batch_size=8 是安全且高效的选择
            if num_frames <= 25:  # 1秒以内
                batch_size = 8  # 4090D 优化
                skip_frames = 1  # 不跳帧，每帧都处理
                mode = 'realtime'
            elif num_frames <= 50:  # 2秒以内
                batch_size = 8  # 4090D 优化
                skip_frames = 1  # 不跳帧，每帧都处理
                mode = 'fast'
            elif num_frames <= 100:  # 4秒以内
                batch_size = 8  # 4090D 优化
                skip_frames = 1  # 不跳帧，每帧都处理
                mode = 'balanced'
            else:  # 4秒以上
                batch_size = 8  # 4090D 优化
                skip_frames = 1  # 不跳帧，每帧都处理
                mode = 'quality'
            
            print(f"⚡ 处理音频段 {segment_index}: {duration:.2f}秒, {num_frames}帧, 模式={mode}")
            
            # 生成输出路径 - 使用正确的挂载路径
            output_dir = "/videos"  # 这是容器内的挂载路径
            os.makedirs(output_dir, exist_ok=True)
            output_filename = f"segment_{session_id}_{segment_index}_{int(time.time()*1000)}.mp4"
            output_path = os.path.join(output_dir, output_filename)
            
            # 调用推理
            success = self.musetalk_service.ultra_fast_inference_parallel(
                template_id=template_id,
                audio_path=audio_path,
                output_path=output_path,
                cache_dir=None,  # 让函数自己拼接正确的路径
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
                    'video_path': f"/videos/{output_filename}",  # 返回挂载路径
                    'video_filename': output_filename,  # 只有文件名
                    'video_url': f"/videos/{output_filename}",  # Web访问路径
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
            # 只清理/tmp下的临时文件，不清理/opt/musetalk/videos下的成品
            pattern = f"/tmp/segment_{session_id}_*.mp4"
            for file in glob.glob(pattern):
                try:
                    os.remove(file)
                except:
                    pass
            
            # 不要清理/opt/musetalk/videos下的文件！这些是最终成品
            # pattern2 = f"/opt/musetalk/videos/segment_{session_id}_*.mp4"
            # 注释掉，保留视频文件供调试和使用
            
            print(f"🧹 清理临时文件: {session_id} (保留成品视频)")
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
    force: bool = False  # 是否强制重新处理


class PreprocessVideoRequest(BaseModel):
    template_id: str
    video_path: str
    force: bool = False  # 是否强制重新处理


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
    """预处理图片模板"""
    service = get_api_service()
    result = service.preprocess_template(request.template_id, request.image_path, request.force)
    if result['success']:
        return result
    else:
        raise HTTPException(status_code=400, detail=result['message'])


@app.post("/api/preprocess_video")
async def preprocess_video(request: PreprocessVideoRequest):
    """预处理视频模板"""
    service = get_api_service()
    result = service.preprocess_video(request.template_id, request.video_path, request.force)
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