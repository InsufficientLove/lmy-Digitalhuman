@echo off
echo ======================================
echo 安装 Edge TTS 语音合成服务
echo ======================================
echo.

REM 检查是否在虚拟环境中
if exist "F:\AI\SadTalker\venv\Scripts\python.exe" (
    echo 使用 SadTalker 虚拟环境安装...
    F:\AI\SadTalker\venv\Scripts\python.exe -m pip install edge-tts
) else (
    echo 使用系统 Python 安装...
    python -m pip install edge-tts
)

echo.
echo ======================================
echo 测试 Edge TTS 是否安装成功
echo ======================================
echo.

edge-tts --help >nul 2>&1
if %errorlevel% equ 0 (
    echo [成功] Edge TTS 安装成功！
    echo.
    echo 正在生成测试音频...
    edge-tts --voice zh-CN-XiaoxiaoNeural --text "恭喜您，Edge TTS 安装成功！" --write-media test_edge_tts.mp3
    
    if exist test_edge_tts.mp3 (
        echo [成功] 测试音频生成成功: test_edge_tts.mp3
        echo.
        echo 是否播放测试音频？(Y/N)
        set /p play=
        if /i "%play%"=="Y" (
            start test_edge_tts.mp3
        )
    )
) else (
    echo [错误] Edge TTS 安装失败，请检查错误信息
)

echo.
echo 按任意键退出...
pause >nul