@echo off
chcp 65001 >nul
echo 🚀 启动增强MuseTalk服务 V4.0
echo ===============================

:: 设置工作目录
cd /d "%~dp0"

:: 检查Python虚拟环境
set VENV_PATH=venv_musetalk\Scripts\python.exe
if exist "%VENV_PATH%" (
    echo ✅ 找到虚拟环境: %VENV_PATH%
    set PYTHON_PATH=%VENV_PATH%
) else (
    echo ⚠️ 虚拟环境不存在，使用系统Python
    set PYTHON_PATH=python
)

:: 检查服务脚本
set SERVICE_SCRIPT=MuseTalk\persistent_musetalk_service.py
if not exist "%SERVICE_SCRIPT%" (
    echo ❌ 服务脚本不存在: %SERVICE_SCRIPT%
    echo 请确保增强MuseTalk系统已正确部署
    pause
    exit /b 1
)

:: 显示配置信息
echo.
echo 📋 配置信息:
echo    Python路径: %PYTHON_PATH%
echo    服务脚本: %SERVICE_SCRIPT%
echo    监听端口: 58080
echo    计算设备: cuda:0
echo.

:: 启动持久化服务
echo 🚀 正在启动持久化MuseTalk服务...
echo 💡 按 Ctrl+C 停止服务
echo.

"%PYTHON_PATH%" "%SERVICE_SCRIPT%" --host 127.0.0.1 --port 58080 --device cuda:0

echo.
echo 🔌 服务已停止
pause