@echo off
chcp 65001 >nul 2>&1
echo ================================================================================
echo                    Deploy to IIS with Virtual Environment
echo ================================================================================
echo.
echo This script will:
echo 1. Build and publish the .NET application
echo 2. Copy the virtual environment to publish directory
echo 3. Copy Python scripts and models
echo 4. Configure paths for IIS deployment
echo.

set /p publish_path="请输入发布路径 (例如: C:\test\publish): "
if "%publish_path%"=="" (
    echo 错误: 发布路径不能为空
    pause
    exit /b 1
)

echo.
echo [1/5] Building .NET application...
cd /d %~dp0
cd LmyDigitalHuman

dotnet publish -c Release -o "%publish_path%" --self-contained false
if %errorlevel% neq 0 (
    echo ❌ .NET发布失败
    pause
    exit /b 1
)

echo ✅ .NET应用发布完成

echo.
echo [2/5] Copying virtual environment...
if exist "venv_musetalk" (
    echo 复制虚拟环境到发布目录...
    xcopy "venv_musetalk" "%publish_path%\venv_musetalk" /E /I /Y /Q
    if %errorlevel% equ 0 (
        echo ✅ 虚拟环境复制完成
    ) else (
        echo ❌ 虚拟环境复制失败
        pause
        exit /b 1
    )
) else (
    echo ❌ 虚拟环境不存在，请先运行 setup-musetalk-basic.bat
    pause
    exit /b 1
)

echo.
echo [3/5] Copying Python scripts and models...
copy "musetalk_service_complete.py" "%publish_path%\" /Y
if exist "models" (
    xcopy "models" "%publish_path%\models" /E /I /Y /Q
    echo ✅ 模型文件复制完成
) else (
    echo ⚠️  模型目录不存在，请确保MuseTalk模型已下载
)

echo.
echo [4/5] Creating necessary directories...
if not exist "%publish_path%\temp" mkdir "%publish_path%\temp"
if not exist "%publish_path%\wwwroot\videos" mkdir "%publish_path%\wwwroot\videos"
if not exist "%publish_path%\wwwroot\templates" mkdir "%publish_path%\wwwroot\templates"

echo.
echo [5/5] Verifying deployment...
echo.
echo 检查关键文件:
if exist "%publish_path%\LmyDigitalHuman.exe" (
    echo ✅ .NET应用程序
) else (
    echo ❌ .NET应用程序缺失
)

if exist "%publish_path%\venv_musetalk\Scripts\python.exe" (
    echo ✅ Python虚拟环境
) else (
    echo ❌ Python虚拟环境缺失
)

if exist "%publish_path%\musetalk_service_complete.py" (
    echo ✅ MuseTalk Python脚本
) else (
    echo ❌ MuseTalk Python脚本缺失
)

echo.
echo 检查edge-tts可用性:
"%publish_path%\venv_musetalk\Scripts\python.exe" -m edge_tts --version >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ edge-tts可用
) else (
    echo ❌ edge-tts不可用
)

echo.
echo ================================================================================
echo IIS Deployment Complete
echo ================================================================================
echo.
echo 发布路径: %publish_path%
echo.
echo IIS配置建议:
echo 1. 应用程序池: .NET 8.0
echo 2. 物理路径: %publish_path%
echo 3. 确保IIS应用程序池有访问虚拟环境的权限
echo.
echo 环境变量配置:
echo PATH应该包含: C:\ffmpeg (系统FFmpeg)
echo.
echo 测试命令:
echo cd "%publish_path%"
echo venv_musetalk\Scripts\python.exe --version
echo venv_musetalk\Scripts\python.exe -m edge_tts --version
echo.
echo 如果遇到权限问题，请确保IIS应用程序池用户有以下权限:
echo - 读取和执行: %publish_path%
echo - 完全控制: %publish_path%\temp
echo - 完全控制: %publish_path%\wwwroot\videos
echo.
pause