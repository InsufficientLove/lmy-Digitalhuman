#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接启动器 - 确保正确的环境和路径
"""

import os
import sys
import argparse
from pathlib import Path

# 禁用输出缓冲
os.environ['PYTHONUNBUFFERED'] = '1'
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

def init_cache_dirs():
    """初始化缓存目录"""
    dirs = [
        '/opt/musetalk/template_cache',
        '/opt/musetalk/cache/torch_compile',
        '/opt/musetalk/templates',
        '/temp'
    ]
    for dir_path in dirs:
        os.makedirs(dir_path, exist_ok=True)
    print("✅ 缓存目录初始化完成")

def init_templates():
    """初始化模板目录结构和软链接"""
    try:
        print("🔧 初始化模板目录结构...")
        
        # 创建必要的目录
        template_cache_dir = os.environ.get('MUSE_TEMPLATE_CACHE_DIR', '/opt/musetalk/template_cache')
        os.makedirs(template_cache_dir, exist_ok=True)
        os.makedirs("/opt/musetalk/repo/musetalk/models", exist_ok=True)
        
        # 软链接路径 - 为了兼容性，创建指向统一缓存目录的链接（修正为小写）
        link_path = "/opt/musetalk/repo/musetalk/models/templates"
        target_path = template_cache_dir
        
        # 如果链接已存在且正确，跳过
        if os.path.islink(link_path):
            if os.readlink(link_path) == target_path:
                # 软链接存在但不再需要，静默跳过
                return
            else:
                # 删除错误的链接
                os.unlink(link_path)
        elif os.path.exists(link_path):
            # 如果是目录，尝试删除（如果为空）
            try:
                os.rmdir(link_path)
            except:
                print(f"⚠️ 无法删除目录: {link_path}")
                return
        
        # 创建软链接
        os.symlink(target_path, link_path)
        print(f"✅ 创建软链接: {link_path} -> {target_path}")
        
        # 列出现有模板
        print("📋 现有模板：")
        if os.path.exists(target_path):
            for item in os.listdir(target_path):
                item_path = os.path.join(target_path, item)
                if os.path.isdir(item_path):
                    pkl_file = os.path.join(item_path, f"{item}_preprocessed.pkl")
                    if os.path.exists(pkl_file):
                        size_mb = os.path.getsize(pkl_file) / 1024 / 1024
                        print(f"  ✅ {item} ({size_mb:.2f} MB)")
                    else:
                        print(f"  ⚠️ {item} (未预处理)")
        else:
            print("  (空)")
            
    except Exception as e:
        print(f"⚠️ 模板初始化失败: {e}")
        # 不阻止服务启动
        pass

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=28888)
    parser.add_argument('--mode', type=str, default='server')
    parser.add_argument('--multi_gpu', action='store_true')
    parser.add_argument('--gpu_id', type=int, default=0)
    args = parser.parse_args()
    
    # 初始化模板目录结构
    init_templates()
    
    # 设置路径（支持通过环境变量 MUSE_TALK_DIR 覆盖）
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    env_musetalk_dir = os.environ.get("MUSE_TALK_DIR", "").strip()
    musetalk_path = Path(env_musetalk_dir) if env_musetalk_dir else (project_root / "MuseTalk")
    
    # 添加路径
    sys.path.insert(0, str(musetalk_path))
    sys.path.insert(0, str(script_dir))
    
    # 切换工作目录
    if musetalk_path.exists():
        os.chdir(musetalk_path)
        print(f"工作目录: {musetalk_path}")
        print(f"Python路径: {sys.path[:3]}")
    else:
        parent = musetalk_path.parent
        print(f"❌ MuseTalk目录不存在: {musetalk_path}")
        try:
            print(f"父目录内容: {list(parent.iterdir())}")
        except Exception:
            pass
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