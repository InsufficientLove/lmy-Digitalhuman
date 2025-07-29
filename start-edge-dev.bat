@echo off
chcp 65001 > nul
color 0D
title 数字人系统 - Edge开发模式启动器

echo ================================================================================
echo                          数字人系统 - Edge开发模式启动器
echo ================================================================================
echo.
echo 🌐 此脚本将启动Microsoft Edge浏览器的开发模式
echo    作为Chrome的备选方案，通常对localhost证书更宽松
echo.
pause

echo [信息] 正在查找Edge安装路径...

REM 查找Edge路径
set EDGE_PATH=""
for %%i in (
    "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    "C:\Program Files\Microsoft\Edge\Application\msedge.exe"
    "%LOCALAPPDATA%\Microsoft\Edge\Application\msedge.exe"
    "%PROGRAMFILES%\Microsoft\Edge\Application\msedge.exe"
    "%PROGRAMFILES(X86)%\Microsoft\Edge\Application\msedge.exe"
) do (
    if exist %%i (
        set EDGE_PATH=%%i
        goto found_edge
    )
)

echo [错误] 未找到Microsoft Edge浏览器！
echo.
echo 请确保Edge已安装，或手动启动Edge并访问：
echo https://localhost:7001/digital-human-test.html
echo.
echo 在Edge中遇到证书警告时：
echo 1. 点击"高级"
echo 2. 点击"继续前往localhost(不安全)"
echo.
pause
goto end

:found_edge
echo [✓] 找到Edge: %EDGE_PATH%

echo [信息] 正在关闭现有Edge进程...
taskkill /f /im msedge.exe >nul 2>&1
timeout /t 2 /nobreak >nul

echo [信息] 创建临时用户数据目录...
set TEMP_DIR=%TEMP%\edge_dev_%RANDOM%
mkdir "%TEMP_DIR%" >nul 2>&1

echo [信息] 启动Edge开发模式...
echo.
echo 🚀 Edge将以以下参数启动：
echo   ✓ 忽略证书错误
echo   ✓ 允许不安全内容
echo   ✓ 禁用安全功能
echo   ✓ 允许访问麦克风
echo.

start "数字人开发Edge" %EDGE_PATH% ^
    --ignore-certificate-errors ^
    --ignore-ssl-errors ^
    --allow-running-insecure-content ^
    --allow-insecure-localhost ^
    --disable-web-security ^
    --user-data-dir="%TEMP_DIR%" ^
    --disable-features=VizDisplayCompositor ^
    --no-sandbox ^
    --disable-extensions ^
    --test-type ^
    --inprivate ^
    "https://localhost:7001/digital-human-test.html"

echo.
echo [✓] Edge开发模式已启动！
echo.
echo 📱 访问地址: https://localhost:7001/digital-human-test.html
echo.
echo 💡 Edge浏览器提示：
echo   - Edge通常对localhost证书更宽松
echo   - 如果看到"不安全"警告，点击"高级"然后"继续访问"
echo   - Edge的隐私模式可能有助于绕过某些限制
echo   - 此实例使用临时配置，不影响正常Edge使用
echo.

:end
echo 按任意键退出...
pause >nul