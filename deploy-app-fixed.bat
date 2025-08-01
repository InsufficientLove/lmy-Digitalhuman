@echo off
chcp 65001 >nul 2>&1
echo ========================================
echo 数字人系统 - 应用部署
echo ========================================
echo.

echo 正在检查Docker状态...
docker info >nul 2>&1
set DOCKER_CHECK_RESULT=%errorLevel%

echo Docker检查错误代码: %DOCKER_CHECK_RESULT%

if %DOCKER_CHECK_RESULT% neq 0 (
    echo 错误: Docker未运行或无法访问
    echo 请检查Docker服务状态: sc query docker
    echo 或尝试重启Docker服务: sc stop docker && sc start docker
    pause
    exit /b 1
)

echo 成功: Docker已就绪
echo.

echo 信息: 创建数据目录...
if not exist "data" mkdir data
if not exist "data\templates" mkdir data\templates
if not exist "data\videos" mkdir data\videos
if not exist "data\temp" mkdir data\temp
if not exist "data\logs" mkdir data\logs
echo 成功: 数据目录创建完成
echo.

echo 信息: 检查docker-compose.yml文件...
if not exist "docker-compose.yml" (
    echo 错误: docker-compose.yml文件不存在
    echo 请确保在项目根目录运行此脚本
    pause
    exit /b 1
)
echo 成功: docker-compose.yml文件存在
echo.

echo 信息: 构建并启动应用...
docker-compose up --build -d

if %errorLevel% equ 0 (
    echo.
    echo ========================================
    echo 成功: 部署成功！
    echo ========================================
    echo.
    echo 访问地址:
    echo   - 主页: http://localhost:5000
    echo   - 测试页面: http://localhost:5000/digital-human-test.html
    echo   - API文档: http://localhost:5000/swagger
    echo.
    echo 管理命令:
    echo   - 查看日志: docker-compose logs -f
    echo   - 停止服务: docker-compose down
    echo   - 重启服务: docker-compose restart
    echo.
) else (
    echo 错误: 部署失败！
    echo 运行以下命令查看详细错误:
    echo docker-compose logs
)

pause