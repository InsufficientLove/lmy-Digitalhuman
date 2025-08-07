#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import psutil
from pathlib import Path

def kill_all_python_processes():
    """强制清理所有Python进程"""
    print("🔥 强制清理所有Python进程...")
    
    killed_count = 0
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['name'] and 'python' in proc.info['name'].lower():
                cmdline = ' '.join(proc.info['cmdline'] or [])
                print(f"发现Python进程 PID:{proc.info['pid']} - {cmdline}")
                
                # 检查是否是MuseTalk相关进程
                if any(keyword in cmdline.lower() for keyword in ['musetalk', 'ultra_fast', 'global_musetalk']):
                    print(f"✅ 终止MuseTalk进程 PID:{proc.info['pid']}")
                    proc.terminate()
                    proc.wait(timeout=5)
                    killed_count += 1
                    
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
            pass
    
    print(f"✅ 已清理 {killed_count} 个Python进程")

def check_port_usage():
    """检查端口占用"""
    print("🔍 检查端口占用...")
    
    ports_to_check = [28888, 19999, 9999]
    for port in ports_to_check:
        try:
            result = subprocess.run(['netstat', '-ano'], 
                                  capture_output=True, text=True, shell=True)
            if f":{port}" in result.stdout:
                print(f"⚠️  端口 {port} 仍被占用")
                # 提取PID并终止
                lines = result.stdout.split('\n')
                for line in lines:
                    if f":{port}" in line and "LISTENING" in line:
                        parts = line.split()
                        if len(parts) >= 5:
                            pid = parts[-1]
                            print(f"终止占用端口{port}的进程 PID:{pid}")
                            try:
                                subprocess.run(['taskkill', '/PID', pid, '/F'], 
                                             capture_output=True)
                            except:
                                pass
            else:
                print(f"✅ 端口 {port} 空闲")
        except:
            pass

def fix_model_paths():
    """修复模型路径问题"""
    print("🔧 检查和修复模型路径...")
    
    script_dir = Path(__file__).parent
    musetalk_dir = script_dir / "MuseTalk"
    
    if not musetalk_dir.exists():
        print(f"❌ MuseTalk目录不存在: {musetalk_dir}")
        return False
    
    # 检查关键模型文件
    required_files = [
        "models/musetalkV15/unet.pth",
        "models/sd-vae/config.json",
        "models/dwpose/dw-ll_ucoco_384.pth"
    ]
    
    all_exist = True
    for file_path in required_files:
        full_path = musetalk_dir / file_path
        if full_path.exists():
            print(f"✅ {file_path}: {full_path.stat().st_size / (1024*1024):.1f}MB")
        else:
            print(f"❌ 缺失: {file_path}")
            all_exist = False
    
    return all_exist

def create_single_service_launcher():
    """创建单一服务启动器，避免双进程问题"""
    print("🚀 创建单一服务启动器...")
    
    script_dir = Path(__file__).parent
    launcher_path = script_dir / "MuseTalkEngine" / "direct_service_launcher.py"
    
    launcher_code = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接服务启动器 - 避免双进程问题
Direct Service Launcher - Avoid dual process issues
"""

import os
import sys
import argparse
from pathlib import Path

def setup_paths_and_environment():
    """设置路径和环境"""
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    musetalk_path = project_root / "MuseTalk"
    
    # 添加必要路径到sys.path
    paths_to_add = [str(musetalk_path), str(script_dir)]
    for path in paths_to_add:
        if os.path.exists(path) and path not in sys.path:
            sys.path.insert(0, path)
    
    # 设置工作目录为MuseTalk
    if musetalk_path.exists():
        os.chdir(musetalk_path)
        print(f"工作目录: {musetalk_path}")
        print(f"Python路径: {sys.path[:3]}")
        return True
    else:
        print(f"❌ MuseTalk目录不存在: {musetalk_path}")
        return False

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=28888)
    parser.add_argument('--mode', type=str, default='server') 
    parser.add_argument('--multi_gpu', action='store_true')
    parser.add_argument('--gpu_id', type=int, default=0)
    args = parser.parse_args()
    
    print("=" * 60)
    print("MuseTalk 直接服务启动器")
    print("=" * 60)
    
    # 设置环境
    if not setup_paths_and_environment():
        sys.exit(1)
    
    # 直接启动服务，无包装器
    try:
        print("🚀 直接启动Ultra Fast服务...")
        from ultra_fast_realtime_inference_v2 import start_ultra_fast_service
        start_ultra_fast_service(args.port)
    except Exception as e:
        print(f"❌ 服务启动失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
'''
    
    with open(launcher_path, 'w', encoding='utf-8') as f:
        f.write(launcher_code)
    
    print(f"✅ 单一服务启动器已创建: {launcher_path}")
    return launcher_path

def main():
    print("MuseTalk 服务架构修复工具")
    print("=" * 50)
    
    # 1. 清理所有Python进程
    kill_all_python_processes()
    
    # 2. 检查端口占用
    check_port_usage()
    
    # 3. 检查模型路径
    model_paths_ok = fix_model_paths()
    
    # 4. 创建单一服务启动器
    launcher_path = create_single_service_launcher()
    
    print("\n" + "=" * 50)
    print("🎉 修复完成!")
    print("\n建议:")
    print("1. 修改C#代码使用新的direct_service_launcher.py")
    print("2. 避免使用start_ultra_fast_service.py包装器")
    print("3. 确保只启动一个Python进程")
    print(f"4. 新启动器路径: {launcher_path}")
    
    if not model_paths_ok:
        print("\n⚠️  警告: 部分模型文件缺失，请检查MuseTalk目录")

if __name__ == "__main__":
    main()