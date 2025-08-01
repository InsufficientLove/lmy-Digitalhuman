@echo off
setlocal enabledelayedexpansion

echo ================================
echo 数字人系统 - Python环境部署脚本
echo ================================
echo.

REM 检查是否以管理员身份运行
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [警告] 建议以管理员身份运行此脚本以确保权限充足
    echo.
)

REM 检查Python是否安装
echo [1/7] 检查Python环境...
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [错误] 未找到Python！请先安装Python 3.8或更高版本
    echo 下载地址: https://python.org/downloads/
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [√] 发现Python版本: %PYTHON_VERSION%

REM 检查pip是否可用
echo [2/7] 检查pip包管理器...
python -m pip --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [错误] pip不可用！请检查Python安装
    pause
    exit /b 1
)
echo [√] pip可用

REM 删除旧的虚拟环境
echo [3/7] 清理旧环境...
if exist "venv_musetalk" (
    echo 删除旧的虚拟环境: venv_musetalk
    rmdir /s /q venv_musetalk
    if exist "venv_musetalk" (
        echo [警告] 无法完全删除旧环境，可能有文件被占用
        echo 请手动删除 venv_musetalk 目录后重试
        pause
        exit /b 1
    )
)
echo [√] 环境清理完成

REM 创建新的虚拟环境
echo [4/7] 创建虚拟环境...
python -m venv venv_musetalk
if %errorLevel% neq 0 (
    echo [错误] 创建虚拟环境失败！
    pause
    exit /b 1
)
echo [√] 虚拟环境创建成功

REM 激活虚拟环境
echo [5/7] 激活虚拟环境...
call venv_musetalk\Scripts\activate.bat
if %errorLevel% neq 0 (
    echo [错误] 激活虚拟环境失败！
    pause
    exit /b 1
)
echo [√] 虚拟环境已激活

REM 升级pip
echo [6/7] 升级pip...
python -m pip install --upgrade pip
if %errorLevel% neq 0 (
    echo [警告] pip升级失败，继续使用当前版本
) else (
    echo [√] pip升级完成
)

REM 安装必需的包
echo [7/7] 安装Python包...
echo.

echo 安装 edge-tts...
pip install edge-tts
if %errorLevel% neq 0 (
    echo [错误] edge-tts安装失败！
    goto :error
)
echo [√] edge-tts安装成功

echo.
echo 安装 PyTorch（CPU版本）...
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
if %errorLevel% neq 0 (
    echo [错误] PyTorch安装失败！
    goto :error
)
echo [√] PyTorch安装成功

REM 检查是否有requirements.txt文件
if exist "requirements.txt" (
    echo.
    echo 安装requirements.txt中的依赖...
    pip install -r requirements.txt
    if %errorLevel% neq 0 (
        echo [警告] requirements.txt中部分包安装失败
    ) else (
        echo [√] requirements.txt安装完成
    )
) else (
    echo [信息] 未找到requirements.txt文件，跳过
)

REM 安装其他常用包
echo.
echo 安装其他必需包...
pip install numpy scipy pillow requests
if %errorLevel% neq 0 (
    echo [警告] 部分常用包安装失败
)

REM 验证安装
echo.
echo ================================
echo 验证安装结果...
echo ================================

python -c "import edge_tts; print('✓ edge-tts 可用')" 2>nul
if %errorLevel% neq 0 (
    echo [错误] edge-tts无法导入！
    goto :error
)

python -c "import torch; print('✓ PyTorch 可用，版本:', torch.__version__)" 2>nul
if %errorLevel% neq 0 (
    echo [错误] PyTorch无法导入！
    goto :error
)

REM 生成包列表
echo.
echo 生成包列表...
pip freeze > requirements_generated.txt
echo [√] 包列表已保存到 requirements_generated.txt

REM 显示环境信息
echo.
echo ================================
echo 环境信息
echo ================================
echo Python路径: %cd%\venv_musetalk\Scripts\python.exe
echo 虚拟环境路径: %cd%\venv_musetalk
echo.

echo ================================
echo 部署成功！
echo ================================
echo.
echo 下一步操作：
echo 1. 确保应用程序配置文件中的Python路径正确
echo 2. 配置IIS应用程序池权限
echo 3. 重启应用程序服务
echo.
echo 配置示例（appsettings.Production.json）：
echo {
echo   "DigitalHuman": {
echo     "EdgeTTS": {
echo       "PythonPath": "venv_musetalk/Scripts/python.exe"
echo     }
echo   }
echo }
echo.
pause
goto :end

:error
echo.
echo ================================
echo 部署失败！
echo ================================
echo.
echo 请检查以下事项：
echo 1. 网络连接是否正常
echo 2. 是否有足够的磁盘空间
echo 3. 防火墙是否阻止了Python包下载
echo 4. 是否以管理员身份运行
echo.
echo 如需帮助，请查看 DEPLOYMENT.md 文件或联系技术支持
echo.
pause
exit /b 1

:end
echo 脚本执行完成