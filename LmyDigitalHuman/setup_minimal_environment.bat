@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ================================================
echo 🚀 数字人最小化环境安装脚本
echo ================================================
echo 跳过有问题的依赖，创建可运行的基础环境
echo.

REM 设置基础路径
set "BASE_DIR=F:\AI\DigitalHuman_Portable"
set "PYTHON_DIR=%BASE_DIR%\python"
set "VENV_DIR=%BASE_DIR%\venv"
set "MUSETALK_DIR=%BASE_DIR%\MuseTalk"
set "SCRIPTS_DIR=%BASE_DIR%\scripts"
set "CONFIG_DIR=%BASE_DIR%\config"
set "LOGS_DIR=%BASE_DIR%\logs"

echo 📁 创建目录结构...
if not exist "%BASE_DIR%" mkdir "%BASE_DIR%"
if not exist "%SCRIPTS_DIR%" mkdir "%SCRIPTS_DIR%"
if not exist "%CONFIG_DIR%" mkdir "%CONFIG_DIR%"
if not exist "%LOGS_DIR%" mkdir "%LOGS_DIR%"
if not exist "%MUSETALK_DIR%" mkdir "%MUSETALK_DIR%"

echo.
echo 🐍 检查Python安装...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 未检测到Python，请先安装Python 3.10.11
    echo 📥 下载地址: https://www.python.org/downloads/release/python-31011/
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
echo 🔥 安装PyTorch (自动检测CUDA)...
nvidia-smi >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ 检测到NVIDIA显卡，安装CUDA版本PyTorch
    pip install torch==2.0.1+cu118 torchvision==0.15.2+cu118 torchaudio==2.0.2+cu118 --index-url https://download.pytorch.org/whl/cu118
) else (
    echo ⚠️ 未检测到NVIDIA显卡，安装CPU版本PyTorch
    pip install torch==2.0.1 torchvision==0.15.2 torchaudio==2.0.2
)

echo.
echo 📚 安装基础依赖 (跳过dlib)...
pip install opencv-python==4.8.1.78
pip install numpy==1.24.3
pip install Pillow==10.0.0
pip install scipy==1.11.1
pip install librosa==0.10.1
pip install soundfile==0.12.1
pip install imageio==2.31.1
pip install imageio-ffmpeg==0.4.8
pip install flask==2.3.2
pip install flask-cors==4.0.0
pip install requests==2.31.0

echo.
echo 📝 创建基础MuseTalk服务文件...
(
echo #!/usr/bin/env python3
echo # -*- coding: utf-8 -*-
echo """
echo 基础MuseTalk HTTP服务
echo """
echo.
echo import os
echo import sys
echo import json
echo import logging
echo import time
echo from pathlib import Path
echo from flask import Flask, request, jsonify
echo from flask_cors import CORS
echo.
echo # 获取脚本所在目录
echo SCRIPT_DIR = Path^(__file__^).parent.absolute^(^)
echo BASE_DIR = SCRIPT_DIR.parent
echo CONFIG_DIR = BASE_DIR / "config"
echo LOGS_DIR = BASE_DIR / "logs"
echo.
echo # 确保日志目录存在
echo LOGS_DIR.mkdir^(exist_ok=True^)
echo.
echo app = Flask^(__name__^)
echo CORS^(app^)
echo.
echo # 配置日志
echo log_file = LOGS_DIR / "musetalk_service.log"
echo logging.basicConfig^(
echo     level=logging.INFO,
echo     format='%%^(asctime^)s - %%^(levelname^)s - %%^(message^)s',
echo     handlers=[
echo         logging.FileHandler^(log_file, encoding='utf-8'^),
echo         logging.StreamHandler^(sys.stdout^)
echo     ]
echo ^)
echo.
echo logger = logging.getLogger^(__name__^)
echo.
echo @app.route^('/health', methods=['GET']^)
echo def health_check^(^):
echo     """健康检查接口"""
echo     try:
echo         import torch
echo         gpu_info = {
echo             "torch_version": torch.__version__,
echo             "cuda_available": torch.cuda.is_available^(^),
echo             "gpu_count": torch.cuda.device_count^(^) if torch.cuda.is_available^(^) else 0
echo         }
echo     except Exception as e:
echo         gpu_info = {"error": str^(e^)}
echo         
echo     return jsonify^({
echo         "status": "healthy",
echo         "service": "MuseTalk Basic",
echo         "gpu_info": gpu_info,
echo         "base_dir": str^(BASE_DIR^)
echo     }^)
echo.
echo @app.route^('/generate', methods=['POST']^)
echo def generate_video^(^):
echo     """生成数字人视频接口 ^(基础版本^)"""
echo     try:
echo         data = request.json
echo         logger.info^(f"收到生成请求: {data}"^)
echo         
echo         # 模拟处理过程
echo         time.sleep^(2^)
echo         
echo         return jsonify^({
echo             "success": True,
echo             "message": "基础服务运行正常，等待完整MuseTalk实现",
echo             "video_path": "/temp/placeholder.mp4",
echo             "processing_time": 2000
echo         }^)
echo         
echo     except Exception as e:
echo         logger.error^(f"生成视频失败: {str^(e^)}"^)
echo         return jsonify^({
echo             "success": False,
echo             "message": f"生成失败: {str^(e^)}"
echo         }^), 500
echo.
echo if __name__ == '__main__':
echo     logger.info^("启动基础MuseTalk服务..."^)
echo     app.run^(host='0.0.0.0', port=8000, debug=False, threaded=True^)
) > "%MUSETALK_DIR%\musetalk_service.py"

echo ✅ 基础服务文件创建完成

echo.
echo 📝 创建启动脚本...
(
echo @echo off
echo chcp 65001 ^>nul
echo echo 🚀 启动MuseTalk基础服务...
echo echo 📍 工作目录: %MUSETALK_DIR%
echo echo 🔗 服务地址: http://localhost:8000
echo echo 💡 这是基础版本，功能有限
echo echo.
echo.
echo call "%VENV_DIR%\Scripts\activate.bat"
echo set CUDA_VISIBLE_DEVICES=0
echo set PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512
echo cd /d "%MUSETALK_DIR%"
echo python musetalk_service.py
echo pause
) > "%SCRIPTS_DIR%\start_musetalk.bat"

echo.
echo 📝 创建环境检查脚本...
(
echo @echo off
echo chcp 65001 ^>nul
echo echo 🔍 环境检测报告
echo echo ================
echo echo 📁 基础目录: %BASE_DIR%
echo if exist "%BASE_DIR%" ^(echo ✅ 基础目录存在^) else ^(echo ❌ 基础目录不存在^)
echo if exist "%VENV_DIR%" ^(echo ✅ 虚拟环境存在^) else ^(echo ❌ 虚拟环境不存在^)
echo if exist "%MUSETALK_DIR%" ^(echo ✅ MuseTalk目录存在^) else ^(echo ❌ MuseTalk目录不存在^)
echo.
echo echo 🐍 Python环境:
echo call "%VENV_DIR%\Scripts\activate.bat"
echo python --version
echo.
echo echo 🔥 PyTorch状态:
echo python -c "import torch; print(f'PyTorch版本: {torch.__version__}'); print(f'CUDA可用: {torch.cuda.is_available()}'); print(f'GPU数量: {torch.cuda.device_count()}' if torch.cuda.is_available() else 'CPU模式')"
echo.
echo echo 📦 关键依赖:
echo python -c "import cv2; print(f'OpenCV: {cv2.__version__}')" 2^>nul ^|^| echo "❌ OpenCV未安装"
echo python -c "import numpy; print(f'NumPy: {numpy.__version__}')" 2^>nul ^|^| echo "❌ NumPy未安装"
echo python -c "import flask; print(f'Flask: {flask.__version__}')" 2^>nul ^|^| echo "❌ Flask未安装"
echo python -c "import librosa; print(f'Librosa: {librosa.__version__}')" 2^>nul ^|^| echo "❌ Librosa未安装"
echo.
echo echo 🎭 MuseTalk状态:
echo if exist "%MUSETALK_DIR%\musetalk_service.py" ^(echo ✅ 基础服务文件存在^) else ^(echo ❌ 服务文件不存在^)
echo.
echo echo 🌐 网络测试:
echo curl -s http://localhost:8000/health 2^>nul ^|^| echo "❌ MuseTalk服务未启动"
echo.
echo pause
) > "%SCRIPTS_DIR%\check_environment.bat"

echo.
echo 📝 创建GPU配置脚本...
(
echo @echo off
echo chcp 65001 ^>nul
echo echo 🎮 GPU配置工具
echo echo ==============
echo.
echo nvidia-smi 2^>nul
echo if %%errorlevel%% neq 0 ^(
echo     echo ❌ 未检测到NVIDIA显卡或驱动
echo     echo 💡 将使用CPU模式
echo     set CUDA_DEVICES=cpu
echo     goto :save_config
echo ^)
echo.
echo echo 请选择GPU配置:
echo echo 1. 单GPU ^(设备0^)
echo echo 2. CPU模式
echo echo.
echo set /p choice="请输入选择 ^(1-2^): "
echo.
echo if "%%choice%%"=="1" ^(
echo     set CUDA_DEVICES=0
echo     echo 📱 配置为单GPU模式
echo ^) else ^(
echo     set CUDA_DEVICES=cpu
echo     echo 💻 配置为CPU模式
echo ^)
echo.
echo :save_config
echo echo 💾 保存配置...
echo echo CUDA_VISIBLE_DEVICES=%%CUDA_DEVICES%% ^> "%CONFIG_DIR%\gpu_config.env"
echo echo PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512 ^>^> "%CONFIG_DIR%\gpu_config.env"
echo echo ✅ GPU配置完成
echo pause
) > "%SCRIPTS_DIR%\configure_gpu.bat"

echo.
echo 📋 创建默认配置文件...
echo CUDA_VISIBLE_DEVICES=0 > "%CONFIG_DIR%\gpu_config.env"
echo PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512 >> "%CONFIG_DIR%\gpu_config.env"

echo.
echo 🎉 最小化环境安装完成！
echo.
echo 📍 安装位置: %BASE_DIR%
echo.
echo 🚀 使用方法:
echo    1. 运行 %SCRIPTS_DIR%\check_environment.bat 检测环境
echo    2. 运行 %SCRIPTS_DIR%\start_musetalk.bat 启动基础服务
echo    3. 访问 http://localhost:8000/health 测试服务
echo.
echo 💡 注意事项:
echo    - 这是基础版本，跳过了dlib和完整MuseTalk源码
echo    - 服务可以启动，但功能有限
echo    - 如需完整功能，请运行 fix_installation_issues.bat 进行修复
echo    - 或手动下载MuseTalk源码到: %MUSETALK_DIR%
echo.
echo 📥 MuseTalk完整版下载地址:
echo    https://github.com/TMElyralab/MuseTalk/archive/refs/heads/main.zip
echo    或使用国内镜像: https://gitee.com/mirrors/MuseTalk.git
echo.
pause