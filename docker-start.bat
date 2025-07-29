@echo off
chcp 65001 > nul
echo ========================================
echo    数字人系统 - Docker容器启动
echo ========================================
echo.

REM 检查Docker是否安装
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到Docker，请先安装Docker Desktop
    echo 下载地址: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

echo [信息] 检测到Docker版本:
docker --version

echo.
echo [信息] 正在构建Docker镜像...
docker build -t lmy-digital-human .
if %errorlevel% neq 0 (
    echo [错误] Docker镜像构建失败
    pause
    exit /b 1
)

echo.
echo [信息] 正在启动Docker容器...
echo [提示] 系统启动后请访问: http://localhost:8080
echo [提示] 按 Ctrl+C 可停止容器
echo.

docker run -it --rm -p 8080:8080 --name lmy-digital-human-container lmy-digital-human

pause