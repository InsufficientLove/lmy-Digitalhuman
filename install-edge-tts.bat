@echo off
chcp 65001 >nul
echo ================================================================================
echo                        快速安装 Edge-TTS 工具
echo ================================================================================
echo.

echo [1/3] 检查 Python 环境...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到 Python 环境，请先安装 Python
    echo 请访问: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [✓] Python 环境正常
python --version

echo.
echo [2/3] 安装 edge-tts...
pip install edge-tts --upgrade --quiet
if %errorlevel% neq 0 (
    echo [错误] edge-tts 安装失败
    echo 请尝试手动执行: pip install edge-tts
    pause
    exit /b 1
)

echo [✓] edge-tts 安装完成

echo.
echo [3/3] 验证安装...
edge-tts --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [警告] edge-tts 命令验证失败，但安装可能成功
    echo 请重启命令行或重新启动应用程序
) else (
    echo [✓] edge-tts 验证成功
)

echo.
echo ================================================================================
echo                           安装完成！
echo ================================================================================
echo 现在可以重新启动数字人应用程序，TTS功能应该可以正常工作了。
echo.
pause