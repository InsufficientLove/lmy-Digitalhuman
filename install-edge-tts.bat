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
echo [2/4] 检查虚拟环境...
if exist "venv\Scripts\activate.bat" (
    echo [✓] 找到虚拟环境，正在激活...
    call venv\Scripts\activate.bat
) else (
    echo [警告] 未找到虚拟环境，将安装到全局环境
    echo [建议] 请先运行 setup-environment.bat 创建虚拟环境
)

echo.
echo [3/4] 安装 edge-tts...
pip install edge-tts --upgrade --quiet
if %errorlevel% neq 0 (
    echo [错误] edge-tts 安装失败
    if exist "venv\Scripts\activate.bat" (
        echo 请尝试手动执行:
        echo   call venv\Scripts\activate.bat
        echo   pip install edge-tts
    ) else (
        echo 请尝试手动执行: pip install edge-tts
    )
    pause
    exit /b 1
)

echo [✓] edge-tts 安装完成

echo.
echo [4/4] 验证安装...
python -c "import edge_tts; print('Edge-TTS: 已安装')" 2>nul
if %errorlevel% neq 0 (
    echo [警告] edge-tts Python模块验证失败
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