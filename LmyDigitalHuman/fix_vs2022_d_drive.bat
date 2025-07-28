@echo off
setlocal enabledelayedexpansion

echo ================================================
echo VS2022环境修复工具 (D盘版本)
echo ================================================
echo.

echo 检测VS2022安装位置...
set "VS2022_PATH="

if exist "D:\Program Files\Microsoft Visual Studio\2022\Community\VC\Tools\MSVC" (
    set "VS2022_PATH=D:\Program Files\Microsoft Visual Studio\2022\Community"
    echo 找到VS2022: !VS2022_PATH!
) else if exist "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Tools\MSVC" (
    set "VS2022_PATH=C:\Program Files\Microsoft Visual Studio\2022\Community"
    echo 找到VS2022: !VS2022_PATH!
) else if exist "C:\Program Files\Microsoft Visual Studio\2022\Professional\VC\Tools\MSVC" (
    set "VS2022_PATH=C:\Program Files\Microsoft Visual Studio\2022\Professional"
    echo 找到VS2022: !VS2022_PATH!
) else (
    echo 未找到VS2022安装
    pause
    exit /b 1
)

echo.
echo 设置VS2022编译环境...

REM 调用VS2022的vcvars64.bat来设置编译环境
echo 调用vcvars64.bat...
call "!VS2022_PATH!\VC\Auxiliary\Build\vcvars64.bat"

if !errorlevel! neq 0 (
    echo VS环境设置失败
    pause
    exit /b 1
)

echo VS环境设置成功

echo.
echo 检查编译器是否可用...
where cl.exe >nul 2>&1
if !errorlevel! equ 0 (
    echo C++编译器可用
    cl.exe 2>&1 | findstr "Microsoft"
) else (
    echo C++编译器不可用
    pause
    exit /b 1
)

echo.
echo 检查虚拟环境...
set "BASE_DIR=F:\AI\DigitalHuman_Portable"
set "VENV_DIR=%BASE_DIR%\venv"

if not exist "%VENV_DIR%\Scripts\activate.bat" (
    echo 虚拟环境不存在，请先运行基础安装脚本
    pause
    exit /b 1
)

echo 激活Python虚拟环境...
call "%VENV_DIR%\Scripts\activate.bat"

echo.
echo 设置编译器环境变量...
set CC=cl.exe
set CXX=cl.exe
set CMAKE_C_COMPILER=cl.exe
set CMAKE_CXX_COMPILER=cl.exe
set CMAKE_GENERATOR=Visual Studio 17 2022
set CMAKE_GENERATOR_PLATFORM=x64

echo.
echo 升级pip和安装编译工具...
python -m pip install --upgrade pip
pip install --upgrade setuptools wheel
pip install cmake

echo.
echo 尝试编译安装dlib...
echo 这可能需要几分钟时间...

pip install --no-cache-dir --force-reinstall --verbose dlib==19.24.2

if !errorlevel! equ 0 (
    echo dlib编译安装成功！
) else (
    echo dlib编译失败，尝试其他方法...
    
    echo 尝试安装兼容版本...
    pip install dlib==19.22.1
    
    if !errorlevel! equ 0 (
        echo dlib兼容版本安装成功！
    ) else (
        echo 所有dlib安装方法都失败了
        echo.
        echo 可能的原因:
        echo 1. Windows SDK路径问题
        echo 2. MSVC工具链配置问题
        echo 3. CMake配置问题
        echo.
        echo 建议使用 setup_minimal_environment.bat 跳过dlib
        pause
        exit /b 1
    )
)

echo.
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

echo.
echo 创建启动脚本...
set "SCRIPTS_DIR=%BASE_DIR%\scripts"
if not exist "%SCRIPTS_DIR%" mkdir "%SCRIPTS_DIR%"

(
echo @echo off
echo echo 启动MuseTalk服务 ^(VS2022 D盘版本^)...
echo call "!VS2022_PATH!\VC\Auxiliary\Build\vcvars64.bat" ^>nul
echo call "%VENV_DIR%\Scripts\activate.bat"
echo set CUDA_VISIBLE_DEVICES=0
echo cd /d "%BASE_DIR%\MuseTalk"
echo python musetalk_service.py
echo pause
) > "%SCRIPTS_DIR%\start_musetalk_d_drive.bat"

echo.
echo 修复完成！
echo.
echo 下一步:
echo 1. 运行 copy_service_files.bat 复制服务文件
echo 2. 启动服务: %SCRIPTS_DIR%\start_musetalk_d_drive.bat
echo.
pause