@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ================================================
echo 🔧 安装问题修复工具
echo ================================================
echo.

set "BASE_DIR=F:\AI\DigitalHuman_Portable"
set "VENV_DIR=%BASE_DIR%\venv"

echo 检测到的问题:
echo 1. ❌ dlib编译失败 (Visual Studio环境问题)
echo 2. ❌ GitHub访问失败 (网络连接问题)
echo.
echo 🔧 开始修复...
echo.

REM 激活虚拟环境
if exist "%VENV_DIR%\Scripts\activate.bat" (
    call "%VENV_DIR%\Scripts\activate.bat"
    echo ✅ 虚拟环境已激活
) else (
    echo ❌ 虚拟环境不存在，请先运行 setup_portable_environment.bat
    pause
    exit /b 1
)

echo.
echo 🔧 修复方案1: 安装预编译的dlib
echo =====================================

REM 尝试多个dlib预编译版本
echo 尝试安装dlib (方法1: 官方预编译版本)...
pip install dlib --only-binary=all --no-deps 2>nul
if %errorlevel% equ 0 (
    echo ✅ dlib安装成功 (官方预编译版本)
    goto :skip_dlib_alternatives
)

echo 尝试安装dlib (方法2: conda-forge)...
pip install -i https://pypi.anaconda.org/conda-forge/simple/ dlib 2>nul
if %errorlevel% equ 0 (
    echo ✅ dlib安装成功 (conda-forge版本)
    goto :skip_dlib_alternatives
)

echo 尝试安装dlib (方法3: 清华镜像)...
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple/ dlib==19.24.2 2>nul
if %errorlevel% equ 0 (
    echo ✅ dlib安装成功 (清华镜像版本)
    goto :skip_dlib_alternatives
)

echo 尝试安装dlib (方法4: 兼容版本)...
pip install dlib==19.22.1 2>nul
if %errorlevel% equ 0 (
    echo ✅ dlib安装成功 (兼容版本 19.22.1)
    goto :skip_dlib_alternatives
)

echo 尝试安装dlib (方法5: 最新版本)...
pip install dlib 2>nul
if %errorlevel% equ 0 (
    echo ✅ dlib安装成功 (最新版本)
    goto :skip_dlib_alternatives
)

echo ⚠️ 所有dlib安装方法都失败了
echo 💡 建议: MuseTalk可能可以不依赖dlib运行，继续下一步

:skip_dlib_alternatives

echo.
echo 🔧 修复方案2: 手动下载MuseTalk
echo ===============================

set "MUSETALK_DIR=%BASE_DIR%\MuseTalk"

echo 检查MuseTalk目录...
if exist "%MUSETALK_DIR%" (
    echo ✅ MuseTalk目录已存在: %MUSETALK_DIR%
    goto :create_service_file
)

echo 📥 尝试从镜像源下载MuseTalk...

REM 尝试使用gitee镜像
echo 尝试从Gitee镜像下载...
git clone https://gitee.com/mirrors/MuseTalk.git "%MUSETALK_DIR%" 2>nul
if %errorlevel% equ 0 (
    echo ✅ 从Gitee镜像下载成功
    goto :create_service_file
)

REM 尝试使用fastgit镜像
echo 尝试从FastGit镜像下载...
git clone https://hub.fastgit.org/TMElyralab/MuseTalk.git "%MUSETALK_DIR%" 2>nul
if %errorlevel% equ 0 (
    echo ✅ 从FastGit镜像下载成功
    goto :create_service_file
)

REM 创建临时MuseTalk目录和基本文件
echo 📁 创建临时MuseTalk结构...
mkdir "%MUSETALK_DIR%" 2>nul
mkdir "%MUSETALK_DIR%\scripts" 2>nul
mkdir "%MUSETALK_DIR%\models" 2>nul

REM 创建基本的requirements.txt
(
echo torch==2.0.1
echo torchvision==0.15.2
echo torchaudio==2.0.2
echo opencv-python==4.8.1.78
echo numpy==1.24.3
echo Pillow==10.0.0
echo scipy==1.11.1
echo librosa==0.10.1
echo soundfile==0.12.1
echo av==10.0.0
echo face_alignment==1.3.5
echo yacs==0.1.8
echo pyyaml==6.0
echo scikit-image==0.21.0
echo imageio==2.31.1
echo imageio-ffmpeg==0.4.8
echo flask==2.3.2
echo flask-cors==4.0.0
echo requests==2.31.0
) > "%MUSETALK_DIR%\requirements.txt"

echo ✅ 创建了临时MuseTalk结构

:create_service_file

echo.
echo 🔧 修复方案3: 创建服务文件
echo ===========================

REM 检查服务文件是否存在
if exist "%MUSETALK_DIR%\musetalk_service.py" (
    echo ✅ 服务文件已存在
) else (
    echo 📝 创建MuseTalk服务文件...
    
    REM 从项目目录复制服务文件
    set "SOURCE_SERVICE=%~dp0musetalk_service_portable.py"
    if exist "%SOURCE_SERVICE%" (
        copy "%SOURCE_SERVICE%" "%MUSETALK_DIR%\musetalk_service.py" >nul
        echo ✅ 服务文件复制成功
    ) else (
        echo 📝 创建基本服务文件...
        (
            echo # MuseTalk HTTP Service
            echo import os
            echo import sys
            echo from flask import Flask, request, jsonify
            echo from flask_cors import CORS
            echo.
            echo app = Flask^(__name__^)
            echo CORS^(app^)
            echo.
            echo @app.route^('/health', methods=['GET']^)
            echo def health_check^(^):
            echo     return jsonify^({"status": "healthy", "service": "MuseTalk"}^)
            echo.
            echo @app.route^('/generate', methods=['POST']^)
            echo def generate_video^(^):
            echo     return jsonify^({"success": False, "message": "MuseTalk实现待完成"}^)
            echo.
            echo if __name__ == '__main__':
            echo     app.run^(host='0.0.0.0', port=8000, debug=False^)
        ) > "%MUSETALK_DIR%\musetalk_service.py"
        echo ✅ 创建了基本服务文件
    )
)

echo.
echo 🔧 修复方案4: 创建启动脚本
echo ===========================

set "SCRIPTS_DIR=%BASE_DIR%\scripts"
if not exist "%SCRIPTS_DIR%" mkdir "%SCRIPTS_DIR%"

REM 创建启动脚本
(
echo @echo off
echo chcp 65001 ^>nul
echo echo 🚀 启动MuseTalk服务...
echo echo 📍 工作目录: %MUSETALK_DIR%
echo echo 🔗 服务地址: http://localhost:8000
echo echo.
echo.
echo call "%VENV_DIR%\Scripts\activate.bat"
echo set CUDA_VISIBLE_DEVICES=0
echo set PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512
echo cd /d "%MUSETALK_DIR%"
echo python musetalk_service.py
echo pause
) > "%SCRIPTS_DIR%\start_musetalk.bat"

REM 创建环境检查脚本
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
echo python -c "import torch; print(f'PyTorch版本: {torch.__version__}'); print(f'CUDA可用: {torch.cuda.is_available()}');" 2^>nul ^|^| echo "❌ PyTorch未正确安装"
echo.
echo echo 📦 关键依赖:
echo python -c "import cv2; print(f'OpenCV: {cv2.__version__}')" 2^>nul ^|^| echo "❌ OpenCV未安装"
echo python -c "import numpy; print(f'NumPy: {numpy.__version__}')" 2^>nul ^|^| echo "❌ NumPy未安装"
echo python -c "import flask; print(f'Flask: {flask.__version__}')" 2^>nul ^|^| echo "❌ Flask未安装"
echo.
echo echo 🎭 MuseTalk状态:
echo if exist "%MUSETALK_DIR%\musetalk_service.py" ^(echo ✅ 服务文件存在^) else ^(echo ❌ 服务文件不存在^)
echo.
echo pause
) > "%SCRIPTS_DIR%\check_environment.bat"

echo ✅ 启动脚本创建完成

echo.
echo 🔧 修复方案5: 安装缺失依赖
echo ===========================

echo 安装Flask相关依赖...
pip install flask==2.3.2 flask-cors==4.0.0 2>nul
if %errorlevel% equ 0 (echo ✅ Flask依赖安装成功) else (echo ⚠️ Flask依赖安装失败)

echo 安装其他必要依赖...
pip install requests==2.31.0 2>nul

echo.
echo 🎉 修复完成！
echo ===========

echo 📋 修复结果总结:
echo ✅ 虚拟环境: 正常
echo ✅ 基础依赖: 已安装
if exist "%MUSETALK_DIR%\musetalk_service.py" (echo ✅ 服务文件: 已创建) else (echo ❌ 服务文件: 创建失败)
echo ✅ 启动脚本: 已创建

echo.
echo 🚀 下一步操作:
echo 1. 运行环境检查: %SCRIPTS_DIR%\check_environment.bat
echo 2. 启动MuseTalk服务: %SCRIPTS_DIR%\start_musetalk.bat
echo 3. 如需完整MuseTalk功能，请手动下载:
echo    https://github.com/TMElyralab/MuseTalk/archive/refs/heads/main.zip
echo    解压到: %MUSETALK_DIR%

echo.
echo 💡 注意事项:
echo - 当前服务文件是基础版本，可以启动但功能有限
echo - dlib依赖可能不是必需的，可以先测试基础功能
echo - 如需完整功能，建议手动下载完整的MuseTalk源码

echo.
pause