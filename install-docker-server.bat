@echo off
chcp 65001 >nul 2>&1
echo ========================================
echo Windows Server Docker Engine 安装
echo ========================================
echo.
echo 注意：此脚本将以管理员权限启动PowerShell
echo Docker Desktop 不支持 Windows Server
echo 我们将安装 Docker Engine + Docker Compose
echo.
echo 按任意键继续，或关闭窗口取消...
pause >nul

echo.
echo 正在启动PowerShell安装脚本...
powershell -ExecutionPolicy Bypass -File "%~dp0install-docker-server.ps1"

echo.
echo 安装完成！请重新打开命令提示符以刷新PATH环境变量
pause