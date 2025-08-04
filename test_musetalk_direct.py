#!/usr/bin/env python3
"""
MuseTalk直接测试脚本 - 放在MuseTalk目录中运行
"""

import sys
import os
import time

def main():
    print("🚀 MuseTalk环境快速诊断")
    print(f"当前目录: {os.getcwd()}")
    print(f"Python路径: {sys.executable}")
    print()
    
    # 1. 测试基本导入
    print("测试1: 基本模块导入")
    try:
        import torch
        print(f"✅ PyTorch {torch.__version__}")
        print(f"✅ CUDA可用: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"✅ GPU数量: {torch.cuda.device_count()}")
        else:
            print("❌ CUDA不可用!")
    except Exception as e:
        print(f"❌ PyTorch导入失败: {e}")
        return
    
    # 2. 测试scripts导入
    print("\n测试2: scripts模块导入")
    try:
        import scripts
        print("✅ scripts模块导入成功")
    except Exception as e:
        print(f"❌ scripts模块导入失败: {e}")
        return
    
    # 3. 测试inference导入
    print("\n测试3: inference模块导入")
    try:
        from scripts import inference
        print("✅ inference模块导入成功")
    except Exception as e:
        print(f"❌ inference模块导入失败: {e}")
        print("详细错误:")
        import traceback
        traceback.print_exc()
        return
    
    # 4. 测试musetalk导入
    print("\n测试4: musetalk模块导入")
    try:
        import musetalk
        print("✅ musetalk模块导入成功")
    except Exception as e:
        print(f"❌ musetalk模块导入失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 5. 测试关键函数导入
    print("\n测试5: 关键函数导入")
    try:
        from musetalk.utils.utils import load_all_model
        print("✅ load_all_model导入成功")
    except Exception as e:
        print(f"❌ load_all_model导入失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n✅ 所有基本测试通过!")
    print("MuseTalk环境看起来正常。")
    print()
    print("如果inference脚本仍然卡住，可能原因:")
    print("1. 模型文件加载时卡住")
    print("2. GPU初始化卡住") 
    print("3. 配置文件解析问题")

if __name__ == "__main__":
    main()