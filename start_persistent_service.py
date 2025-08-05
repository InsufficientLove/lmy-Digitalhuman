#!/usr/bin/env python3
"""
启动持久化MuseTalk服务脚本
自动检测环境，启动持久化服务
"""

import os
import sys
import subprocess
import time
import signal
from pathlib import Path

def find_python_executable():
    """查找可用的Python执行程序"""
    project_root = Path(__file__).parent
    
    # 优先使用venv_musetalk
    possible_paths = [
        project_root / "venv_musetalk" / "Scripts" / "python.exe",  # Windows
        project_root / "venv_musetalk" / "bin" / "python",         # Linux/Mac
        "python",  # 系统Python
        "python3"  # 系统Python3
    ]
    
    for python_path in possible_paths:
        try:
            if isinstance(python_path, Path):
                if python_path.exists():
                    print(f"✅ 找到Python: {python_path}")
                    return str(python_path)
            else:
                # 测试系统Python
                result = subprocess.run([python_path, "--version"], 
                                       capture_output=True, 
                                       text=True, 
                                       timeout=5)
                if result.returncode == 0:
                    print(f"✅ 找到系统Python: {python_path}")
                    return python_path
        except Exception:
            continue
    
    raise RuntimeError("❌ 未找到可用的Python解释器")

def start_persistent_service(python_path, port=58080):
    """启动持久化服务"""
    project_root = Path(__file__).parent
    service_script = project_root / "MuseTalk" / "persistent_musetalk_service.py"
    
    if not service_script.exists():
        raise FileNotFoundError(f"❌ 服务脚本不存在: {service_script}")
    
    print(f"🚀 启动持久化MuseTalk服务...")
    print(f"📡 端口: {port}")
    print(f"🐍 Python: {python_path}")
    print(f"📜 脚本: {service_script}")
    
    # 启动服务
    cmd = [
        python_path,
        str(service_script),
        "--host", "127.0.0.1",
        "--port", str(port),
        "--device", "cuda:0"
    ]
    
    print(f"💻 执行命令: {' '.join(cmd)}")
    
    try:
        # 启动进程
        process = subprocess.Popen(
            cmd,
            cwd=str(project_root),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # 实时输出日志
        for line in iter(process.stdout.readline, ''):
            print(line.rstrip())
            
    except KeyboardInterrupt:
        print(f"\n🛑 收到中断信号，正在关闭服务...")
        process.terminate()
        process.wait()
        print(f"🔌 服务已关闭")
    except Exception as e:
        print(f"❌ 启动服务失败: {e}")
        raise

def main():
    """主函数"""
    try:
        # 检查参数
        port = 58080
        if len(sys.argv) > 1:
            try:
                port = int(sys.argv[1])
            except ValueError:
                print(f"❌ 无效端口号: {sys.argv[1]}")
                sys.exit(1)
        
        # 查找Python
        python_path = find_python_executable()
        
        # 启动服务
        start_persistent_service(python_path, port)
        
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()