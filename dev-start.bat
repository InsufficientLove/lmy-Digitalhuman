@echo off
chcp 65001 > nul
echo ========================================
echo    数字人系统 - 开发模式启动
echo ========================================
echo.

echo [信息] 开发模式启动中...
echo [提示] 开发模式支持热重载，代码修改后自动重启
echo [提示] 系统启动后请访问: https://localhost:7001 或 http://localhost:5001
echo [提示] 按 Ctrl+C 可停止服务
echo.

cd LmyDigitalHuman
dotnet watch run --urls "https://localhost:7001;http://localhost:5001"

pause