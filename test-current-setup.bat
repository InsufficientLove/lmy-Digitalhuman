@echo off
chcp 65001 >nul
echo ================================================================================
echo                    🧪 测试当前项目配置
echo ================================================================================
echo.
echo 此脚本将测试现有的数字人项目是否可以正常运行
echo 包括原有功能和新增的WebRTC功能
echo.
pause

echo ================================================================================
echo [步骤 1/5] 环境检查
echo ================================================================================

echo [1.1] 检查.NET环境...
dotnet --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] .NET未安装或未在PATH中
    pause
    goto end
)

for /f %%i in ('dotnet --version 2^>^&1') do set DOTNET_VERSION=%%i
echo [✓] .NET版本: %DOTNET_VERSION%

echo [1.2] 检查Python环境...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [警告] Python未安装，部分功能可能无法使用
) else (
    for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
    echo [✓] Python版本: %PYTHON_VERSION%
)

echo [1.3] 检查GPU环境...
nvidia-smi >nul 2>&1
if %errorlevel% neq 0 (
    echo [警告] NVIDIA GPU或驱动未检测到
) else (
    echo [✓] NVIDIA GPU环境可用
)

echo ================================================================================
echo [步骤 2/5] 项目文件检查
echo ================================================================================

echo [2.1] 检查项目结构...
if not exist "LmyDigitalHuman\LmyDigitalHuman.csproj" (
    echo [错误] 项目文件不存在
    pause
    goto end
)
echo [✓] 项目文件存在

echo [2.2] 检查Web资源...
if not exist "LmyDigitalHuman\wwwroot\digital-human-test.html" (
    echo [错误] 测试页面不存在
    pause
    goto end
)
echo [✓] 测试页面存在

echo [2.3] 检查WebRTC脚本...
if not exist "LmyDigitalHuman\wwwroot\js\webrtc-realtime.js" (
    echo [错误] WebRTC脚本不存在
    pause
    goto end
)
echo [✓] WebRTC脚本存在

echo ================================================================================
echo [步骤 3/5] 编译项目
echo ================================================================================

echo [3.1] 还原NuGet包...
cd LmyDigitalHuman
dotnet restore --verbosity quiet
if %errorlevel% neq 0 (
    echo [错误] NuGet包还原失败
    cd ..
    pause
    goto end
)
echo [✓] NuGet包还原成功

echo [3.2] 编译项目...
dotnet build --configuration Release --verbosity quiet
if %errorlevel% neq 0 (
    echo [错误] 项目编译失败
    echo.
    echo [建议] 运行以下命令查看详细错误:
    echo   cd LmyDigitalHuman
    echo   dotnet build
    cd ..
    pause
    goto end
)
echo [✓] 项目编译成功

cd ..

echo ================================================================================
echo [步骤 4/5] 检查端口占用
echo ================================================================================

echo [4.1] 检查端口5000...
netstat -an | findstr ":5000" >nul 2>&1
if %errorlevel% equ 0 (
    echo [警告] 端口5000已被占用，可能需要停止其他服务
) else (
    echo [✓] 端口5000可用
)

echo [4.2] 检查端口7001...
netstat -an | findstr ":7001" >nul 2>&1
if %errorlevel% equ 0 (
    echo [警告] 端口7001已被占用，可能需要停止其他服务
) else (
    echo [✓] 端口7001可用
)

echo ================================================================================
echo [步骤 5/5] 启动测试
echo ================================================================================

echo [5.1] 准备启动项目...
echo.
echo 🚀 项目将在以下地址启动:
echo   - HTTP:  http://localhost:5000
echo   - HTTPS: https://localhost:7001
echo   - 测试页面: http://localhost:5000/digital-human-test.html
echo.
echo 📋 功能测试清单:
echo   ✅ 数字人模板选择
echo   ✅ 文本对话功能
echo   ✅ 语音对话功能  
echo   ✅ 实时对话功能
echo   🆕 WebRTC实时通信 (新功能)
echo.
choice /c YN /m "是否现在启动项目进行测试"
if errorlevel 2 goto success

echo.
echo [信息] 正在启动项目...
echo [提示] 按 Ctrl+C 停止服务
echo.

cd LmyDigitalHuman
dotnet run
cd ..

:success
echo.
echo ================================================================================
echo                              ✅ 测试完成
echo ================================================================================
echo.
echo [✅] 环境检查通过
echo [✅] 项目文件完整
echo [✅] 编译成功
echo [✅] 端口检查完成
echo.
echo 💡 使用说明:
echo   1. 手动启动: cd LmyDigitalHuman && dotnet run
echo   2. 访问测试页面: http://localhost:5000/digital-human-test.html
echo   3. 测试原有功能确保正常工作
echo   4. 测试新的WebRTC实时通信功能
echo.
echo 🔧 如果遇到问题:
echo   - 检查.NET 8.0是否正确安装
echo   - 确保端口5000和7001未被占用
echo   - 查看控制台输出的详细错误信息
echo.
goto end

:end
echo.
echo 按任意键退出...
pause >nul