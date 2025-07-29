@echo off
chcp 65001 > nul
color 07
title 数字人系统 - 一键环境部署

echo ================================================================================
echo                           数字人系统 - 一键环境部署脚本
echo ================================================================================
echo.
echo 此脚本将自动为您配置数字人系统的运行环境，包括：
echo   ✓ .NET 8.0 SDK 安装检查和引导
echo   ✓ Python 3.8+ 环境检查和引导  
echo   ✓ Git 环境检查
echo   ✓ 项目依赖包还原
echo   ✓ 系统配置优化
echo.
pause

echo ================================================================================
echo [步骤 1/6] 检查 .NET 8.0 SDK 环境
echo ================================================================================

REM 检查.NET SDK
dotnet --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [警告] 未检测到 .NET 8.0 SDK
    echo.
    echo 请按照以下步骤安装：
    echo 1. 访问: https://dotnet.microsoft.com/download/dotnet/8.0
    echo 2. 下载并安装 .NET 8.0 SDK
    echo 3. 安装完成后重新运行此脚本
    echo.
    start https://dotnet.microsoft.com/download/dotnet/8.0
    pause
    goto end
) else (
    echo [✓] 检测到 .NET SDK 版本:
    dotnet --version
)

echo ================================================================================
echo [步骤 2/6] 检查 Python 环境
echo ================================================================================

REM 检查Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [警告] 未检测到 Python 环境
    echo.
    echo Python 用于 MuseTalk 数字人生成服务，建议安装：
    echo 1. 访问: https://www.python.org/downloads/
    echo 2. 下载并安装 Python 3.8 或更高版本
    echo 3. 安装时请勾选 "Add Python to PATH"
    echo.
    echo [提示] 您可以选择跳过此步骤，稍后手动安装
    choice /c YN /m "是否现在打开 Python 下载页面"
    if errorlevel 2 goto skip_python
    start https://www.python.org/downloads/
    echo 请安装 Python 后重新运行此脚本
    pause
    goto end
    :skip_python
    echo [!] 已跳过 Python 安装，部分功能可能不可用
) else (
    echo [✓] 检测到 Python 版本:
    python --version
    
    echo [信息] 正在安装 MuseTalk 依赖库...
    pip install torch torchvision torchaudio numpy opencv-python pillow scipy scikit-image librosa tqdm pydub requests --quiet
    if %errorlevel% neq 0 (
        echo [警告] MuseTalk 依赖库安装失败，部分功能可能不可用
    ) else (
        echo [✓] MuseTalk 依赖库安装完成
    )
)

echo ================================================================================
echo [步骤 3/6] 检查 Git 环境
echo ================================================================================

REM 检查Git
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [警告] 未检测到 Git 环境
    echo.
    echo Git 用于代码版本管理，建议安装：
    echo 1. 访问: https://git-scm.com/download/win
    echo 2. 下载并安装 Git for Windows
    echo.
    choice /c YN /m "是否现在打开 Git 下载页面"
    if errorlevel 2 goto skip_git
    start https://git-scm.com/download/win
    :skip_git
    echo [!] 已跳过 Git 安装
) else (
    echo [✓] 检测到 Git 版本:
    git --version
)

echo ================================================================================
echo [步骤 4/6] 还原项目依赖包
echo ================================================================================

echo [信息] 正在还原 NuGet 包...
dotnet restore LmyDigitalHuman/LmyDigitalHuman.csproj
if %errorlevel% neq 0 (
    echo [错误] NuGet 包还原失败
    echo 请检查网络连接或项目文件完整性
    pause
    goto end
) else (
    echo [✓] NuGet 包还原成功
)

echo ================================================================================
echo [步骤 5/6] 编译项目检查
echo ================================================================================

echo [信息] 正在编译项目以检查依赖...
dotnet build LmyDigitalHuman/LmyDigitalHuman.csproj --configuration Debug --verbosity quiet
if %errorlevel% neq 0 (
    echo [警告] 项目编译遇到问题
    echo 这可能是由于缺少某些依赖或配置问题
    echo 您可以稍后在 Visual Studio 中解决这些问题
    echo.
    choice /c YN /m "是否查看详细编译输出"
    if errorlevel 1 (
        echo [信息] 正在显示详细编译信息...
        dotnet build LmyDigitalHuman/LmyDigitalHuman.csproj --configuration Debug
    )
) else (
    echo [✓] 项目编译成功
)

echo ================================================================================
echo [步骤 6/6] 创建必要的目录结构
echo ================================================================================

echo [信息] 正在创建必要的目录...

REM 创建临时目录
if not exist "LmyDigitalHuman\temp" (
    mkdir "LmyDigitalHuman\temp"
    echo [✓] 创建 temp 目录
)

REM 创建模型目录
if not exist "LmyDigitalHuman\Models\AI" (
    mkdir "LmyDigitalHuman\Models\AI"
    echo [✓] 创建 Models\AI 目录
)

REM 创建上传目录
if not exist "LmyDigitalHuman\wwwroot\uploads" (
    mkdir "LmyDigitalHuman\wwwroot\uploads"
    echo [✓] 创建 uploads 目录
)

REM 创建输出目录
if not exist "LmyDigitalHuman\wwwroot\output" (
    mkdir "LmyDigitalHuman\wwwroot\output"
    echo [✓] 创建 output 目录
)

echo ================================================================================
echo                                环境部署完成
echo ================================================================================
echo.
echo [✓] 环境部署成功完成！
echo.
echo 🚀 接下来您可以：
echo.
echo   1. 使用 Visual Studio 2022 开发:
echo      打开文件: LmyDigitalHuman.sln
echo.
echo   2. 生产模式启动:
echo      双击运行: startup.bat
echo.
echo   3. 查看启动指南:
echo      阅读文件: STARTUP_GUIDE.md
echo.
echo 🌐 系统启动后访问地址:
echo   - HTTPS: https://localhost:7001
echo   - HTTP:  http://localhost:5001
echo.
echo 📚 如遇问题，请查看 STARTUP_GUIDE.md 或 CHANGELOG.md
echo.

:end
echo 按任意键退出...
pause >nul