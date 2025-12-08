#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
资产预处理脚本 - 离线提取视频人脸坐标
Author: 数字人后端团队
Hardware: 2x RTX 4090D (24GB VRAM)
Purpose: 预处理视频，提取每帧的人脸边界框，为实时推理做准备
"""

import os
import sys
import cv2
import json
import pickle
import numpy as np
import argparse
from pathlib import Path
from tqdm import tqdm
import warnings
warnings.filterwarnings("ignore")

# 添加 MuseTalk 路径
MUSETALK_PATH = os.environ.get('MUSE_TALK_DIR', '/opt/musetalk/repo/MuseTalk')
sys.path.insert(0, MUSETALK_PATH)

try:
    from musetalk.utils.preprocessing import get_landmark_and_bbox
    print("✅ 成功导入 MuseTalk 人脸检测模块")
except ImportError as e:
    print(f"❌ 无法导入 MuseTalk 模块: {e}")
    print(f"请确保 MUSE_TALK_DIR 环境变量正确设置: {MUSETALK_PATH}")
    sys.exit(1)


class VideoFacePreprocessor:
    """视频人脸预处理器 - 提取边界框坐标"""
    
    def __init__(self, video_path: str, output_dir: str = "./data/preprocessed"):
        """
        初始化预处理器
        
        Args:
            video_path: 输入视频路径 (MP4)
            output_dir: 输出目录
        """
        self.video_path = Path(video_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 验证视频文件
        if not self.video_path.exists():
            raise FileNotFoundError(f"视频文件不存在: {video_path}")
        
        print(f"📹 视频路径: {self.video_path}")
        print(f"💾 输出目录: {self.output_dir}")
    
    def extract_frames(self):
        """提取视频的所有帧"""
        cap = cv2.VideoCapture(str(self.video_path))
        
        if not cap.isOpened():
            raise RuntimeError(f"无法打开视频: {self.video_path}")
        
        # 获取视频信息
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        print(f"📊 视频信息:")
        print(f"   - 分辨率: {width}x{height}")
        print(f"   - 帧率: {fps:.2f} FPS")
        print(f"   - 总帧数: {total_frames}")
        
        frames = []
        frame_indices = []
        
        print("📦 正在提取视频帧...")
        pbar = tqdm(total=total_frames, desc="提取帧")
        
        frame_idx = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            frames.append(frame)
            frame_indices.append(frame_idx)
            frame_idx += 1
            pbar.update(1)
        
        pbar.close()
        cap.release()
        
        print(f"✅ 成功提取 {len(frames)} 帧")
        
        return frames, frame_indices, fps
    
    def detect_face_bboxes(self, frames):
        """
        批量检测人脸边界框
        
        Args:
            frames: 视频帧列表
        
        Returns:
            bbox_list: 每帧的边界框 [(x1, y1, x2, y2), ...]
            landmarks_list: 每帧的关键点坐标
        """
        print("🔍 开始人脸检测...")
        
        # 保存临时帧用于检测
        temp_dir = self.output_dir / "temp_frames"
        temp_dir.mkdir(exist_ok=True)
        
        temp_paths = []
        for i, frame in enumerate(tqdm(frames, desc="保存临时帧")):
            temp_path = temp_dir / f"frame_{i:06d}.jpg"
            cv2.imwrite(str(temp_path), frame)
            temp_paths.append(str(temp_path))
        
        # 使用 MuseTalk 的人脸检测
        print("⚙️ 调用 MuseTalk 人脸检测...")
        try:
            coord_list, frame_list = get_landmark_and_bbox(temp_paths)
            print(f"✅ 检测完成，获得 {len(coord_list)} 个结果")
        except Exception as e:
            print(f"❌ 人脸检测失败: {e}")
            raise
        
        # 清理临时文件
        import shutil
        shutil.rmtree(temp_dir)
        
        # 转换关键点为边界框
        bbox_list = []
        landmarks_list = []
        
        print("📐 计算边界框...")
        for landmarks in tqdm(coord_list, desc="处理关键点"):
            if landmarks is None or len(landmarks) == 0:
                # 使用默认值
                bbox_list.append((0, 0, 0, 0))
                landmarks_list.append(None)
                continue
            
            # 从关键点计算边界框
            if isinstance(landmarks, np.ndarray):
                if landmarks.ndim == 2 and landmarks.shape[1] == 2:
                    # 关键点坐标 (N, 2)
                    x_coords = landmarks[:, 0]
                    y_coords = landmarks[:, 1]
                    
                    # 过滤无效坐标
                    valid_mask = (x_coords > 0) & (y_coords > 0)
                    if np.any(valid_mask):
                        x_coords = x_coords[valid_mask]
                        y_coords = y_coords[valid_mask]
                        
                        # 计算边界框并添加边距
                        margin = 30
                        x1 = int(np.min(x_coords) - margin)
                        y1 = int(np.min(y_coords) - margin)
                        x2 = int(np.max(x_coords) + margin)
                        y2 = int(np.max(y_coords) + margin)
                        
                        bbox_list.append((x1, y1, x2, y2))
                        landmarks_list.append(landmarks.tolist())
                    else:
                        bbox_list.append((0, 0, 0, 0))
                        landmarks_list.append(None)
                else:
                    bbox_list.append((0, 0, 0, 0))
                    landmarks_list.append(None)
            else:
                bbox_list.append((0, 0, 0, 0))
                landmarks_list.append(None)
        
        return bbox_list, landmarks_list
    
    def save_results(self, bbox_list, landmarks_list, fps):
        """
        保存预处理结果
        
        Args:
            bbox_list: 边界框列表
            landmarks_list: 关键点列表
            fps: 视频帧率
        """
        video_name = self.video_path.stem
        
        # 保存为 pickle 格式（高性能加载）
        pkl_path = self.output_dir / f"{video_name}_bbox.pkl"
        with open(pkl_path, 'wb') as f:
            pickle.dump({
                'bbox_list': bbox_list,
                'landmarks_list': landmarks_list,
                'fps': fps,
                'frame_count': len(bbox_list),
                'video_name': video_name,
                'video_path': str(self.video_path)
            }, f, protocol=pickle.HIGHEST_PROTOCOL)
        
        print(f"💾 Pickle 文件已保存: {pkl_path}")
        
        # 同时保存为 JSON 格式（便于查看）
        json_path = self.output_dir / f"{video_name}_bbox.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump({
                'bbox_list': bbox_list,
                'fps': fps,
                'frame_count': len(bbox_list),
                'video_name': video_name,
                'video_path': str(self.video_path)
            }, f, indent=2, ensure_ascii=False)
        
        print(f"📄 JSON 文件已保存: {json_path}")
        
        # 保存统计信息
        valid_frames = sum(1 for bbox in bbox_list if bbox != (0, 0, 0, 0))
        print(f"\n📊 预处理统计:")
        print(f"   - 总帧数: {len(bbox_list)}")
        print(f"   - 有效帧: {valid_frames} ({valid_frames/len(bbox_list)*100:.1f}%)")
        print(f"   - 帧率: {fps:.2f} FPS")
    
    def run(self):
        """执行完整的预处理流程"""
        print("=" * 60)
        print("🚀 开始视频人脸预处理")
        print("=" * 60)
        
        # 1. 提取帧
        frames, frame_indices, fps = self.extract_frames()
        
        # 2. 检测人脸
        bbox_list, landmarks_list = self.detect_face_bboxes(frames)
        
        # 3. 保存结果
        self.save_results(bbox_list, landmarks_list, fps)
        
        print("\n" + "=" * 60)
        print("✅ 预处理完成!")
        print("=" * 60)
        
        return True


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='视频人脸预处理工具 - 提取每帧的人脸边界框',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 处理单个视频
  python preprocess_assets.py --video ./data/video/idle.mp4
  
  # 指定输出目录
  python preprocess_assets.py --video ./data/video/idle.mp4 --output ./data/preprocessed
        """
    )
    
    parser.add_argument(
        '--video',
        type=str,
        default='./data/video/idle.mp4',
        help='输入视频路径 (默认: ./data/video/idle.mp4)'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default='./data/preprocessed',
        help='输出目录 (默认: ./data/preprocessed)'
    )
    
    args = parser.parse_args()
    
    try:
        preprocessor = VideoFacePreprocessor(
            video_path=args.video,
            output_dir=args.output
        )
        
        success = preprocessor.run()
        
        if success:
            print("\n✅ 预处理成功完成!")
            sys.exit(0)
        else:
            print("\n❌ 预处理失败!")
            sys.exit(1)
    
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
