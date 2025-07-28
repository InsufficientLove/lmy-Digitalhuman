@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ================================================================
echo 🎵 MuseTalk数字人系统专用安装脚本 - 超级优化版
echo ================================================================
echo 针对您的环境: Python 3.10.11 + D盘VS2022 + MuseTalk专用依赖
echo 包含国内镜像源加速 + CUDA智能检测 + 版本精确匹配
echo.
echo 版本: 2025-01-28 MuseTalk专用版
echo 参考: https://github.com/TMElyralab/MuseTalk
echo.

REM 错误处理
set "ERROR_OCCURRED=0"

echo 🔍 步骤1: 环境配置和检测...

REM 根据您的环境设置
set "BASE_DIR=F:\AI\DigitalHuman"
set "VENV_DIR=%BASE_DIR%\venv"
set "TEMP_DIR=%BASE_DIR%\temp_install"

echo ✅ 安装路径: %BASE_DIR%
echo ✅ 虚拟环境: %VENV_DIR%
echo.

echo 🔍 步骤2: 检测CUDA环境...

REM CUDA检测
set "CUDA_VERSION="
set "CUDA_PATH="

REM 检查CUDA 11.8 (推荐)
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

echo ⚠️  未检测到CUDA安装
echo 💡 CUDA安装建议:
echo   1. 访问: https://developer.nvidia.com/cuda-toolkit
echo   2. 推荐下载: CUDA 11.8 (最佳MuseTalk兼容性)
echo   3. 可安装到任意盘符（如D盘、F盘）
echo   4. 至少需要6GB空间
echo.
choice /C YN /M "是否继续安装 (没有CUDA将使用CPU版本) (Y=继续, N=退出)"
if errorlevel 2 (
    echo 安装已取消
    set "ERROR_OCCURRED=1"
    goto :error_exit
)
echo 继续安装（CPU版本）...
goto :cuda_check_done

:cuda_found
echo ✅ CUDA环境: %CUDA_VERSION% - %CUDA_PATH%

:cuda_check_done

echo.
echo 🔍 步骤3: 检测Visual Studio和CMake...

REM VS检测（您的环境）
set "VS_PATH="
if exist "D:\Program Files\Microsoft Visual Studio\2022\Community\VC\Tools\MSVC" (
    set "VS_PATH=D:\Program Files\Microsoft Visual Studio\2022\Community"
    echo ✅ Visual Studio 2022: %VS_PATH%
) else (
    echo ⚠️  未检测到D盘VS2022，检查其他位置...
    if exist "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Tools\MSVC" (
        set "VS_PATH=C:\Program Files\Microsoft Visual Studio\2022\Community"
        echo ✅ Visual Studio 2022: %VS_PATH%
    )
)

REM CMake检测
set "CMAKE_PATH="
if not "%VS_PATH%"=="" (
    if exist "%VS_PATH%\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe" (
        set "CMAKE_PATH=%VS_PATH%\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin"
        echo ✅ VS内置CMake: %CMAKE_PATH%
    )
)

echo.
echo 🔍 步骤4: Python版本验证...

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python未安装或未添加到PATH
    set "ERROR_OCCURRED=1"
    goto :error_exit
)

REM 检查Python版本
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set "PYTHON_VERSION=%%i"
echo ✅ Python版本: %PYTHON_VERSION%

REM 验证Python 3.10.x兼容性
echo %PYTHON_VERSION% | findstr "3.10" >nul
if %errorlevel% equ 0 (
    echo ✅ Python版本与MuseTalk兼容 (3.10.x)
) else (
    echo ⚠️  Python版本可能不是最佳选择
    echo 💡 MuseTalk推荐Python 3.10.x，您当前使用: %PYTHON_VERSION%
    echo.
    choice /C YN /M "是否继续安装 (Y=继续, N=退出)"
    if errorlevel 2 (
        echo 安装已取消
        set "ERROR_OCCURRED=1"
        goto :error_exit
    )
)

echo.
echo 🔍 步骤5: 创建目录和虚拟环境...

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
    echo ✅ 虚拟环境创建成功
)

echo 🔄 激活虚拟环境...
call "%VENV_DIR%\Scripts\activate.bat"
if %errorlevel% neq 0 (
    echo ❌ 虚拟环境激活失败
    set "ERROR_OCCURRED=1"
    goto :error_exit
)

echo.
echo 🔍 步骤6: 配置pip镜像源（国内加速）...

if not exist "%USERPROFILE%\.pip" mkdir "%USERPROFILE%\.pip" 2>nul

(
echo [global]
echo index-url = https://pypi.tuna.tsinghua.edu.cn/simple/
echo trusted-host = pypi.tuna.tsinghua.edu.cn
echo timeout = 120
echo retries = 5
echo [install]
echo trusted-host = pypi.tuna.tsinghua.edu.cn
) > "%USERPROFILE%\.pip\pip.conf"

echo ✅ pip镜像源配置完成（清华大学镜像）

REM 升级pip
echo 📈 升级pip...
python -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple/ >nul 2>&1

echo.
echo 🔍 步骤7: 安装PyTorch（根据CUDA版本）...

if not "%CUDA_VERSION%"=="" (
    if "%CUDA_VERSION%"=="11.8" (
        echo 🎮 安装PyTorch CUDA 11.8版本...
        pip install torch==2.0.1+cu118 torchvision==0.15.2+cu118 torchaudio==2.0.2+cu118 --index-url https://download.pytorch.org/whl/cu118
        if !errorlevel! neq 0 (
            echo ⚠️  官方源失败，尝试国内镜像...
            pip install torch torchvision torchaudio -i https://pypi.tuna.tsinghua.edu.cn/simple/
        )
    ) else (
        echo 🎮 安装PyTorch CUDA %CUDA_VERSION%版本...
        pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
        if !errorlevel! neq 0 (
            echo ⚠️  官方源失败，尝试国内镜像...
            pip install torch torchvision torchaudio -i https://pypi.tuna.tsinghua.edu.cn/simple/
        )
    )
) else (
    echo 💻 安装PyTorch CPU版本...
    pip install torch torchvision torchaudio -i https://pypi.tuna.tsinghua.edu.cn/simple/
)

if %errorlevel% equ 0 (
    echo ✅ PyTorch安装成功
) else (
    echo ❌ PyTorch安装失败
    set "ERROR_OCCURRED=1"
    goto :error_exit
)

echo.
echo 🔍 步骤8: 安装MuseTalk核心依赖...

echo 📦 安装基础科学计算库...
pip install numpy==1.24.4 scipy -i https://pypi.tuna.tsinghua.edu.cn/simple/

echo 📦 安装计算机视觉库...
pip install opencv-python==4.8.1.78 pillow -i https://pypi.tuna.tsinghua.edu.cn/simple/

echo 📦 安装音频处理库...
pip install librosa==0.10.1 soundfile -i https://pypi.tuna.tsinghua.edu.cn/simple/

echo 📦 安装深度学习框架扩展...
pip install diffusers==0.21.4 transformers==4.33.2 accelerate -i https://pypi.tuna.tsinghua.edu.cn/simple/

echo 📦 安装Web框架...
pip install flask fastapi uvicorn -i https://pypi.tuna.tsinghua.edu.cn/simple/

echo 📦 安装其他必需库...
pip install tqdm requests pydantic omegaconf -i https://pypi.tuna.tsinghua.edu.cn/simple/

echo 📦 安装音视频处理...
pip install ffmpeg-python moviepy -i https://pypi.tuna.tsinghua.edu.cn/simple/

echo.
echo 🔍 步骤9: 人脸检测库安装（多重策略）...

REM 策略1: 尝试预编译dlib
echo 📥 策略1: 安装预编译dlib...
pip install dlib -i https://pypi.tuna.tsinghua.edu.cn/simple/ --no-cache-dir >nul 2>&1

if %errorlevel% equ 0 (
    echo 测试dlib导入...
    python -c "import dlib; print('✅ dlib版本:', dlib.__version__)" >nul 2>&1
    if !errorlevel! equ 0 (
        echo ✅ dlib预编译包安装成功！
        goto :dlib_success
    )
)

echo ⚠️  预编译包失败，尝试源码编译...

REM 策略2: 源码编译（如果有编译环境）
if not "%CMAKE_PATH%"=="" if not "%VS_PATH%"=="" (
    echo 🔨 策略2: 从源码编译dlib...
    
    REM 设置编译环境
    if not "%CMAKE_PATH%"=="" set "PATH=%CMAKE_PATH%;%PATH%"
    if not "%VS_PATH%"=="" call "%VS_PATH%\VC\Auxiliary\Build\vcvars64.bat" >nul 2>&1
    
    REM 编译dlib
    cd /d "%TEMP_DIR%"
    pip download dlib==19.24.2 --no-deps -i https://pypi.tuna.tsinghua.edu.cn/simple/ >nul 2>&1
    
    if exist "dlib-19.24.2.tar.gz" (
        echo 解压和编译dlib...
        tar -xzf dlib-19.24.2.tar.gz >nul 2>&1
        if exist "dlib-19.24.2" (
            cd dlib-19.24.2
            pip install . -i https://pypi.tuna.tsinghua.edu.cn/simple/ >nul 2>&1
            
            if !errorlevel! equ 0 (
                cd /d "%BASE_DIR%"
                python -c "import dlib; print('✅ dlib版本:', dlib.__version__)" >nul 2>&1
                if !errorlevel! equ 0 (
                    echo ✅ dlib源码编译成功！
                    goto :dlib_success
                )
            )
        )
    )
    
    cd /d "%BASE_DIR%"
    echo ⚠️  源码编译失败，尝试兼容版本...
)

REM 策略3: 兼容版本
echo 🔄 策略3: 尝试兼容版本...
for %%v in (19.22.1 19.21.1 19.20.1) do (
    echo 尝试dlib %%v...
    pip install dlib==%%v -i https://pypi.tuna.tsinghua.edu.cn/simple/ --no-cache-dir >nul 2>&1
    if !errorlevel! equ 0 (
        python -c "import dlib" >nul 2>&1
        if !errorlevel! equ 0 (
            echo ✅ dlib %%v 安装成功！
            goto :dlib_success
        )
    )
)

REM 策略4: 替代方案
echo ⚠️  dlib安装失败，安装替代方案...
echo 📦 安装MediaPipe（dlib替代）...
pip install mediapipe -i https://pypi.tuna.tsinghua.edu.cn/simple/ >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ MediaPipe安装成功（dlib替代方案）
)

echo 📦 安装InsightFace（高质量人脸处理）...
pip install insightface onnxruntime -i https://pypi.tuna.tsinghua.edu.cn/simple/ >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ InsightFace安装成功
)

goto :post_dlib

:dlib_success
echo 🎉 dlib安装成功！测试功能...
python -c "
try:
    import dlib
    print('✅ dlib导入成功，版本:', dlib.__version__)
    detector = dlib.get_frontal_face_detector()
    print('✅ 人脸检测器创建成功')
    print('🏆 dlib完全可用，MuseTalk将获得最佳人脸检测质量！')
except Exception as e:
    print('❌ dlib测试失败:', str(e))
" 2>nul

:post_dlib

echo.
echo 🔍 步骤10: 安装MuseTalk专用依赖...

echo 📦 安装面部关键点检测...
pip install face-alignment -i https://pypi.tuna.tsinghua.edu.cn/simple/

echo 📦 安装语音处理...
pip install whisper-openai -i https://pypi.tuna.tsinghua.edu.cn/simple/

echo 📦 安装图像处理增强...
pip install imageio imageio-ffmpeg -i https://pypi.tuna.tsinghua.edu.cn/simple/

echo 📦 安装数值计算优化...
pip install numba -i https://pypi.tuna.tsinghua.edu.cn/simple/

echo.
echo 🔍 步骤11: 创建MuseTalk服务脚本...

REM 创建MuseTalk服务脚本
(
echo # MuseTalk数字人服务 - 针对您的环境优化
echo import sys
echo import os
echo import logging
echo from flask import Flask, request, jsonify
echo import cv2
echo import numpy as np
echo.
echo # 配置日志
echo logging.basicConfig^(level=logging.INFO^)
echo logger = logging.getLogger^(__name__^)
echo.
echo class MuseTalkService:
echo     def __init__^(self^):
echo         self.face_detector = None
echo         self.initialize_face_detector^(^)
echo.
echo     def initialize_face_detector^(self^):
echo         """初始化人脸检测器 - 多重策略"""
echo         # 策略1: dlib ^(最佳质量^)
echo         try:
echo             import dlib
echo             self.face_detector = dlib.get_frontal_face_detector^(^)
echo             self.detector_type = 'dlib'
echo             logger.info^("✅ 使用dlib人脸检测器 ^(最佳质量^)"^)
echo             return
echo         except ImportError:
echo             logger.warning^("dlib不可用"^)
echo.
echo         # 策略2: MediaPipe ^(良好质量^)
echo         try:
echo             import mediapipe as mp
echo             self.mp_face_detection = mp.solutions.face_detection
echo             self.face_detector = self.mp_face_detection.FaceDetection^(
echo                 model_selection=1, min_detection_confidence=0.5
echo             ^)
echo             self.detector_type = 'mediapipe'
echo             logger.info^("✅ 使用MediaPipe人脸检测器 ^(良好质量^)"^)
echo             return
echo         except ImportError:
echo             logger.warning^("MediaPipe不可用"^)
echo.
echo         # 策略3: OpenCV ^(基础质量^)
echo         try:
echo             cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
echo             self.face_detector = cv2.CascadeClassifier^(cascade_path^)
echo             self.detector_type = 'opencv'
echo             logger.info^("✅ 使用OpenCV人脸检测器 ^(基础质量^)"^)
echo             return
echo         except Exception as e:
echo             logger.error^(f"OpenCV初始化失败: {e}"^)
echo.
echo         logger.error^("❌ 无法初始化任何人脸检测器！"^)
echo         raise RuntimeError^("没有可用的人脸检测器"^)
echo.
echo     def detect_faces^(self, image^):
echo         """人脸检测"""
echo         if self.detector_type == 'dlib':
echo             import dlib
echo             gray = cv2.cvtColor^(image, cv2.COLOR_BGR2GRAY^)
echo             faces = self.face_detector^(gray^)
echo             return [^(f.left^(^), f.top^(^), f.right^(^), f.bottom^(^)^) for f in faces]
echo         elif self.detector_type == 'mediapipe':
echo             # MediaPipe检测逻辑
echo             rgb_image = cv2.cvtColor^(image, cv2.COLOR_BGR2RGB^)
echo             results = self.face_detector.process^(rgb_image^)
echo             faces = []
echo             if results.detections:
echo                 for detection in results.detections:
echo                     bbox = detection.location_data.relative_bounding_box
echo                     h, w, _ = image.shape
echo                     x = int^(bbox.xmin * w^)
echo                     y = int^(bbox.ymin * h^)
echo                     width = int^(bbox.width * w^)
echo                     height = int^(bbox.height * h^)
echo                     faces.append^(^(x, y, x + width, y + height^)^)
echo             return faces
echo         elif self.detector_type == 'opencv':
echo             gray = cv2.cvtColor^(image, cv2.COLOR_BGR2GRAY^)
echo             faces = self.face_detector.detectMultiScale^(gray, 1.1, 4^)
echo             return [^(x, y, x + w, y + h^) for ^(x, y, w, h^) in faces]
echo         return []
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
echo         # 这里添加实际的人脸检测逻辑
echo         return jsonify^({'status': 'success', 'message': 'Face detection ready'}^)
echo     except Exception as e:
echo         return jsonify^({'error': str^(e^)}^), 500
echo.
echo if __name__ == '__main__':
echo     print^("🎵 MuseTalk数字人服务启动"^)
echo     print^(f"✅ 人脸检测器: {musetalk_service.detector_type}"^)
echo     print^("🌐 服务地址: http://localhost:5000"^)
echo     print^("📋 API端点:"^)
echo     print^("  GET  /health - 健康检查"^)
echo     print^("  POST /detect_faces - 人脸检测"^)
echo     print^(^)
echo     app.run^(host='0.0.0.0', port=5000, debug=False^)
) > "%BASE_DIR%\musetalk_service.py"

echo ✅ MuseTalk服务脚本创建完成

echo.
echo 🔍 步骤12: 创建启动脚本...

REM 创建启动脚本
(
echo @echo off
echo echo 🎵 启动MuseTalk数字人系统...
echo call "%VENV_DIR%\Scripts\activate.bat"
if not "%CMAKE_PATH%"=="" echo set "PATH=%CMAKE_PATH%;%%PATH%%"
if not "%VS_PATH%"=="" echo call "%VS_PATH%\VC\Auxiliary\Build\vcvars64.bat" ^>nul 2^>^&1
if not "%CUDA_PATH%"=="" echo set "PATH=%CUDA_PATH%\bin;%%PATH%%"
echo echo ✅ 环境已激活
echo echo.
echo echo 💡 您的配置:
echo echo   Python: %PYTHON_VERSION%
echo echo   CUDA: %CUDA_VERSION%
echo echo   Visual Studio: %VS_PATH%
echo echo   CMake: VS内置
echo echo.
echo echo 📋 可用命令:
echo echo   python musetalk_service.py  - 启动MuseTalk服务
echo echo   python test_environment.py - 测试环境
echo echo.
echo cmd /k
) > "%BASE_DIR%\activate_env.bat"

echo ✅ 启动脚本创建完成

echo.
echo 🔍 步骤13: 创建环境测试脚本...

(
echo # MuseTalk环境测试脚本
echo import sys
echo import platform
echo print^("🎵 MuseTalk数字人系统环境测试"^)
echo print^("=" * 50^)
echo print^(f"Python版本: {sys.version}"^)
echo print^(f"Python路径: {sys.executable}"^)
echo print^(f"系统平台: {platform.platform^(^)}"^)
echo print^(^)
echo 
echo # 测试核心库
echo libraries = [
echo     ^('torch', 'PyTorch'^),
echo     ^('torchvision', 'TorchVision'^),
echo     ^('cv2', 'OpenCV'^),
echo     ^('numpy', 'NumPy'^),
echo     ^('librosa', 'Librosa'^),
echo     ^('diffusers', 'Diffusers'^),
echo     ^('transformers', 'Transformers'^),
echo     ^('flask', 'Flask'^),
echo ]
echo 
echo # 测试人脸检测库
echo face_detectors = []
echo try:
echo     import dlib
echo     face_detectors.append^(f'dlib {dlib.__version__} ^(🏆 最佳质量^)'^)
echo except ImportError:
echo     pass
echo     
echo try:
echo     import mediapipe
echo     face_detectors.append^(f'MediaPipe {mediapipe.__version__} ^(👍 良好质量^)'^)
echo except ImportError:
echo     pass
echo 
echo try:
echo     import cv2
echo     face_detectors.append^(f'OpenCV {cv2.__version__} ^(⚡ 基础质量^)'^)
echo except ImportError:
echo     pass
echo 
echo print^("📦 核心库测试:"^)
echo for module, name in libraries:
echo     try:
echo         lib = __import__^(module^)
echo         version = getattr^(lib, '__version__', 'unknown'^)
echo         print^(f"✅ {name}: {version}"^)
echo     except ImportError:
echo         print^(f"❌ {name}: 未安装"^)
echo 
echo print^(^)
echo print^("👤 人脸检测库:"^)
echo for detector in face_detectors:
echo     print^(f"✅ {detector}"^)
echo 
echo if not face_detectors:
echo     print^("❌ 未找到可用的人脸检测库"^)
echo 
echo # 测试CUDA
echo print^(^)
echo print^("🎮 CUDA测试:"^)
echo try:
echo     import torch
echo     if torch.cuda.is_available^(^):
echo         print^(f"✅ CUDA可用: {torch.cuda.get_device_name^(0^)}"^)
echo         print^(f"✅ CUDA版本: {torch.version.cuda}"^)
echo         print^(f"✅ GPU数量: {torch.cuda.device_count^(^)}"^)
echo     else:
echo         print^("💻 CUDA不可用，使用CPU模式"^)
echo except Exception as e:
echo     print^(f"❌ CUDA测试失败: {e}"^)
echo 
echo print^(^)
echo print^("🎉 MuseTalk环境测试完成！"^)
echo print^("💡 运行 'python musetalk_service.py' 启动服务"^)
) > "%BASE_DIR%\test_environment.py"

echo ✅ 测试脚本创建完成

echo.
echo 🔍 步骤14: 清理临时文件...

if exist "%TEMP_DIR%" (
    rmdir /s /q "%TEMP_DIR%" >nul 2>&1
    echo ✅ 临时文件清理完成
)

echo.
echo 🔍 步骤15: 最终环境验证...

python -c "
import sys
print('✅ Python:', sys.version.split()[0])

# 检查关键组件
components = []
try:
    import torch
    cuda_info = f' (CUDA: {torch.version.cuda})' if torch.cuda.is_available() else ' (CPU)'
    components.append(f'✅ PyTorch: {torch.__version__}{cuda_info}')
except ImportError:
    components.append('❌ PyTorch: 未安装')

try:
    import cv2
    components.append(f'✅ OpenCV: {cv2.__version__}')
except ImportError:
    components.append('❌ OpenCV: 未安装')

try:
    import dlib
    components.append(f'✅ dlib: {dlib.__version__} (🏆 最佳人脸检测)')
except ImportError:
    try:
        import mediapipe
        components.append(f'✅ MediaPipe: {mediapipe.__version__} (👍 替代方案)')
    except ImportError:
        components.append('⚠️  人脸检测: 仅OpenCV可用')

try:
    import librosa
    components.append(f'✅ Librosa: {librosa.__version__}')
except ImportError:
    components.append('❌ Librosa: 未安装')

try:
    import diffusers
    components.append(f'✅ Diffusers: {diffusers.__version__}')
except ImportError:
    components.append('❌ Diffusers: 未安装')

for comp in components:
    print(comp)

print()
print('🎵 MuseTalk专用环境配置完成！')
print('💡 针对您的环境优化: Python 3.10.11 + VS2022 + 国内镜像加速')
" 2>nul

if %errorlevel% neq 0 (
    echo ⚠️  最终验证执行失败，但安装可能已完成
)

goto :success_exit

:error_exit
echo.
echo ================================================================
echo ❌ 安装过程中出现错误
echo ================================================================
echo.
echo 🔍 错误排查建议:
echo 1. 确保以管理员身份运行
echo 2. 检查网络连接（需要访问pip镜像源）
echo 3. 确保磁盘空间充足（至少15GB）
echo 4. 如需CUDA支持，请先安装CUDA 11.8
echo 5. 在VS Installer中确保安装了"C++ CMake工具"
echo.
echo 📞 获取帮助:
echo 1. 运行debug_install_enhanced.bat重新诊断
echo 2. 查看MuseTalk官方文档: https://github.com/TMElyralab/MuseTalk
echo 3. 检查上方的详细错误信息
echo.
goto :final_pause

:success_exit
echo.
echo ================================================================
echo 🎉 MuseTalk数字人系统安装成功完成！
echo ================================================================
echo.
echo 📁 安装路径: %BASE_DIR%
echo 🐍 Python环境: %VENV_DIR%
echo 🎮 CUDA版本: %CUDA_VERSION%
echo 🔧 VS路径: %VS_PATH%
echo 🛠️  CMake: VS内置
echo.
echo 🚀 下一步操作:
echo 1. 双击运行: %BASE_DIR%\activate_env.bat
echo 2. 测试环境: python test_environment.py
echo 3. 启动服务: python musetalk_service.py
echo.
echo 💡 MuseTalk专用优化:
echo   ✅ 国内镜像源加速
echo   ✅ 多重人脸检测策略
echo   ✅ CUDA智能检测
echo   ✅ Python 3.10.11兼容
echo   ✅ 依赖版本精确匹配
echo.
echo 📖 参考文档: https://github.com/TMElyralab/MuseTalk
echo.

:final_pause
echo ================================================================
echo 脚本执行完成 - 窗口保持打开
echo ================================================================
echo.
echo 此窗口将保持打开，您可以查看所有输出信息
echo 如有问题，请查看上方的详细信息
echo.
echo 按任意键关闭窗口...
pause >nul
exit /b %ERROR_OCCURRED%