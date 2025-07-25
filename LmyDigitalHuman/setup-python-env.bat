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
echo [步骤3] 在 SadTalker 环境中安装 Edge-TTS...
if exist "%SADTALKER_VENV%\Scripts\python.exe" (
    echo 使用 SadTalker 环境: %SADTALKER_VENV%
    "%SADTALKER_VENV%\Scripts\python.exe" -m pip install edge-tts
    
    REM 验证安装
    "%SADTALKER_VENV%\Scripts\python.exe" -c "import edge_tts; print('[成功] Edge-TTS 版本:', edge_tts.__version__)"
) else (
    echo [跳过] SadTalker 环境安装
)

echo.
echo [步骤4] 在系统 Python 中安装 Edge-TTS（备用）...
python -m pip install edge-tts

echo.
echo [步骤5] 检查 Whisper 环境...
echo 正在检查 Whisper 是否已安装...
python -c "import whisper" 2>nul
if %errorlevel% neq 0 (
    echo [提示] Whisper 未安装。如果需要语音识别功能，请运行：
    echo pip install openai-whisper
    echo.
    echo 注意：Whisper 安装包较大，建议使用国内镜像：
    echo pip install -i https://pypi.tuna.tsinghua.edu.cn/simple openai-whisper
) else (
    echo [成功] Whisper 已安装
)

echo.
echo [步骤6] 创建配置文件...
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
echo [步骤7] 测试环境...
echo.
echo 测试 Edge-TTS...
if exist "%SADTALKER_VENV%\Scripts\python.exe" (
    "%SADTALKER_VENV%\Scripts\python.exe" -m edge_tts --voice zh-CN-XiaoxiaoNeural --text "环境配置成功" --write-media test_env.mp3
) else (
    python -m edge_tts --voice zh-CN-XiaoxiaoNeural --text "环境配置成功" --write-media test_env.mp3
)

if exist test_env.mp3 (
    echo [成功] Edge-TTS 测试通过！
    del test_env.mp3
) else (
    echo [警告] Edge-TTS 测试失败，请检查安装
)

echo.
echo ============================================
echo    环境配置完成！
echo ============================================
echo.
echo 配置摘要：
echo - Python 路径: %SADTALKER_VENV%\Scripts\python.exe
echo - Edge-TTS: 已安装（支持语音合成）
echo - Whisper: 需要时请手动安装（支持语音识别）
echo.
echo 【下一步操作】
echo 1. 启动 LmyDigitalHuman 项目
echo 2. 如果遇到问题，请查看 logs 目录下的日志文件
echo.
pause