#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ultra Fast Service Startup Wrapper
Ultra Fast服务启动包装器 - 确保所有依赖正确设置
"""

import os
import sys
import argparse
from pathlib import Path

def setup_environment():
    """设置环境和依赖"""
    # 获取脚本目录
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    # 添加必要的路径到Python路径
    musetalk_path = project_root / "MuseTalk"
    musetalk_engine_path = script_dir
    
    paths_to_add = [str(musetalk_path), str(musetalk_engine_path)]
    
    for path in paths_to_add:
        if path not in sys.path:
            sys.path.insert(0, path)
    
    # 设置工作目录为MuseTalkEngine
    os.chdir(script_dir)
    
    print(f"🔧 工作目录设置为: {script_dir}")
    print(f"🔧 Python路径已添加: {paths_to_add}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Ultra Fast MuseTalk Service Wrapper')
    parser.add_argument('--port', type=int, default=28888, help='服务端口')
    parser.add_argument('--mode', type=str, default='server', help='运行模式 (兼容性参数)')
    parser.add_argument('--multi_gpu', action='store_true', help='启用多GPU (兼容性参数)')
    parser.add_argument('--gpu_id', type=int, default=0, help='GPU ID (兼容性参数)')
    
    args = parser.parse_args()
    
    # 设置环境
    setup_environment()
    
    print("🚀 启动Ultra Fast MuseTalk服务...")
    print(f"📊 配置参数:")
    print(f"   - 端口: {args.port}")
    print(f"   - 模式: {args.mode}")
    print(f"   - 多GPU: {args.multi_gpu}")
    print(f"   - GPU ID: {args.gpu_id}")
    
    # 导入并启动Ultra Fast服务
    try:
        from ultra_fast_realtime_inference_v2 import start_ultra_fast_service
        start_ultra_fast_service(args.port)
    except ImportError as e:
        print(f"❌ 导入Ultra Fast服务失败: {str(e)}")
        print("🔧 尝试使用备用全局服务...")
        try:
            from global_musetalk_service import main as global_main
            # 设置参数兼容全局服务
            sys.argv = ['global_musetalk_service.py', '--mode', 'server', '--multi_gpu', '--port', str(args.port), '--gpu_id', str(args.gpu_id)]
            global_main()
        except ImportError:
            print("❌ 备用服务也无法启动")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Ultra Fast服务启动失败: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()