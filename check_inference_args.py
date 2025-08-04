#!/usr/bin/env python3
"""
检查MuseTalk inference.py支持的参数
"""

import subprocess
import sys
import os

def check_inference_help():
    """检查inference.py的帮助信息"""
    print("🔍 检查inference.py支持的参数...")
    
    try:
        # 运行帮助命令
        result = subprocess.run([
            sys.executable, '-m', 'scripts.inference', '--help'
        ], capture_output=True, text=True, timeout=30)
        
        print(f"退出码: {result.returncode}")
        print("\n📋 标准输出:")
        print(result.stdout)
        print("\n❌ 错误输出:")
        print(result.stderr)
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("⚠️  命令超时")
        return False
    except Exception as e:
        print(f"❌ 执行失败: {e}")
        return False

def analyze_config_file():
    """分析配置文件内容"""
    print("\n📄 分析配置文件...")
    
    config_file = "configs/inference/test.yaml"
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                content = f.read()
                print(f"✅ {config_file} 内容:")
                print("-" * 50)
                print(content)
                print("-" * 50)
        except Exception as e:
            print(f"❌ 读取配置文件失败: {e}")
    else:
        print(f"❌ 配置文件不存在: {config_file}")

def main():
    print("🚀 MuseTalk inference参数检查")
    print("=" * 60)
    
    # 确保在MuseTalk目录中
    if 'MuseTalk' not in os.getcwd():
        print("❌ 请在MuseTalk目录中运行此脚本")
        return
    
    # 检查帮助信息
    check_inference_help()
    
    # 分析配置文件
    analyze_config_file()

if __name__ == "__main__":
    main()