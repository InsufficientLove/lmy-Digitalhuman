@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ================================================
echo Ultimate dlib Solution for Complex D Drive Setup
echo ================================================
echo All tools on D drive: VS2022 + CMake + Python + Project
echo.

REM Environment paths - all on D drive
set "VS2022_PATH=D:\Program Files\Microsoft Visual Studio\2022\Community"
set "CMAKE_PATH=D:\Program Files\CMake\bin"
set "BASE_DIR=F:\AI\DigitalHuman_Portable"
set "VENV_DIR=%BASE_DIR%\venv"

echo Verifying D drive environment...
if not exist "%VS2022_PATH%\VC\Tools\MSVC" (
    echo ERROR: VS2022 not found at %VS2022_PATH%
    pause
    exit /b 1
)

if not exist "%CMAKE_PATH%\cmake.exe" (
    echo ERROR: CMake not found at %CMAKE_PATH%
    pause
    exit /b 1
)

if not exist "%VENV_DIR%\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found at %VENV_DIR%
    pause
    exit /b 1
)

echo SUCCESS: VS2022 found at %VS2022_PATH%
echo SUCCESS: CMake found at %CMAKE_PATH%
echo SUCCESS: Python venv found at %VENV_DIR%

echo.
echo Setting up complete D drive environment...

REM Critical: Set D drive CMake first in PATH
set "PATH=%CMAKE_PATH%;%PATH%"

REM Initialize VS2022 environment
echo Initializing VS2022 environment...
call "%VS2022_PATH%\VC\Auxiliary\Build\vcvars64.bat" >nul 2>&1

REM Activate Python environment
echo Activating Python environment...
call "%VENV_DIR%\Scripts\activate.bat"

echo.
echo Verifying environment setup...
echo CMake location:
where cmake 2>nul || echo CMake not in PATH
echo CMake version:
cmake --version 2>nul || echo CMake execution failed
echo Compiler location:
where cl 2>nul || echo Compiler not found
echo Python location:
where python

echo.
echo Configuring pip for Chinese mirrors...
if not exist "%USERPROFILE%\.pip" mkdir "%USERPROFILE%\.pip"

(
echo [global]
echo index-url = https://pypi.tuna.tsinghua.edu.cn/simple/
echo trusted-host = pypi.tuna.tsinghua.edu.cn
echo timeout = 120
echo retries = 5
echo [install]
echo trusted-host = pypi.tuna.tsinghua.edu.cn
) > "%USERPROFILE%\.pip\pip.conf"

echo.
echo Upgrading pip and build tools...
python -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple/
pip install --upgrade setuptools wheel cmake -i https://pypi.tuna.tsinghua.edu.cn/simple/

echo.
echo ================================================
echo Method 1: Pre-compiled dlib wheel (Fastest)
echo ================================================

echo Trying pre-compiled dlib wheels...
pip install dlib -i https://pypi.tuna.tsinghua.edu.cn/simple/ --only-binary=all --no-cache-dir

if !errorlevel! equ 0 (
    echo SUCCESS: Pre-compiled dlib installed!
    goto :install_alternatives
)

echo Pre-compiled wheel failed, trying different sources...
pip install dlib -i https://mirrors.aliyun.com/pypi/simple/ --only-binary=all --no-cache-dir

if !errorlevel! equ 0 (
    echo SUCCESS: dlib installed from Aliyun!
    goto :install_alternatives
)

echo.
echo ================================================
echo Method 2: Explicit D Drive CMake Compilation
echo ================================================

echo Setting explicit CMake environment variables...
set CMAKE_GENERATOR=Visual Studio 17 2022
set CMAKE_GENERATOR_PLATFORM=x64
set CMAKE_GENERATOR_TOOLSET=v143
set CMAKE_BUILD_TYPE=Release
set CMAKE_C_COMPILER=cl.exe
set CMAKE_CXX_COMPILER=cl.exe

REM Force use D drive CMake
set CMAKE_COMMAND=%CMAKE_PATH%\cmake.exe

echo Using CMake: %CMAKE_COMMAND%
echo Testing CMake execution:
"%CMAKE_COMMAND%" --version

echo.
echo Attempting dlib compilation with explicit D drive CMake...
set CMAKE_ARGS=-DCMAKE_GENERATOR="Visual Studio 17 2022" -DCMAKE_GENERATOR_PLATFORM=x64

pip install dlib==19.24.2 -i https://pypi.tuna.tsinghua.edu.cn/simple/ --no-cache-dir --verbose

if !errorlevel! equ 0 (
    echo SUCCESS: dlib compiled with D drive CMake!
    goto :install_alternatives
)

echo.
echo ================================================
echo Method 3: Manual dlib compilation
echo ================================================

echo Creating temporary build directory...
if not exist "%BASE_DIR%\temp_build" mkdir "%BASE_DIR%\temp_build"
cd /d "%BASE_DIR%\temp_build"

echo Downloading dlib source...
pip download dlib==19.24.2 --no-deps -i https://pypi.tuna.tsinghua.edu.cn/simple/

if exist dlib-19.24.2.tar.gz (
    echo Extracting dlib...
    tar -xzf dlib-19.24.2.tar.gz
    cd dlib-19.24.2
    
    echo Creating build directory...
    if exist build rmdir /s /q build
    mkdir build
    cd build
    
    echo Running CMake with D drive tools...
    "%CMAKE_COMMAND%" .. ^
        -G "Visual Studio 17 2022" ^
        -A x64 ^
        -DCMAKE_BUILD_TYPE=Release ^
        -DDLIB_NO_GUI_SUPPORT=ON ^
        -DDLIB_JPEG_SUPPORT=OFF ^
        -DDLIB_PNG_SUPPORT=OFF ^
        -DDLIB_GIF_SUPPORT=OFF
    
    if !errorlevel! equ 0 (
        echo CMake configuration successful!
        echo Building dlib...
        "%CMAKE_COMMAND%" --build . --config Release --parallel 4
        
        if !errorlevel! equ 0 (
            echo Build successful! Installing...
            cd ..
            pip install . -i https://pypi.tuna.tsinghua.edu.cn/simple/
            
            if !errorlevel! equ 0 (
                echo SUCCESS: Manual dlib compilation completed!
                cd /d "%BASE_DIR%"
                goto :install_alternatives
            )
        )
    )
    
    cd /d "%BASE_DIR%"
)

echo.
echo ================================================
echo Method 4: Compatible dlib versions
echo ================================================

echo Trying older compatible dlib versions...
pip install dlib==19.22.1 -i https://pypi.tuna.tsinghua.edu.cn/simple/

if !errorlevel! equ 0 (
    echo SUCCESS: dlib 19.22.1 installed!
    goto :install_alternatives
)

pip install dlib==19.21.1 -i https://pypi.tuna.tsinghua.edu.cn/simple/

if !errorlevel! equ 0 (
    echo SUCCESS: dlib 19.21.1 installed!
    goto :install_alternatives
)

:install_alternatives
echo.
echo ================================================
echo Installing Face Detection Alternatives
echo ================================================

echo Installing MediaPipe (latest available version)...
pip install mediapipe -i https://pypi.tuna.tsinghua.edu.cn/simple/ --no-cache-dir

if !errorlevel! equ 0 (
    echo SUCCESS: MediaPipe installed!
) else (
    echo WARNING: MediaPipe installation failed
)

echo Installing face_recognition...
pip install face_recognition -i https://pypi.tuna.tsinghua.edu.cn/simple/

if !errorlevel! equ 0 (
    echo SUCCESS: face_recognition installed!
) else (
    echo WARNING: face_recognition installation failed
)

echo Installing additional CV libraries...
pip install opencv-python -i https://pypi.tuna.tsinghua.edu.cn/simple/

echo.
echo ================================================
echo Testing Installation Results
echo ================================================

echo Testing face detection libraries...
python -c "
import sys
print('Python path:', sys.executable)
print()

# Test dlib
try:
    import dlib
    print('SUCCESS: dlib version', dlib.__version__)
    detector = dlib.get_frontal_face_detector()
    print('SUCCESS: dlib face detector loaded')
    dlib_available = True
except Exception as e:
    print('FAILED: dlib not available -', str(e))
    dlib_available = False

# Test MediaPipe
try:
    import mediapipe as mp
    print('SUCCESS: MediaPipe version', mp.__version__)
    mp_face_detection = mp.solutions.face_detection
    print('SUCCESS: MediaPipe face detection available')
    mediapipe_available = True
except Exception as e:
    print('FAILED: MediaPipe not available -', str(e))
    mediapipe_available = False

# Test OpenCV
try:
    import cv2
    print('SUCCESS: OpenCV version', cv2.__version__)
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    print('SUCCESS: OpenCV face detection available')
    opencv_available = True
except Exception as e:
    print('FAILED: OpenCV not available -', str(e))
    opencv_available = False

# Summary
print()
print('=== FACE DETECTION SUMMARY ===')
if dlib_available:
    print('BEST: dlib - High quality 68-point face landmarks')
elif mediapipe_available:
    print('GOOD: MediaPipe - Fast and accurate face detection')
elif opencv_available:
    print('BASIC: OpenCV - Basic face detection')
else:
    print('ERROR: No face detection available!')
    
print()
print('=== RECOMMENDATIONS ===')
if dlib_available:
    print('Perfect setup! Use dlib for best quality.')
elif mediapipe_available:
    print('Good setup! MediaPipe provides excellent quality.')
elif opencv_available:
    print('Basic setup. Consider installing dlib or MediaPipe.')
else:
    print('Critical: No face detection available. Check installation.')
"

echo.
echo ================================================
echo Environment Summary
echo ================================================
echo.
echo D Drive Complex Environment:
echo   VS2022: %VS2022_PATH%
echo   CMake: %CMAKE_PATH%
echo   Python: %VENV_DIR%
echo   Project: All on D drive
echo.
echo Optimizations Applied:
echo   - D drive CMake priority in PATH
echo   - VS2022 environment initialization
echo   - Chinese mirror acceleration
echo   - Multiple installation methods
echo   - UTF-8 encoding for no garbled text
echo.
echo Next Steps:
echo 1. If any face detection works, proceed with MuseTalk setup
echo 2. Test with: test_d_drive_environment.bat
echo 3. Start service: start_musetalk_d_drive.bat
echo.

if exist "%BASE_DIR%\temp_build" (
    echo Cleaning up temporary files...
    rmdir /s /q "%BASE_DIR%\temp_build"
)

echo.
echo Script completed! Check results above.
pause