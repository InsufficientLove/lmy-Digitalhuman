@echo off
chcp 65001 > nul
color 0C
title 编译错误修复助手

echo ================================================================================
echo                             编译错误修复助手
echo ================================================================================
echo.
echo 此脚本将帮助您诊断和修复常见的编译错误
echo.
pause

echo ================================================================================
echo [步骤 1/5] 环境检查
echo ================================================================================

echo [检查] .NET SDK...
dotnet --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [❌] .NET SDK 未安装
    echo 请先运行 setup-environment.bat
    pause
    exit /b 1
) else (
    echo [✓] .NET SDK 已安装: 
    dotnet --version
)

echo ================================================================================
echo [步骤 2/5] 清理项目缓存
echo ================================================================================

echo [信息] 正在清理构建缓存...
cd LmyDigitalHuman

dotnet clean --verbosity quiet
if exist "bin" rmdir /s /q "bin"
if exist "obj" rmdir /s /q "obj"

echo [✓] 缓存清理完成

echo ================================================================================
echo [步骤 3/5] 还原 NuGet 包
echo ================================================================================

echo [信息] 正在重新还原 NuGet 包...
dotnet restore --force --verbosity normal
if %errorlevel% neq 0 (
    echo [❌] NuGet 包还原失败
    echo.
    echo 可能的解决方案：
    echo 1. 检查网络连接
    echo 2. 清理 NuGet 缓存: dotnet nuget locals all --clear
    echo 3. 检查防火墙设置
    pause
    exit /b 1
) else (
    echo [✓] NuGet 包还原成功
)

echo ================================================================================
echo [步骤 4/5] 编译诊断
echo ================================================================================

echo [信息] 正在进行编译诊断...
echo [信息] 显示详细编译信息...
echo.

dotnet build --configuration Debug --verbosity normal
set BUILD_RESULT=%errorlevel%

echo.
echo ================================================================================
echo [步骤 5/5] 诊断结果
echo ================================================================================

if %BUILD_RESULT% equ 0 (
    echo [✅] 编译成功！
    echo.
    echo 项目已经可以正常运行了，您可以：
    echo   - 运行 startup.bat 启动生产环境
    echo   - 运行 dev-start.bat 启动开发环境
    echo   - 在 Visual Studio 2022 中打开项目
) else (
    echo [❌] 编译仍有错误
    echo.
    echo 📋 常见编译错误解决方案：
    echo.
    echo 1. 缺少 using 语句：
    echo    - 在文件顶部添加: using LmyDigitalHuman.Models;
    echo.
    echo 2. 类型不匹配：
    echo    - 检查方法返回类型是否与接口定义一致
    echo    - 使用完全限定名称，如: Models.SpeechRecognitionResult
    echo.
    echo 3. 缺少属性：
    echo    - 检查模型类是否包含所需的属性
    echo    - 参考 UnifiedModels.cs 中的完整定义
    echo.
    echo 4. NuGet 包版本冲突：
    echo    - 检查 .csproj 文件中的包版本
    echo    - 尝试更新到兼容版本
    echo.
    echo 💡 建议：
    echo   - 在 Visual Studio 2022 中打开项目获得更好的错误提示
    echo   - 查看 CHANGELOG.md 了解已修复的问题
    echo   - 逐个文件检查和修复错误
)

echo.
cd ..

pause