@echo off
chcp 65001 >nul 2>&1
echo ========================================
echo 数字人系统 - 应用部署
echo ========================================
echo.

REM 检查Docker是否运行
docker info >nul 2>&1
if %errorLevel% neq 0 (
    echo ❌ Docker未运行！请先安装Docker Engine
    echo 运行: powershell -ExecutionPolicy Bypass -File setup-docker.ps1
    pause
    exit /b 1
)

echo ✅ Docker已就绪
echo.

REM 创建数据目录
echo 📁 创建数据目录...
if not exist "data" mkdir data
if not exist "data\templates" mkdir data\templates
if not exist "data\videos" mkdir data\videos
if not exist "data\temp" mkdir data\temp
if not exist "data\logs" mkdir data\logs

echo ✅ 数据目录创建完成
echo.

REM 构建和启动
echo 🔨 构建并启动应用...
docker-compose up --build -d

if %errorLevel% equ 0 (
    echo.
    echo ========================================
    echo 🎉 部署成功！
    echo ========================================
    echo.
    echo 🌐 访问地址:
    echo   - 主页: http://localhost:5000
    echo   - 测试页面: http://localhost:5000/digital-human-test.html
    echo   - API文档: http://localhost:5000/swagger
    echo.
    echo 📊 管理命令:
    echo   - 查看日志: docker-compose logs -f
    echo   - 停止服务: docker-compose down
    echo   - 重启服务: docker-compose restart
    echo.
) else (
    echo ❌ 部署失败！请检查日志
    docker-compose logs
)

pause