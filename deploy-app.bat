@echo off
chcp 65001 >nul 2>&1
echo ========================================
echo 数字人系统 - 应用部署
echo ========================================
echo.

REM 检查Docker是否运行
docker info >nul 2>&1
if %errorLevel% neq 0 (
    echo 错误: Docker未运行！请先手动安装Docker Engine
    echo 参考README中的手动安装步骤
    pause
    exit /b 1
)

echo 成功: Docker已就绪
echo.

REM 创建数据目录
echo 信息: 创建数据目录...
if not exist "data" mkdir data
if not exist "data\templates" mkdir data\templates
if not exist "data\videos" mkdir data\videos
if not exist "data\temp" mkdir data\temp
if not exist "data\logs" mkdir data\logs

echo 成功: 数据目录创建完成
echo.

REM 配置Docker镜像源（解决网络超时问题）
echo 信息: 配置Docker镜像源...
if not exist "%USERPROFILE%\.docker" mkdir "%USERPROFILE%\.docker"
echo {> "%USERPROFILE%\.docker\daemon.json"
echo   "registry-mirrors": [>> "%USERPROFILE%\.docker\daemon.json"
echo     "https://mirror.ccs.tencentyun.com",>> "%USERPROFILE%\.docker\daemon.json"
echo     "https://registry.docker-cn.com">> "%USERPROFILE%\.docker\daemon.json"
echo   ]>> "%USERPROFILE%\.docker\daemon.json"
echo }>> "%USERPROFILE%\.docker\daemon.json"

REM 重启Docker服务以应用镜像源
echo 信息: 重启Docker服务...
sc stop docker >nul 2>&1
timeout /t 3 >nul
sc start docker >nul 2>&1
timeout /t 5 >nul

REM 构建和启动
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
    echo 错误: 部署失败！请检查日志
    echo 运行以下命令查看详细错误:
    echo docker-compose logs
)

pause