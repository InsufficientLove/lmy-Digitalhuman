@echo off
chcp 65001 >nul 2>&1
echo ========================================
echo 数字人系统 - VS调试环境检查
echo ========================================
echo.

echo 信息: 检查虚拟环境...
if exist "venv_musetalk\Scripts\python.exe" (
    echo 成功: 虚拟环境已就绪 - venv_musetalk
    venv_musetalk\Scripts\python.exe --version
) else (
    echo 警告: 虚拟环境不存在，将使用系统Python
    python --version 2>nul || echo 错误: Python未安装
)
echo.

echo 信息: 检查Ollama服务...
curl -s http://localhost:11434/api/version >nul 2>&1
if %errorLevel% equ 0 (
    echo 成功: Ollama服务运行中
) else (
    echo 警告: Ollama服务未运行
    echo 请在另一个窗口运行: ollama serve
)
echo.

echo 信息: 检查CUDA环境...
nvidia-smi >nul 2>&1
if %errorLevel% equ 0 (
    echo 成功: NVIDIA GPU驱动已安装
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader,nounits
) else (
    echo 警告: 未检测到NVIDIA GPU或驱动
)
echo.

echo 信息: 创建必要目录...
if not exist "LmyDigitalHuman\temp" mkdir LmyDigitalHuman\temp
if not exist "LmyDigitalHuman\wwwroot\templates" mkdir LmyDigitalHuman\wwwroot\templates
if not exist "LmyDigitalHuman\wwwroot\videos" mkdir LmyDigitalHuman\wwwroot\videos
if not exist "models" mkdir models
echo 成功: 目录结构已就绪
echo.

echo ========================================
echo VS调试环境检查完成
echo ========================================
echo.
echo 优化配置:
echo - 端口: http://localhost:5000
echo - 测试页面: http://localhost:5000/digital-human-test.html
echo - 虚拟环境: venv_musetalk (优先)
echo - GPU加速: 已启用 (Whisper + MuseTalk)
echo - 实时延迟目标: 150ms
echo - 批处理大小: 商用8, 实时4
echo.
echo 现在可以在VS2022中按F5启动调试！
echo.
pause