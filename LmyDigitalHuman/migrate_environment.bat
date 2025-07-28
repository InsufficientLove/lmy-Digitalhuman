@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ================================================
echo 🚚 数字人环境迁移工具
echo ================================================
echo.

echo 请选择操作:
echo 1. 📦 打包当前环境 (源机器)
echo 2. 📂 部署环境包 (目标机器)
echo 3. 🔧 快速配置检查
echo 4. 🗑️ 清理临时文件
echo.
set /p choice="请输入选择 (1-4): "

if "%choice%"=="1" goto :pack_environment
if "%choice%"=="2" goto :deploy_environment
if "%choice%"=="3" goto :quick_check
if "%choice%"=="4" goto :cleanup
echo ❌ 无效选择
goto :end

:pack_environment
echo.
echo 📦 开始打包环境...
set "SOURCE_DIR=F:\AI\DigitalHuman_Portable"
set "PACK_DIR=F:\AI\DigitalHuman_Package"
set "TIMESTAMP=%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%"
set "TIMESTAMP=!TIMESTAMP: =0!"

if not exist "%SOURCE_DIR%" (
    echo ❌ 源目录不存在: %SOURCE_DIR%
    echo 💡 请先运行 setup_portable_environment.bat 安装环境
    goto :end
)

echo 🗂️ 创建打包目录...
if exist "%PACK_DIR%" rmdir /s /q "%PACK_DIR%"
mkdir "%PACK_DIR%"

echo 📋 复制核心文件...
echo   - 复制虚拟环境...
xcopy "%SOURCE_DIR%\venv" "%PACK_DIR%\venv" /E /I /H /Y >nul
echo   - 复制MuseTalk源码...
xcopy "%SOURCE_DIR%\MuseTalk" "%PACK_DIR%\MuseTalk" /E /I /H /Y >nul
echo   - 复制配置文件...
xcopy "%SOURCE_DIR%\config" "%PACK_DIR%\config" /E /I /H /Y >nul
echo   - 复制启动脚本...
xcopy "%SOURCE_DIR%\scripts" "%PACK_DIR%\scripts" /E /I /H /Y >nul

echo 📦 复制预训练模型 (可能需要较长时间)...
if exist "%SOURCE_DIR%\models" (
    xcopy "%SOURCE_DIR%\models" "%PACK_DIR%\models" /E /I /H /Y >nul
    echo ✅ 模型复制完成
) else (
    echo ⚠️ 模型目录不存在，跳过复制
)

echo 📝 创建环境信息文件...
(
echo # 数字人环境包信息
echo 打包时间: %date% %time%
echo 源路径: %SOURCE_DIR%
echo Python版本: 
python --version 2^>nul ^|^| echo "未检测到Python"
echo.
echo # GPU信息
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader,nounits 2^>nul ^|^| echo "未检测到NVIDIA GPU"
echo.
echo # 已安装的关键包
echo ## PyTorch
pip show torch 2^>nul ^| findstr "Version"
echo ## OpenCV
pip show opencv-python 2^>nul ^| findstr "Version"
echo ## MuseTalk依赖
pip show librosa soundfile 2^>nul ^| findstr "Version"
) > "%PACK_DIR%\environment_info.txt"

echo 📄 创建部署说明...
(
echo @echo off
echo chcp 65001 ^>nul
echo echo 🚀 数字人环境快速部署
echo echo ========================
echo echo.
echo echo 📍 当前目录: %%cd%%
echo echo 🎯 目标目录: F:\AI\DigitalHuman_Portable
echo echo.
echo echo 正在部署环境...
echo if exist "F:\AI\DigitalHuman_Portable" ^(
echo     echo 🗑️ 删除现有环境...
echo     rmdir /s /q "F:\AI\DigitalHuman_Portable"
echo ^)
echo echo 📂 创建目标目录...
echo mkdir "F:\AI\DigitalHuman_Portable"
echo echo 📋 复制文件...
echo xcopy "%%cd%%\*" "F:\AI\DigitalHuman_Portable\" /E /I /H /Y ^>nul
echo echo ✅ 环境部署完成！
echo echo.
echo echo 🔧 配置GPU设备...
echo cd /d "F:\AI\DigitalHuman_Portable\scripts"
echo call configure_gpu.bat
echo echo.
echo echo 🏥 测试环境...
echo call check_environment.bat
echo echo.
echo echo 🚀 启动服务...
echo call start_musetalk.bat
) > "%PACK_DIR%\deploy.bat"

echo 💾 创建压缩包...
set "ZIP_NAME=DigitalHuman_Portable_%TIMESTAMP%.zip"
if exist "%ZIP_NAME%" del "%ZIP_NAME%"

REM 尝试使用PowerShell压缩
powershell -command "Compress-Archive -Path '%PACK_DIR%\*' -DestinationPath '%ZIP_NAME%' -Force" 2>nul
if %errorlevel% equ 0 (
    echo ✅ 压缩包创建成功: %ZIP_NAME%
    echo 📊 文件大小:
    dir "%ZIP_NAME%" | findstr "%ZIP_NAME%"
) else (
    echo ⚠️ PowerShell压缩失败，环境文件位于: %PACK_DIR%
    echo 💡 请手动压缩该目录或使用其他压缩工具
)

echo.
echo 🎉 环境打包完成！
echo 📦 打包目录: %PACK_DIR%
if exist "%ZIP_NAME%" echo 📄 压缩文件: %ZIP_NAME%
echo.
echo 📋 迁移步骤:
echo   1. 将压缩包复制到目标机器
echo   2. 解压到任意目录
echo   3. 运行 deploy.bat 进行部署
echo   4. 根据目标机器GPU配置调整设置
goto :end

:deploy_environment
echo.
echo 📂 开始部署环境...
echo.
echo 请输入环境包路径 (拖拽文件夹到此处):
set /p PACKAGE_PATH="路径: "

REM 移除引号
set "PACKAGE_PATH=%PACKAGE_PATH:"=%"

if not exist "%PACKAGE_PATH%" (
    echo ❌ 路径不存在: %PACKAGE_PATH%
    goto :end
)

echo 🎯 部署到: F:\AI\DigitalHuman_Portable
if exist "F:\AI\DigitalHuman_Portable" (
    echo ⚠️ 目标目录已存在，是否覆盖? (y/n)
    set /p confirm="确认: "
    if /i not "!confirm!"=="y" goto :end
    echo 🗑️ 删除现有环境...
    rmdir /s /q "F:\AI\DigitalHuman_Portable"
)

echo 📂 创建目标目录...
mkdir "F:\AI\DigitalHuman_Portable"

echo 📋 复制文件...
xcopy "%PACKAGE_PATH%\*" "F:\AI\DigitalHuman_Portable\" /E /I /H /Y >nul

echo ✅ 文件复制完成

echo 🔧 配置GPU设备...
cd /d "F:\AI\DigitalHuman_Portable\scripts"
if exist "configure_gpu.bat" (
    call configure_gpu.bat
) else (
    echo ⚠️ GPU配置脚本不存在，使用默认配置
)

echo 🏥 环境检查...
if exist "check_environment.bat" (
    call check_environment.bat
) else (
    echo ⚠️ 环境检查脚本不存在
)

echo.
echo 🎉 环境部署完成！
echo 🚀 使用以下命令启动服务:
echo    cd /d F:\AI\DigitalHuman_Portable\scripts
echo    start_musetalk.bat
goto :end

:quick_check
echo.
echo 🔧 快速配置检查...
echo ================

echo 📁 检查目录结构...
set "BASE_DIR=F:\AI\DigitalHuman_Portable"
if exist "%BASE_DIR%" (echo ✅ 基础目录存在) else (echo ❌ 基础目录不存在)
if exist "%BASE_DIR%\venv" (echo ✅ 虚拟环境存在) else (echo ❌ 虚拟环境不存在)
if exist "%BASE_DIR%\MuseTalk" (echo ✅ MuseTalk目录存在) else (echo ❌ MuseTalk目录不存在)
if exist "%BASE_DIR%\config" (echo ✅ 配置目录存在) else (echo ❌ 配置目录不存在)
if exist "%BASE_DIR%\scripts" (echo ✅ 脚本目录存在) else (echo ❌ 脚本目录不存在)

echo.
echo 🐍 检查Python环境...
if exist "%BASE_DIR%\venv\Scripts\python.exe" (
    echo ✅ Python可执行文件存在
    "%BASE_DIR%\venv\Scripts\python.exe" --version
) else (
    echo ❌ Python可执行文件不存在
)

echo.
echo 🎮 检查GPU状态...
nvidia-smi >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ NVIDIA驱动正常
    nvidia-smi --query-gpu=name --format=csv,noheader
) else (
    echo ⚠️ NVIDIA驱动未检测到或有问题
)

echo.
echo 📋 检查配置文件...
if exist "%BASE_DIR%\config\gpu_config.env" (
    echo ✅ GPU配置文件存在
    type "%BASE_DIR%\config\gpu_config.env"
) else (
    echo ❌ GPU配置文件不存在
)

echo.
echo 🌐 检查服务状态...
curl -s http://localhost:8000/health >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ MuseTalk服务正在运行
    curl -s http://localhost:8000/health
) else (
    echo ❌ MuseTalk服务未运行
)

goto :end

:cleanup
echo.
echo 🗑️ 清理临时文件...
echo.

set "CLEAN_PATHS=F:\AI\DigitalHuman_Package F:\AI\DigitalHuman_Portable\logs F:\AI\DigitalHuman_Portable\temp"

for %%p in (%CLEAN_PATHS%) do (
    if exist "%%p" (
        echo 🗑️ 清理: %%p
        rmdir /s /q "%%p" 2>nul
        if %errorlevel% equ 0 (echo ✅ 已清理) else (echo ⚠️ 清理失败)
    ) else (
        echo ⚪ 不存在: %%p
    )
)

echo.
echo 🗑️ 清理压缩包...
del /q DigitalHuman_Portable_*.zip 2>nul
if %errorlevel% equ 0 (echo ✅ 压缩包已清理) else (echo ⚪ 无压缩包需要清理)

echo.
echo ✅ 清理完成！
goto :end

:end
echo.
pause