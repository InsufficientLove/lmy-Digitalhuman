#!/usr/bin/env python3
"""
简单的Python环境测试脚本
"""
import sys
import os

print("🚀 Python环境测试开始...")
print(f"🐍 Python版本: {sys.version}")
print(f"🐍 Python路径: {sys.executable}")
print(f"🐍 工作目录: {os.getcwd()}")
print(f"🐍 Python路径列表:")
for path in sys.path:
    print(f"   - {path}")

# 测试torch导入
try:
    import torch
    print(f"✅ torch版本: {torch.__version__}")
    print(f"✅ torch路径: {torch.__file__}")
    print(f"✅ CUDA可用: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"✅ GPU数量: {torch.cuda.device_count()}")
        for i in range(torch.cuda.device_count()):
            print(f"   GPU {i}: {torch.cuda.get_device_name(i)}")
    else:
        print("⚠️ CUDA不可用")
except ImportError as e:
    print(f"❌ torch导入失败: {str(e)}")
    sys.exit(1)
except Exception as e:
    print(f"❌ torch测试失败: {str(e)}")
    sys.exit(1)

print("✅ Python环境测试完成！")