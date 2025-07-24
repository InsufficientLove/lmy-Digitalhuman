@echo off
echo ======================================
echo 在 SadTalker 虚拟环境中安装 Edge TTS
echo ======================================
echo.

REM 设置 SadTalker 虚拟环境路径
set SADTALKER_VENV_PATH=F:\AI\SadTalker\venv

REM 检查虚拟环境是否存在
if not exist "%SADTALKER_VENV_PATH%\Scripts\python.exe" (
    echo [错误] 找不到 SadTalker 虚拟环境！
    echo 请确认路径: %SADTALKER_VENV_PATH%
    echo.
    echo 如果您的 SadTalker 安装在其他位置，请修改此脚本中的 SADTALKER_VENV_PATH 变量
    pause
    exit /b 1
)

echo 找到 SadTalker 虚拟环境: %SADTALKER_VENV_PATH%
echo.

REM 使用 SadTalker 虚拟环境中的 pip 安装 edge-tts
echo 正在安装 edge-tts...
"%SADTALKER_VENV_PATH%\Scripts\python.exe" -m pip install edge-tts

REM 检查安装结果
"%SADTALKER_VENV_PATH%\Scripts\python.exe" -c "import edge_tts; print('Edge TTS 版本:', edge_tts.__version__)" 2>nul
if %errorlevel% equ 0 (
    echo.
    echo [成功] Edge TTS 安装成功！
    echo.
    echo 测试 Edge TTS...
    "%SADTALKER_VENV_PATH%\Scripts\python.exe" -m edge_tts --voice zh-CN-XiaoxiaoNeural --text "恭喜您，Edge TTS 在 SadTalker 环境中安装成功！" --write-media test_sadtalker_edge_tts.mp3
    
    if exist test_sadtalker_edge_tts.mp3 (
        echo [成功] 测试音频生成成功: test_sadtalker_edge_tts.mp3
        echo.
        echo 是否播放测试音频？(Y/N)
        set /p play=
        if /i "%play%"=="Y" (
            start test_sadtalker_edge_tts.mp3
        )
    )
) else (
    echo.
    echo [错误] Edge TTS 安装失败！
    echo 请检查错误信息并手动安装：
    echo %SADTALKER_VENV_PATH%\Scripts\pip.exe install edge-tts
)

echo.
echo 按任意键退出...
pause >nul