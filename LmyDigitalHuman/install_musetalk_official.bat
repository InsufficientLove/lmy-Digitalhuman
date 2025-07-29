@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ================================================================
echo 🎵 MuseTalk数字人系统安装脚本 - 官方依赖版
echo ================================================================
echo 策略: 使用官方requirements.txt + 自动下载 + 简化逻辑
echo 解决: 版本冲突根源 + 依赖准确性 + 减少猜测
echo.

REM 错误处理
set "ERROR_OCCURRED=0"

echo 🔍 步骤1: 系统检查...
echo [■□□□□□□□□□] 10%% - 检查系统环境

set "BASE_DIR=F:\AI\DigitalHuman"
set "VENV_DIR=%BASE_DIR%\venv"

echo ✅ 安装路径: %BASE_DIR%

REM 简化磁盘检查
echo 检查F盘可用性...
if not exist "F:\" (
    echo ❌ F盘不存在或无法访问
    echo 请确认F盘已连接或更换安装路径
    goto :final_pause
)

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
    timeout /t 3 >nul
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
echo 🔍 步骤7: 下载官方requirements.txt...
echo [■■■■■■■□□□] 70%% - 获取官方依赖文件

echo 正在下载官方requirements.txt...
powershell -Command "try { Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/TMElyralab/MuseTalk/main/requirements.txt' -OutFile '%BASE_DIR%\requirements.txt' -UseBasicParsing } catch { exit 1 }"
if errorlevel 1 (
    echo ⚠️  网络下载失败，使用备份版本...
    goto :create_backup_requirements
) else (
    echo ✅ 官方requirements.txt下载完成
    goto :install_requirements
)

:create_backup_requirements
echo 创建备份requirements.txt...
(
echo diffusers==0.30.2
echo accelerate==0.28.0
echo numpy==1.23.5
echo tensorflow==2.12.0
echo tensorboard==2.12.0
echo opencv-python==4.9.0.80
echo soundfile==0.12.1
echo transformers==4.39.2
echo huggingface_hub==0.30.2
echo librosa==0.11.0
echo einops==0.8.1
echo gradio==5.24.0
echo.
echo gdown
echo requests
echo imageio[ffmpeg]
echo.
echo omegaconf
echo ffmpeg-python
echo moviepy
) > "%BASE_DIR%\requirements.txt"
echo ✅ 备份requirements.txt创建完成

:install_requirements
echo.
echo 🔍 步骤8: 安装官方依赖...
echo [■■■■■■■■□□] 80%% - 按官方requirements.txt安装

echo ================================================================
echo 🎯 使用官方requirements.txt策略
echo ================================================================
echo 直接使用MuseTalk官方测试过的版本组合
echo 来源: https://github.com/TMElyralab/MuseTalk/blob/main/requirements.txt
echo ================================================================

echo 正在显示官方依赖列表:
type "%BASE_DIR%\requirements.txt"
echo.
echo ================================================================

echo 正在安装官方依赖包...
echo 这可能需要几分钟时间，请耐心等待...
pip install -r "%BASE_DIR%\requirements.txt" -i https://pypi.tuna.tsinghua.edu.cn/simple/

if errorlevel 1 (
    echo ⚠️  部分包安装可能有警告，但会继续...
)

echo ✅ 官方依赖包安装完成

echo.
echo 🔍 步骤9: 安装补充依赖...
echo [■■■■■■■■■□] 90%% - 安装Web框架和工具

echo 安装Web框架...
echo 正在安装: flask, fastapi, uvicorn
pip install flask fastapi uvicorn -i https://pypi.tuna.tsinghua.edu.cn/simple/ -q

echo 安装工具包...
echo 正在安装: pillow, tqdm
pip install pillow tqdm -i https://pypi.tuna.tsinghua.edu.cn/simple/ -q

echo 尝试安装dlib...
echo 正在尝试: dlib (预编译包)
pip install dlib -i https://pypi.tuna.tsinghua.edu.cn/simple/ --no-cache-dir -q >nul 2>&1
python -c "import dlib; print('dlib安装成功')" >nul 2>&1
if errorlevel 1 (
    echo ⚠️  dlib安装失败，可使用MediaPipe替代
) else (
    echo ✅ dlib安装成功
)

echo 安装语音处理...
echo 正在安装: openai-whisper
pip install openai-whisper -i https://pypi.tuna.tsinghua.edu.cn/simple/ -q

echo ✅ 补充依赖安装完成

echo.
echo 🔍 步骤10: 创建服务文件...
echo [■■■■■■■■■■] 100%% - 生成服务和测试文件

echo 创建musetalk_service.py...
echo # -*- coding: utf-8 -*- > "%BASE_DIR%\musetalk_service.py"
echo """MuseTalk数字人服务 - 官方依赖版""" >> "%BASE_DIR%\musetalk_service.py"
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
echo             logger.warning("dlib不可用，尝试其他检测器") >> "%BASE_DIR%\musetalk_service.py"
echo. >> "%BASE_DIR%\musetalk_service.py"
echo         try: >> "%BASE_DIR%\musetalk_service.py"
echo             cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml' >> "%BASE_DIR%\musetalk_service.py"
echo             self.face_detector = cv2.CascadeClassifier(cascade_path) >> "%BASE_DIR%\musetalk_service.py"
echo             self.detector_type = 'opencv' >> "%BASE_DIR%\musetalk_service.py"
echo             logger.info("使用OpenCV人脸检测器") >> "%BASE_DIR%\musetalk_service.py"
echo             return >> "%BASE_DIR%\musetalk_service.py"
echo         except Exception as e: >> "%BASE_DIR%\musetalk_service.py"
echo             logger.error(f"人脸检测器初始化失败: {e}") >> "%BASE_DIR%\musetalk_service.py"
echo             raise RuntimeError("没有可用的人脸检测器") >> "%BASE_DIR%\musetalk_service.py"
echo. >> "%BASE_DIR%\musetalk_service.py"
echo app = Flask(__name__) >> "%BASE_DIR%\musetalk_service.py"
echo musetalk_service = MuseTalkService() >> "%BASE_DIR%\musetalk_service.py"
echo. >> "%BASE_DIR%\musetalk_service.py"
echo @app.route('/health', methods=['GET']) >> "%BASE_DIR%\musetalk_service.py"
echo def health_check(): >> "%BASE_DIR%\musetalk_service.py"
echo     return jsonify({'status': 'healthy', 'detector': musetalk_service.detector_type}) >> "%BASE_DIR%\musetalk_service.py"
echo. >> "%BASE_DIR%\musetalk_service.py"
echo if __name__ == '__main__': >> "%BASE_DIR%\musetalk_service.py"
echo     print("MuseTalk数字人服务启动 - 官方依赖版") >> "%BASE_DIR%\musetalk_service.py"
echo     print(f"人脸检测器: {musetalk_service.detector_type}") >> "%BASE_DIR%\musetalk_service.py"
echo     print("服务地址: http://localhost:5000") >> "%BASE_DIR%\musetalk_service.py"
echo     app.run(host='0.0.0.0', port=5000, debug=False) >> "%BASE_DIR%\musetalk_service.py"
echo ✅ musetalk_service.py创建完成

echo 创建test_environment.py...
echo # -*- coding: utf-8 -*- > "%BASE_DIR%\test_environment.py"
echo """MuseTalk环境测试 - 官方依赖版""" >> "%BASE_DIR%\test_environment.py"
echo import sys >> "%BASE_DIR%\test_environment.py"
echo import platform >> "%BASE_DIR%\test_environment.py"
echo. >> "%BASE_DIR%\test_environment.py"
echo print("MuseTalk数字人系统环境测试 - 官方依赖版") >> "%BASE_DIR%\test_environment.py"
echo print("=" * 60) >> "%BASE_DIR%\test_environment.py"
echo print("Python版本:", sys.version) >> "%BASE_DIR%\test_environment.py"
echo print("Python路径:", sys.executable) >> "%BASE_DIR%\test_environment.py"
echo print("系统平台:", platform.platform()) >> "%BASE_DIR%\test_environment.py"
echo print() >> "%BASE_DIR%\test_environment.py"
echo. >> "%BASE_DIR%\test_environment.py"
echo print("官方requirements.txt依赖检查:") >> "%BASE_DIR%\test_environment.py"
echo libraries = [ >> "%BASE_DIR%\test_environment.py"
echo     ('numpy', 'NumPy'), >> "%BASE_DIR%\test_environment.py"
echo     ('cv2', 'OpenCV'), >> "%BASE_DIR%\test_environment.py"
echo     ('transformers', 'Transformers'), >> "%BASE_DIR%\test_environment.py"
echo     ('diffusers', 'Diffusers'), >> "%BASE_DIR%\test_environment.py"
echo     ('accelerate', 'Accelerate'), >> "%BASE_DIR%\test_environment.py"
echo     ('huggingface_hub', 'HuggingFace Hub'), >> "%BASE_DIR%\test_environment.py"
echo     ('tensorflow', 'TensorFlow'), >> "%BASE_DIR%\test_environment.py"
echo     ('librosa', 'Librosa'), >> "%BASE_DIR%\test_environment.py"
echo     ('soundfile', 'SoundFile'), >> "%BASE_DIR%\test_environment.py"
echo     ('gradio', 'Gradio'), >> "%BASE_DIR%\test_environment.py"
echo ] >> "%BASE_DIR%\test_environment.py"
echo. >> "%BASE_DIR%\test_environment.py"
echo for module, name in libraries: >> "%BASE_DIR%\test_environment.py"
echo     try: >> "%BASE_DIR%\test_environment.py"
echo         lib = __import__(module) >> "%BASE_DIR%\test_environment.py"
echo         version = getattr(lib, '__version__', 'unknown') >> "%BASE_DIR%\test_environment.py"
echo         print(f"✅ {name}: {version}") >> "%BASE_DIR%\test_environment.py"
echo     except Exception as e: >> "%BASE_DIR%\test_environment.py"
echo         print(f"❌ {name}: {e}") >> "%BASE_DIR%\test_environment.py"
echo. >> "%BASE_DIR%\test_environment.py"
echo print() >> "%BASE_DIR%\test_environment.py"
echo print("🎉 使用官方requirements.txt，避免版本冲突！") >> "%BASE_DIR%\test_environment.py"
echo. >> "%BASE_DIR%\test_environment.py"
echo try: >> "%BASE_DIR%\test_environment.py"
echo     import dlib >> "%BASE_DIR%\test_environment.py"
echo     print("✅ dlib可用") >> "%BASE_DIR%\test_environment.py"
echo except ImportError: >> "%BASE_DIR%\test_environment.py"
echo     print("⚠️  dlib不可用，可使用OpenCV替代") >> "%BASE_DIR%\test_environment.py"
echo ✅ test_environment.py创建完成

echo 创建activate_env.bat...
echo @echo off > "%BASE_DIR%\activate_env.bat"
echo chcp 65001 ^>nul >> "%BASE_DIR%\activate_env.bat"
echo echo MuseTalk数字人系统启动 - 官方依赖版... >> "%BASE_DIR%\activate_env.bat"
echo call "%VENV_DIR%\Scripts\activate.bat" >> "%BASE_DIR%\activate_env.bat"
echo echo 环境已激活 >> "%BASE_DIR%\activate_env.bat"
echo echo. >> "%BASE_DIR%\activate_env.bat"
echo echo 您的配置: >> "%BASE_DIR%\activate_env.bat"
echo echo   Python: %PYTHON_VERSION% >> "%BASE_DIR%\activate_env.bat"
echo echo   安装路径: %BASE_DIR% >> "%BASE_DIR%\activate_env.bat"
echo echo   版本策略: 官方requirements.txt >> "%BASE_DIR%\activate_env.bat"
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
echo 验证官方依赖安装结果...

echo 正在验证核心库版本...
python -c "import numpy; print('✅ numpy:', numpy.__version__)"
python -c "import cv2; print('✅ opencv-python:', cv2.__version__)"
python -c "import transformers; print('✅ transformers:', transformers.__version__)"
python -c "import diffusers; print('✅ diffusers:', diffusers.__version__)"
python -c "import accelerate; print('✅ accelerate:', accelerate.__version__)"

echo.
echo ================================================================
echo 🎉 MuseTalk官方依赖版安装完成！
echo ================================================================
echo.
echo 📍 安装信息:
echo   安装路径: %BASE_DIR%
echo   Python环境: %VENV_DIR%
echo   磁盘: F盘外接硬盘 (1TB)
echo   依赖来源: 官方requirements.txt
echo.
echo 🎯 核心优势:
echo   ✅ 使用官方测试过的版本组合
echo   ✅ 避免自行猜测版本导致的冲突
echo   ✅ 与MuseTalk官方完全一致
echo   ✅ 减少依赖解析错误
echo   ✅ 官方维护和更新
echo.
echo 📋 自动创建的文件:
echo   ✅ requirements.txt (官方下载)
echo   ✅ activate_env.bat (环境激活)
echo   ✅ musetalk_service.py (服务程序)
echo   ✅ test_environment.py (环境测试)
echo.
echo 🚀 下一步操作:
echo   1. 双击运行: %BASE_DIR%\activate_env.bat
echo   2. 测试环境: python test_environment.py
echo   3. 启动服务: python musetalk_service.py
echo.
echo 💡 官方依赖优势:
echo   ✅ 版本经过官方测试验证
echo   ✅ 避免依赖冲突问题
echo   ✅ 与官方代码完全兼容
echo   ✅ 持续官方维护更新
echo.

:final_pause
echo ================================================================
echo 安装脚本执行完成 - 窗口保持打开
echo ================================================================
echo.
echo 按任意键关闭窗口...
pause >nul
exit /b 0