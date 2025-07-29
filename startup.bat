@echo off
chcp 65001 > nul
color 0B
title 数字人系统 - 生产环境启动

echo ================================================================================
echo                            数字人系统 - 生产环境启动
echo ================================================================================
echo.
echo 正在启动数字人系统生产环境...
echo.

REM 检查.NET SDK是否安装
dotnet --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到 .NET 8.0 SDK
    echo.
    echo 请先运行 setup-environment.bat 配置环境
    echo 或访问: https://dotnet.microsoft.com/download/dotnet/8.0
    echo.
    pause
    exit /b 1
)

echo [✓] .NET SDK 版本: 
dotnet --version

echo.
echo [信息] 正在还原 NuGet 包...
dotnet restore LmyDigitalHuman/LmyDigitalHuman.csproj --verbosity quiet
if %errorlevel% neq 0 (
    echo [错误] NuGet 包还原失败
    echo 请检查网络连接或运行 setup-environment.bat
    pause
    exit /b 1
)

echo [信息] 正在编译项目（Release 模式）...
dotnet build LmyDigitalHuman/LmyDigitalHuman.csproj --configuration Release --verbosity quiet
if %errorlevel% neq 0 (
    echo [错误] 项目编译失败
    echo.
    echo 可能的解决方案：
    echo 1. 在 Visual Studio 2022 中打开项目解决编译错误
    echo 2. 运行 dev-start.bat 查看详细错误信息
    echo 3. 查看 STARTUP_GUIDE.md 获取帮助
    echo.
    pause
    exit /b 1
)

echo.
echo ================================================================================
echo                              系统启动中...
echo ================================================================================
echo.
echo [✓] 环境检查通过
echo [✓] 依赖包已就绪  
echo [✓] 项目编译成功
echo.
echo 🌐 系统启动后访问地址：
echo     HTTPS: https://localhost:7001
echo     HTTP:  http://localhost:5001
echo.
echo 💡 提示：
echo     - 首次启动可能需要较长时间
echo     - 按 Ctrl+C 可停止服务
echo     - 如需开发模式，请使用 dev-start.bat
echo.

cd LmyDigitalHuman
dotnet run --configuration Release --urls "https://localhost:7001;http://localhost:5001"

echo.
echo 系统已停止运行
pause