@echo off
setlocal enabledelayedexpansion

echo ================================================
echo dlib Installation with China Mirrors
echo ================================================
echo Using domestic mirrors for faster downloads
echo.

echo Configuring pip mirrors...
if not exist "%USERPROFILE%\.pip" mkdir "%USERPROFILE%\.pip"

(
echo [global]
echo index-url = https://pypi.tuna.tsinghua.edu.cn/simple/
echo trusted-host = pypi.tuna.tsinghua.edu.cn
echo timeout = 120
echo retries = 3
echo [install]
echo trusted-host = pypi.tuna.tsinghua.edu.cn
) > "%USERPROFILE%\.pip\pip.conf"

echo Mirror configured: Tsinghua University
echo.

echo Detecting VS2022 installation...
set "VS2022_PATH="

if exist "D:\Program Files\Microsoft Visual Studio\2022\Community\VC\Tools\MSVC" (
    set "VS2022_PATH=D:\Program Files\Microsoft Visual Studio\2022\Community"
    echo Found VS2022: !VS2022_PATH!
) else if exist "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Tools\MSVC" (
    set "VS2022_PATH=C:\Program Files\Microsoft Visual Studio\2022\Community"
    echo Found VS2022: !VS2022_PATH!
) else (
    echo VS2022 not found
    pause
    exit /b 1
)

echo.
echo Setting up VS2022 environment...
call "!VS2022_PATH!\VC\Auxiliary\Build\vcvars64.bat"

echo.
echo Activating Python environment...
set "BASE_DIR=F:\AI\DigitalHuman_Portable"
set "VENV_DIR=%BASE_DIR%\venv"
call "%VENV_DIR%\Scripts\activate.bat"

echo.
echo Setting CMake environment variables...
set CMAKE_GENERATOR=Visual Studio 17 2022
set CMAKE_GENERATOR_PLATFORM=x64
set CMAKE_GENERATOR_TOOLSET=v143
set CMAKE_BUILD_TYPE=Release
set CMAKE_C_COMPILER=cl.exe
set CMAKE_CXX_COMPILER=cl.exe

echo.
echo ================================================
echo Method 1: dlib from Tsinghua Mirror
echo ================================================

echo Upgrading build tools with mirror...
python -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple/
pip install --upgrade setuptools wheel -i https://pypi.tuna.tsinghua.edu.cn/simple/
pip install cmake -i https://pypi.tuna.tsinghua.edu.cn/simple/

echo Attempting dlib installation from Tsinghua mirror...
pip install dlib==19.24.2 -i https://pypi.tuna.tsinghua.edu.cn/simple/ --verbose

if !errorlevel! equ 0 (
    echo SUCCESS: dlib installed from Tsinghua mirror!
    goto :test_dlib
)

echo.
echo ================================================
echo Method 2: dlib from Aliyun Mirror
echo ================================================

echo Trying Aliyun mirror...
pip install dlib==19.24.2 -i https://mirrors.aliyun.com/pypi/simple/ --verbose

if !errorlevel! equ 0 (
    echo SUCCESS: dlib installed from Aliyun mirror!
    goto :test_dlib
)

echo.
echo ================================================
echo Method 3: dlib from Douban Mirror
echo ================================================

echo Trying Douban mirror...
pip install dlib==19.24.2 -i https://pypi.douban.com/simple/ --verbose

if !errorlevel! equ 0 (
    echo SUCCESS: dlib installed from Douban mirror!
    goto :test_dlib
)

echo.
echo ================================================
echo Method 4: Pre-compiled wheels from mirrors
echo ================================================

echo Trying pre-compiled wheels...
pip install dlib==19.22.1 -i https://pypi.tuna.tsinghua.edu.cn/simple/

if !errorlevel! equ 0 (
    echo SUCCESS: dlib compatible version installed!
    goto :test_dlib
)

echo.
echo ================================================
echo Method 5: Manual compilation with mirrors
echo ================================================

echo Downloading dlib source from mirror...
pip download dlib==19.24.2 -i https://pypi.tuna.tsinghua.edu.cn/simple/ --no-deps

if exist dlib-19.24.2.tar.gz (
    echo Extracting source...
    tar -xzf dlib-19.24.2.tar.gz
    cd dlib-19.24.2
    
    echo Manual compilation with VS2022...
    mkdir build
    cd build
    
    cmake .. -G "Visual Studio 17 2022" -A x64 -DCMAKE_BUILD_TYPE=Release -DDLIB_NO_GUI_SUPPORT=ON
    
    if !errorlevel! equ 0 (
        cmake --build . --config Release
        
        if !errorlevel! equ 0 (
            cd ..
            pip install . -i https://pypi.tuna.tsinghua.edu.cn/simple/
            
            if !errorlevel! equ 0 (
                echo SUCCESS: dlib manually compiled!
                cd ..\..
                goto :test_dlib
            )
        )
    )
    cd ..\..
)

echo.
echo ================================================
echo Method 6: Alternative face detection libraries
echo ================================================

echo Installing MediaPipe as alternative...
pip install mediapipe==0.10.3 -i https://pypi.tuna.tsinghua.edu.cn/simple/

if !errorlevel! equ 0 (
    echo MediaPipe installed successfully!
    echo This can be used as dlib alternative for face detection
)

echo Installing face_recognition (may include dlib)...
pip install face_recognition -i https://pypi.tuna.tsinghua.edu.cn/simple/

echo.
echo All methods attempted. Checking final status...
goto :test_dlib

:test_dlib
echo.
echo ================================================
echo Testing Installation
echo ================================================

echo Testing dlib import...
python -c "import dlib; print(f'SUCCESS: dlib version {dlib.__version__} imported successfully')"

if !errorlevel! equ 0 (
    echo.
    echo Testing face detection capability...
    python -c "
import dlib
import numpy as np
detector = dlib.get_frontal_face_detector()
print('Face detector loaded successfully')
print('dlib is ready for high-quality face detection!')
"
    
    echo.
    echo ================================================
    echo dlib Installation Successful!
    echo ================================================
    echo.
    echo Benefits of dlib installation:
    echo ✅ 68-point facial landmark detection
    echo ✅ High precision face tracking  
    echo ✅ Better lip-sync accuracy
    echo ✅ Stable video generation
    echo ✅ GPU acceleration support
    echo.
    echo Next steps:
    echo 1. Download face models: download_dlib_models.bat
    echo 2. Test with MuseTalk service
    
) else (
    echo.
    echo dlib import failed, checking alternatives...
    
    python -c "
try:
    import mediapipe as mp
    print('MediaPipe available as dlib alternative')
except ImportError:
    print('MediaPipe not available')

try:
    import cv2
    print('OpenCV available for basic face detection')
except ImportError:
    print('OpenCV not available')
"
    
    echo.
    echo ================================================
    echo Alternative Solutions
    echo ================================================
    echo.
    echo dlib installation failed, but you have alternatives:
    echo 1. Use MediaPipe for face detection (good quality)
    echo 2. Use OpenCV for basic face detection
    echo 3. Try conda installation: conda install -c conda-forge dlib
    echo 4. Use the no-dlib version for basic functionality
)

echo.
echo Mirror configuration saved for future use:
echo %USERPROFILE%\.pip\pip.conf
echo.
pause