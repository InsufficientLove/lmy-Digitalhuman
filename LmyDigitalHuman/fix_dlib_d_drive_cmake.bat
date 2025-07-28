@echo off
setlocal enabledelayedexpansion

echo ================================================
echo dlib Compilation with D Drive CMake 4.1.0
echo ================================================
echo Using D drive CMake and VS2022 for optimal compatibility
echo.

echo Detecting D drive installations...
set "VS2022_PATH=D:\Program Files\Microsoft Visual Studio\2022\Community"
set "CMAKE_PATH=D:\Program Files\CMake\bin"

echo Checking VS2022...
if exist "%VS2022_PATH%\VC\Tools\MSVC" (
    echo ✅ VS2022 found: %VS2022_PATH%
) else (
    echo ❌ VS2022 not found at expected location
    pause
    exit /b 1
)

echo Checking CMake...
if exist "%CMAKE_PATH%\cmake.exe" (
    echo ✅ CMake found: %CMAKE_PATH%
    "%CMAKE_PATH%\cmake.exe" --version | findstr "cmake version"
) else (
    echo ❌ CMake not found at expected location
    pause
    exit /b 1
)

echo.
echo Setting up D drive environment...

REM Add D drive CMake to PATH first
set "PATH=%CMAKE_PATH%;%PATH%"

REM Set up VS2022 environment
call "%VS2022_PATH%\VC\Auxiliary\Build\vcvars64.bat"

echo.
echo Verifying environment setup...
echo CMake path:
where cmake
echo CMake version:
cmake --version

echo Compiler path:
where cl

echo.
echo Activating Python environment...
set "BASE_DIR=F:\AI\DigitalHuman_Portable"
set "VENV_DIR=%BASE_DIR%\venv"

if not exist "%VENV_DIR%\Scripts\activate.bat" (
    echo ❌ Virtual environment not found
    echo Please run setup script first
    pause
    exit /b 1
)

call "%VENV_DIR%\Scripts\activate.bat"

echo.
echo Configuring pip mirrors for faster downloads...
if not exist "%USERPROFILE%\.pip" mkdir "%USERPROFILE%\.pip"

(
echo [global]
echo index-url = https://pypi.tuna.tsinghua.edu.cn/simple/
echo trusted-host = pypi.tuna.tsinghua.edu.cn
echo timeout = 120
echo retries = 3
) > "%USERPROFILE%\.pip\pip.conf"

echo.
echo Setting CMake environment variables for dlib...
set CMAKE_GENERATOR=Visual Studio 17 2022
set CMAKE_GENERATOR_PLATFORM=x64
set CMAKE_GENERATOR_TOOLSET=v143
set CMAKE_BUILD_TYPE=Release
set CMAKE_C_COMPILER=cl.exe
set CMAKE_CXX_COMPILER=cl.exe

REM Explicitly set CMake path
set CMAKE_COMMAND=%CMAKE_PATH%\cmake.exe

echo.
echo Upgrading build tools...
python -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple/
pip install --upgrade setuptools wheel -i https://pypi.tuna.tsinghua.edu.cn/simple/

echo.
echo ================================================
echo Method 1: Direct dlib installation with D drive CMake
echo ================================================

echo Attempting dlib compilation with explicit CMake path...
set CMAKE_ARGS=-DCMAKE_GENERATOR="Visual Studio 17 2022" -DCMAKE_GENERATOR_PLATFORM=x64 -DCMAKE_BUILD_TYPE=Release
pip install --no-cache-dir --force-reinstall --verbose dlib==19.24.2 -i https://pypi.tuna.tsinghua.edu.cn/simple/

if !errorlevel! equ 0 (
    echo ✅ SUCCESS: dlib compiled successfully with D drive CMake!
    goto :test_dlib
)

echo.
echo ================================================
echo Method 2: Manual compilation with D drive tools
echo ================================================

echo Downloading dlib source...
pip download dlib==19.24.2 -i https://pypi.tuna.tsinghua.edu.cn/simple/ --no-deps

if exist dlib-19.24.2.tar.gz (
    echo Extracting dlib source...
    tar -xzf dlib-19.24.2.tar.gz
    cd dlib-19.24.2
    
    echo Creating build directory...
    if exist build rmdir /s /q build
    mkdir build
    cd build
    
    echo Running CMake configuration with D drive tools...
    echo Using CMake: %CMAKE_PATH%\cmake.exe
    echo Using VS2022: %VS2022_PATH%
    
    "%CMAKE_PATH%\cmake.exe" .. ^
        -G "Visual Studio 17 2022" ^
        -A x64 ^
        -DCMAKE_BUILD_TYPE=Release ^
        -DDLIB_NO_GUI_SUPPORT=ON ^
        -DDLIB_JPEG_SUPPORT=OFF ^
        -DDLIB_PNG_SUPPORT=OFF ^
        -DDLIB_GIF_SUPPORT=OFF ^
        -DCMAKE_INSTALL_PREFIX=../install
    
    if !errorlevel! equ 0 (
        echo ✅ CMake configuration successful!
        echo Building dlib...
        
        "%CMAKE_PATH%\cmake.exe" --build . --config Release --parallel 4
        
        if !errorlevel! equ 0 (
            echo ✅ Build successful!
            echo Installing dlib...
            cd ..
            pip install . -i https://pypi.tuna.tsinghua.edu.cn/simple/
            
            if !errorlevel! equ 0 (
                echo ✅ SUCCESS: dlib manually compiled and installed!
                cd ..
                goto :test_dlib
            )
        )
    ) else (
        echo ❌ CMake configuration failed
        cd ..\..
    )
) else (
    echo ❌ Failed to download dlib source
)

echo.
echo ================================================
echo Method 3: Alternative versions with mirrors
echo ================================================

echo Trying dlib 19.22.1 (more compatible)...
pip install dlib==19.22.1 -i https://pypi.tuna.tsinghua.edu.cn/simple/

if !errorlevel! equ 0 (
    echo ✅ SUCCESS: dlib 19.22.1 installed!
    goto :test_dlib
)

echo Trying from Aliyun mirror...
pip install dlib==19.24.2 -i https://mirrors.aliyun.com/pypi/simple/

if !errorlevel! equ 0 (
    echo ✅ SUCCESS: dlib installed from Aliyun mirror!
    goto :test_dlib
)

echo.
echo ================================================
echo Method 4: Face detection alternatives
echo ================================================

echo Installing MediaPipe as high-quality alternative...
pip install mediapipe==0.10.3 -i https://pypi.tuna.tsinghua.edu.cn/simple/

if !errorlevel! equ 0 (
    echo ✅ MediaPipe installed successfully!
    echo This provides excellent face detection as dlib alternative
)

echo Installing other face detection libraries...
pip install face_recognition -i https://pypi.tuna.tsinghua.edu.cn/simple/

goto :test_dlib

:test_dlib
echo.
echo ================================================
echo Testing Installation Results
echo ================================================

echo Testing dlib import...
python -c "
try:
    import dlib
    print(f'✅ SUCCESS: dlib version {dlib.__version__} imported successfully')
    
    # Test face detection
    detector = dlib.get_frontal_face_detector()
    print('✅ Face detector loaded successfully')
    print('✅ dlib is ready for high-quality face detection!')
    
    dlib_available = True
except ImportError as e:
    print(f'❌ dlib import failed: {e}')
    dlib_available = False

# Test alternatives
try:
    import mediapipe as mp
    print('✅ MediaPipe available as alternative')
    mediapipe_available = True
except ImportError:
    print('❌ MediaPipe not available')
    mediapipe_available = False

try:
    import cv2
    print('✅ OpenCV available for basic face detection')
    opencv_available = True
except ImportError:
    print('❌ OpenCV not available')
    opencv_available = False

# Summary
print()
print('📊 Face Detection Capabilities Summary:')
if dlib_available:
    print('🏆 dlib: Available (Best quality, 68-point landmarks)')
elif mediapipe_available:
    print('🥈 MediaPipe: Available (Good quality, fast)')
elif opencv_available:
    print('🥉 OpenCV: Available (Basic quality)')
else:
    print('❌ No face detection available')
"

echo.
echo ================================================
echo Environment Summary
echo ================================================
echo.
echo 🔧 D Drive Setup:
echo   VS2022: %VS2022_PATH%
echo   CMake: %CMAKE_PATH%
echo   Python: %VENV_DIR%
echo.
echo 🌐 Mirrors configured:
echo   Primary: Tsinghua University
echo   Backup: Aliyun, Douban
echo.

python -c "
import sys
print(f'🐍 Python: {sys.version}')

try:
    import torch
    print(f'🔥 PyTorch: {torch.__version__} (CUDA: {torch.cuda.is_available()})')
except ImportError:
    print('❌ PyTorch not installed')

try:
    import cv2
    print(f'👁️ OpenCV: {cv2.__version__}')
except ImportError:
    print('❌ OpenCV not installed')
"

echo.
echo 🎯 Next steps:
echo 1. If dlib installed: download_dlib_models.bat
echo 2. Test MuseTalk service: setup_with_mirrors.bat
echo 3. Start service: start_musetalk_mirrors.bat
echo.
echo 💡 The D drive CMake setup should resolve compilation issues!
echo.
pause