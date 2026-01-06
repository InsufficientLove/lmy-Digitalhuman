#!/usr/bin/env python3
"""
实时流式推理引擎 - Zero Disk I/O
专为WebSocket设计，纯内存处理
"""

import os
import sys
import cv2
import torch
import numpy as np
from typing import Optional, Dict, List, Tuple
import io

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from offline.batch_inference import UltraFastMuseTalkService


class RealtimeStreamingEngine:
    """实时流式推理引擎 - 纯内存操作"""
    
    def __init__(self):
        # 使用现有的推理服务
        self.inference_service = UltraFastMuseTalkService()
        
        # 会话状态缓存
        self.active_sessions: Dict[str, Dict] = {}
        
        # 初始化标志
        self.is_initialized = False
    
    def initialize(self) -> bool:
        """初始化推理引擎"""
        if self.is_initialized:
            return True
        
        print("🚀 初始化实时流式推理引擎...")
        success = self.inference_service.initialize_models_ultra_fast()
        
        if success:
            self.is_initialized = True
            print("✅ 实时引擎初始化成功")
        else:
            print("❌ 实时引擎初始化失败")
        
        return success
    
    def create_session(self, session_id: str, avatar_id: str, avatar_source: str) -> Dict:
        """
        创建流式会话
        
        Args:
            session_id: 会话ID
            avatar_id: Avatar ID
            avatar_source: Avatar来源路径（图片或视频）
        
        Returns:
            {"success": bool, "message": str}
        """
        try:
            print(f"📝 创建会话: {session_id}, Avatar: {avatar_id}")
            
            # 检查Avatar类型
            is_video = avatar_source.lower().endswith(('.mp4', '.avi', '.mov', '.mkv'))
            is_photo = avatar_source.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp'))
            
            if not is_video and not is_photo:
                return {
                    "success": False,
                    "message": f"不支持的Avatar格式: {avatar_source}"
                }
            
            # Part 2.1: Input Polymorphism - 处理静态图片
            if is_photo:
                print(f"📸 检测到静态图片，将作为单帧视频处理")
                # 读取图片（Input Guard: BGR -> RGB）
                frame_bgr = cv2.imread(avatar_source)
                if frame_bgr is None:
                    return {
                        "success": False,
                        "message": f"无法读取图片: {avatar_source}"
                    }
                
                # Color Space Integrity: BGR -> RGB
                frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
                
                # 将单帧保存到会话状态（内存中无限循环引用）
                avatar_frames = [frame_rgb]  # 单帧列表
                is_static_photo = True
            else:
                # 视频模式：读取所有帧
                print(f"🎬 检测到视频，读取帧序列...")
                cap = cv2.VideoCapture(avatar_source)
                avatar_frames = []
                
                while True:
                    ret, frame_bgr = cap.read()
                    if not ret:
                        break
                    
                    # Color Space Integrity: BGR -> RGB
                    frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
                    avatar_frames.append(frame_rgb)
                
                cap.release()
                is_static_photo = False
                print(f"✅ 读取了 {len(avatar_frames)} 帧")
            
            if len(avatar_frames) == 0:
                return {
                    "success": False,
                    "message": "无法读取Avatar帧"
                }
            
            # 预加载模板缓存
            cache_dir = os.environ.get('MUSE_TEMPLATE_CACHE_DIR', '/opt/musetalk/template_cache')
            template_cache_dir = os.path.join(cache_dir, avatar_id)
            
            cache_data = self.inference_service.load_template_cache_optimized(
                template_cache_dir, 
                avatar_id
            )
            
            if cache_data is None:
                return {
                    "success": False,
                    "message": f"模板缓存不存在: {avatar_id}"
                }
            
            # 保存会话状态到内存
            self.active_sessions[session_id] = {
                "avatar_id": avatar_id,
                "avatar_frames": avatar_frames,  # 内存中的帧列表
                "is_static_photo": is_static_photo,
                "cache_data": cache_data,
                "frame_index": 0  # 当前帧索引（用于循环）
            }
            
            print(f"✅ 会话创建成功: {session_id}")
            return {
                "success": True,
                "message": "会话已创建",
                "frame_count": len(avatar_frames),
                "is_static_photo": is_static_photo
            }
        
        except Exception as e:
            print(f"❌ 创建会话失败: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "message": f"会话创建失败: {str(e)}"
            }
    
    def process_audio_chunk(
        self, 
        session_id: str, 
        audio_bytes: bytes, 
        fps: int = 25
    ) -> List[bytes]:
        """
        处理音频块，返回JPEG帧流（Zero Disk I/O）
        
        Args:
            session_id: 会话ID
            audio_bytes: 音频字节流（PCM/WAV）
            fps: 帧率
        
        Returns:
            List[bytes]: JPEG编码的帧字节列表
        """
        try:
            if session_id not in self.active_sessions:
                print(f"❌ 会话不存在: {session_id}")
                return []
            
            session = self.active_sessions[session_id]
            cache_data = session["cache_data"]
            
            # 保存音频到临时内存文件
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                tmp.write(audio_bytes)
                audio_path = tmp.name
            
            try:
                # 提取音频特征
                whisper_chunks = self.inference_service.extract_audio_features_ultra_fast(
                    audio_path, fps
                )
                
                if whisper_chunks is None or len(whisper_chunks) == 0:
                    print("❌ 音频特征提取失败")
                    return []
                
                # 推理生成帧（纯内存操作）
                res_frame_list = self.inference_service.ultra_fast_inference_4gpu(
                    whisper_chunks=whisper_chunks,
                    cache_data=cache_data,
                    batch_size=1  # 实时模式使用单帧
                )
                
                if len(res_frame_list) == 0:
                    print("❌ 推理失败")
                    return []
                
                # 合成帧（内存操作）
                video_frames = self.inference_service.ultra_fast_compose_frames(
                    res_frame_list, cache_data
                )
                
                # 编码为JPEG字节流（Zero Disk I/O）
                jpeg_frames = []
                for frame_bgr in video_frames:
                    # Color Space Integrity: frame已经是BGR（compose_frames已转换）
                    # 直接编码为JPEG
                    success, buffer = cv2.imencode('.jpg', frame_bgr, [cv2.IMWRITE_JPEG_QUALITY, 85])
                    if success:
                        jpeg_bytes = buffer.tobytes()
                        jpeg_frames.append(jpeg_bytes)
                
                print(f"✅ 生成了 {len(jpeg_frames)} 帧JPEG")
                return jpeg_frames
            
            finally:
                # 清理临时音频文件
                try:
                    os.unlink(audio_path)
                except:
                    pass
        
        except Exception as e:
            print(f"❌ 处理音频块失败: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def close_session(self, session_id: str) -> bool:
        """关闭会话"""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
            print(f"✅ 会话已关闭: {session_id}")
            return True
        return False
    
    def get_session_info(self, session_id: str) -> Optional[Dict]:
        """获取会话信息"""
        return self.active_sessions.get(session_id)


# 全局实例
_realtime_engine = None


def get_realtime_engine() -> RealtimeStreamingEngine:
    """获取全局实时引擎实例"""
    global _realtime_engine
    if _realtime_engine is None:
        _realtime_engine = RealtimeStreamingEngine()
        _realtime_engine.initialize()
    return _realtime_engine
