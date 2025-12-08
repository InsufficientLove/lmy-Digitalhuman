#!/bin/bash
# MuseTalk 项目重构脚本
# 目标：分离 Python、C#、遗留代码

set -e  # 遇到错误立即退出

echo "=========================================="
echo "🔧 开始重构项目结构"
echo "=========================================="

# 定义基础路径
BASE_DIR="/opt/musetalk/repo"
WORKSPACE_DIR="/workspace"

# 如果在 /workspace 目录，使用 /workspace 作为基础目录
if [ -d "$WORKSPACE_DIR/LmyDigitalHuman" ]; then
    BASE_DIR="$WORKSPACE_DIR"
fi

cd "$BASE_DIR"

echo "📂 当前工作目录: $(pwd)"

# ========================================
# 第一步：创建新目录结构
# ========================================
echo ""
echo "[1/4] 创建新目录结构..."

mkdir -p backend_python/musetalk
mkdir -p backend_python/scripts
mkdir -p backend_python/configs
mkdir -p backend_dotnet
mkdir -p legacy

echo "✅ 目录创建完成"

# ========================================
# 第二步：移动 Python 文件
# ========================================
echo ""
echo "[2/4] 移动 Python 相关文件..."

# 移动 MuseTalkEngine 下的所有内容到 backend_python
if [ -d "MuseTalkEngine" ]; then
    echo "  📦 移动 MuseTalkEngine/ -> backend_python/"
    
    # 移动核心 Python 文件
    [ -f "MuseTalkEngine/main_realtime.py" ] && mv MuseTalkEngine/main_realtime.py backend_python/
    [ -f "MuseTalkEngine/main.py" ] && mv MuseTalkEngine/main.py backend_python/
    [ -f "MuseTalkEngine/preprocess_assets.py" ] && mv MuseTalkEngine/preprocess_assets.py backend_python/
    
    # 移动 core, offline, streaming 目录
    [ -d "MuseTalkEngine/core" ] && mv MuseTalkEngine/core backend_python/
    [ -d "MuseTalkEngine/offline" ] && mv MuseTalkEngine/offline backend_python/
    [ -d "MuseTalkEngine/streaming" ] && mv MuseTalkEngine/streaming backend_python/
    
    # 移动脚本文件
    [ -f "MuseTalkEngine/start_realtime_service.sh" ] && mv MuseTalkEngine/start_realtime_service.sh backend_python/scripts/
    [ -f "MuseTalkEngine/test_realtime_system.py" ] && mv MuseTalkEngine/test_realtime_system.py backend_python/scripts/
    [ -f "MuseTalkEngine/test_imports.py" ] && mv MuseTalkEngine/test_imports.py backend_python/scripts/
    
    # 移动配置文件
    [ -f "MuseTalkEngine/.env.example" ] && mv MuseTalkEngine/.env.example backend_python/configs/
    [ -f "MuseTalkEngine/requirements_realtime.txt" ] && mv MuseTalkEngine/requirements_realtime.txt backend_python/
    [ -f "MuseTalkEngine/requirements.txt" ] && mv MuseTalkEngine/requirements.txt backend_python/
    [ -f "MuseTalkEngine/requirements_complete.txt" ] && mv MuseTalkEngine/requirements_complete.txt backend_python/
    [ -f "MuseTalkEngine/requirements_musetalk_official.txt" ] && mv MuseTalkEngine/requirements_musetalk_official.txt backend_python/
    
    # 移动文档
    [ -f "MuseTalkEngine/README_REALTIME.md" ] && mv MuseTalkEngine/README_REALTIME.md backend_python/
    [ -f "MuseTalkEngine/QUICKSTART.md" ] && mv MuseTalkEngine/QUICKSTART.md backend_python/
    [ -f "MuseTalkEngine/IMPLEMENTATION_SUMMARY.md" ] && mv MuseTalkEngine/IMPLEMENTATION_SUMMARY.md backend_python/
    [ -f "MuseTalkEngine/INDEX.md" ] && mv MuseTalkEngine/INDEX.md backend_python/
    [ -f "MuseTalkEngine/交付说明.md" ] && mv MuseTalkEngine/交付说明.md backend_python/
    
    # 移动 Dockerfile
    [ -f "MuseTalkEngine/Dockerfile" ] && mv MuseTalkEngine/Dockerfile backend_python/
    [ -f "MuseTalkEngine/Dockerfile.cuda11" ] && mv MuseTalkEngine/Dockerfile.cuda11 backend_python/
    
    # 删除空的 MuseTalkEngine 目录
    if [ -d "MuseTalkEngine" ] && [ -z "$(ls -A MuseTalkEngine)" ]; then
        rmdir MuseTalkEngine
        echo "  🗑️  删除空目录 MuseTalkEngine/"
    fi
fi

# 移动根目录下的 Python 脚本到 legacy
for file in check_template.py fix_mmcv.sh fix_model_paths.sh fix_paths.sh; do
    if [ -f "$file" ]; then
        mv "$file" legacy/
        echo "  📦 移动 $file -> legacy/"
    fi
done

echo "✅ Python 文件移动完成"

# ========================================
# 第三步：移动 C# 文件
# ========================================
echo ""
echo "[3/4] 移动 C# 相关文件..."

# 移动 LmyDigitalHuman 目录
if [ -d "LmyDigitalHuman" ]; then
    mv LmyDigitalHuman backend_dotnet/
    echo "  📦 移动 LmyDigitalHuman/ -> backend_dotnet/"
fi

# 移动 .sln 文件
if [ -f "LmyDigitalHuman.sln" ]; then
    mv LmyDigitalHuman.sln backend_dotnet/
    echo "  📦 移动 LmyDigitalHuman.sln -> backend_dotnet/"
fi

echo "✅ C# 文件移动完成"

# ========================================
# 第四步：移动遗留文件
# ========================================
echo ""
echo "[4/4] 移动遗留文件..."

# 移动 Jupyter Notebooks
find . -maxdepth 1 -name "*.ipynb" -exec mv {} legacy/ \; 2>/dev/null || true

# 移动旧的脚本
[ -f "check_docker.sh" ] && mv check_docker.sh legacy/
[ -f "implementation_plan.md" ] && mv implementation_plan.md legacy/

echo "✅ 遗留文件移动完成"

# ========================================
# 创建 README 文件
# ========================================
echo ""
echo "[+] 创建 README 文件..."

cat > README.md << 'EOL'
# LmyDigitalHuman 项目

## 📂 项目结构

```
/opt/musetalk/repo/
├── backend_python/           # Python 后端（MuseTalk 核心）
│   ├── main_realtime.py     # 实时推理服务入口
│   ├── preprocess_assets.py # 视频预处理脚本
│   ├── core/                # 核心模块
│   ├── offline/             # 离线推理
│   ├── streaming/           # 流式处理
│   ├── scripts/             # 工具脚本
│   │   ├── check_env.py     # 环境检查脚本 ⭐
│   │   └── start_realtime_service.sh
│   └── configs/             # 配置文件
│       └── .env.example
│
├── backend_dotnet/          # C# 后端（中控服务）
│   ├── LmyDigitalHuman/
│   └── LmyDigitalHuman.sln
│
└── legacy/                  # 遗留代码（不再使用）
    ├── *.ipynb
    └── 旧脚本

```

## 🚀 快速开始

### 1. 环境检查（必须！）
```bash
cd /opt/musetalk/repo/backend_python
python scripts/check_env.py
```

### 2. 启动服务
```bash
cd /opt/musetalk/repo/backend_python
./scripts/start_realtime_service.sh
```

## 📖 文档

- [快速开始](backend_python/QUICKSTART.md)
- [完整文档](backend_python/README_REALTIME.md)
- [交付说明](backend_python/交付说明.md)

## 🔧 环境要求

- Ubuntu 22.04
- CUDA 12.9
- Python 3.9+
- 模型路径：`/opt/musetalk/models/`

EOL

echo "✅ README.md 创建完成"

# ========================================
# 完成
# ========================================
echo ""
echo "=========================================="
echo "✅ 项目重构完成！"
echo "=========================================="
echo ""
echo "📊 新的目录结构："
echo ""
tree -L 2 -d "$BASE_DIR" 2>/dev/null || ls -la "$BASE_DIR"
echo ""
echo "🎯 下一步："
echo "  1. cd /opt/musetalk/repo/backend_python"
echo "  2. python scripts/check_env.py"
echo "  3. ./scripts/start_realtime_service.sh"
echo ""
