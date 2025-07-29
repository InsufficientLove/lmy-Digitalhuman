@echo off
chcp 65001 > nul
echo ========================================
echo    数字人系统启动脚本
echo ========================================
echo.

REM 检查.NET SDK是否安装
dotnet --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到.NET SDK，请先安装.NET 8.0 SDK
    echo 下载地址: https://dotnet.microsoft.com/download/dotnet/8.0
    pause
    exit /b 1
)

echo [信息] 检测到.NET SDK版本:
dotnet --version

echo.
echo [信息] 正在还原NuGet包...
dotnet restore LmyDigitalHuman/LmyDigitalHuman.csproj
if %errorlevel% neq 0 (
    echo [错误] NuGet包还原失败
    pause
    exit /b 1
)

echo.
echo [信息] 正在编译项目...
dotnet build LmyDigitalHuman/LmyDigitalHuman.csproj --configuration Release
if %errorlevel% neq 0 (
    echo [错误] 项目编译失败，请检查代码错误
    pause
    exit /b 1
)

echo.
echo [信息] 正在启动数字人系统...
echo [提示] 系统启动后请访问: https://localhost:7001 或 http://localhost:5001
echo [提示] 按 Ctrl+C 可停止服务
echo.

cd LmyDigitalHuman
dotnet run --configuration Release --urls "https://localhost:7001;http://localhost:5001"

pause