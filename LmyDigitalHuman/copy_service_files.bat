@echo off
chcp 65001 >nul
echo 📋 复制MuseTalk服务文件...

set "TARGET_DIR=F:\AI\DigitalHuman_Portable\MuseTalk"
set "SOURCE_FILE=%~dp0musetalk_service_portable.py"

if not exist "%TARGET_DIR%" (
    echo ❌ 目标目录不存在: %TARGET_DIR%
    echo 💡 请先运行 setup_portable_environment.bat
    pause
    exit /b 1
)

if not exist "%SOURCE_FILE%" (
    echo ❌ 源文件不存在: %SOURCE_FILE%
    pause
    exit /b 1
)

echo 📁 目标目录: %TARGET_DIR%
echo 📄 源文件: %SOURCE_FILE%

copy "%SOURCE_FILE%" "%TARGET_DIR%\musetalk_service.py" >nul
if %errorlevel% equ 0 (
    echo ✅ 服务文件复制成功
    echo 📍 位置: %TARGET_DIR%\musetalk_service.py
) else (
    echo ❌ 复制失败
)

echo.
pause