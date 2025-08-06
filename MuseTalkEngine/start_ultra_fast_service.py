#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ultra Fast Service Startup Wrapper
Ultra Fast服务启动包装器 - 适配用户实际项目结构
"""

import os
import sys
import argparse
from pathlib import Path

def setup_environment():
    """设置环境和依赖 - 适配实际项目结构"""
    # 获取脚本目录
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    # 根据实际项目结构添加路径
    musetalk_path = project_root / "MuseTalk"  # 用户的MuseTalk模型目录
    musetalk_official_path = project_root / "MuseTalk_official"  # 官方源码
    musetalk_engine_path = script_dir  # MuseTalkEngine目录
    
    paths_to_add = [
        str(musetalk_path), 
        str(musetalk_official_path),
        str(musetalk_engine_path)
    ]
    
    for path in paths_to_add:
        if os.path.exists(path) and path not in sys.path:
            sys.path.insert(0, path)
    
    # 设置工作目录为MuseTalk (包含模型文件的目录)
    if os.path.exists(musetalk_path):
        os.chdir(musetalk_path)
        current_dir = musetalk_path
        print(f"工作目录设置为: {current_dir} (MuseTalk模型目录)")
    else:
        os.chdir(script_dir)
        current_dir = script_dir
        print(f"工作目录设置为: {current_dir} (MuseTalkEngine目录)")
    
    print(f"Python路径已添加: {[p for p in paths_to_add if os.path.exists(p)]}")

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
    
    print("启动Ultra Fast MuseTalk服务...")
    print(f"配置参数:")
    print(f"   - 端口: {args.port}")
    print(f"   - 模式: {args.mode}")
    print(f"   - 多GPU: {args.multi_gpu}")
    print(f"   - GPU ID: {args.gpu_id}")
    
    # 导入并启动Ultra Fast服务
    try:
        print("尝试启动Ultra Fast V2推理引擎...")
        from ultra_fast_realtime_inference_v2 import start_ultra_fast_service
        start_ultra_fast_service(args.port)
    except ImportError as e:
        print(f"Ultra Fast V2服务导入失败: {str(e)}")
        print("尝试使用备用全局服务...")
        try:
            from global_musetalk_service import main as global_main
            # 设置参数兼容全局服务
            original_argv = sys.argv[:]
            sys.argv = [
                'global_musetalk_service.py', 
                '--mode', 'server', 
                '--multi_gpu' if args.multi_gpu else '--single_gpu',
                '--port', str(args.port), 
                '--gpu_id', str(args.gpu_id)
            ]
            global_main()
            sys.argv = original_argv
        except ImportError as e2:
            print(f"备用服务也无法启动: {str(e2)}")
            print("请检查:")
            print("   1. MuseTalk模型文件是否在 MuseTalk/ 目录中")
            print("   2. 虚拟环境是否正确激活")
            print("   3. 依赖包是否完整安装")
            sys.exit(1)
    except Exception as e:
        print(f"Ultra Fast服务启动失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()