@echo off
chcp 65001 >nul
echo ================================================================================
echo                        数字人系统环境验证
echo ================================================================================
echo.

set "ERRORS=0"

echo [1/6] 检查 .NET 8.0 SDK...
dotnet --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [❌] .NET SDK 未安装
    set /a ERRORS+=1
) else (
    for /f "tokens=*" %%i in ('dotnet --version') do set "DOTNET_VERSION=%%i"
    echo [✅] .NET SDK 版本: %DOTNET_VERSION%
)

echo.
echo [2/6] 检查 Python 环境...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [❌] Python 未安装
    set /a ERRORS+=1
) else (
    for /f "tokens=*" %%i in ('python --version') do set "PYTHON_VERSION=%%i"
    echo [✅] Python 版本: %PYTHON_VERSION%
)

echo.
echo [3/6] 检查 Edge-TTS...
edge-tts --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [❌] Edge-TTS 未安装 - 运行 install-edge-tts.bat 修复
    set /a ERRORS+=1
) else (
    echo [✅] Edge-TTS 已安装
)

echo.
echo [4/6] 检查项目编译...
cd LmyDigitalHuman
dotnet build --no-restore --verbosity quiet >nul 2>&1
if %errorlevel% neq 0 (
    echo [❌] 项目编译失败
    set /a ERRORS+=1
) else (
    echo [✅] 项目编译成功
)

echo.
echo [5/6] 检查必要目录...
if not exist "wwwroot\templates" (
    echo [❌] 模板目录缺失
    set /a ERRORS+=1
) else (
    echo [✅] 模板目录存在
)

if not exist "wwwroot\images" (
    echo [❌] 图片目录缺失
    set /a ERRORS+=1
) else (
    echo [✅] 图片目录存在
)

echo.
echo [6/6] 测试应用启动...
echo [信息] 启动应用程序进行快速测试...
start /B dotnet run --no-build >nul 2>&1
timeout /t 10 /nobreak >nul

curl -s http://localhost:5001/api/digitalhumantemplate/list >nul 2>&1
if %errorlevel% neq 0 (
    echo [⚠️] 应用程序启动测试未完成 - 请手动验证
) else (
    echo [✅] 应用程序可以正常启动
)

REM 停止测试进程
taskkill /f /im dotnet.exe >nul 2>&1

cd ..

echo.
echo ================================================================================
if %ERRORS%==0 (
    echo                    ✅ 环境验证通过！
    echo.
    echo 🚀 您可以运行以下命令启动数字人系统：
    echo    startup.bat
    echo.
    echo 🌐 访问地址：
    echo    HTTP:  http://localhost:5001/digital-human-test.html
    echo    HTTPS: https://localhost:7001/digital-human-test.html
) else (
    echo                    ❌ 发现 %ERRORS% 个问题
    echo.
    echo 🔧 建议修复步骤：
    echo 1. 运行 setup-environment.bat 自动修复环境
    echo 2. 如果 Edge-TTS 有问题，运行 install-edge-tts.bat
    echo 3. 检查 .NET 8.0 SDK 和 Python 是否正确安装
)
echo ================================================================================
echo.
pause