#!/bin/bash
# 快速依赖检查脚本

echo "=== 快速依赖检查 ==="
echo ""

echo "1. 检查 Python 版本:"
python3 --version

echo ""
echo "2. 检查关键库是否真的缺失:"

# 定义要检查的库
libs=(
    "torch:PyTorch"
    "numpy:NumPy"
    "cv2:OpenCV"
    "PIL:Pillow"
    "transformers:Transformers"
    "fastapi:FastAPI"
)

for lib_info in "${libs[@]}"; do
    IFS=':' read -r lib name <<< "$lib_info"
    if python3 -c "import $lib" 2>/dev/null; then
        echo "✅ $name ($lib) - 已安装"
    else
        echo "❌ $name ($lib) - 未安装"
    fi
done

echo ""
echo "3. 检查配置文件位置:"
for path in "/opt/musetalk/repo/config_paths.py" "/opt/musetalk/repo/MuseTalkEngine/config_paths.py"; do
    if [ -f "$path" ]; then
        echo "✅ 找到: $path"
    else
        echo "❌ 未找到: $path"
    fi
done

echo ""
echo "4. 检查 MuseTalk 源码:"
for path in "/opt/musetalk/repo/MuseTalk" "/opt/musetalk/repo/backend_python/musetalk"; do
    if [ -d "$path" ]; then
        echo "✅ 找到: $path"
    else
        echo "❌ 未找到: $path"
    fi
done

echo ""
echo "=== 检查完成 ==="
