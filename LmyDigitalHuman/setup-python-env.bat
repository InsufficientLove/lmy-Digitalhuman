@echo off
chcp 65001 > nul
echo ============================================
echo    LmyDigitalHuman Python 环境安装脚本
echo ============================================
echo.
echo 【重要提示】
echo 此脚本将安装以下组件：
echo 1. Python 环境检查和配置
echo 2. Edge-TTS (语音合成)
echo 3. Whisper (语音识别) - 如果有独立环境
echo 4. 相关 Python 依赖
echo.
echo 【手动操作要求】
echo 1. 请确保已安装 Python 3.8+ 和 pip
echo 2. 请确保已安装并配置好 SadTalker 环境
echo 3. 如果需要 GPU 支持，请先安装 CUDA 和 cuDNN
echo.
pause

echo.
echo [步骤1] 检查 Python 环境...
python --version
if %errorlevel% neq 0 (
    echo [错误] 未找到 Python！请先安装 Python 3.8 或更高版本。
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo.
echo [步骤2] 检查 SadTalker 环境...
set SADTALKER_PATH=F:\AI\SadTalker
set SADTALKER_VENV=%SADTALKER_PATH%\venv
if not exist "%SADTALKER_VENV%\Scripts\python.exe" (
    echo [警告] 未找到 SadTalker 虚拟环境！
    echo 预期路径: %SADTALKER_VENV%
    echo.
    echo 请手动修改此脚本中的 SADTALKER_PATH 变量为您的 SadTalker 安装路径
    set /p CUSTOM_PATH="或者现在输入 SadTalker 路径（直接回车跳过）: "
    if not "%CUSTOM_PATH%"=="" (
        set SADTALKER_PATH=%CUSTOM_PATH%
        set SADTALKER_VENV=%SADTALKER_PATH%\venv
    )
)

echo.
echo [步骤3] 在 SadTalker 环境中安装依赖...
if exist "%SADTALKER_VENV%\Scripts\python.exe" (
    echo 使用 SadTalker 环境: %SADTALKER_VENV%
    
    REM 安装 PyTorch 1.12.1 + CUDA 11.3
    echo 安装 PyTorch 1.12.1 + CUDA 11.3...
    "%SADTALKER_VENV%\Scripts\python.exe" -m pip install torch==1.12.1+cu113 torchvision==0.13.1+cu113 torchaudio==0.12.1 --extra-index-url https://download.pytorch.org/whl/cu113
    
    REM 安装 SadTalker 核心依赖
    echo 安装 SadTalker 依赖...
    "%SADTALKER_VENV%\Scripts\python.exe" -m pip install numpy==1.23.4 face_alignment==1.3.5 imageio==2.19.3 imageio-ffmpeg==0.4.7
    "%SADTALKER_VENV%\Scripts\python.exe" -m pip install librosa==0.9.2 numba resampy==0.3.1 pydub==0.25.1 scipy==1.10.1
    "%SADTALKER_VENV%\Scripts\python.exe" -m pip install kornia==0.6.8 tqdm yacs==0.1.8 pyyaml joblib==1.1.0
    "%SADTALKER_VENV%\Scripts\python.exe" -m pip install scikit-image==0.19.3 basicsr==1.4.2 facexlib==0.3.0
    "%SADTALKER_VENV%\Scripts\python.exe" -m pip install gradio gfpgan av safetensors
    
    REM 安装 Edge-TTS 和 Whisper
    echo 安装 Edge-TTS 和 Whisper...
    "%SADTALKER_VENV%\Scripts\python.exe" -m pip install edge-tts openai-whisper
    
    REM 验证安装
    "%SADTALKER_VENV%\Scripts\python.exe" -c "import torch; print('[成功] PyTorch 版本:', torch.__version__, '- CUDA 可用:', torch.cuda.is_available())"
    "%SADTALKER_VENV%\Scripts\python.exe" -c "import edge_tts; print('[成功] Edge-TTS 版本:', edge_tts.__version__)"
) else (
    echo [跳过] SadTalker 环境安装
)

echo.
echo [步骤4] 下载 SadTalker 模型（可选）...
if exist "%SADTALKER_PATH%\checkpoints" (
    echo [提示] checkpoints 目录已存在，跳过模型下载
) else (
    echo [提示] 需要手动下载 SadTalker 模型
    echo 请参考文档下载模型文件到：
    echo %SADTALKER_PATH%\checkpoints
    echo.
    echo 模型下载地址：
    echo - 百度网盘：https://pan.baidu.com/s/1tb0pBh2vZO5YD5vRNe_ZXg （提取码：sadt）
    echo - Google Drive：https://drive.google.com/drive/folders/1Wd88VDoLhVzYsQ30_qDVluQHjqQHrmYKr
)

echo.
echo [步骤5] 创建配置文件...
if exist "appsettings.json" (
    echo 正在更新配置文件中的 Python 路径...
    REM 这里可以使用 PowerShell 来更新 JSON
    powershell -Command "(Get-Content appsettings.json) -replace '\"PythonPath\": \".*?\"', '\"PythonPath\": \"%SADTALKER_VENV:\=\\%\\Scripts\\python.exe\"' | Set-Content appsettings.json.tmp"
    if exist appsettings.json.tmp (
        move /y appsettings.json.tmp appsettings.json > nul
        echo [成功] 配置文件已更新
    )
)

echo.
echo [步骤6] 快速测试...
echo.
if exist "%SADTALKER_VENV%\Scripts\python.exe" (
    echo 测试 Edge-TTS...
    "%SADTALKER_VENV%\Scripts\python.exe" -c "import edge_tts; print('[成功] Edge-TTS 已安装')" 2>nul
    if %errorlevel% neq 0 (
        echo [警告] Edge-TTS 测试失败
    )
    
    echo 测试 PyTorch...
    "%SADTALKER_VENV%\Scripts\python.exe" -c "import torch; print('[成功] PyTorch 已安装, CUDA:', torch.cuda.is_available())" 2>nul
    if %errorlevel% neq 0 (
        echo [警告] PyTorch 测试失败
    )
)

echo.
echo ============================================
echo    环境配置完成！
echo ============================================
echo.
echo Python 路径已更新到配置文件
echo.
echo 【下一步】
echo 1. 运行环境检查: check-environment.bat
echo 2. 下载 SadTalker 模型（如果还没有）
echo 3. 启动系统: dotnet run
echo 4. 访问: http://localhost:5000
echo.
pause