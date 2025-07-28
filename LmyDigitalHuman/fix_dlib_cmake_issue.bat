@echo off
setlocal enabledelayedexpansion

echo ================================================
echo dlib CMake Configuration Fix
echo ================================================
echo Targeting specific CMake issues for dlib compilation
echo.

echo Detecting VS2022 and CMake...
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
echo Setting up VS2022 environment with specific CMake configuration...

REM Set VS2022 environment
call "!VS2022_PATH!\VC\Auxiliary\Build\vcvars64.bat"

echo.
echo Checking CMake version and configuration...
cmake --version
if %errorlevel% neq 0 (
    echo CMake not found in PATH
    echo Adding VS2022 CMake to PATH...
    set "PATH=!VS2022_PATH!\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin;!PATH!"
    cmake --version
)

echo.
echo Activating Python environment...
set "BASE_DIR=F:\AI\DigitalHuman_Portable"
set "VENV_DIR=%BASE_DIR%\venv"
call "%VENV_DIR%\Scripts\activate.bat"

echo.
echo Setting specific CMake environment variables for dlib...
set CMAKE_GENERATOR=Visual Studio 17 2022
set CMAKE_GENERATOR_PLATFORM=x64
set CMAKE_GENERATOR_TOOLSET=v143
set CMAKE_BUILD_TYPE=Release

REM Force specific compiler paths
set CMAKE_C_COMPILER=cl.exe
set CMAKE_CXX_COMPILER=cl.exe

REM Set Windows SDK version explicitly
for /f "tokens=*" %%i in ('dir "C:\Program Files (x86)\Windows Kits\10\Include" /b /ad ^| findstr "10\." ^| sort /r') do (
    set "WINDOWS_SDK_VERSION=%%i"
    goto :sdk_found
)
:sdk_found

if defined WINDOWS_SDK_VERSION (
    echo Using Windows SDK: %WINDOWS_SDK_VERSION%
    set CMAKE_SYSTEM_VERSION=%WINDOWS_SDK_VERSION%
) else (
    echo Warning: Could not detect Windows SDK version
)

echo.
echo Upgrading build tools...
python -m pip install --upgrade pip setuptools wheel
pip install --upgrade cmake

echo.
echo Attempting dlib compilation with specific CMake flags...

REM Method 1: Direct pip install with verbose output and specific CMake args
echo Method 1: Direct compilation with CMake arguments...
set CMAKE_ARGS=-DCMAKE_GENERATOR="Visual Studio 17 2022" -DCMAKE_GENERATOR_PLATFORM=x64 -DCMAKE_BUILD_TYPE=Release

pip install --no-cache-dir --force-reinstall --verbose dlib==19.24.2

if !errorlevel! equ 0 (
    echo SUCCESS: dlib compiled successfully!
    goto :test_dlib
)

echo.
echo Method 1 failed, trying Method 2: Manual CMake configuration...

REM Method 2: Download source and compile manually
echo Downloading dlib source...
pip download --no-deps dlib==19.24.2
if exist dlib-19.24.2.tar.gz (
    echo Extracting dlib source...
    tar -xzf dlib-19.24.2.tar.gz
    cd dlib-19.24.2
    
    echo Creating build directory...
    mkdir build
    cd build
    
    echo Running CMake configuration...
    cmake .. -G "Visual Studio 17 2022" -A x64 -DCMAKE_BUILD_TYPE=Release -DDLIB_NO_GUI_SUPPORT=ON -DDLIB_JPEG_SUPPORT=OFF -DDLIB_PNG_SUPPORT=OFF -DDLIB_GIF_SUPPORT=OFF
    
    if !errorlevel! equ 0 (
        echo CMake configuration successful, building...
        cmake --build . --config Release
        
        if !errorlevel! equ 0 (
            echo Manual build successful, installing...
            cd ..
            pip install .
            
            if !errorlevel! equ 0 (
                echo SUCCESS: dlib manually compiled and installed!
                cd ..\..
                goto :test_dlib
            )
        )
    )
    
    cd ..\..
)

echo.
echo Method 2 failed, trying Method 3: Simplified configuration...

REM Method 3: Try with minimal CMake configuration
echo Method 3: Minimal CMake configuration...
set CMAKE_ARGS=-DDLIB_NO_GUI_SUPPORT=ON -DDLIB_JPEG_SUPPORT=OFF

pip install --no-cache-dir --force-reinstall dlib==19.24.2 --global-option=build_ext --global-option=--cmake-args="-DDLIB_NO_GUI_SUPPORT=ON"

if !errorlevel! equ 0 (
    echo SUCCESS: dlib installed with minimal configuration!
    goto :test_dlib
)

echo.
echo Method 3 failed, trying Method 4: Alternative version...
pip install dlib==19.22.1

if !errorlevel! equ 0 (
    echo SUCCESS: dlib alternative version installed!
    goto :test_dlib
)

echo.
echo All methods failed. Analyzing the issue...
echo.
echo Possible solutions:
echo 1. Check if Windows SDK is properly installed
echo 2. Verify CMake can find the compiler
echo 3. Try installing Visual Studio Build Tools separately
echo 4. Use conda instead of pip for dlib
echo.
echo Would you like to try conda installation? (y/n)
set /p use_conda="Enter choice: "

if /i "%use_conda%"=="y" (
    echo Installing conda dlib...
    pip install conda
    conda install -c conda-forge dlib
)

goto :end

:test_dlib
echo.
echo Testing dlib installation...
python -c "import dlib; print(f'dlib version: {dlib.__version__}'); print('dlib import successful!')"

if !errorlevel! equ 0 (
    echo.
    echo ================================================
    echo dlib Installation Successful!
    echo ================================================
    echo.
    echo Testing face detection capability...
    python -c "
import dlib
import numpy as np
detector = dlib.get_frontal_face_detector()
predictor_path = 'shape_predictor_68_face_landmarks.dat'
print('Face detector loaded successfully')
print('dlib is ready for MuseTalk!')
"
    
    echo.
    echo Next steps:
    echo 1. Download face landmark predictor model
    echo 2. Continue with MuseTalk setup
    echo 3. Test full pipeline
    
) else (
    echo dlib import test failed
)

:end
echo.
pause