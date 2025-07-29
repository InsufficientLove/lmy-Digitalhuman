@echo off
chcp 65001 >nul
echo ================================================================================
echo              🎤 下载Whisper.NET Large模型
echo ================================================================================
echo.
echo [📊] 模型信息:
echo   - 名称: Whisper Large v3
echo   - 大小: ~2.9GB
echo   - 准确率: 最高
echo   - 下载一次永久使用
echo.
pause

if not exist "LmyDigitalHuman\Models" mkdir "LmyDigitalHuman\Models"

cd LmyDigitalHuman\Models

echo ================================================================================
echo [步骤 1/2] 开始下载
echo ================================================================================

if exist "ggml-large-v3.bin" (
    echo [ℹ️] 模型文件已存在
    for %%I in ("ggml-large-v3.bin") do echo [📊] 文件大小: %%~zI bytes
    goto verify
)

echo [📥] 正在下载Whisper Large模型...
echo [🔗] 下载地址: https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3.bin
echo.

curl -L -o ggml-large-v3.bin https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3.bin

if %errorlevel% neq 0 (
    echo [⚠️] curl下载失败，尝试PowerShell...
    powershell -Command "Invoke-WebRequest -Uri 'https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3.bin' -OutFile 'ggml-large-v3.bin'"
)

:verify
echo.
echo ================================================================================
echo [步骤 2/2] 验证下载结果  
echo ================================================================================

if exist "ggml-large-v3.bin" (
    for %%I in ("ggml-large-v3.bin") do (
        echo [✅] 文件存在: %%~zI bytes
        if %%~zI gtr 2000000000 (
            echo [🎉] 下载成功！文件大小正常
        ) else (
            echo [⚠️] 文件可能不完整，大小异常
        )
    )
) else (
    echo [❌] 下载失败，文件不存在
)

cd ..\..

echo.
echo ================================================================================
echo                           下载完成
echo ================================================================================

echo [💡] 使用说明:
echo   - 模型位置: LmyDigitalHuman\Models\ggml-large-v3.bin
echo   - 配置已更新: appsettings.json
echo   - 程序启动时会自动使用此模型
echo   - 识别准确率最高，适合生产环境
echo.

echo 按任意键退出...
pause >nul