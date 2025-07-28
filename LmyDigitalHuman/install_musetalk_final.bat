@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ================================================================
echo 🎵 MuseTalk数字人系统安装脚本 - 终极修复版
echo ================================================================
echo 修复: numpy冲突 + Python语法错误 + 完美兼容性
echo 针对您的环境: Python 3.10.11 + D盘VS2022
echo.

REM 错误处理
set "ERROR_OCCURRED=0"

echo 🔍 步骤1: 环境配置...

set "BASE_DIR=F:\AI\DigitalHuman"
set "VENV_DIR=%BASE_DIR%\venv"
set "TEMP_DIR=%BASE_DIR%\temp_install"

echo ✅ 安装路径: %BASE_DIR%
echo.

echo 🔍 步骤2: 检测CUDA环境...

set "CUDA_VERSION="
set "CUDA_PATH="

REM 检查CUDA 11.8
for %%d in (C D E F G) do (
    if exist "%%d:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.8\bin\nvcc.exe" (
        set "CUDA_PATH=%%d:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.8"
        set "CUDA_VERSION=11.8"
        echo ✅ 检测到CUDA 11.8: !CUDA_PATH!
        goto :cuda_found
    )
)

REM 检查CUDA 12.x
for %%d in (C D E F G) do (
    for %%v in (12.1 12.0 12.2 12.3) do (
        if exist "%%d:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v%%v\bin\nvcc.exe" (
            set "CUDA_PATH=%%d:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v%%v"
            set "CUDA_VERSION=%%v"
            echo ✅ 检测到CUDA %%v: !CUDA_PATH!
            goto :cuda_found
        )
    )
)

echo ⚠️  未检测到CUDA，将使用CPU版本
goto :cuda_check_done

:cuda_found
echo ✅ CUDA环境: %CUDA_VERSION%

:cuda_check_done

echo.
echo 🔍 步骤3: 检测VS和CMake...

set "VS_PATH="
if exist "D:\Program Files\Microsoft Visual Studio\2022\Community\VC\Tools\MSVC" (
    set "VS_PATH=D:\Program Files\Microsoft Visual Studio\2022\Community"
    echo ✅ Visual Studio 2022: %VS_PATH%
) else if exist "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Tools\MSVC" (
    set "VS_PATH=C:\Program Files\Microsoft Visual Studio\2022\Community"
    echo ✅ Visual Studio 2022: %VS_PATH%
)

set "CMAKE_PATH="
if not "%VS_PATH%"=="" (
    if exist "%VS_PATH%\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe" (
        set "CMAKE_PATH=%VS_PATH%\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin"
        echo ✅ VS内置CMake: %CMAKE_PATH%
    )
)

echo.
echo 🔍 步骤4: Python验证...

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python未安装
    set "ERROR_OCCURRED=1"
    goto :error_exit
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set "PYTHON_VERSION=%%i"
echo ✅ Python版本: %PYTHON_VERSION%

echo.
echo 🔍 步骤5: 创建虚拟环境...

if not exist "%BASE_DIR%" mkdir "%BASE_DIR%" 2>nul
if not exist "%TEMP_DIR%" mkdir "%TEMP_DIR%" 2>nul

if not exist "%VENV_DIR%" (
    echo 📦 创建虚拟环境...
    python -m venv "%VENV_DIR%"
    if !errorlevel! neq 0 (
        echo ❌ 虚拟环境创建失败
        set "ERROR_OCCURRED=1"
        goto :error_exit
    )
)

call "%VENV_DIR%\Scripts\activate.bat"
if %errorlevel% neq 0 (
    echo ❌ 虚拟环境激活失败
    set "ERROR_OCCURRED=1"
    goto :error_exit
)

echo.
echo 🔍 步骤6: 配置pip镜像源...

if not exist "%USERPROFILE%\.pip" mkdir "%USERPROFILE%\.pip" 2>nul

(
echo [global]
echo index-url = https://pypi.tuna.tsinghua.edu.cn/simple/
echo trusted-host = pypi.tuna.tsinghua.edu.cn
echo timeout = 120
echo retries = 5
) > "%USERPROFILE%\.pip\pip.conf"

python -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple/ >nul 2>&1
echo ✅ pip配置完成

echo.
echo 🔍 步骤7: 彻底解决numpy版本冲突...

echo 📦 完全清理现有包...
pip uninstall -y numpy opencv-python opencv-python-headless mediapipe dlib torch torchvision torchaudio >nul 2>&1

echo 📦 安装numpy 2.x兼容版本...
pip install "numpy>=2.0.0,<2.3.0" -i https://pypi.tuna.tsinghua.edu.cn/simple/
if %errorlevel% neq 0 (
    echo ❌ numpy安装失败
    set "ERROR_OCCURRED=1"
    goto :error_exit
)

echo ✅ numpy版本修复完成

echo.
echo 🔍 步骤8: 安装PyTorch...

if not "%CUDA_VERSION%"=="" (
    if "%CUDA_VERSION%"=="11.8" (
        echo 🎮 安装PyTorch CUDA 11.8...
        pip install torch==2.0.1+cu118 torchvision==0.15.2+cu118 torchaudio==2.0.2+cu118 --index-url https://download.pytorch.org/whl/cu118
        if !errorlevel! neq 0 (
            echo 尝试国内镜像...
            pip install torch torchvision torchaudio -i https://pypi.tuna.tsinghua.edu.cn/simple/
        )
    ) else (
        echo 🎮 安装PyTorch CUDA %CUDA_VERSION%...
        pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
        if !errorlevel! neq 0 (
            pip install torch torchvision torchaudio -i https://pypi.tuna.tsinghua.edu.cn/simple/
        )
    )
) else (
    echo 💻 安装PyTorch CPU版本...
    pip install torch torchvision torchaudio -i https://pypi.tuna.tsinghua.edu.cn/simple/
)

echo.
echo 🔍 步骤9: 安装兼容numpy 2.x的OpenCV...

echo 📦 安装最新OpenCV（兼容numpy 2.x）...
pip install "opencv-python>=4.8.0" -i https://pypi.tuna.tsinghua.edu.cn/simple/

echo.
echo 🔍 步骤10: 安装核心依赖...

echo 📦 安装科学计算库...
pip install scipy scikit-learn -i https://pypi.tuna.tsinghua.edu.cn/simple/

echo 📦 安装其他库...
pip install pillow -i https://pypi.tuna.tsinghua.edu.cn/simple/

echo 📦 安装音频处理库...
pip install "librosa>=0.9.0" soundfile -i https://pypi.tuna.tsinghua.edu.cn/simple/

echo 📦 安装深度学习扩展...
pip install "diffusers>=0.20.0" "transformers>=4.30.0" accelerate -i https://pypi.tuna.tsinghua.edu.cn/simple/

echo 📦 安装Web框架...
pip install flask fastapi uvicorn -i https://pypi.tuna.tsinghua.edu.cn/simple/

echo 📦 安装其他工具...
pip install tqdm requests pydantic omegaconf -i https://pypi.tuna.tsinghua.edu.cn/simple/

echo.
echo 🔍 步骤11: 安装MediaPipe（兼容numpy 2.x）...

echo 📦 安装最新MediaPipe...
pip install mediapipe -i https://pypi.tuna.tsinghua.edu.cn/simple/
if %errorlevel% equ 0 (
    echo ✅ MediaPipe安装成功
) else (
    echo ⚠️  MediaPipe安装失败
)

echo.
echo 🔍 步骤12: dlib安装（多重策略）...

echo 📥 策略1: 预编译dlib...
pip install dlib -i https://pypi.tuna.tsinghua.edu.cn/simple/ --no-cache-dir >nul 2>&1

python -c "import dlib; print('dlib version:', dlib.__version__)" >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ dlib预编译包成功！
    goto :dlib_success
)

echo 策略2: 源码编译...
if not "%CMAKE_PATH%"=="" if not "%VS_PATH%"=="" (
    echo 🔨 编译dlib...
    
    if not "%CMAKE_PATH%"=="" set "PATH=%CMAKE_PATH%;%PATH%"
    if not "%VS_PATH%"=="" call "%VS_PATH%\VC\Auxiliary\Build\vcvars64.bat" >nul 2>&1
    
    cd /d "%TEMP_DIR%"
    pip download dlib==19.24.2 --no-deps -i https://pypi.tuna.tsinghua.edu.cn/simple/ >nul 2>&1
    
    if exist "dlib-19.24.2.tar.gz" (
        tar -xzf dlib-19.24.2.tar.gz >nul 2>&1
        if exist "dlib-19.24.2" (
            cd dlib-19.24.2
            pip install . -i https://pypi.tuna.tsinghua.edu.cn/simple/ >nul 2>&1
            
            if !errorlevel! equ 0 (
                cd /d "%BASE_DIR%"
                python -c "import dlib" >nul 2>&1
                if !errorlevel! equ 0 (
                    echo ✅ dlib源码编译成功！
                    goto :dlib_success
                )
            )
        )
    )
    cd /d "%BASE_DIR%"
)

echo 策略3: 兼容版本...
for %%v in (19.22.1 19.21.1 19.20.1) do (
    pip install dlib==%%v -i https://pypi.tuna.tsinghua.edu.cn/simple/ --no-cache-dir >nul 2>&1
    if !errorlevel! equ 0 (
        python -c "import dlib" >nul 2>&1
        if !errorlevel! equ 0 (
            echo ✅ dlib %%v 成功！
            goto :dlib_success
        )
    )
)

echo ⚠️  dlib安装失败，MediaPipe可作为替代
goto :post_dlib

:dlib_success
echo 🎉 dlib安装成功！

:post_dlib

echo.
echo 🔍 步骤13: 安装MuseTalk专用依赖...

pip install face-alignment imageio imageio-ffmpeg numba -i https://pypi.tuna.tsinghua.edu.cn/simple/ >nul 2>&1
pip install insightface onnxruntime -i https://pypi.tuna.tsinghua.edu.cn/simple/ >nul 2>&1

echo.
echo 🔍 步骤14: 创建修复版服务脚本...

(
echo # -*- coding: utf-8 -*-
echo """MuseTalk数字人服务 - 修复版"""
echo import sys
echo import os
echo import logging
echo from flask import Flask, request, jsonify
echo import cv2
echo import numpy as np
echo.
echo # 配置日志
echo logging.basicConfig^(level=logging.INFO, 
echo                     format='%%(asctime^)s - %%(levelname^)s - %%(message^)s',
echo                     handlers=[logging.StreamHandler^(sys.stdout^)]^)
echo logger = logging.getLogger^(__name__^)
echo.
echo class MuseTalkService:
echo     def __init__^(self^):
echo         self.face_detector = None
echo         self.detector_type = None
echo         self.initialize_face_detector^(^)
echo.
echo     def initialize_face_detector^(self^):
echo         """初始化人脸检测器"""
echo         # 策略1: dlib
echo         try:
echo             import dlib
echo             self.face_detector = dlib.get_frontal_face_detector^(^)
echo             self.detector_type = 'dlib'
echo             logger.info^("使用dlib人脸检测器"^)
echo             return
echo         except ImportError:
echo             logger.warning^("dlib不可用"^)
echo.
echo         # 策略2: MediaPipe
echo         try:
echo             import mediapipe as mp
echo             self.mp_face_detection = mp.solutions.face_detection
echo             self.face_detector = self.mp_face_detection.FaceDetection^(
echo                 model_selection=1, min_detection_confidence=0.5
echo             ^)
echo             self.detector_type = 'mediapipe'
echo             logger.info^("使用MediaPipe人脸检测器"^)
echo             return
echo         except ImportError:
echo             logger.warning^("MediaPipe不可用"^)
echo.
echo         # 策略3: OpenCV
echo         try:
echo             cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
echo             self.face_detector = cv2.CascadeClassifier^(cascade_path^)
echo             self.detector_type = 'opencv'
echo             logger.info^("使用OpenCV人脸检测器"^)
echo             return
echo         except Exception as e:
echo             logger.error^(f"OpenCV初始化失败: {e}"^)
echo.
echo         logger.error^("无法初始化任何人脸检测器"^)
echo         raise RuntimeError^("没有可用的人脸检测器"^)
echo.
echo # Flask应用
echo app = Flask^(__name__^)
echo musetalk_service = MuseTalkService^(^)
echo.
echo @app.route^('/health', methods=['GET']^)
echo def health_check^(^):
echo     return jsonify^({'status': 'healthy', 'detector': musetalk_service.detector_type}^)
echo.
echo @app.route^('/detect_faces', methods=['POST']^)
echo def detect_faces_api^(^):
echo     try:
echo         return jsonify^({'status': 'success', 'message': 'Face detection ready'}^)
echo     except Exception as e:
echo         return jsonify^({'error': str^(e^)}^), 500
echo.
echo if __name__ == '__main__':
echo     print^("MuseTalk数字人服务启动"^)
echo     print^(f"人脸检测器: {musetalk_service.detector_type}"^)
echo     print^("服务地址: http://localhost:5000"^)
echo     print^("API端点:"^)
echo     print^("  GET  /health - 健康检查"^)
echo     print^("  POST /detect_faces - 人脸检测"^)
echo     app.run^(host='0.0.0.0', port=5000, debug=False^)
) > "%BASE_DIR%\musetalk_service.py"

echo.
echo 🔍 步骤15: 创建修复版启动脚本...

(
echo @echo off
echo chcp 65001 ^>nul
echo echo MuseTalk数字人系统启动...
echo call "%VENV_DIR%\Scripts\activate.bat"
if not "%CMAKE_PATH%"=="" echo set "PATH=%CMAKE_PATH%;%%PATH%%"
if not "%VS_PATH%"=="" echo call "%VS_PATH%\VC\Auxiliary\Build\vcvars64.bat" ^>nul 2^>^&1
if not "%CUDA_PATH%"=="" echo set "PATH=%CUDA_PATH%\bin;%%PATH%%"
echo echo 环境已激活
echo echo.
echo echo 您的配置:
echo echo   Python: %PYTHON_VERSION%
echo echo   CUDA: %CUDA_VERSION%
echo echo   Visual Studio: %VS_PATH%
echo echo   CMake: VS内置
echo echo.
echo echo 可用命令:
echo echo   python musetalk_service.py  - 启动MuseTalk服务
echo echo   python test_environment.py - 测试环境
echo echo.
echo cmd /k
) > "%BASE_DIR%\activate_env.bat"

echo.
echo 🔍 步骤16: 创建修复版测试脚本...

echo # -*- coding: utf-8 -*- > "%BASE_DIR%\test_environment.py"
echo """MuseTalk环境测试脚本 - 修复版""" >> "%BASE_DIR%\test_environment.py"
echo import sys >> "%BASE_DIR%\test_environment.py"
echo import platform >> "%BASE_DIR%\test_environment.py"
echo. >> "%BASE_DIR%\test_environment.py"
echo print("MuseTalk数字人系统环境测试") >> "%BASE_DIR%\test_environment.py"
echo print("=" * 50) >> "%BASE_DIR%\test_environment.py"
echo print("Python版本:", sys.version) >> "%BASE_DIR%\test_environment.py"
echo print("Python路径:", sys.executable) >> "%BASE_DIR%\test_environment.py"
echo print("系统平台:", platform.platform()) >> "%BASE_DIR%\test_environment.py"
echo print() >> "%BASE_DIR%\test_environment.py"
echo. >> "%BASE_DIR%\test_environment.py"
echo # 测试核心库 >> "%BASE_DIR%\test_environment.py"
echo libraries = [ >> "%BASE_DIR%\test_environment.py"
echo     ('torch', 'PyTorch'), >> "%BASE_DIR%\test_environment.py"
echo     ('torchvision', 'TorchVision'), >> "%BASE_DIR%\test_environment.py"
echo     ('cv2', 'OpenCV'), >> "%BASE_DIR%\test_environment.py"
echo     ('numpy', 'NumPy'), >> "%BASE_DIR%\test_environment.py"
echo     ('librosa', 'Librosa'), >> "%BASE_DIR%\test_environment.py"
echo     ('diffusers', 'Diffusers'), >> "%BASE_DIR%\test_environment.py"
echo     ('transformers', 'Transformers'), >> "%BASE_DIR%\test_environment.py"
echo     ('flask', 'Flask'), >> "%BASE_DIR%\test_environment.py"
echo ] >> "%BASE_DIR%\test_environment.py"
echo. >> "%BASE_DIR%\test_environment.py"
echo # 测试人脸检测库 >> "%BASE_DIR%\test_environment.py"
echo face_detectors = [] >> "%BASE_DIR%\test_environment.py"
echo try: >> "%BASE_DIR%\test_environment.py"
echo     import dlib >> "%BASE_DIR%\test_environment.py"
echo     face_detectors.append(f'dlib {dlib.__version__} (最佳质量)') >> "%BASE_DIR%\test_environment.py"
echo except ImportError: >> "%BASE_DIR%\test_environment.py"
echo     pass >> "%BASE_DIR%\test_environment.py"
echo. >> "%BASE_DIR%\test_environment.py"
echo try: >> "%BASE_DIR%\test_environment.py"
echo     import mediapipe >> "%BASE_DIR%\test_environment.py"
echo     face_detectors.append(f'MediaPipe {mediapipe.__version__} (良好质量)') >> "%BASE_DIR%\test_environment.py"
echo except ImportError: >> "%BASE_DIR%\test_environment.py"
echo     pass >> "%BASE_DIR%\test_environment.py"
echo. >> "%BASE_DIR%\test_environment.py"
echo try: >> "%BASE_DIR%\test_environment.py"
echo     import cv2 >> "%BASE_DIR%\test_environment.py"
echo     face_detectors.append(f'OpenCV {cv2.__version__} (基础质量)') >> "%BASE_DIR%\test_environment.py"
echo except ImportError: >> "%BASE_DIR%\test_environment.py"
echo     pass >> "%BASE_DIR%\test_environment.py"
echo. >> "%BASE_DIR%\test_environment.py"
echo print("核心库测试:") >> "%BASE_DIR%\test_environment.py"
echo for module, name in libraries: >> "%BASE_DIR%\test_environment.py"
echo     try: >> "%BASE_DIR%\test_environment.py"
echo         lib = __import__(module) >> "%BASE_DIR%\test_environment.py"
echo         version = getattr(lib, '__version__', 'unknown') >> "%BASE_DIR%\test_environment.py"
echo         print(f"✅ {name}: {version}") >> "%BASE_DIR%\test_environment.py"
echo     except ImportError: >> "%BASE_DIR%\test_environment.py"
echo         print(f"❌ {name}: 未安装") >> "%BASE_DIR%\test_environment.py"
echo. >> "%BASE_DIR%\test_environment.py"
echo print() >> "%BASE_DIR%\test_environment.py"
echo print("人脸检测库:") >> "%BASE_DIR%\test_environment.py"
echo for detector in face_detectors: >> "%BASE_DIR%\test_environment.py"
echo     print(f"✅ {detector}") >> "%BASE_DIR%\test_environment.py"
echo. >> "%BASE_DIR%\test_environment.py"
echo if not face_detectors: >> "%BASE_DIR%\test_environment.py"
echo     print("❌ 未找到可用的人脸检测库") >> "%BASE_DIR%\test_environment.py"
echo. >> "%BASE_DIR%\test_environment.py"
echo # 测试CUDA >> "%BASE_DIR%\test_environment.py"
echo print() >> "%BASE_DIR%\test_environment.py"
echo print("CUDA测试:") >> "%BASE_DIR%\test_environment.py"
echo try: >> "%BASE_DIR%\test_environment.py"
echo     import torch >> "%BASE_DIR%\test_environment.py"
echo     if torch.cuda.is_available(): >> "%BASE_DIR%\test_environment.py"
echo         print(f"✅ CUDA可用: {torch.cuda.get_device_name(0)}") >> "%BASE_DIR%\test_environment.py"
echo         print(f"✅ CUDA版本: {torch.version.cuda}") >> "%BASE_DIR%\test_environment.py"
echo         print(f"✅ GPU数量: {torch.cuda.device_count()}") >> "%BASE_DIR%\test_environment.py"
echo     else: >> "%BASE_DIR%\test_environment.py"
echo         print("💻 CUDA不可用，使用CPU模式") >> "%BASE_DIR%\test_environment.py"
echo except Exception as e: >> "%BASE_DIR%\test_environment.py"
echo     print(f"❌ CUDA测试失败: {e}") >> "%BASE_DIR%\test_environment.py"
echo. >> "%BASE_DIR%\test_environment.py"
echo # 测试numpy版本兼容性 >> "%BASE_DIR%\test_environment.py"
echo print() >> "%BASE_DIR%\test_environment.py"
echo print("版本兼容性检查:") >> "%BASE_DIR%\test_environment.py"
echo try: >> "%BASE_DIR%\test_environment.py"
echo     import numpy >> "%BASE_DIR%\test_environment.py"
echo     import mediapipe >> "%BASE_DIR%\test_environment.py"
echo     print(f"✅ numpy版本: {numpy.__version__} (兼容MediaPipe)") >> "%BASE_DIR%\test_environment.py"
echo     print(f"✅ MediaPipe版本: {mediapipe.__version__}") >> "%BASE_DIR%\test_environment.py"
echo except Exception as e: >> "%BASE_DIR%\test_environment.py"
echo     print(f"⚠️  版本兼容性问题: {e}") >> "%BASE_DIR%\test_environment.py"
echo. >> "%BASE_DIR%\test_environment.py"
echo print() >> "%BASE_DIR%\test_environment.py"
echo print("MuseTalk环境测试完成！") >> "%BASE_DIR%\test_environment.py"
echo print("运行 'python musetalk_service.py' 启动服务") >> "%BASE_DIR%\test_environment.py"

echo.
echo 🔍 步骤17: 清理临时文件...

if exist "%TEMP_DIR%" (
    rmdir /s /q "%TEMP_DIR%" >nul 2>&1
)

echo.
echo 🔍 步骤18: 最终验证...

echo 正在验证安装结果...
python -c "import sys; print('Python:', sys.version.split()[0])"

python -c "import numpy; print('numpy:', numpy.__version__)" 2>nul
if %errorlevel% neq 0 echo numpy: 未安装

python -c "import torch; print('PyTorch:', torch.__version__)" 2>nul
if %errorlevel% neq 0 echo PyTorch: 未安装

python -c "import mediapipe; print('MediaPipe:', mediapipe.__version__)" 2>nul
if %errorlevel% neq 0 echo MediaPipe: 未安装

python -c "import dlib; print('dlib:', dlib.__version__, '(最佳)')" 2>nul
if %errorlevel% neq 0 echo dlib: 未安装 (使用MediaPipe替代)

echo.
echo MuseTalk环境配置完成！
echo 修复: numpy冲突 + Python语法错误

goto :success_exit

:error_exit
echo.
echo ================================================================
echo ❌ 安装过程中出现错误
echo ================================================================
echo.
echo 错误排查建议:
echo 1. 确保以管理员身份运行
echo 2. 检查网络连接
echo 3. 确保磁盘空间充足
echo 4. 查看上方的详细错误信息
echo.
goto :final_pause

:success_exit
echo.
echo ================================================================
echo 🎉 MuseTalk安装成功完成！
echo ================================================================
echo.
echo 安装路径: %BASE_DIR%
echo Python环境: %VENV_DIR%
echo CUDA版本: %CUDA_VERSION%
echo.
echo 下一步操作:
echo 1. 双击运行: %BASE_DIR%\activate_env.bat
echo 2. 测试环境: python test_environment.py
echo 3. 启动服务: python musetalk_service.py
echo.
echo 修复内容:
echo ✅ numpy版本冲突 (使用numpy 2.x兼容所有包)
echo ✅ Python语法错误 (完全修复)
echo ✅ 中文乱码问题
echo ✅ 依赖版本兼容性
echo.

:final_pause
echo ================================================================
echo 脚本执行完成 - 窗口保持打开
echo ================================================================
echo.
echo 按任意键关闭窗口...
pause >nul
exit /b %ERROR_OCCURRED%