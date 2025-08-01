@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion

echo ================================
echo 数字人系统 - Docker 部署脚本 (Windows)
echo ================================
echo.

REM 检查Docker是否安装
docker --version >nul 2>&1
if %errorLevel% neq 0 (
    echo ❌ Docker 未安装！请先安装Docker Desktop
    echo 下载地址: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

REM 检查Docker Compose
docker-compose --version >nul 2>&1
if %errorLevel% neq 0 (
    docker compose version >nul 2>&1
    if %errorLevel% neq 0 (
        echo ❌ Docker Compose 未安装！
        pause
        exit /b 1
    )
)

REM 获取部署模式
set DEPLOY_MODE=%1
if "%DEPLOY_MODE%"=="" set DEPLOY_MODE=development

echo 🚀 部署模式: %DEPLOY_MODE%
echo.

REM 创建必要的目录
echo 📁 创建数据目录...
if not exist "data" mkdir data
if not exist "data\templates" mkdir data\templates
if not exist "data\videos" mkdir data\videos
if not exist "data\temp" mkdir data\temp
if not exist "data\logs" mkdir data\logs
if not exist "models" mkdir models
if not exist "nginx" mkdir nginx

echo ✅ 目录创建完成
echo.

REM 构建镜像
echo 🔨 构建Docker镜像...
docker-compose build --no-cache
if %errorLevel% neq 0 (
    echo ❌ 镜像构建失败！
    pause
    exit /b 1
)

echo ✅ 镜像构建成功
echo.

REM 启动服务
echo 🚀 启动服务...

if "%DEPLOY_MODE%"=="production" (
    echo 🌐 生产模式 - 启动完整服务栈（包含Nginx）
    docker-compose --profile production up -d
) else (
    echo 🔧 开发模式 - 仅启动核心服务
    docker-compose up -d digitalhuman ollama
)

if %errorLevel% neq 0 (
    echo ❌ 服务启动失败！
    pause
    exit /b 1
)

REM 等待服务启动
echo ⏳ 等待服务启动...
timeout /t 10 /nobreak >nul

REM 健康检查
echo 🔍 检查服务状态...
docker-compose ps

echo.
echo 🩺 健康检查...

REM 检查数字人服务
set "SERVICE_READY=false"
for /l %%i in (1,1,10) do (
    curl -f http://localhost:5000/api/diagnostics/system-info >nul 2>&1
    if !errorLevel! equ 0 (
        echo ✅ 数字人服务正常运行
        set "SERVICE_READY=true"
        goto :service_check_done
    )
    echo ⏳ 等待服务响应... (%%i/10)
    timeout /t 3 /nobreak >nul
)

:service_check_done
if "%SERVICE_READY%"=="false" (
    echo ⚠️  数字人服务可能未完全启动，请检查日志
)

REM 检查Ollama服务
curl -f http://localhost:11434/api/version >nul 2>&1
if %errorLevel% equ 0 (
    echo ✅ Ollama服务正常运行
) else (
    echo ⚠️  Ollama服务可能未完全启动，请检查日志
)

echo.
echo ================================
echo 🎉 部署完成！
echo ================================
echo.
echo 服务地址：
echo   数字人API: http://localhost:5000
echo   Swagger文档: http://localhost:5000/swagger
echo   Ollama API: http://localhost:11434
echo   系统诊断: http://localhost:5000/api/diagnostics/python-environments

if "%DEPLOY_MODE%"=="production" (
    echo   Web界面: http://localhost (通过Nginx)
)

echo.
echo 常用命令：
echo   查看日志: docker-compose logs -f digitalhuman
echo   停止服务: docker-compose down
echo   重启服务: docker-compose restart
echo   查看状态: docker-compose ps
echo.

echo 下一步操作：
echo 1. 访问 http://localhost:5000/api/diagnostics/python-environments 检查Python环境
echo 2. 确保Ollama已下载所需模型: docker exec ollama-service ollama pull qwen2.5vl:7b
echo 3. 上传数字人模板到 .\data\templates\ 目录
echo 4. 测试API接口功能
echo.

echo 如需帮助，请查看日志:
echo   docker-compose logs digitalhuman
echo   docker-compose logs ollama
echo.
pause