@echo off
chcp 65001 > nul
echo ======================================
echo    LmyDigitalHuman 环境检查工具
echo ======================================
echo.

REM 读取配置文件中的Python路径
set PYTHON_PATH=F:/AI/SadTalker/venv/Scripts/python.exe

echo [1] 检查Python环境...
if exist "%PYTHON_PATH%" (
    echo [成功] 找到Python: %PYTHON_PATH%
    echo.
    echo Python版本:
    "%PYTHON_PATH%" --version
    echo.
) else (
    echo [错误] 未找到Python: %PYTHON_PATH%
    echo 请检查配置文件中的Python路径设置
    echo.
)

echo [2] 检查Edge-TTS安装...
"%PYTHON_PATH%" -c "import edge_tts; print('[成功] Edge-TTS已安装，版本:', edge_tts.__version__)" 2>nul
if %errorlevel% neq 0 (
    echo [错误] Edge-TTS未安装
    echo 请运行: "%PYTHON_PATH%" -m pip install edge-tts
) else (
    echo 测试Edge-TTS命令:
    "%PYTHON_PATH%" -m edge_tts --list-voices | findstr /i "zh-CN" | head -5
)
echo.

echo [3] 检查PyTorch安装...
"%PYTHON_PATH%" -c "import torch; print('[成功] PyTorch已安装，版本:', torch.__version__, '- CUDA可用:', torch.cuda.is_available())" 2>nul
if %errorlevel% neq 0 (
    echo [错误] PyTorch未安装
    echo 请运行: "%PYTHON_PATH%" -m pip install torch==1.12.1+cu113 torchvision==0.13.1+cu113 torchaudio==0.12.1 --extra-index-url https://download.pytorch.org/whl/cu113
)
echo.

echo [4] 检查SadTalker依赖...
"%PYTHON_PATH%" -c "import numpy; print('[成功] numpy已安装，版本:', numpy.__version__)" 2>nul
if %errorlevel% neq 0 (
    echo [错误] numpy未安装
)

"%PYTHON_PATH%" -c "import cv2; print('[成功] opencv-python已安装')" 2>nul
if %errorlevel% neq 0 (
    echo [警告] opencv-python未安装（可能影响视频处理）
)

"%PYTHON_PATH%" -c "import librosa; print('[成功] librosa已安装')" 2>nul
if %errorlevel% neq 0 (
    echo [警告] librosa未安装（可能影响音频处理）
)
echo.

echo [5] 检查SadTalker目录...
set SADTALKER_PATH=F:/AI/SadTalker
if exist "%SADTALKER_PATH%\inference.py" (
    echo [成功] 找到SadTalker: %SADTALKER_PATH%
    
    REM 检查模型文件
    if exist "%SADTALKER_PATH%\checkpoints" (
        echo [成功] checkpoints目录存在
        dir "%SADTALKER_PATH%\checkpoints" /b | findstr /i ".pth .tar .safetensors" > nul
        if %errorlevel% equ 0 (
            echo [成功] 发现模型文件
        ) else (
            echo [警告] checkpoints目录为空，请下载SadTalker模型
        )
    ) else (
        echo [错误] checkpoints目录不存在，请下载SadTalker模型
    )
) else (
    echo [错误] 未找到SadTalker: %SADTALKER_PATH%
)
echo.

echo [6] 检查Whisper安装...
"%PYTHON_PATH%" -c "import whisper; print('[成功] Whisper已安装')" 2>nul
if %errorlevel% neq 0 (
    echo [警告] Whisper未安装
    echo 如需语音识别功能，请运行: "%PYTHON_PATH%" -m pip install openai-whisper
)
echo.

echo [7] 检查CUDA环境...
where nvcc >nul 2>&1
if %errorlevel% equ 0 (
    echo [成功] CUDA已安装
    nvcc --version | findstr /i "release"
) else (
    echo [警告] 未检测到CUDA（nvcc不在PATH中）
)

nvidia-smi >nul 2>&1
if %errorlevel% equ 0 (
    echo [成功] NVIDIA驱动正常
    nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader
) else (
    echo [警告] 未检测到NVIDIA驱动
)
echo.

echo ======================================
echo    环境检查完成
echo ======================================
echo.
echo 如有错误，请按照提示进行修复
echo.
pause