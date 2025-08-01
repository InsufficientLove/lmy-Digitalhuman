@echo off
setlocal enabledelayedexpansion

echo ========================================
echo Windows Server 2019 环境检查工具
echo ========================================
echo.

set "ALL_GOOD=true"

echo [1] 检查 Python 环境...
python --version >nul 2>&1
if %errorLevel% equ 0 (
    for /f "tokens=2" %%i in ('python --version 2^>^&1') do (
        echo ✅ Python 版本: %%i
    )
    
    REM 检查 edge-tts
    python -c "import edge_tts; print('edge-tts 版本:', edge_tts.__version__)" >nul 2>&1
    if %errorLevel% equ 0 (
        echo ✅ edge-tts 已安装
    ) else (
        echo ❌ edge-tts 未安装
        echo    解决方案: pip install edge-tts
        set "ALL_GOOD=false"
    )
) else (
    echo ❌ Python 未安装或未添加到PATH
    set "ALL_GOOD=false"
)

echo.
echo [2] 检查 .NET 环境...
dotnet --version >nul 2>&1
if %errorLevel% equ 0 (
    for /f %%i in ('dotnet --version 2^>^&1') do (
        echo ✅ .NET SDK 版本: %%i
    )
) else (
    echo ❌ .NET SDK 未安装
    set "ALL_GOOD=false"
)

echo.
echo [3] 检查 Visual Studio 2022...
if exist "C:\Program Files\Microsoft Visual Studio\2022\Professional\Common7\IDE\devenv.exe" (
    echo ✅ Visual Studio 2022 Professional 已安装
) else if exist "C:\Program Files\Microsoft Visual Studio\2022\Community\Common7\IDE\devenv.exe" (
    echo ✅ Visual Studio 2022 Community 已安装
) else if exist "C:\Program Files\Microsoft Visual Studio\2022\Enterprise\Common7\IDE\devenv.exe" (
    echo ✅ Visual Studio 2022 Enterprise 已安装
) else (
    echo ⚠️  Visual Studio 2022 路径未找到（可能安装在其他位置）
)

echo.
echo [4] 检查 Ollama 服务...
curl -f http://localhost:11434/api/version >nul 2>&1
if %errorLevel% equ 0 (
    echo ✅ Ollama 服务正在运行
) else (
    echo ❌ Ollama 服务未运行
    echo    请启动 Ollama 或检查端口 11434
    set "ALL_GOOD=false"
)

echo.
echo [5] 检查 Docker 环境...
docker --version >nul 2>&1
if %errorLevel% equ 0 (
    for /f "tokens=3" %%i in ('docker --version 2^>^&1') do (
        echo ✅ Docker 版本: %%i
    )
    
    REM 检查 Docker 是否运行
    docker info >nul 2>&1
    if %errorLevel% equ 0 (
        echo ✅ Docker 服务正在运行
    ) else (
        echo ❌ Docker 服务未运行
        echo    请启动 Docker Desktop
        set "ALL_GOOD=false"
    )
) else (
    echo ❌ Docker 未安装
    echo    请安装 Docker Desktop for Windows
    set "ALL_GOOD=false"
)

echo.
echo [6] 检查项目目录结构...
if exist "LmyDigitalHuman\LmyDigitalHuman.csproj" (
    echo ✅ 主项目文件存在
) else (
    echo ❌ 未找到 LmyDigitalHuman.csproj
    set "ALL_GOOD=false"
)

if exist "docker-compose.yml" (
    echo ✅ Docker Compose 配置存在
) else (
    echo ❌ 未找到 docker-compose.yml
    set "ALL_GOOD=false"
)

if exist "LmyDigitalHuman\musetalk_service_complete.py" (
    echo ✅ Python 脚本存在
) else (
    echo ❌ 未找到 musetalk_service_complete.py
    set "ALL_GOOD=false"
)

echo.
echo [7] 测试 Python 包导入...
python -c "
try:
    import edge_tts
    print('✅ edge_tts 导入成功')
except ImportError as e:
    print('❌ edge_tts 导入失败:', e)

try:
    import requests
    print('✅ requests 导入成功')
except ImportError as e:
    print('❌ requests 导入失败:', e)
"

echo.
echo ========================================
echo 环境检查完成
echo ========================================

if "%ALL_GOOD%"=="true" (
    echo.
    echo 🎉 环境检查通过！
    echo.
    echo 📋 下一步操作：
    echo    VS调试: 在 Visual Studio 中打开解决方案并按F5运行
    echo    Docker部署: 运行 deploy-docker.bat
    echo.
    echo 🌐 服务地址：
    echo    VS调试模式: http://localhost:5000 或 https://localhost:5001
    echo    Docker模式: http://localhost:5000 (通过容器)
    echo.
) else (
    echo.
    echo ❌ 环境检查发现问题，请解决上述标记为❌的项目
    echo.
    echo 🔧 常见解决方案：
    echo    1. 安装 edge-tts: pip install edge-tts
    echo    2. 启动 Ollama 服务
    echo    3. 安装 Docker Desktop for Windows
    echo    4. 确保在正确的项目目录中运行此脚本
    echo.
)

echo 💡 提示：
echo    - VS调试使用系统Python环境
echo    - Docker部署使用容器内Python环境
echo    - 两种模式可以并存，互不干扰
echo.

pause