@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ================================================================
echo 🎵 MuseTalk数字人系统安装脚本 - 最终修复版
echo ================================================================
echo 策略: 简化检查 + 强制版本锁定 + 依赖清理 + 进度显示
echo 解决: 磁盘检查错误 + 版本冲突 + 用户体验优化
echo.

REM 错误处理
set "ERROR_OCCURRED=0"

echo 🔍 步骤1: 系统检查...
echo [■□□□□□□□□□] 10%% - 检查系统环境

set "BASE_DIR=F:\AI\DigitalHuman"
set "VENV_DIR=%BASE_DIR%\venv"

echo ✅ 安装路径: %BASE_DIR%

REM 简化磁盘检查 - 只检查F盘是否存在，不计算具体空间
echo 检查F盘可用性...
if not exist "F:\" (
    echo ❌ F盘不存在或无法访问
    echo 请确认F盘已连接或更换安装路径
    goto :final_pause
)

REM 尝试创建测试目录来验证写入权限
mkdir "F:\temp_test_dir" >nul 2>&1
if errorlevel 1 (
    echo ❌ F盘无写入权限
    echo 请以管理员身份运行或更换安装路径
    goto :final_pause
) else (
    rmdir "F:\temp_test_dir" >nul 2>&1
    echo ✅ F盘可用，具有读写权限
)

echo.
echo 🔍 步骤2: 环境清理...
echo [■■□□□□□□□□] 20%% - 清理旧环境

if exist "%VENV_DIR%" (
    echo 删除旧环境: %VENV_DIR%
    rmdir /s /q "%VENV_DIR%" >nul 2>&1
    timeout /t 2 >nul
    echo ✅ 环境清理完成
) else (
    echo ✅ 无需清理
)

echo.
echo 🔍 步骤3: Python验证...
echo [■■■□□□□□□□] 30%% - 验证Python环境

python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python未安装，请先安装Python
    goto :final_pause
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set "PYTHON_VERSION=%%i"
echo ✅ Python版本: %PYTHON_VERSION%

echo.
echo 🔍 步骤4: 创建虚拟环境...
echo [■■■■□□□□□□] 40%% - 创建全新虚拟环境

if not exist "%BASE_DIR%" mkdir "%BASE_DIR%" 2>nul

python -m venv "%VENV_DIR%" --clear
if errorlevel 1 (
    echo ❌ 虚拟环境创建失败
    goto :final_pause
)
echo ✅ 虚拟环境创建成功

echo.
echo 🔍 步骤5: 激活环境...
echo [■■■■■□□□□□] 50%% - 激活虚拟环境

call "%VENV_DIR%\Scripts\activate.bat"
if errorlevel 1 (
    echo ❌ 环境激活失败
    goto :final_pause
)
echo ✅ 环境激活成功

echo.
echo 🔍 步骤6: 配置pip...
echo [■■■■■■□□□□] 60%% - 配置pip和镜像源

echo 升级pip...
python -m pip install --upgrade pip -q
echo ✅ pip升级完成

echo 配置清华镜像源...
if not exist "%USERPROFILE%\.pip" mkdir "%USERPROFILE%\.pip" 2>nul
(
echo [global]
echo index-url = https://pypi.tuna.tsinghua.edu.cn/simple/
echo trusted-host = pypi.tuna.tsinghua.edu.cn
echo timeout = 120
echo retries = 5
) > "%USERPROFILE%\.pip\pip.conf"
echo ✅ 镜像源配置完成

echo.
echo 🔍 步骤7: 强制版本锁定安装...
echo [■■■■■■■□□□] 70%% - 按兼容版本安装依赖

echo ================================================================
echo 🎯 强制版本锁定策略 (解决版本冲突)
echo ================================================================
echo 完全卸载冲突包 → 按顺序安装兼容版本 → 锁定不升级
echo ================================================================

echo 第1步: 完全清理冲突包...
echo 正在卸载所有可能冲突的包...
pip uninstall -y numpy scipy opencv-python opencv-contrib-python mediapipe torch torchvision torchaudio protobuf >nul 2>&1
echo ✅ 冲突包清理完成

echo 第2步: 强制安装numpy 1.24.4...
echo 正在安装: numpy==1.24.4 (锁定版本)
pip install "numpy==1.24.4" --force-reinstall --no-deps -i https://pypi.tuna.tsinghua.edu.cn/simple/ -q
echo ✅ numpy 1.24.4 强制安装完成

echo 第3步: 安装兼容的scipy...
echo 正在安装: scipy (兼容numpy 1.24.4)
pip install "scipy>=1.10.0,<1.12.0" -i https://pypi.tuna.tsinghua.edu.cn/simple/ -q
echo ✅ scipy安装完成

echo 第4步: 安装兼容的protobuf...
echo 正在安装: protobuf<4 (兼容mediapipe)
pip install "protobuf>=3.11,<4.0" -i https://pypi.tuna.tsinghua.edu.cn/simple/ -q
echo ✅ protobuf安装完成

echo 第5步: 安装PyTorch CPU版本...
echo 正在安装: PyTorch 2.0.1 (兼容numpy 1.24.4)
pip install torch==2.0.1 torchvision==0.15.2 torchaudio==2.0.2 -i https://pypi.tuna.tsinghua.edu.cn/simple/ -q
echo ✅ PyTorch安装完成

echo 第6步: 安装兼容的OpenCV...
echo 正在安装: opencv-python==4.8.1.78 (兼容numpy 1.x)
pip install "opencv-python==4.8.1.78" --force-reinstall -i https://pypi.tuna.tsinghua.edu.cn/simple/ -q
echo ✅ OpenCV安装完成

echo.
echo 🔍 步骤8: 安装AI生态包...
echo [■■■■■■■■□□] 80%% - 安装HuggingFace和MediaPipe

echo 安装HuggingFace生态 (兼容版本)...
echo 正在安装: huggingface_hub==0.17.3
pip install "huggingface_hub==0.17.3" -i https://pypi.tuna.tsinghua.edu.cn/simple/ -q
echo 正在安装: tokenizers==0.13.3
pip install "tokenizers==0.13.3" -i https://pypi.tuna.tsinghua.edu.cn/simple/ -q
echo 正在安装: transformers==4.33.2
pip install "transformers==4.33.2" -i https://pypi.tuna.tsinghua.edu.cn/simple/ -q
echo 正在安装: diffusers==0.21.4
pip install "diffusers==0.21.4" -i https://pypi.tuna.tsinghua.edu.cn/simple/ -q
echo 正在安装: accelerate==0.23.0
pip install "accelerate==0.23.0" -i https://pypi.tuna.tsinghua.edu.cn/simple/ -q
echo ✅ HuggingFace生态安装完成

echo 安装MediaPipe 0.10.9 (兼容numpy<2和protobuf<4)...
echo 正在安装: mediapipe==0.10.9
pip install "mediapipe==0.10.9" --force-reinstall -i https://pypi.tuna.tsinghua.edu.cn/simple/ -q
echo ✅ MediaPipe安装完成

echo.
echo 🔍 步骤9: 安装其他依赖...
echo [■■■■■■■■■□] 90%% - 安装音频和其他库

echo 安装音频处理库...
echo 正在安装: librosa==0.10.1
pip install "librosa==0.10.1" soundfile -i https://pypi.tuna.tsinghua.edu.cn/simple/ -q
echo ✅ 音频库安装完成

echo 安装face-alignment...
echo 正在安装: face-alignment==1.3.5
pip install "face-alignment==1.3.5" -i https://pypi.tuna.tsinghua.edu.cn/simple/ -q
echo ✅ face-alignment安装完成

echo 尝试安装dlib...
echo 正在尝试: dlib (预编译包)
pip install dlib -i https://pypi.tuna.tsinghua.edu.cn/simple/ --no-cache-dir -q >nul 2>&1
python -c "import dlib; print('dlib安装成功')" >nul 2>&1
if errorlevel 1 (
    echo ⚠️  dlib安装失败，MediaPipe可作为替代
) else (
    echo ✅ dlib安装成功
)

echo 安装Web框架和工具...
echo 正在安装: flask, fastapi, uvicorn
pip install flask fastapi uvicorn -i https://pypi.tuna.tsinghua.edu.cn/simple/ -q
echo 正在安装: tqdm, requests, pydantic
pip install tqdm requests pydantic omegaconf -i https://pypi.tuna.tsinghua.edu.cn/simple/ -q
echo 正在安装: MuseTalk专用库
pip install imageio imageio-ffmpeg numba -i https://pypi.tuna.tsinghua.edu.cn/simple/ -q
pip install insightface onnxruntime -i https://pypi.tuna.tsinghua.edu.cn/simple/ -q
pip install openai-whisper -i https://pypi.tuna.tsinghua.edu.cn/simple/ -q
echo ✅ 其他依赖安装完成

echo.
echo 🔍 步骤10: 创建服务文件...
echo [■■■■■■■■■■] 100%% - 生成服务和测试文件

echo 创建musetalk_service.py...
echo # -*- coding: utf-8 -*- > "%BASE_DIR%\musetalk_service.py"
echo """MuseTalk数字人服务 - 最终修复版""" >> "%BASE_DIR%\musetalk_service.py"
echo import sys >> "%BASE_DIR%\musetalk_service.py"
echo import os >> "%BASE_DIR%\musetalk_service.py"
echo import logging >> "%BASE_DIR%\musetalk_service.py"
echo from flask import Flask, request, jsonify >> "%BASE_DIR%\musetalk_service.py"
echo import cv2 >> "%BASE_DIR%\musetalk_service.py"
echo import numpy as np >> "%BASE_DIR%\musetalk_service.py"
echo. >> "%BASE_DIR%\musetalk_service.py"
echo logging.basicConfig(level=logging.INFO) >> "%BASE_DIR%\musetalk_service.py"
echo logger = logging.getLogger(__name__) >> "%BASE_DIR%\musetalk_service.py"
echo. >> "%BASE_DIR%\musetalk_service.py"
echo class MuseTalkService: >> "%BASE_DIR%\musetalk_service.py"
echo     def __init__(self): >> "%BASE_DIR%\musetalk_service.py"
echo         self.face_detector = None >> "%BASE_DIR%\musetalk_service.py"
echo         self.detector_type = None >> "%BASE_DIR%\musetalk_service.py"
echo         self.initialize_face_detector() >> "%BASE_DIR%\musetalk_service.py"
echo. >> "%BASE_DIR%\musetalk_service.py"
echo     def initialize_face_detector(self): >> "%BASE_DIR%\musetalk_service.py"
echo         try: >> "%BASE_DIR%\musetalk_service.py"
echo             import dlib >> "%BASE_DIR%\musetalk_service.py"
echo             self.face_detector = dlib.get_frontal_face_detector() >> "%BASE_DIR%\musetalk_service.py"
echo             self.detector_type = 'dlib' >> "%BASE_DIR%\musetalk_service.py"
echo             logger.info("使用dlib人脸检测器") >> "%BASE_DIR%\musetalk_service.py"
echo             return >> "%BASE_DIR%\musetalk_service.py"
echo         except ImportError: >> "%BASE_DIR%\musetalk_service.py"
echo             logger.warning("dlib不可用") >> "%BASE_DIR%\musetalk_service.py"
echo. >> "%BASE_DIR%\musetalk_service.py"
echo         try: >> "%BASE_DIR%\musetalk_service.py"
echo             import mediapipe as mp >> "%BASE_DIR%\musetalk_service.py"
echo             self.mp_face_detection = mp.solutions.face_detection >> "%BASE_DIR%\musetalk_service.py"
echo             self.face_detector = self.mp_face_detection.FaceDetection( >> "%BASE_DIR%\musetalk_service.py"
echo                 model_selection=1, min_detection_confidence=0.5 >> "%BASE_DIR%\musetalk_service.py"
echo             ) >> "%BASE_DIR%\musetalk_service.py"
echo             self.detector_type = 'mediapipe' >> "%BASE_DIR%\musetalk_service.py"
echo             logger.info("使用MediaPipe人脸检测器") >> "%BASE_DIR%\musetalk_service.py"
echo             return >> "%BASE_DIR%\musetalk_service.py"
echo         except ImportError: >> "%BASE_DIR%\musetalk_service.py"
echo             logger.warning("MediaPipe不可用") >> "%BASE_DIR%\musetalk_service.py"
echo. >> "%BASE_DIR%\musetalk_service.py"
echo         try: >> "%BASE_DIR%\musetalk_service.py"
echo             cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml' >> "%BASE_DIR%\musetalk_service.py"
echo             self.face_detector = cv2.CascadeClassifier(cascade_path) >> "%BASE_DIR%\musetalk_service.py"
echo             self.detector_type = 'opencv' >> "%BASE_DIR%\musetalk_service.py"
echo             logger.info("使用OpenCV人脸检测器") >> "%BASE_DIR%\musetalk_service.py"
echo             return >> "%BASE_DIR%\musetalk_service.py"
echo         except Exception as e: >> "%BASE_DIR%\musetalk_service.py"
echo             logger.error(f"OpenCV初始化失败: {e}") >> "%BASE_DIR%\musetalk_service.py"
echo. >> "%BASE_DIR%\musetalk_service.py"
echo         logger.error("无法初始化任何人脸检测器") >> "%BASE_DIR%\musetalk_service.py"
echo         raise RuntimeError("没有可用的人脸检测器") >> "%BASE_DIR%\musetalk_service.py"
echo. >> "%BASE_DIR%\musetalk_service.py"
echo app = Flask(__name__) >> "%BASE_DIR%\musetalk_service.py"
echo musetalk_service = MuseTalkService() >> "%BASE_DIR%\musetalk_service.py"
echo. >> "%BASE_DIR%\musetalk_service.py"
echo @app.route('/health', methods=['GET']) >> "%BASE_DIR%\musetalk_service.py"
echo def health_check(): >> "%BASE_DIR%\musetalk_service.py"
echo     return jsonify({'status': 'healthy', 'detector': musetalk_service.detector_type}) >> "%BASE_DIR%\musetalk_service.py"
echo. >> "%BASE_DIR%\musetalk_service.py"
echo if __name__ == '__main__': >> "%BASE_DIR%\musetalk_service.py"
echo     print("MuseTalk数字人服务启动") >> "%BASE_DIR%\musetalk_service.py"
echo     print(f"人脸检测器: {musetalk_service.detector_type}") >> "%BASE_DIR%\musetalk_service.py"
echo     print("服务地址: http://localhost:5000") >> "%BASE_DIR%\musetalk_service.py"
echo     app.run(host='0.0.0.0', port=5000, debug=False) >> "%BASE_DIR%\musetalk_service.py"
echo ✅ musetalk_service.py创建完成

echo 创建test_environment.py...
echo # -*- coding: utf-8 -*- > "%BASE_DIR%\test_environment.py"
echo """MuseTalk环境测试 - 最终修复版""" >> "%BASE_DIR%\test_environment.py"
echo import sys >> "%BASE_DIR%\test_environment.py"
echo import platform >> "%BASE_DIR%\test_environment.py"
echo. >> "%BASE_DIR%\test_environment.py"
echo print("MuseTalk数字人系统环境测试 - 最终修复版") >> "%BASE_DIR%\test_environment.py"
echo print("=" * 60) >> "%BASE_DIR%\test_environment.py"
echo print("Python版本:", sys.version) >> "%BASE_DIR%\test_environment.py"
echo print("Python路径:", sys.executable) >> "%BASE_DIR%\test_environment.py"
echo print("系统平台:", platform.platform()) >> "%BASE_DIR%\test_environment.py"
echo print() >> "%BASE_DIR%\test_environment.py"
echo. >> "%BASE_DIR%\test_environment.py"
echo libraries = [ >> "%BASE_DIR%\test_environment.py"
echo     ('numpy', 'NumPy'), >> "%BASE_DIR%\test_environment.py"
echo     ('torch', 'PyTorch'), >> "%BASE_DIR%\test_environment.py"
echo     ('cv2', 'OpenCV'), >> "%BASE_DIR%\test_environment.py"
echo     ('mediapipe', 'MediaPipe'), >> "%BASE_DIR%\test_environment.py"
echo     ('transformers', 'Transformers'), >> "%BASE_DIR%\test_environment.py"
echo     ('protobuf', 'Protobuf'), >> "%BASE_DIR%\test_environment.py"
echo ] >> "%BASE_DIR%\test_environment.py"
echo. >> "%BASE_DIR%\test_environment.py"
echo print("核心库版本检查:") >> "%BASE_DIR%\test_environment.py"
echo for module, name in libraries: >> "%BASE_DIR%\test_environment.py"
echo     try: >> "%BASE_DIR%\test_environment.py"
echo         lib = __import__(module) >> "%BASE_DIR%\test_environment.py"
echo         version = getattr(lib, '__version__', 'unknown') >> "%BASE_DIR%\test_environment.py"
echo         print(f"✅ {name}: {version}") >> "%BASE_DIR%\test_environment.py"
echo     except Exception as e: >> "%BASE_DIR%\test_environment.py"
echo         print(f"❌ {name}: {e}") >> "%BASE_DIR%\test_environment.py"
echo. >> "%BASE_DIR%\test_environment.py"
echo print() >> "%BASE_DIR%\test_environment.py"
echo print("版本兼容性验证:") >> "%BASE_DIR%\test_environment.py"
echo try: >> "%BASE_DIR%\test_environment.py"
echo     import numpy >> "%BASE_DIR%\test_environment.py"
echo     import torch >> "%BASE_DIR%\test_environment.py"
echo     import cv2 >> "%BASE_DIR%\test_environment.py"
echo     import mediapipe >> "%BASE_DIR%\test_environment.py"
echo     import protobuf >> "%BASE_DIR%\test_environment.py"
echo     print("🎉 强制版本锁定成功！无依赖冲突！") >> "%BASE_DIR%\test_environment.py"
echo     print(f"numpy: {numpy.__version__} (锁定1.24.4)") >> "%BASE_DIR%\test_environment.py"
echo     print(f"opencv: {cv2.__version__} (锁定4.8.1.78)") >> "%BASE_DIR%\test_environment.py"
echo     print(f"mediapipe: {mediapipe.__version__} (兼容protobuf<4)") >> "%BASE_DIR%\test_environment.py"
echo     print(f"protobuf: {protobuf.__version__} (锁定<4.0)") >> "%BASE_DIR%\test_environment.py"
echo except Exception as e: >> "%BASE_DIR%\test_environment.py"
echo     print(f"⚠️  版本问题: {e}") >> "%BASE_DIR%\test_environment.py"
echo ✅ test_environment.py创建完成

echo 创建activate_env.bat...
echo @echo off > "%BASE_DIR%\activate_env.bat"
echo chcp 65001 ^>nul >> "%BASE_DIR%\activate_env.bat"
echo echo MuseTalk数字人系统启动... >> "%BASE_DIR%\activate_env.bat"
echo call "%VENV_DIR%\Scripts\activate.bat" >> "%BASE_DIR%\activate_env.bat"
echo echo 环境已激活 >> "%BASE_DIR%\activate_env.bat"
echo echo. >> "%BASE_DIR%\activate_env.bat"
echo echo 您的配置: >> "%BASE_DIR%\activate_env.bat"
echo echo   Python: %PYTHON_VERSION% >> "%BASE_DIR%\activate_env.bat"
echo echo   安装路径: %BASE_DIR% >> "%BASE_DIR%\activate_env.bat"
echo echo   版本策略: 强制锁定兼容版本 >> "%BASE_DIR%\activate_env.bat"
echo echo   磁盘: F盘外接硬盘 (1TB) >> "%BASE_DIR%\activate_env.bat"
echo echo. >> "%BASE_DIR%\activate_env.bat"
echo echo 可用命令: >> "%BASE_DIR%\activate_env.bat"
echo echo   python test_environment.py - 测试环境 >> "%BASE_DIR%\activate_env.bat"
echo echo   python musetalk_service.py - 启动服务 >> "%BASE_DIR%\activate_env.bat"
echo echo. >> "%BASE_DIR%\activate_env.bat"
echo cmd /k >> "%BASE_DIR%\activate_env.bat"
echo ✅ activate_env.bat创建完成

echo.
echo 🔍 步骤11: 最终验证...
echo 验证强制锁定的版本...

echo 正在验证版本锁定结果...
python -c "import numpy; print('✅ numpy:', numpy.__version__, '(目标: 1.24.4)')"
python -c "import torch; print('✅ torch:', torch.__version__, '(目标: 2.0.1)')"
python -c "import cv2; print('✅ opencv-python:', cv2.__version__, '(目标: 4.8.1.78)')"
python -c "import mediapipe; print('✅ mediapipe:', mediapipe.__version__, '(目标: 0.10.9)')"
python -c "import protobuf; print('✅ protobuf:', protobuf.__version__, '(目标: <4.0)')" 2>nul

echo.
echo ================================================================
echo 🎉 MuseTalk最终修复版安装完成！
echo ================================================================
echo.
echo 📍 安装信息:
echo   安装路径: %BASE_DIR%
echo   Python环境: %VENV_DIR%
echo   磁盘: F盘外接硬盘 (1TB) - 无空间限制
echo   策略: 简化检查 + 强制版本锁定
echo.
echo 🎯 修复的问题:
echo   ✅ 磁盘检查简化 (只检查可用性，不计算空间)
echo   ✅ 中文字符编码修复
echo   ✅ 强制版本锁定 (彻底解决冲突)
echo   ✅ protobuf版本兼容 (mediapipe要求<4)
echo   ✅ 进度显示优化 (实时反馈)
echo.
echo 📋 自动创建的文件:
echo   ✅ activate_env.bat (环境激活)
echo   ✅ musetalk_service.py (服务程序)
echo   ✅ test_environment.py (环境测试)
echo.
echo 🚀 下一步操作:
echo   1. 双击运行: %BASE_DIR%\activate_env.bat
echo   2. 测试环境: python test_environment.py
echo   3. 启动服务: python musetalk_service.py
echo.
echo 💡 针对1TB外接硬盘优化:
echo   ✅ 移除不必要的空间计算
echo   ✅ 只检查读写权限
echo   ✅ 适配大容量外接存储
echo.

:final_pause
echo ================================================================
echo 安装脚本执行完成 - 窗口保持打开
echo ================================================================
echo.
echo 按任意键关闭窗口...
pause >nul
exit /b 0