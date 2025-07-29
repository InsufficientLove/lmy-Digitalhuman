@echo off
chcp 65001 > nul
color 0E
title 数字人系统 - 开发环境启动

echo ================================================================================
echo                           数字人系统 - 开发环境启动
echo ================================================================================
echo.
echo 正在启动数字人系统开发环境（支持热重载）...
echo.

REM 检查.NET SDK
dotnet --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到 .NET 8.0 SDK
    echo 请先运行 setup-environment.bat 配置环境
    pause
    exit /b 1
)

echo [✓] .NET SDK 版本: 
dotnet --version

echo.
echo [信息] 开发模式特性：
echo   ✓ 代码热重载 - 修改代码后自动重启
echo   ✓ 详细日志输出 - 便于调试
echo   ✓ 开发环境配置 - 使用 appsettings.json
echo.

echo [信息] 正在还原依赖包...
dotnet restore LmyDigitalHuman/LmyDigitalHuman.csproj --verbosity minimal

echo.
echo ================================================================================
echo                              开发服务器启动中...
echo ================================================================================
echo.
echo 🌐 开发服务器地址：
echo     HTTPS: https://localhost:7001
echo     HTTP:  http://localhost:5001
echo.
echo 💡 开发提示：
echo     - 修改代码后会自动重新编译和重启
echo     - 查看控制台输出了解运行状态
echo     - 按 Ctrl+C 停止开发服务器
echo     - 如遇编译错误，会显示详细信息
echo.

cd LmyDigitalHuman
dotnet watch run --urls "https://localhost:7001;http://localhost:5001"

echo.
echo 开发服务器已停止
pause