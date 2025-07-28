@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ================================================
echo dlib Compilation with VS Built-in CMake ONLY
echo ================================================
echo Using ONLY Visual Studio built-in CMake tools
echo No external CMake installation needed
echo.

REM Environment paths - VS2022 with built-in CMake
set "VS2022_PATH=D:\Program Files\Microsoft Visual Studio\2022\Community"
set "VS_CMAKE_PATH=%VS2022_PATH%\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin"
set "BASE_DIR=F:\AI\DigitalHuman_Portable"
set "VENV_DIR=%BASE_DIR%\venv"

echo ===========================================
echo 1. Environment Verification
echo ===========================================

echo Checking VS2022 installation...
if exist "%VS2022_PATH%\VC\Tools\MSVC" (
    echo ✅ VS2022 found: %VS2022_PATH%
) else (
    echo ❌ VS2022 not found at: %VS2022_PATH%
    echo.
    echo ERROR: VS2022 is required for this script
    echo Press any key to exit...
    pause >nul
    exit /b 1
)

echo Checking VS built-in CMake...
if exist "%VS_CMAKE_PATH%\cmake.exe" (
    echo ✅ VS built-in CMake found: %VS_CMAKE_PATH%
    echo CMake version:
    "%VS_CMAKE_PATH%\cmake.exe" --version
) else (
    echo ❌ VS built-in CMake not found at: %VS_CMAKE_PATH%
    echo.
    echo ERROR: VS CMake tools not installed
    echo Please install "C++ CMake tools for Visual Studio" in VS Installer
    echo Press any key to exit...
    pause >nul
    exit /b 1
)

echo Checking Python virtual environment...
if exist "%VENV_DIR%\Scripts\activate.bat" (
    echo ✅ Virtual environment found: %VENV_DIR%
) else (
    echo ❌ Virtual environment not found: %VENV_DIR%
    echo.
    echo ERROR: Run a setup script first to create virtual environment
    echo Press any key to exit...
    pause >nul
    exit /b 1
)

echo.
echo ===========================================
echo 2. Environment Setup
echo ===========================================

echo Setting up VS2022 environment with built-in CMake...

REM Critical: Use ONLY VS built-in CMake, clear any external CMake from PATH
echo Clearing external CMake from PATH...
set "PATH=%SystemRoot%\system32;%SystemRoot%;%SystemRoot%\System32\Wbem"

REM Add VS built-in CMake FIRST in PATH
echo Adding VS built-in CMake to PATH...
set "PATH=%VS_CMAKE_PATH%;%PATH%"

REM Initialize VS2022 environment
echo Initializing VS2022 build environment...
call "%VS2022_PATH%\VC\Auxiliary\Build\vcvars64.bat"

if !errorlevel! neq 0 (
    echo ❌ Failed to initialize VS2022 environment
    echo Press any key to exit...
    pause >nul
    exit /b 1
)

REM Activate Python environment
echo Activating Python virtual environment...
call "%VENV_DIR%\Scripts\activate.bat"

echo.
echo ===========================================
echo 3. Tool Verification
echo ===========================================

echo Verifying CMake (should be VS built-in)...
where cmake
echo.
echo CMake version:
cmake --version
echo.

echo Verifying C++ compiler...
where cl
echo.
echo Compiler version:
cl 2>&1 | findstr "Microsoft"

echo.
echo ===========================================
echo 4. Pip Configuration
echo ===========================================

echo Configuring pip mirrors for faster downloads...
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

echo ✅ Pip mirrors configured

echo.
echo Upgrading pip and build tools...
python -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple/
pip install --upgrade setuptools wheel -i https://pypi.tuna.tsinghua.edu.cn/simple/

echo.
echo ===========================================
echo 5. dlib Compilation Method 1: Direct pip install
echo ===========================================

echo Setting CMake environment variables for VS built-in tools...
set CMAKE_GENERATOR=Visual Studio 17 2022
set CMAKE_GENERATOR_PLATFORM=x64
set CMAKE_GENERATOR_TOOLSET=v143
set CMAKE_BUILD_TYPE=Release
set CMAKE_C_COMPILER=cl.exe
set CMAKE_CXX_COMPILER=cl.exe

REM Force use of VS built-in CMake
set CMAKE_COMMAND=%VS_CMAKE_PATH%\cmake.exe

echo Using CMake: %CMAKE_COMMAND%
echo Testing CMake execution:
"%CMAKE_COMMAND%" --version

echo.
echo Attempting dlib installation with VS built-in CMake...
echo This may take several minutes, please wait...
echo.

pip install dlib==19.24.2 -i https://pypi.tuna.tsinghua.edu.cn/simple/ --no-cache-dir --verbose

if !errorlevel! equ 0 (
    echo.
    echo ✅ SUCCESS: dlib compiled successfully with VS built-in CMake!
    echo Testing dlib import...
    python -c "import dlib; print('dlib version:', dlib.__version__); print('dlib working correctly!')"
    goto :success_end
) else (
    echo.
    echo ❌ Method 1 failed, trying alternative approach...
)

echo.
echo ===========================================
echo 6. dlib Compilation Method 2: Manual build
echo ===========================================

echo Creating temporary build directory...
if not exist "%BASE_DIR%\temp_build" mkdir "%BASE_DIR%\temp_build"
cd /d "%BASE_DIR%\temp_build"

echo Downloading dlib source code...
pip download dlib==19.24.2 --no-deps -i https://pypi.tuna.tsinghua.edu.cn/simple/

if exist dlib-19.24.2.tar.gz (
    echo ✅ dlib source downloaded
    echo Extracting source...
    tar -xzf dlib-19.24.2.tar.gz
    cd dlib-19.24.2
    
    echo Creating build directory...
    if exist build rmdir /s /q build
    mkdir build
    cd build
    
    echo.
    echo Running CMake configuration with VS built-in CMake...
    echo Using: %CMAKE_COMMAND%
    echo.
    
    "%CMAKE_COMMAND%" .. ^
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
        echo.
        echo Building dlib (this will take several minutes)...
        "%CMAKE_COMMAND%" --build . --config Release --parallel 4
        
        if !errorlevel! equ 0 (
            echo ✅ Build successful!
            echo Installing dlib...
            cd ..
            pip install . -i https://pypi.tuna.tsinghua.edu.cn/simple/
            
            if !errorlevel! equ 0 (
                echo.
                echo ✅ SUCCESS: dlib manually compiled and installed!
                echo Testing dlib import...
                python -c "import dlib; print('dlib version:', dlib.__version__); print('dlib working correctly!')"
                cd /d "%BASE_DIR%"
                goto :success_end
            else (
                echo ❌ dlib installation failed
                cd /d "%BASE_DIR%"
            )
        else (
            echo ❌ dlib build failed
            cd /d "%BASE_DIR%"
        )
    ) else (
        echo ❌ CMake configuration failed
        cd /d "%BASE_DIR%"
    )
) else (
    echo ❌ Failed to download dlib source
    cd /d "%BASE_DIR%"
)

echo.
echo ===========================================
echo 7. dlib Compilation Method 3: Compatible versions
echo ===========================================

echo Trying older dlib versions that might be more compatible...

echo Trying dlib 19.22.1...
pip install dlib==19.22.1 -i https://pypi.tuna.tsinghua.edu.cn/simple/ --no-cache-dir

if !errorlevel! equ 0 (
    echo ✅ SUCCESS: dlib 19.22.1 installed!
    python -c "import dlib; print('dlib version:', dlib.__version__)"
    goto :success_end
)

echo Trying dlib 19.21.1...
pip install dlib==19.21.1 -i https://pypi.tuna.tsinghua.edu.cn/simple/ --no-cache-dir

if !errorlevel! equ 0 (
    echo ✅ SUCCESS: dlib 19.21.1 installed!
    python -c "import dlib; print('dlib version:', dlib.__version__)"
    goto :success_end
)

echo.
echo ===========================================
echo 8. Alternative Face Detection Libraries
echo ===========================================

echo dlib compilation failed with all methods.
echo Installing alternative face detection libraries...

echo Installing MediaPipe...
pip install mediapipe -i https://pypi.tuna.tsinghua.edu.cn/simple/ --no-cache-dir

if !errorlevel! equ 0 (
    echo ✅ MediaPipe installed successfully!
    python -c "import mediapipe as mp; print('MediaPipe version:', mp.__version__)"
) else (
    echo ❌ MediaPipe installation failed
)

echo Installing face_recognition (if possible)...
pip install face_recognition -i https://pypi.tuna.tsinghua.edu.cn/simple/

echo Installing additional OpenCV...
pip install opencv-python -i https://pypi.tuna.tsinghua.edu.cn/simple/

goto :final_status

:success_end
echo.
echo ===========================================
echo 🎉 SUCCESS: dlib Installation Complete!
echo ===========================================
echo.
echo ✅ dlib has been successfully compiled and installed!
echo ✅ Using VS built-in CMake tools worked!
echo.
echo Testing final dlib functionality...
python -c "
try:
    import dlib
    print('✅ dlib import: SUCCESS')
    print('   Version:', dlib.__version__)
    
    # Test face detector
    detector = dlib.get_frontal_face_detector()
    print('✅ Face detector: OK')
    
    print()
    print('🏆 EXCELLENT: You now have the BEST face detection quality!')
    print('   dlib provides 68-point facial landmarks')
    print('   Perfect for high-quality digital human generation')
    
except Exception as e:
    print('❌ dlib test failed:', str(e))
"

echo.
echo Installing MediaPipe as additional option...
pip install mediapipe -i https://pypi.tuna.tsinghua.edu.cn/simple/ --no-cache-dir

goto :final_status

:final_status
echo.
echo ===========================================
echo Final Installation Status
echo ===========================================

python -c "
print('🔍 Final Component Check:')
print()

# Check dlib
try:
    import dlib
    print('✅ dlib: INSTALLED and working!')
    print('   Version:', dlib.__version__)
    print('   🏆 BEST quality face detection available')
    dlib_status = True
except ImportError:
    print('❌ dlib: Not available')
    dlib_status = False

# Check MediaPipe
try:
    import mediapipe as mp
    print('✅ MediaPipe: Available')
    print('   Version:', mp.__version__)
    print('   🥈 GOOD quality alternative')
    mp_status = True
except ImportError:
    print('❌ MediaPipe: Not available')
    mp_status = False

# Check OpenCV
try:
    import cv2
    print('✅ OpenCV: Available')
    print('   Version:', cv2.__version__)
    print('   🥉 BASIC quality fallback')
    cv_status = True
except ImportError:
    print('❌ OpenCV: Not available')
    cv_status = False

print()
print('📊 OVERALL STATUS:')
if dlib_status:
    print('🎉 EXCELLENT: dlib working with VS built-in CMake!')
    print('   You have the best possible face detection setup')
    print('   Ready for high-quality digital human generation')
elif mp_status:
    print('👍 GOOD: MediaPipe available as alternative')
    print('   Good quality face detection for digital humans')
elif cv_status:
    print('⚠️ BASIC: Only OpenCV available')
    print('   Limited quality, consider troubleshooting dlib')
else:
    print('❌ CRITICAL: No face detection available')
    print('   Need to resolve installation issues')
"

echo.
echo ===========================================
echo VS Built-in CMake Results Summary
echo ===========================================
echo.
echo Environment used:
echo   VS2022: %VS2022_PATH%
echo   VS CMake: %VS_CMAKE_PATH%
echo   Python: %VENV_DIR%
echo.
echo Strategy: Use ONLY VS built-in CMake tools
echo Result: Check status above
echo.

if exist "%BASE_DIR%\temp_build" (
    echo Cleaning up temporary files...
    rmdir /s /q "%BASE_DIR%\temp_build"
)

echo.
echo ===========================================
echo Next Steps
echo ===========================================
echo.
echo 1. Review the status above
echo 2. If dlib worked: You're ready for production!
echo 3. If dlib failed: MediaPipe is still very good
echo 4. Run verify_installation_status.bat for detailed check
echo 5. Start MuseTalk service and test
echo.
echo ===========================================
echo Script Complete - Window Stays Open
echo ===========================================
echo.
echo This window will NOT close automatically.
echo You can review all the output above.
echo.
echo Press any key when you're ready to close...
pause >nul