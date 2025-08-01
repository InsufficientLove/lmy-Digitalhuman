@echo off
chcp 65001 >nul 2>&1
echo ========================================
echo 服务器配置分析工具
echo ========================================
echo.
echo 此工具将分析您的服务器配置并提供定制化建议：
echo.
echo ✅ 检查 Hyper-V 状态和虚拟机使用情况
echo ✅ 分析服务器角色和资源
echo ✅ 提供针对性的 Docker 安装方案
echo ✅ 避免不必要的服务重启或配置变更
echo.
echo 按任意键开始分析...
pause >nul

echo.
echo 正在启动配置分析...
powershell -ExecutionPolicy Bypass -File "%~dp0analyze-server-config.ps1"

pause