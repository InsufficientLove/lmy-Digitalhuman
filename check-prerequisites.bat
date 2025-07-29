@echo off
chcp 65001 >nul
echo ================================================================================
echo                🔍 商用级环境先决条件检查
echo ================================================================================
echo.
echo 此脚本将检查部署4GPU商用级数字人系统所需的所有先决条件
echo.
pause

echo ================================================================================
echo [步骤 1/8] 基础软件环境检查
echo ================================================================================

echo [1.1] 检查Python版本...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [❌] Python未安装
    echo [📝] 需要: Python 3.10.11+
    echo [💾] 下载: https://www.python.org/downloads/
    set MISSING_DEPS=1
) else (
    for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
    echo [✅] Python版本: %PYTHON_VERSION%
    
    python -c "import sys; exit(0 if sys.version_info >= (3, 10, 11) else 1)" 2>nul
    if %errorlevel% neq 0 (
        echo [⚠️] Python版本可能过低，建议3.10.11+
    )
)

echo [1.2] 检查pip版本...
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [❌] pip未安装或不可用
    set MISSING_DEPS=1
) else (
    for /f "tokens=2" %%i in ('pip --version 2^>^&1') do set PIP_VERSION=%%i
    echo [✅] pip版本: %PIP_VERSION%
)

echo [1.3] 检查Git...
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [❌] Git未安装
    echo [📝] 需要: Git (用于下载模型)
    echo [💾] 下载: https://git-scm.com/
    set MISSING_DEPS=1
) else (
    for /f "tokens=3" %%i in ('git --version 2^>^&1') do set GIT_VERSION=%%i
    echo [✅] Git版本: %GIT_VERSION%
)

echo [1.4] 检查.NET SDK...
dotnet --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [❌] .NET SDK未安装
    echo [📝] 需要: .NET 8.0 SDK
    echo [💾] 下载: https://dotnet.microsoft.com/download/dotnet/8.0
    set MISSING_DEPS=1
) else (
    for /f %%i in ('dotnet --version 2^>^&1') do set DOTNET_VERSION=%%i
    echo [✅] .NET版本: %DOTNET_VERSION%
)

echo ================================================================================
echo [步骤 2/8] CUDA环境检查
echo ================================================================================

echo [2.1] 检查CUDA版本...
nvcc --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [❌] CUDA未安装或nvcc不可用
    echo [📝] 需要: CUDA 12.1+
    echo [💾] 下载: https://developer.nvidia.com/cuda-12-1-0-download-archive
    set MISSING_DEPS=1
) else (
    for /f "tokens=6 delims=, " %%i in ('nvcc --version ^| findstr "release"') do set CUDA_VERSION=%%i
    echo [✅] CUDA版本: %CUDA_VERSION%
    
    echo %CUDA_VERSION% | findstr "12.1" >nul
    if %errorlevel% neq 0 (
        echo [⚠️] 建议使用CUDA 12.1以获得最佳性能
    )
)

echo [2.2] 检查NVIDIA驱动...
nvidia-smi >nul 2>&1
if %errorlevel% neq 0 (
    echo [❌] NVIDIA驱动未安装或GPU不可用
    echo [📝] 需要: NVIDIA驱动 535.0+
    set MISSING_DEPS=1
) else (
    echo [✅] NVIDIA驱动可用
    nvidia-smi --query-gpu=driver_version --format=csv,noheader,nounits | head -1 > temp_driver.txt 2>nul
    if exist temp_driver.txt (
        set /p DRIVER_VERSION=<temp_driver.txt
        echo [📊] 驱动版本: %DRIVER_VERSION%
        del temp_driver.txt
    )
)

echo [2.3] 检查GPU配置...
nvidia-smi --list-gpus >nul 2>&1
if %errorlevel% equ 0 (
    nvidia-smi --list-gpus | find /c "GPU" > temp_gpu_count.txt
    set /p GPU_COUNT=<temp_gpu_count.txt
    del temp_gpu_count.txt
    echo [📊] 检测到 %GPU_COUNT% 张GPU
    
    if %GPU_COUNT% GEQ 4 (
        echo [✅] GPU数量满足4GPU商用要求
    ) else (
        echo [⚠️] GPU数量少于4张，将使用单GPU模式
    )
    
    echo [📊] GPU详情:
    nvidia-smi --query-gpu=index,name,memory.total --format=csv,noheader
) else (
    echo [❌] 无法获取GPU信息
    set MISSING_DEPS=1
)

echo ================================================================================
echo [步骤 3/8] 系统资源检查
echo ================================================================================

echo [3.1] 检查系统内存...
for /f "skip=1 tokens=4" %%i in ('wmic OS get TotalVisibleMemorySize /value') do (
    if not "%%i"=="" (
        set /a TOTAL_RAM=%%i/1024
        echo [📊] 系统内存: %TOTAL_RAM%MB
        
        if %TOTAL_RAM% LSS 16384 (
            echo [⚠️] 内存少于16GB，可能影响性能
        ) else if %TOTAL_RAM% LSS 32768 (
            echo [✅] 内存充足 (建议32GB+以获得最佳性能)
        ) else (
            echo [✅] 内存充足，满足商用要求
        )
    )
)

echo [3.2] 检查磁盘空间...
for /f "tokens=3" %%i in ('dir /-c ^| findstr "bytes free"') do (
    set DISK_FREE=%%i
    echo [📊] 可用磁盘空间: %DISK_FREE% bytes
)

REM 简单检查是否有足够空间 (至少100GB)
dir /-c | findstr "bytes free" | findstr /r "[0-9][0-9],[0-9][0-9][0-9],[0-9][0-9][0-9],[0-9][0-9][0-9]" >nul
if %errorlevel% equ 0 (
    echo [✅] 磁盘空间充足
) else (
    echo [⚠️] 磁盘空间可能不足，建议至少100GB (模型文件很大)
)

echo ================================================================================
echo [步骤 4/8] 网络和端口检查
echo ================================================================================

echo [4.1] 检查网络连接...
ping -n 1 8.8.8.8 >nul 2>&1
if %errorlevel% equ 0 (
    echo [✅] 网络连接正常
) else (
    echo [⚠️] 网络连接可能有问题，下载模型时可能失败
)

echo [4.2] 检查关键端口...
netstat -an | findstr ":5000" >nul 2>&1
if %errorlevel% equ 0 (
    echo [⚠️] 端口5000已占用
) else (
    echo [✅] 端口5000可用
)

netstat -an | findstr ":7001" >nul 2>&1
if %errorlevel% equ 0 (
    echo [⚠️] 端口7001已占用
) else (
    echo [✅] 端口7001可用
)

echo ================================================================================
echo [步骤 5/8] Python包管理检查
echo ================================================================================

echo [5.1] 检查虚拟环境支持...
python -m venv --help >nul 2>&1
if %errorlevel% equ 0 (
    echo [✅] 虚拟环境支持正常
) else (
    echo [❌] 虚拟环境不支持
    set MISSING_DEPS=1
)

echo [5.2] 检查pip升级...
python -m pip install --upgrade pip --dry-run >nul 2>&1
if %errorlevel% equ 0 (
    echo [✅] pip可以正常升级
) else (
    echo [⚠️] pip升级可能有问题
)

echo ================================================================================
echo [步骤 6/8] 模型存储检查
echo ================================================================================

echo [6.1] 检查Hugging Face缓存目录...
if exist "%USERPROFILE%\.cache\huggingface" (
    echo [📊] HF缓存目录存在: %USERPROFILE%\.cache\huggingface
) else (
    echo [📝] HF缓存目录将被创建: %USERPROFILE%\.cache\huggingface
)

echo [6.2] 检查现有模型...
set MODEL_COUNT=0
if exist "%USERPROFILE%\.cache\huggingface\transformers" (
    for /d %%i in ("%USERPROFILE%\.cache\huggingface\transformers\*") do set /a MODEL_COUNT+=1
    echo [📊] 已缓存模型数量: %MODEL_COUNT%
) else (
    echo [📝] 暂无缓存模型，将从头下载
)

echo ================================================================================
echo [步骤 7/8] 特殊依赖检查
echo ================================================================================

echo [7.1] 检查Visual C++ Redistributable...
reg query "HKLM\SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64" >nul 2>&1
if %errorlevel% equ 0 (
    echo [✅] Visual C++ Redistributable已安装
) else (
    echo [⚠️] 可能需要Visual C++ Redistributable
    echo [💾] 下载: https://aka.ms/vs/17/release/vc_redist.x64.exe
)

echo [7.2] 检查Windows SDK (可选)...
reg query "HKLM\SOFTWARE\WOW6432Node\Microsoft\Microsoft SDKs\Windows" >nul 2>&1
if %errorlevel% equ 0 (
    echo [✅] Windows SDK可用
) else (
    echo [📝] Windows SDK未检测到 (通常不是必需的)
)

echo ================================================================================
echo [步骤 8/8] 总结和建议
echo ================================================================================

echo.
echo 📋 环境检查完成！
echo.

if defined MISSING_DEPS (
    echo [❌] 发现缺失的依赖项，请先安装:
    echo.
    echo 🔧 必需安装项:
    if not defined PYTHON_VERSION echo   - Python 3.10.11+
    if not defined GIT_VERSION echo   - Git
    if not defined DOTNET_VERSION echo   - .NET 8.0 SDK
    if not defined CUDA_VERSION echo   - CUDA 12.1+
    echo.
    echo 📝 安装完成后请重新运行此脚本
    echo.
) else (
    echo [✅] 所有基础依赖都已满足！
    echo.
    echo 🚀 您可以继续进行下一步:
    echo.
    echo 📥 需要下载和安装的组件:
    echo   1. vLLM 推理引擎
    echo   2. PyTorch 2.1.0 (CUDA 12.1)
    echo   3. MuseTalk 相关模型
    echo   4. 大语言模型 (Qwen2.5-14B-Instruct)
    echo   5. TTS 和语音识别模型
    echo.
    echo 💡 下一步命令:
    echo   deploy-production-now.bat  # 一键部署
    echo   或
    echo   setup-quad-gpu-commercial.bat  # 手动配置
    echo.
    echo 📊 预计下载大小: ~50-80GB
    echo ⏱️  预计安装时间: 30-60分钟 (取决于网络速度)
    echo.
)

echo ================================================================================
echo                              检查完成
echo ================================================================================
echo.
echo 按任意键退出...
pause >nul