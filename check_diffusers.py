#!/usr/bin/env python3
"""检查 diffusers 安装问题"""

import sys
import subprocess

print("=" * 50)
print("🔍 Diffusers 诊断工具")
print("=" * 50)
print()

# 1. 尝试导入
print("[1/4] 尝试导入 diffusers...")
try:
    import diffusers
    print(f"✅ 成功导入！版本: {diffusers.__version__}")
    print(f"   安装路径: {diffusers.__file__}")
    sys.exit(0)
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    print()

# 2. 检查是否安装
print("[2/4] 检查 pip 列表...")
result = subprocess.run(
    ["pip", "list", "--format=freeze"],
    capture_output=True,
    text=True
)

diffusers_found = False
for line in result.stdout.split('\n'):
    if 'diffusers' in line.lower():
        print(f"✅ 在 pip 列表中: {line}")
        diffusers_found = True

if not diffusers_found:
    print("❌ 未在 pip 列表中找到 diffusers")
print()

# 3. 检查依赖
print("[3/4] 检查关键依赖...")
deps = {
    "numpy": "NumPy",
    "PIL": "Pillow",
    "torch": "PyTorch",
    "transformers": "Transformers"
}

for module, name in deps.items():
    try:
        __import__(module)
        print(f"✅ {name}")
    except ImportError:
        print(f"❌ {name} - 缺失（diffusers 需要）")
print()

# 4. 尝试安装并显示详细输出
print("[4/4] 建议操作：")
print()
print("手动安装并查看详细日志：")
print("  python3 -m pip install diffusers==0.24.0 -v")
print()
print("或尝试最新版本：")
print("  python3 -m pip install diffusers")
print()
print("检查是否有冲突：")
print("  pip check")
print()
