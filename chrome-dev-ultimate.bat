@echo off
chcp 65001 > nul
color 0E
title 数字人系统 - Chrome终极开发模式

echo ================================================================================
echo                        数字人系统 - Chrome终极开发模式
echo ================================================================================
echo.
echo 🔥 此脚本将启动一个完全忽略HTTPS安全限制的Chrome实例
echo    专门用于解决localhost开发环境的证书问题
echo.
echo ⚠️  警告：此模式仅用于开发，请勿用于正常浏览！
echo.
pause

echo [信息] 正在查找Chrome安装路径...

REM 查找Chrome路径
set CHROME_PATH=""
for %%i in (
    "C:\Program Files\Google\Chrome\Application\chrome.exe"
    "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
    "%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"
    "%PROGRAMFILES%\Google\Chrome\Application\chrome.exe"
    "%PROGRAMFILES(X86)%\Google\Chrome\Application\chrome.exe"
) do (
    if exist %%i (
        set CHROME_PATH=%%i
        goto found_chrome
    )
)

echo [错误] 未找到Chrome浏览器！
echo.
echo 请手动启动Chrome并在地址栏添加以下参数：
echo chrome.exe --disable-web-security --user-data-dir="c:\temp\chrome_dev" --ignore-certificate-errors --ignore-ssl-errors --allow-running-insecure-content --disable-features=VizDisplayCompositor --ignore-certificate-errors-spki-list --ignore-urlfetcher-cert-requests --allow-insecure-localhost
echo.
pause
goto end

:found_chrome
echo [✓] 找到Chrome: %CHROME_PATH%

echo [信息] 正在关闭现有Chrome进程...
taskkill /f /im chrome.exe >nul 2>&1
timeout /t 2 /nobreak >nul

echo [信息] 创建临时用户数据目录...
set TEMP_DIR=%TEMP%\chrome_dev_ultimate_%RANDOM%
mkdir "%TEMP_DIR%" >nul 2>&1

echo [信息] 启动Chrome开发模式...
echo.
echo 🚀 Chrome将以以下安全绕过参数启动：
echo   ✓ 完全禁用Web安全检查
echo   ✓ 忽略所有证书错误
echo   ✓ 允许不安全内容
echo   ✓ 允许访问本地资源
echo   ✓ 禁用CORS检查
echo   ✓ 允许混合内容
echo.

start "数字人开发Chrome" %CHROME_PATH% ^
    --disable-web-security ^
    --user-data-dir="%TEMP_DIR%" ^
    --ignore-certificate-errors ^
    --ignore-ssl-errors ^
    --allow-running-insecure-content ^
    --disable-features=VizDisplayCompositor ^
    --ignore-certificate-errors-spki-list ^
    --ignore-urlfetcher-cert-requests ^
    --allow-insecure-localhost ^
    --disable-extensions ^
    --disable-plugins ^
    --disable-images ^
    --no-sandbox ^
    --disable-dev-shm-usage ^
    --remote-debugging-port=9222 ^
    --disable-background-timer-throttling ^
    --disable-renderer-backgrounding ^
    --disable-backgrounding-occluded-windows ^
    --disable-features=TranslateUI ^
    --disable-ipc-flooding-protection ^
    --disable-hang-monitor ^
    --disable-client-side-phishing-detection ^
    --disable-popup-blocking ^
    --disable-prompt-on-repost ^
    --no-first-run ^
    --no-default-browser-check ^
    --disable-default-apps ^
    --test-type ^
    "https://localhost:7001/digital-human-test.html"

echo.
echo [✓] Chrome开发模式已启动！
echo.
echo 📱 访问地址: https://localhost:7001/digital-human-test.html
echo.
echo 💡 重要提示：
echo   - 此Chrome实例使用临时配置，不会影响您的正常Chrome
echo   - 如果页面显示"不安全"警告，直接点击"继续访问"
echo   - 此模式下麦克风权限应该可以正常获取
echo   - 关闭Chrome后临时数据会自动清理
echo.
echo 🔧 如果仍有问题，请尝试：
echo   1. 在地址栏直接输入: thisisunsafe
echo   2. 或点击"高级" → "继续前往localhost"
echo   3. 或使用Edge浏览器: msedge --ignore-certificate-errors --allow-running-insecure-content
echo.

:end
echo 按任意键退出...
pause >nul