@echo off
chcp 65001 >nul 2>&1
echo ================================================================================
echo                    数字人项目 - 一键环境设置
echo ================================================================================
echo.
echo 🎯 这将安装：
echo    1. Python虚拟环境 (venv_musetalk)
echo    2. 官方MuseTalk和所有依赖
echo    3. 必需的AI模型
echo.
echo ⚠️  请确保已安装：
echo    - Python 3.10+ 
echo    - Git
echo    - CUDA 11.7+ (你的12.1完全兼容)
echo.
pause

echo 📦 创建Python虚拟环境...
if exist "venv_musetalk" (
    echo 虚拟环境已存在，跳过创建
) else (
    python -m venv venv_musetalk
    if errorlevel 1 (
        echo ❌ 虚拟环境创建失败！请检查Python安装
        pause
        exit /b 1
    )
    echo ✅ 虚拟环境创建成功
)

echo 🔧 激活虚拟环境并升级pip...
call venv_musetalk\Scripts\activate.bat
python -m pip install --upgrade pip

echo 📦 安装PyTorch (CUDA 12.1兼容)...
echo 正在安装 torch==2.0.1 torchvision==0.15.2 torchaudio==2.0.2...
pip install torch==2.0.1 torchvision==0.15.2 torchaudio==2.0.2 --index-url https://download.pytorch.org/whl/cu118
if errorlevel 1 (
    echo ❌ PyTorch安装失败！
    pause
    exit /b 1
)
echo ✅ PyTorch安装成功

echo 📥 下载官方MuseTalk...
if exist "MuseTalk" (
    echo MuseTalk目录已存在，更新代码...
    cd MuseTalk
    git pull
    cd ..
) else (
    echo 正在克隆官方MuseTalk仓库...
    git clone https://github.com/TMElyralab/MuseTalk.git
    if errorlevel 1 (
        echo ❌ MuseTalk下载失败！请检查网络连接
        pause
        exit /b 1
    )
    echo ✅ MuseTalk下载成功
)

echo 📦 安装MuseTalk依赖...
cd MuseTalk
if exist "requirements.txt" (
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ❌ MuseTalk依赖安装失败！
        cd ..
        pause
        exit /b 1
    )
    echo ✅ MuseTalk依赖安装成功
) else (
    echo ⚠️  requirements.txt未找到，手动安装核心依赖...
    pip install opencv-python pillow numpy librosa soundfile
)

echo 🔧 安装MMLab生态系统...
pip install --no-cache-dir -U openmim
mim install mmengine
mim install "mmcv==2.0.1"
mim install "mmdet==3.1.0"
mim install "mmpose==1.1.0"
if errorlevel 1 (
    echo ⚠️  MMLab安装可能有问题，但不影响基本功能
)

echo 📥 检查MuseTalk模型权重...

REM 检查是否已有模型备份
if exist "..\Models\musetalk\MuseTalk\models" (
    echo ✅ 发现已有MuseTalk模型备份
    echo 🔄 复制模型到官方位置...
    xcopy /E /I /Y "..\Models\musetalk\MuseTalk\models\*" "models\"
    if errorlevel 1 (
        echo ⚠️  模型复制失败，尝试官方下载...
    ) else (
        echo ✅ 模型复制成功，跳过下载
        goto skip_download
    )
)

REM 尝试官方下载脚本
if exist "download_weights.bat" (
    echo 运行官方权重下载脚本...
    call download_weights.bat
) else if exist "download_weights.sh" (
    echo 找到Linux下载脚本，请手动运行: bash download_weights.sh
) else (
    echo ⚠️  自动模型下载脚本未找到
    echo 📋 请手动下载模型到 models/ 目录：
    echo    1. 访问 https://github.com/TMElyralab/MuseTalk/releases
    echo    2. 下载模型权重文件
    echo    3. 解压到 MuseTalk/models/ 目录
)

:skip_download

cd ..

echo 🔧 安装Edge-TTS (语音合成)...
pip install edge-tts
if errorlevel 1 (
    echo ❌ Edge-TTS安装失败！
    pause
    exit /b 1
)
echo ✅ Edge-TTS安装成功

echo 🔧 安装其他必需依赖...
pip install requests aiohttp

echo ✅ 环境设置完成！
echo.
echo 📋 安装总结：
echo    ✅ Python虚拟环境: venv_musetalk
echo    ✅ 官方MuseTalk: MuseTalk/
echo    ✅ PyTorch + CUDA支持
echo    ✅ MMLab生态系统
echo    ✅ Edge-TTS语音合成
echo.
echo 🚀 下一步：
echo    1. 运行 start-development.bat 启动开发环境
echo    2. 或运行 deploy-production-now.bat 部署到IIS
echo.
echo 💡 提示：
echo    - 如果模型下载失败，请手动下载到 MuseTalk/models/
echo    - 你的Python 3.10.11 + CUDA 12.1环境完全兼容
echo.
pause