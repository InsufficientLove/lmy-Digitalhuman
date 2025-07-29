@echo off
chcp 65001 >nul
echo ================================================================================
echo                🔍 4GPU商用级环境验证
echo ================================================================================
echo.
echo 此脚本将验证您的服务器是否满足4GPU商用级部署要求
echo.
pause

echo ================================================================================
echo [步骤 1/6] 基础环境检查
echo ================================================================================

echo [1.1] 检查Python版本...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] Python未安装
    echo [要求] Python 3.10.11+
    pause
    goto end
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [✓] Python版本: %PYTHON_VERSION%

REM 检查Python版本是否满足要求
python -c "import sys; exit(0 if sys.version_info >= (3, 10, 11) else 1)" 2>nul
if %errorlevel% neq 0 (
    echo [警告] Python版本可能不满足要求，建议3.10.11+
)

echo [1.2] 检查CUDA版本...
nvcc --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] CUDA未安装或未在PATH中
    echo [要求] CUDA 12.1+
    pause
    goto end
)

for /f "tokens=6 delims=, " %%i in ('nvcc --version ^| findstr "release"') do set CUDA_VERSION=%%i
echo [✓] CUDA版本: %CUDA_VERSION%

echo [1.3] 检查.NET版本...
dotnet --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] .NET未安装
    echo [要求] .NET 8.0
    pause
    goto end
)

for /f %%i in ('dotnet --version 2^>^&1') do set DOTNET_VERSION=%%i
echo [✓] .NET版本: %DOTNET_VERSION%

echo ================================================================================
echo [步骤 2/6] GPU硬件检查
echo ================================================================================

echo [2.1] 检查GPU数量和型号...
nvidia-smi --list-gpus > temp_gpu_list.txt 2>&1
if %errorlevel% neq 0 (
    echo [错误] 无法获取GPU信息
    del temp_gpu_list.txt 2>nul
    pause
    goto end
)

set GPU_COUNT=0
for /f %%i in ('type temp_gpu_list.txt ^| find /c "GPU"') do set GPU_COUNT=%%i
echo [信息] 检测到 %GPU_COUNT% 张GPU

if %GPU_COUNT% LSS 4 (
    echo [警告] GPU数量少于4张，将使用单GPU模式
    echo [建议] 4GPU商用版需要4张RTX4090或同等级GPU
    choice /c YN /m "是否继续使用单GPU模式"
    if errorlevel 2 (
        del temp_gpu_list.txt 2>nul
        goto end
    )
    set DEPLOYMENT_MODE=single
) else (
    echo [✓] GPU数量满足4GPU商用要求
    set DEPLOYMENT_MODE=quad
)

echo [2.2] 检查GPU型号...
type temp_gpu_list.txt
del temp_gpu_list.txt

echo [2.3] 检查显存容量...
nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits > temp_memory.txt 2>&1
if %errorlevel% equ 0 (
    set TOTAL_MEMORY=0
    for /f %%i in (temp_memory.txt) do set /a TOTAL_MEMORY+=%%i
    echo [信息] 总显存: %TOTAL_MEMORY%MB
    
    if %TOTAL_MEMORY% LSS 80000 (
        echo [警告] 总显存少于80GB，性能可能受限
    ) else (
        echo [✓] 显存容量充足
    )
    del temp_memory.txt
)

echo ================================================================================
echo [步骤 3/6] 网络和端口检查
echo ================================================================================

echo [3.1] 检查关键端口...
set PORT_ISSUES=0

netstat -an | findstr ":5000" >nul 2>&1
if %errorlevel% equ 0 (
    echo [警告] 端口5000已占用
    set /a PORT_ISSUES+=1
) else (
    echo [✓] 端口5000可用
)

netstat -an | findstr ":7001" >nul 2>&1
if %errorlevel% equ 0 (
    echo [警告] 端口7001已占用
    set /a PORT_ISSUES+=1
) else (
    echo [✓] 端口7001可用
)

if %PORT_ISSUES% GTR 0 (
    echo [建议] 请停止占用端口的服务或修改配置
)

echo ================================================================================
echo [步骤 4/6] 系统资源检查
echo ================================================================================

echo [4.1] 检查系统内存...
for /f "skip=1 tokens=4" %%i in ('wmic OS get TotalVisibleMemorySize /value') do (
    if not "%%i"=="" (
        set /a TOTAL_RAM=%%i/1024
        echo [信息] 系统内存: %TOTAL_RAM%MB
        
        if %TOTAL_RAM% LSS 32768 (
            echo [警告] 系统内存少于32GB，建议升级
        ) else (
            echo [✓] 系统内存充足
        )
    )
)

echo [4.2] 检查CPU核心数...
echo [信息] CPU核心数: %NUMBER_OF_PROCESSORS%
if %NUMBER_OF_PROCESSORS% LSS 16 (
    echo [警告] CPU核心数较少，可能影响并发性能
) else (
    echo [✓] CPU核心数充足
)

echo ================================================================================
echo [步骤 5/6] 磁盘空间检查
echo ================================================================================

echo [5.1] 检查可用磁盘空间...
for /f "tokens=3" %%i in ('dir /-c ^| findstr "bytes free"') do (
    set DISK_FREE=%%i
    echo [信息] 可用磁盘空间: %DISK_FREE% bytes
)

REM 检查是否有足够空间（至少50GB）
dir /-c | findstr "bytes free" | findstr /r "[0-9][0-9],[0-9][0-9][0-9],[0-9][0-9][0-9],[0-9][0-9][0-9]" >nul
if %errorlevel% equ 0 (
    echo [✓] 磁盘空间充足
) else (
    echo [警告] 磁盘空间可能不足，建议至少50GB可用空间
)

echo ================================================================================
echo [步骤 6/6] 部署建议
echo ================================================================================

echo.
echo 📋 环境评估结果:
echo   - Python: %PYTHON_VERSION%
echo   - CUDA: %CUDA_VERSION%
echo   - .NET: %DOTNET_VERSION%
echo   - GPU数量: %GPU_COUNT%张
echo   - 建议部署模式: %DEPLOYMENT_MODE%GPU
echo.

if "%DEPLOYMENT_MODE%"=="quad" (
    echo 🚀 推荐部署方案: 4GPU商用级
    echo.
    echo 性能预期:
    echo   ⚡ 端到端延迟: ^<370ms
    echo   👥 并发用户: 50+
    echo   🎯 商用级稳定性
    echo.
    echo 部署命令:
    echo   setup-quad-gpu-commercial.bat
    echo   start-commercial.bat
    echo.
) else (
    echo 🎮 推荐部署方案: 单GPU演示级
    echo.
    echo 性能预期:
    echo   ⚡ 端到端延迟: 4-6秒
    echo   👥 并发用户: 1-5
    echo   🧪 适合测试演示
    echo.
    echo 部署命令:
    echo   setup-single-gpu.bat
    echo   start-single-gpu.bat
    echo.
)

choice /c YN /m "是否现在开始部署"
if errorlevel 2 goto success

echo.
echo [信息] 开始部署...
if "%DEPLOYMENT_MODE%"=="quad" (
    call setup-quad-gpu-commercial.bat
) else (
    call setup-single-gpu.bat
)

:success
echo.
echo ================================================================================
echo                              ✅ 验证完成
echo ================================================================================
echo.
echo 💡 下一步操作:
echo   1. 根据建议选择部署脚本
echo   2. 运行对应的启动脚本
echo   3. 访问 http://localhost:5000/digital-human-test.html
echo   4. 进行功能测试和性能验证
echo.

:end
echo.
echo 按任意键退出...
pause >nul