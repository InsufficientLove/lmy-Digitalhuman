@echo off
chcp 65001 >nul 2>&1
echo ================================================================================
echo              🎤 下载Whisper.NET Large模型 (修复版)
echo ================================================================================
echo.
echo [📊] 模型信息:
echo   - 名称: Whisper Large v3
echo   - 大小: ~2.9GB
echo   - 准确率: 最高
echo   - 下载一次永久使用
echo.
echo 按任意键开始下载...
pause

REM 创建Models目录
if not exist "LmyDigitalHuman" (
    echo [❌] 错误: 未找到LmyDigitalHuman目录
    echo [💡] 请确保在项目根目录运行此脚本
    pause
    exit /b 1
)

if not exist "LmyDigitalHuman\Models" (
    echo [📁] 创建Models目录...
    mkdir "LmyDigitalHuman\Models"
)

echo ================================================================================
echo [步骤 1/3] 检查现有文件
echo ================================================================================

cd LmyDigitalHuman\Models

if exist "ggml-large-v3.bin" (
    echo [ℹ️] 模型文件已存在
    for %%I in ("ggml-large-v3.bin") do (
        echo [📊] 文件大小: %%~zI bytes
        if %%~zI gtr 2000000000 (
            echo [✅] 文件大小正常，无需重新下载
            goto success
        ) else (
            echo [⚠️] 文件大小异常，重新下载
            del "ggml-large-v3.bin" 2>nul
        )
    )
)

echo ================================================================================
echo [步骤 2/3] 开始下载 
echo ================================================================================

echo [📥] 正在下载Whisper Large模型...
echo [🔗] 下载地址: https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3.bin
echo [⏱️] 预计时间: 10-30分钟 (取决于网络速度)
echo.

REM 方法1: 使用curl下载
echo [🔄] 尝试方法1: curl下载...
curl --version >nul 2>&1
if %errorlevel% equ 0 (
    curl -L --progress-bar -o ggml-large-v3.bin https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3.bin
    if %errorlevel% equ 0 (
        echo [✅] curl下载成功
        goto verify
    ) else (
        echo [⚠️] curl下载失败，尝试其他方法
    )
) else (
    echo [ℹ️] curl不可用，跳过
)

REM 方法2: 使用PowerShell下载
echo [🔄] 尝试方法2: PowerShell下载...
powershell -Command "try { Write-Host '[📊] 开始PowerShell下载...'; $ProgressPreference = 'Continue'; Invoke-WebRequest -Uri 'https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3.bin' -OutFile 'ggml-large-v3.bin' -UseBasicParsing; Write-Host '[✅] PowerShell下载完成' } catch { Write-Host '[❌] PowerShell下载失败:' $_.Exception.Message }"

if exist "ggml-large-v3.bin" (
    echo [✅] PowerShell下载成功
    goto verify
) else (
    echo [❌] PowerShell下载失败
)

REM 方法3: 手动下载指导
echo [📋] 自动下载失败，请手动下载:
echo.
echo [🔗] 1. 访问: https://huggingface.co/ggerganov/whisper.cpp/tree/main
echo [📥] 2. 下载: ggml-large-v3.bin
echo [📁] 3. 保存到: %CD%
echo.
echo 下载完成后按任意键继续验证...
pause

:verify
echo.
echo ================================================================================
echo [步骤 3/3] 验证下载结果  
echo ================================================================================

if exist "ggml-large-v3.bin" (
    for %%I in ("ggml-large-v3.bin") do (
        echo [📊] 文件大小: %%~zI bytes
        if %%~zI gtr 2000000000 (
            echo [🎉] 下载成功！文件大小正常 (大于2GB)
            goto success
        ) else (
            echo [⚠️] 文件可能不完整，大小: %%~zI bytes
            echo [💡] 建议重新下载或检查网络连接
        )
    )
) else (
    echo [❌] 下载失败，文件不存在
    goto failure
)

:success
cd ..\..
echo.
echo ================================================================================
echo                           下载成功
echo ================================================================================
echo.
echo [✅] Whisper Large模型下载完成！
echo [📁] 位置: LmyDigitalHuman\Models\ggml-large-v3.bin
echo [⚙️] 配置: appsettings.json中已配置
echo [🚀] 程序启动时会自动使用此模型
echo.
goto end

:failure
cd ..\..
echo.
echo ================================================================================
echo                           下载失败
echo ================================================================================
echo.
echo [❌] 自动下载失败，请尝试:
echo.
echo [方案1] 手动下载:
echo   1. 访问: https://huggingface.co/ggerganov/whisper.cpp/tree/main
echo   2. 下载: ggml-large-v3.bin (~2.9GB)
echo   3. 保存到: LmyDigitalHuman\Models\
echo.
echo [方案2] 使用较小模型:
echo   - 可以先使用程序自带的base模型 (~142MB)
echo   - 稍后手动下载large模型
echo.

:end
echo 按任意键退出...
pause >nul
exit /b 0