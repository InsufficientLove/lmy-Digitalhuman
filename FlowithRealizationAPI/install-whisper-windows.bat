@echo off
echo 正在安装 OpenAI Whisper for Windows...
echo.

REM 检查Python是否可用
echo [1/4] 检查Python环境...
F:\AI\Python\python.exe --version
if errorlevel 1 (
    echo 错误: Python未找到，请检查路径 F:\AI\Python\python.exe
    pause
    exit /b 1
)

REM 升级pip
echo.
echo [2/4] 升级pip...
F:\AI\Python\python.exe -m pip install --upgrade pip

REM 安装openai-whisper
echo.
echo [3/4] 安装 openai-whisper...
F:\AI\Python\python.exe -m pip install openai-whisper

REM 验证安装
echo.
echo [4/4] 验证安装...
F:\AI\Python\python.exe -m whisper --help
if errorlevel 1 (
    echo 错误: Whisper安装失败
    pause
    exit /b 1
)

echo.
echo ✅ OpenAI Whisper 安装成功！
echo.
echo 注意事项：
echo - 确保 FFmpeg 已安装并在 PATH 中
echo - 如果没有 FFmpeg，请从 https://ffmpeg.org/download.html 下载
echo.
pause