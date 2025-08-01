@echo off
chcp 65001 >nul 2>&1
echo ========================================
echo 数字人系统 - 本地运行
echo ========================================
echo.

echo 信息: 检查.NET环境...
dotnet --version >nul 2>&1
if %errorLevel% neq 0 (
    echo 错误: .NET SDK未安装
    echo 请从 https://dotnet.microsoft.com/download 下载安装
    pause
    exit /b 1
)
echo 成功: .NET环境就绪
echo.

echo 信息: 检查Python环境...
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo 错误: Python未安装或不在PATH中
    pause
    exit /b 1
)
echo 成功: Python环境就绪
echo.

echo 信息: 检查Ollama服务...
curl -s http://localhost:11434/api/version >nul 2>&1
if %errorLevel% neq 0 (
    echo 警告: Ollama服务未运行
    echo 请运行: ollama serve
    echo 继续运行应用（部分功能可能不可用）
) else (
    echo 成功: Ollama服务运行中
)
echo.

echo 信息: 安装Python依赖...
python -m pip install -r requirements.txt
echo.

echo 信息: 创建数据目录...
if not exist "data" mkdir data
if not exist "data\templates" mkdir data\templates
if not exist "data\videos" mkdir data\videos
if not exist "data\temp" mkdir data\temp
if not exist "data\logs" mkdir data\logs
if not exist "LmyDigitalHuman\wwwroot\templates" mkdir LmyDigitalHuman\wwwroot\templates
if not exist "LmyDigitalHuman\wwwroot\videos" mkdir LmyDigitalHuman\wwwroot\videos
echo 成功: 数据目录创建完成
echo.

echo 信息: 启动应用...
cd LmyDigitalHuman
echo.
echo ========================================
echo 应用启动中...
echo 访问地址: http://localhost:5000
echo 测试页面: http://localhost:5000/digital-human-test.html
echo 按 Ctrl+C 停止应用
echo ========================================
echo.

dotnet run --urls "http://localhost:5000"