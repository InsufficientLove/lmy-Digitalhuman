@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ================================================
echo 🚀 数字人便携式环境安装脚本
echo ================================================
echo.

REM 设置基础路径
set "BASE_DIR=F:\AI\DigitalHuman_Portable"
set "PYTHON_DIR=%BASE_DIR%\python"
set "VENV_DIR=%BASE_DIR%\venv"
set "MUSETALK_DIR=%BASE_DIR%\MuseTalk"
set "MODELS_DIR=%BASE_DIR%\models"
set "SCRIPTS_DIR=%BASE_DIR%\scripts"
set "CONFIG_DIR=%BASE_DIR%\config"
set "LOGS_DIR=%BASE_DIR%\logs"

echo 📁 创建目录结构...
if not exist "%BASE_DIR%" mkdir "%BASE_DIR%"
if not exist "%PYTHON_DIR%" mkdir "%PYTHON_DIR%"
if not exist "%MODELS_DIR%" mkdir "%MODELS_DIR%"
if not exist "%SCRIPTS_DIR%" mkdir "%SCRIPTS_DIR%"
if not exist "%CONFIG_DIR%" mkdir "%CONFIG_DIR%"
if not exist "%LOGS_DIR%" mkdir "%LOGS_DIR%"

echo.
echo 🐍 检查Python安装...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 未检测到Python，请先安装Python 3.10.11
    echo 📥 下载地址: https://www.python.org/downloads/release/python-31011/
    echo 💡 建议选择 "Windows installer (64-bit)" 并勾选 "Add Python to PATH"
    pause
    exit /b 1
)

echo ✅ Python已安装
python --version

echo.
echo 🔧 创建虚拟环境...
if exist "%VENV_DIR%" (
    echo 🗑️ 删除现有虚拟环境...
    rmdir /s /q "%VENV_DIR%"
)

python -m venv "%VENV_DIR%"
if %errorlevel% neq 0 (
    echo ❌ 虚拟环境创建失败
    pause
    exit /b 1
)

echo ✅ 虚拟环境创建成功

echo.
echo 📦 激活虚拟环境并升级pip...
call "%VENV_DIR%\Scripts\activate.bat"
python -m pip install --upgrade pip

echo.
echo 🔥 安装PyTorch (CUDA支持)...
echo 💡 检测显卡数量...

REM 检测NVIDIA显卡
nvidia-smi >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ 检测到NVIDIA显卡，安装CUDA版本PyTorch
    pip install torch==2.0.1+cu118 torchvision==0.15.2+cu118 torchaudio==2.0.2+cu118 --index-url https://download.pytorch.org/whl/cu118
) else (
    echo ⚠️ 未检测到NVIDIA显卡，安装CPU版本PyTorch
    pip install torch==2.0.1 torchvision==0.15.2 torchaudio==2.0.2
)

echo.
echo 📚 安装MuseTalk依赖...
pip install opencv-python==4.8.1.78
pip install numpy==1.24.3
pip install Pillow==10.0.0
pip install scipy==1.11.1
pip install librosa==0.10.1
pip install soundfile==0.12.1
pip install av==10.0.0
pip install face_alignment==1.3.5
pip install yacs==0.1.8
pip install pyyaml==6.0
pip install scikit-image==0.21.0
pip install imageio==2.31.1
pip install imageio-ffmpeg==0.4.8
pip install flask==2.3.2
pip install flask-cors==4.0.0
pip install requests==2.31.0

REM 尝试安装dlib (可能需要Visual Studio)
echo.
echo 🔨 安装dlib (可能需要编译)...
pip install dlib==19.24.2
if %errorlevel% neq 0 (
    echo ⚠️ dlib安装失败，尝试使用预编译版本...
    pip install https://files.pythonhosted.org/packages/0e/ce/f8a3cff33ac03a8219768f0694c5d703c8e037e6aba2e865f9bae22ed63c/dlib-19.24.2-cp310-cp310-win_amd64.whl
)

echo.
echo 📥 下载MuseTalk源码...
if exist "%MUSETALK_DIR%" (
    echo 🗑️ 删除现有MuseTalk目录...
    rmdir /s /q "%MUSETALK_DIR%"
)

git clone https://github.com/TMElyralab/MuseTalk.git "%MUSETALK_DIR%"
if %errorlevel% neq 0 (
    echo ❌ MuseTalk下载失败，请检查网络连接或手动下载
    echo 📥 手动下载地址: https://github.com/TMElyralab/MuseTalk/archive/refs/heads/main.zip
    pause
    exit /b 1
)

echo ✅ MuseTalk源码下载完成

echo.
echo 📦 下载预训练模型...
cd /d "%MUSETALK_DIR%"
if exist "scripts\download_models.py" (
    python scripts\download_models.py
    if %errorlevel% neq 0 (
        echo ⚠️ 自动下载模型失败，请手动下载
        echo 📥 模型下载地址: https://huggingface.co/TMElyralab/MuseTalk
    )
) else (
    echo ⚠️ 下载脚本不存在，请手动下载模型到 %MODELS_DIR%
)

echo.
echo 📝 创建启动脚本...
cd /d "%SCRIPTS_DIR%"

REM 创建启动MuseTalk服务的脚本
(
echo @echo off
echo chcp 65001 ^>nul
echo setlocal
echo.
echo echo 🚀 启动MuseTalk服务...
echo echo 📍 工作目录: %MUSETALK_DIR%
echo echo 🔗 服务地址: http://localhost:8000
echo echo.
echo.
echo REM 激活虚拟环境
echo call "%VENV_DIR%\Scripts\activate.bat"
echo.
echo REM 设置环境变量
echo set CUDA_VISIBLE_DEVICES=0
echo set PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512
echo.
echo REM 切换到MuseTalk目录
echo cd /d "%MUSETALK_DIR%"
echo.
echo REM 启动服务
echo python musetalk_service.py
echo.
echo pause
) > start_musetalk.bat

REM 创建检测环境的脚本
(
echo @echo off
echo chcp 65001 ^>nul
echo setlocal
echo.
echo echo 🔍 环境检测报告
echo echo ================
echo.
echo echo 📁 基础目录: %BASE_DIR%
echo if exist "%BASE_DIR%" ^(echo ✅ 基础目录存在^) else ^(echo ❌ 基础目录不存在^)
echo.
echo echo 🐍 Python环境:
echo call "%VENV_DIR%\Scripts\activate.bat"
echo python --version
echo.
echo echo 🔥 PyTorch状态:
echo python -c "import torch; print(f'PyTorch版本: {torch.__version__}'); print(f'CUDA可用: {torch.cuda.is_available()}'); print(f'CUDA设备数: {torch.cuda.device_count()}' if torch.cuda.is_available() else 'CPU模式')"
echo.
echo echo 📦 关键依赖:
echo python -c "import cv2; print(f'OpenCV: {cv2.__version__}')" 2^>nul ^|^| echo "❌ OpenCV未安装"
echo python -c "import numpy; print(f'NumPy: {numpy.__version__}')" 2^>nul ^|^| echo "❌ NumPy未安装"
echo python -c "import librosa; print(f'Librosa: {librosa.__version__}')" 2^>nul ^|^| echo "❌ Librosa未安装"
echo.
echo echo 🎭 MuseTalk状态:
echo if exist "%MUSETALK_DIR%\musetalk_service.py" ^(echo ✅ 服务文件存在^) else ^(echo ❌ 服务文件不存在^)
echo.
echo echo 🌐 网络测试:
echo curl -s http://localhost:8000/health 2^>nul ^|^| echo "❌ MuseTalk服务未启动"
echo.
echo pause
) > check_environment.bat

REM 创建多GPU配置脚本
(
echo @echo off
echo chcp 65001 ^>nul
echo setlocal
echo.
echo echo 🎮 GPU配置工具
echo echo ==============
echo.
echo nvidia-smi 2^>nul
echo if %%errorlevel%% neq 0 ^(
echo     echo ❌ 未检测到NVIDIA显卡或驱动
echo     goto :end
echo ^)
echo.
echo echo.
echo echo 请选择GPU配置:
echo echo 1. 单GPU (设备0)
echo echo 2. 双GPU (设备0,1)
echo echo 3. 自定义配置
echo echo.
echo set /p choice="请输入选择 (1-3): "
echo.
echo if "%%choice%%"=="1" ^(
echo     set CUDA_DEVICES=0
echo     echo 📱 配置为单GPU模式
echo ^) else if "%%choice%%"=="2" ^(
echo     set CUDA_DEVICES=0,1
echo     echo 🔥 配置为双GPU模式
echo ^) else if "%%choice%%"=="3" ^(
echo     set /p CUDA_DEVICES="请输入GPU设备ID (如: 0,1,2): "
echo ^) else ^(
echo     echo ❌ 无效选择
echo     goto :end
echo ^)
echo.
echo echo 💾 保存配置到环境文件...
echo echo CUDA_VISIBLE_DEVICES=%%CUDA_DEVICES%% ^> "%CONFIG_DIR%\gpu_config.env"
echo echo PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512 ^>^> "%CONFIG_DIR%\gpu_config.env"
echo.
echo echo ✅ GPU配置完成: %%CUDA_DEVICES%%
echo.
echo :end
echo pause
) > configure_gpu.bat

echo.
echo 📋 创建配置文件...
cd /d "%CONFIG_DIR%"

REM 创建默认GPU配置
echo CUDA_VISIBLE_DEVICES=0 > gpu_config.env
echo PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512 >> gpu_config.env

REM 创建服务配置
(
echo {
echo   "host": "0.0.0.0",
echo   "port": 8000,
echo   "debug": false,
echo   "model_config": {
echo     "batch_size": 4,
echo     "fps": 25,
echo     "quality": "medium",
echo     "enable_emotion": true
echo   },
echo   "paths": {
echo     "models": "%MODELS_DIR%",
echo     "temp": "%BASE_DIR%\\temp",
echo     "output": "%BASE_DIR%\\output"
echo   }
echo }
) > service_config.json

echo.
echo 🎉 便携式环境安装完成！
echo.
echo 📍 安装位置: %BASE_DIR%
echo.
echo 🚀 使用方法:
echo    1. 运行 %SCRIPTS_DIR%\start_musetalk.bat 启动服务
echo    2. 运行 %SCRIPTS_DIR%\check_environment.bat 检测环境
echo    3. 运行 %SCRIPTS_DIR%\configure_gpu.bat 配置GPU
echo.
echo 📝 配置文件位置: %CONFIG_DIR%
echo 📊 日志文件位置: %LOGS_DIR%
echo.
pause