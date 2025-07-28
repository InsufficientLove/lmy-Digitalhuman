@echo off
setlocal enabledelayedexpansion

echo ================================================
echo VS2022 Environment Fix Tool (D Drive Version)
echo ================================================
echo.

echo Detecting VS2022 installation...
set "VS2022_PATH="

if exist "D:\Program Files\Microsoft Visual Studio\2022\Community\VC\Tools\MSVC" (
    set "VS2022_PATH=D:\Program Files\Microsoft Visual Studio\2022\Community"
    echo Found VS2022: !VS2022_PATH!
) else if exist "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Tools\MSVC" (
    set "VS2022_PATH=C:\Program Files\Microsoft Visual Studio\2022\Community"
    echo Found VS2022: !VS2022_PATH!
) else if exist "C:\Program Files\Microsoft Visual Studio\2022\Professional\VC\Tools\MSVC" (
    set "VS2022_PATH=C:\Program Files\Microsoft Visual Studio\2022\Professional"
    echo Found VS2022: !VS2022_PATH!
) else (
    echo VS2022 not found
    pause
    exit /b 1
)

echo.
echo Setting up VS2022 build environment...

REM Call VS2022 vcvars64.bat to setup build environment
echo Calling vcvars64.bat...
call "!VS2022_PATH!\VC\Auxiliary\Build\vcvars64.bat"

if !errorlevel! neq 0 (
    echo VS environment setup failed
    pause
    exit /b 1
)

echo VS environment setup successful

echo.
echo Checking if compiler is available...
where cl.exe >nul 2>&1
if !errorlevel! equ 0 (
    echo C++ compiler is available
    cl.exe 2>&1 | findstr "Microsoft"
) else (
    echo C++ compiler not available
    pause
    exit /b 1
)

echo.
echo Checking virtual environment...
set "BASE_DIR=F:\AI\DigitalHuman_Portable"
set "VENV_DIR=%BASE_DIR%\venv"

if not exist "%VENV_DIR%\Scripts\activate.bat" (
    echo Virtual environment not found, please run basic setup script first
    pause
    exit /b 1
)

echo Activating Python virtual environment...
call "%VENV_DIR%\Scripts\activate.bat"

echo.
echo Setting compiler environment variables...
set CC=cl.exe
set CXX=cl.exe
set CMAKE_C_COMPILER=cl.exe
set CMAKE_CXX_COMPILER=cl.exe
set CMAKE_GENERATOR=Visual Studio 17 2022
set CMAKE_GENERATOR_PLATFORM=x64

echo.
echo Upgrading pip and installing build tools...
python -m pip install --upgrade pip
pip install --upgrade setuptools wheel
pip install cmake

echo.
echo Attempting to compile and install dlib...
echo This may take several minutes...

pip install --no-cache-dir --force-reinstall --verbose dlib==19.24.2

if !errorlevel! equ 0 (
    echo dlib compilation and installation successful!
) else (
    echo dlib compilation failed, trying alternative methods...
    
    echo Trying compatible version...
    pip install dlib==19.22.1
    
    if !errorlevel! equ 0 (
        echo dlib compatible version installed successfully!
    ) else (
        echo All dlib installation methods failed
        echo.
        echo Possible causes:
        echo 1. Windows SDK path issues
        echo 2. MSVC toolchain configuration problems
        echo 3. CMake configuration issues
        echo.
        echo Recommendation: Use setup_minimal_environment.bat to skip dlib
        pause
        exit /b 1
    )
)

echo.
echo Installing other dependencies...
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
echo Creating startup script...
set "SCRIPTS_DIR=%BASE_DIR%\scripts"
if not exist "%SCRIPTS_DIR%" mkdir "%SCRIPTS_DIR%"

(
echo @echo off
echo echo Starting MuseTalk Service ^(VS2022 D Drive Version^)...
echo call "!VS2022_PATH!\VC\Auxiliary\Build\vcvars64.bat" ^>nul
echo call "%VENV_DIR%\Scripts\activate.bat"
echo set CUDA_VISIBLE_DEVICES=0
echo cd /d "%BASE_DIR%\MuseTalk"
echo python musetalk_service.py
echo pause
) > "%SCRIPTS_DIR%\start_musetalk_d_drive.bat"

echo.
echo Fix completed!
echo.
echo Next steps:
echo 1. Run copy_service_files.bat to copy service files
echo 2. Start service: %SCRIPTS_DIR%\start_musetalk_d_drive.bat
echo.
pause