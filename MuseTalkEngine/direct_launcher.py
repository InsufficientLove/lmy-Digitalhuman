#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接启动器 - 确保正确的环境和路径
"""

import os
import sys
import argparse
from pathlib import Path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=28888)
    parser.add_argument('--mode', type=str, default='server')
    parser.add_argument('--multi_gpu', action='store_true')
    parser.add_argument('--gpu_id', type=int, default=0)
    args = parser.parse_args()
    
    # 设置路径
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    musetalk_path = project_root / "MuseTalk"
    
    # 添加路径
    sys.path.insert(0, str(musetalk_path))
    sys.path.insert(0, str(script_dir))
    
    # 切换工作目录
    if musetalk_path.exists():
        os.chdir(musetalk_path)
        print(f"工作目录: {musetalk_path}")
        print(f"Python路径: {sys.path[:3]}")
    else:
        print(f"❌ MuseTalk目录不存在: {musetalk_path}")
        sys.exit(1)
    
    # 直接启动服务
    try:
        print("🚀 启动Ultra Fast服务...")
        from ultra_fast_realtime_inference_v2 import start_ultra_fast_service
        start_ultra_fast_service(args.port)
    except Exception as e:
        print(f"❌ 服务启动失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()