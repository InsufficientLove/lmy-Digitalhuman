@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ================================================
echo 🔧 VS2022环境修复工具 - 解决dlib编译问题
echo ================================================
echo.

echo 🔍 检测VS2022环境...

REM 检查VS2022安装路径
set "VS2022_PATH="
for /d %%i in ("C:\Program Files\Microsoft Visual Studio\2022\*") do (
    if exist "%%i\VC\Tools\MSVC" (
        set "VS2022_PATH=%%i"
        echo ✅ 找到VS2022: %%i
        goto :found_vs
    )
)

for /d %%i in ("D:\Program Files\Microsoft Visual Studio\2022\*") do (
    if exist "%%i\VC\Tools\MSVC" (
        set "VS2022_PATH=%%i"
        echo ✅ 找到VS2022: %%i
        goto :found_vs
    )
)

echo ❌ 未找到VS2022安装，请检查安装路径
pause
exit /b 1

:found_vs

echo.
echo 🔧 配置VS2022编译环境...

REM 设置VS环境变量
set "VCINSTALLDIR=%VS2022_PATH%\VC\"
set "VS170COMNTOOLS=%VS2022_PATH%\Common7\Tools\"

REM 查找最新的MSVC工具链版本
for /f "delims=" %%i in ('dir "%VS2022_PATH%\VC\Tools\MSVC" /b /ad /o-n') do (
    set "MSVC_VERSION=%%i"
    goto :found_msvc
)

:found_msvc
echo ✅ MSVC版本: %MSVC_VERSION%

REM 设置完整的编译器路径
set "MSVC_PATH=%VS2022_PATH%\VC\Tools\MSVC\%MSVC_VERSION%"
set "CMAKE_GENERATOR=Visual Studio 17 2022"

echo.
echo 🔍 检查必要组件...

REM 检查CMake
cmake --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ CMake未安装或不在PATH中
    echo 💡 请安装CMake或将其添加到PATH
    echo 📥 下载地址: https://cmake.org/download/
    pause
    exit /b 1
) else (
    echo ✅ CMake已安装
    cmake --version | findstr /r "cmake version"
)

REM 检查Git
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Git未安装或不在PATH中
    echo 💡 请安装Git或将其添加到PATH
) else (
    echo ✅ Git已安装
)

echo.
echo 🔧 修复Python虚拟环境中的dlib安装...

set "BASE_DIR=F:\AI\DigitalHuman_Portable"
set "VENV_DIR=%BASE_DIR%\venv"

if not exist "%VENV_DIR%\Scripts\activate.bat" (
    echo ❌ 虚拟环境不存在，请先运行基础安装脚本
    pause
    exit /b 1
)

echo 激活虚拟环境...
call "%VENV_DIR%\Scripts\activate.bat"

echo.
echo 🔧 方法1: 使用VS2022环境编译dlib...

REM 调用VS2022的vcvars64.bat来设置编译环境
call "%VS2022_PATH%\VC\Auxiliary\Build\vcvars64.bat" >nul 2>&1

REM 设置编译器环境变量
set CC=cl.exe
set CXX=cl.exe
set CMAKE_C_COMPILER=cl.exe
set CMAKE_CXX_COMPILER=cl.exe
set CMAKE_GENERATOR=Visual Studio 17 2022
set CMAKE_GENERATOR_PLATFORM=x64

echo 环境变量设置完成，开始编译dlib...
pip install --upgrade setuptools wheel
pip install cmake

echo 尝试编译安装dlib...
pip install --no-cache-dir --force-reinstall dlib==19.24.2
if %errorlevel% equ 0 (
    echo ✅ dlib编译安装成功！
    goto :install_other_deps
)

echo.
echo 🔧 方法2: 使用预编译wheel...
echo 尝试从不同源安装预编译版本...

pip install --no-deps dlib==19.24.2 --find-links https://github.com/sachadee/Dlib/releases/download/v19.22.1/
if %errorlevel% equ 0 (
    echo ✅ 预编译dlib安装成功！
    goto :install_other_deps
)

echo.
echo 🔧 方法3: 从conda-forge安装...
pip install --index-url https://pypi.anaconda.org/conda-forge/simple/ dlib
if %errorlevel% equ 0 (
    echo ✅ conda-forge dlib安装成功！
    goto :install_other_deps
)

echo.
echo 🔧 方法4: 使用兼容版本...
pip install dlib==19.22.1
if %errorlevel% equ 0 (
    echo ✅ 兼容版本dlib安装成功！
    goto :install_other_deps
)

echo.
echo ⚠️ 所有dlib安装方法都失败了
echo 💡 可能的解决方案：
echo 1. 检查VS2022是否安装了"MSVC v143 - VS 2022 C++ x64/x86生成工具"
echo 2. 检查是否安装了"Windows 11 SDK"
echo 3. 重启命令行后重试
echo 4. 使用setup_minimal_environment.bat跳过dlib
echo.
echo 是否继续安装其他依赖？(y/n)
set /p continue_install="请选择: "
if /i "%continue_install%" neq "y" (
    pause
    exit /b 1
)

:install_other_deps

echo.
echo 📦 安装其他必要依赖...

REM 安装face_alignment（可能需要dlib）
echo 安装face_alignment...
pip install face_alignment==1.3.5
if %errorlevel% neq 0 (
    echo ⚠️ face_alignment安装失败，可能需要dlib
)

echo 安装其他依赖...
pip install opencv-python==4.8.1.78
pip install numpy==1.24.3
pip install Pillow==10.0.0
pip install scipy==1.11.1
pip install librosa==0.10.1
pip install soundfile==0.12.1
pip install imageio==2.31.1
pip install imageio-ffmpeg==0.4.8
pip install flask==2.3.2
pip install flask-cors==4.0.0
pip install requests==2.31.0
pip install yacs==0.1.8
pip install pyyaml==6.0
pip install scikit-image==0.21.0

echo.
echo 🔧 重新尝试下载MuseTalk源码...

set "MUSETALK_DIR=%BASE_DIR%\MuseTalk"

if exist "%MUSETALK_DIR%" (
    echo MuseTalk目录已存在，跳过下载
    goto :create_scripts
)

echo 尝试从GitHub下载...
git clone https://github.com/TMElyralab/MuseTalk.git "%MUSETALK_DIR%"
if %errorlevel% equ 0 (
    echo ✅ MuseTalk从GitHub下载成功
    goto :create_scripts
)

echo 尝试从Gitee镜像下载...
git clone https://gitee.com/mirrors/MuseTalk.git "%MUSETALK_DIR%"
if %errorlevel% equ 0 (
    echo ✅ MuseTalk从Gitee下载成功
    goto :create_scripts
)

echo ⚠️ MuseTalk下载失败，创建基础结构...
mkdir "%MUSETALK_DIR%" 2>nul

:create_scripts

echo.
echo 📝 创建启动脚本...

set "SCRIPTS_DIR=%BASE_DIR%\scripts"
if not exist "%SCRIPTS_DIR%" mkdir "%SCRIPTS_DIR%"

REM 创建带VS环境的启动脚本
(
echo @echo off
echo chcp 65001 ^>nul
echo echo 🚀 启动MuseTalk服务 ^(VS2022环境^)...
echo echo 📍 工作目录: %MUSETALK_DIR%
echo echo 🔗 服务地址: http://localhost:8000
echo echo.
echo.
echo REM 设置VS2022编译环境
echo call "%VS2022_PATH%\VC\Auxiliary\Build\vcvars64.bat" ^>nul 2^>^&1
echo.
echo REM 激活Python虚拟环境
echo call "%VENV_DIR%\Scripts\activate.bat"
echo.
echo REM 设置GPU环境
echo set CUDA_VISIBLE_DEVICES=0
echo set PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512
echo.
echo REM 启动服务
echo cd /d "%MUSETALK_DIR%"
echo if exist musetalk_service.py ^(
echo     python musetalk_service.py
echo ^) else ^(
echo     echo ❌ musetalk_service.py不存在
echo     echo 💡 请运行 copy_service_files.bat 复制服务文件
echo     pause
echo ^)
echo pause
) > "%SCRIPTS_DIR%\start_musetalk_vs2022.bat"

echo ✅ VS2022环境启动脚本创建完成

echo.
echo 📝 创建环境诊断脚本...
(
echo @echo off
echo chcp 65001 ^>nul
echo echo 🔍 VS2022环境诊断报告
echo echo ========================
echo echo.
echo echo 📁 VS2022路径: %VS2022_PATH%
echo echo 📁 MSVC版本: %MSVC_VERSION%
echo echo 📁 虚拟环境: %VENV_DIR%
echo echo.
echo echo 🔧 编译工具检查:
echo cmake --version 2^>nul ^|^| echo "❌ CMake未安装"
echo echo.
echo echo 🐍 Python环境:
echo call "%VENV_DIR%\Scripts\activate.bat"
echo python --version
echo echo.
echo echo 📦 关键依赖检查:
echo python -c "import dlib; print(f'✅ dlib: {dlib.__version__}')" 2^>nul ^|^| echo "❌ dlib未安装"
echo python -c "import cv2; print(f'✅ OpenCV: {cv2.__version__}')" 2^>nul ^|^| echo "❌ OpenCV未安装"
echo python -c "import torch; print(f'✅ PyTorch: {torch.__version__}')" 2^>nul ^|^| echo "❌ PyTorch未安装"
echo python -c "import face_alignment; print('✅ face_alignment已安装')" 2^>nul ^|^| echo "❌ face_alignment未安装"
echo echo.
echo echo 🎭 MuseTalk状态:
echo if exist "%MUSETALK_DIR%\musetalk_service.py" ^(echo ✅ 服务文件存在^) else ^(echo ❌ 服务文件不存在^)
echo if exist "%MUSETALK_DIR%\models" ^(echo ✅ 模型目录存在^) else ^(echo ❌ 模型目录不存在^)
echo echo.
echo pause
) > "%SCRIPTS_DIR%\diagnose_vs2022.bat"

echo.
echo 🎉 VS2022环境修复完成！
echo.
echo 📋 修复结果:
python -c "import dlib; print(f'✅ dlib: {dlib.__version__}')" 2>nul || echo "❌ dlib: 安装失败"
python -c "import torch; print(f'✅ PyTorch: {torch.__version__}')" 2>nul || echo "❌ PyTorch: 未安装"

echo.
echo 🚀 下一步操作:
echo 1. 运行诊断: %SCRIPTS_DIR%\diagnose_vs2022.bat
echo 2. 复制服务文件: copy_service_files.bat
echo 3. 启动服务: %SCRIPTS_DIR%\start_musetalk_vs2022.bat
echo.
echo 💡 如果dlib仍然安装失败:
echo - 检查VS2022组件："MSVC v143"和"Windows SDK"
echo - 重启命令行后重试
echo - 或使用 setup_minimal_environment.bat 跳过dlib
echo.
pause