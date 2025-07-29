@echo off
chcp 65001 > nul
color 0A
title 数字人系统 - 开发专用Chrome启动器

echo ================================================================================
echo                          数字人系统 - 开发专用Chrome启动器
echo ================================================================================
echo.
echo 此工具将启动一个忽略HTTPS证书错误的Chrome浏览器实例
echo 专门用于数字人系统的开发和测试
echo.
echo 🔧 启动参数：
echo   ✓ 忽略证书错误
echo   ✓ 允许不安全的localhost
echo   ✓ 禁用web安全检查
echo   ✓ 允许访问麦克风和摄像头
echo.
pause

echo [信息] 正在启动开发专用Chrome...

REM 尝试不同的Chrome安装路径
set CHROME_PATH=""

REM 检查常见的Chrome安装路径
if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" (
    set CHROME_PATH="C:\Program Files\Google\Chrome\Application\chrome.exe"
) else if exist "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" (
    set CHROME_PATH="C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
) else if exist "%USERPROFILE%\AppData\Local\Google\Chrome\Application\chrome.exe" (
    set CHROME_PATH="%USERPROFILE%\AppData\Local\Google\Chrome\Application\chrome.exe"
) else (
    echo [错误] 未找到Chrome浏览器
    echo.
    echo 请确保Chrome已安装，或手动启动Chrome并添加以下参数：
    echo --ignore-certificate-errors --ignore-ssl-errors --allow-running-insecure-content --disable-web-security --allow-insecure-localhost --unsafely-treat-insecure-origin-as-secure=https://localhost:7001
    echo.
    pause
    goto end
)

echo [✓] 找到Chrome: %CHROME_PATH%

REM 启动Chrome with开发参数
start "数字人开发Chrome" %CHROME_PATH% ^
    --ignore-certificate-errors ^
    --ignore-ssl-errors ^
    --allow-running-insecure-content ^
    --disable-web-security ^
    --allow-insecure-localhost ^
    --unsafely-treat-insecure-origin-as-secure=https://localhost:7001 ^
    --disable-features=VizDisplayCompositor ^
    --user-data-dir="%TEMP%\chrome-dev-profile" ^
    https://localhost:7001/digital-human-test.html

echo.
echo [✓] Chrome已启动！
echo.
echo 💡 提示：
echo   - 此Chrome实例使用临时配置文件
echo   - 专门用于开发，不会影响您的正常Chrome配置
echo   - 关闭此窗口不会影响Chrome运行
echo.
echo 🌐 如果自动跳转失败，请手动访问：
echo   https://localhost:7001/digital-human-test.html
echo.

:end
echo 按任意键退出...
pause >nul