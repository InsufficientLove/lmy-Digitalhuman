@echo off
chcp 65001 >nul 2>&1
echo ========================================
echo Docker 状态测试
echo ========================================
echo.

echo 测试1: 执行 docker info
docker info >nul 2>&1
echo 错误代码: %errorLevel%

if %errorLevel% neq 0 (
    echo 结果: Docker检查失败
) else (
    echo 结果: Docker检查成功
)

echo.
echo 测试2: 执行 docker version
docker version >nul 2>&1
echo 错误代码: %errorLevel%

echo.
echo 测试3: 显示 docker info 详细输出
docker info

echo.
echo 测试4: 显示当前目录
echo 当前目录: %CD%

echo.
echo 测试5: 检查 docker-compose.yml 是否存在
if exist "docker-compose.yml" (
    echo docker-compose.yml 文件存在
) else (
    echo docker-compose.yml 文件不存在
)

echo.
pause