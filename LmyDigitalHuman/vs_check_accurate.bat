@echo off

echo VS2022 Component Check (Accurate)
echo ====================================

echo.
echo 1. VS2022 installation:
if exist "D:\Program Files\Microsoft Visual Studio\2022\Community" (
    echo    FOUND: VS2022 Community on D drive
    set "VS_PATH=D:\Program Files\Microsoft Visual Studio\2022\Community"
) else if exist "C:\Program Files\Microsoft Visual Studio\2022\Community" (
    echo    FOUND: VS2022 Community on C drive
    set "VS_PATH=C:\Program Files\Microsoft Visual Studio\2022\Community"
) else if exist "C:\Program Files\Microsoft Visual Studio\2022\Professional" (
    echo    FOUND: VS2022 Professional
    set "VS_PATH=C:\Program Files\Microsoft Visual Studio\2022\Professional"
) else (
    echo    NOT FOUND
    goto :end
)

echo.
echo 2. MSVC compiler:
if exist "%VS_PATH%\VC\Tools\MSVC" (
    echo    FOUND
) else (
    echo    NOT FOUND
)

echo.
echo 3. Windows SDK (checking multiple locations):
set "SDK_FOUND=0"

REM 检查C盘标准位置
if exist "C:\Program Files (x86)\Windows Kits\10" (
    echo    FOUND: Windows 10 SDK on C drive
    set "SDK_FOUND=1"
)

if exist "C:\Program Files (x86)\Windows Kits\11" (
    echo    FOUND: Windows 11 SDK on C drive
    set "SDK_FOUND=1"
)

REM 检查D盘位置
if exist "D:\Program Files (x86)\Windows Kits\10" (
    echo    FOUND: Windows 10 SDK on D drive
    set "SDK_FOUND=1"
)

if exist "D:\Program Files (x86)\Windows Kits\11" (
    echo    FOUND: Windows 11 SDK on D drive
    set "SDK_FOUND=1"
)

REM 检查VS2022内置SDK
if exist "%VS_PATH%\VC\Auxiliary\Build\Microsoft.VCToolsVersion.default.txt" (
    echo    FOUND: VS2022 integrated build tools
    set "SDK_FOUND=1"
)

if "%SDK_FOUND%"=="0" (
    echo    NOT FOUND in standard locations
)

echo.
echo 4. CMake:
cmake --version >nul 2>&1
if %errorlevel% equ 0 (
    echo    FOUND
) else (
    echo    NOT FOUND
)

echo.
echo 5. Testing VS2022 environment setup:
if exist "%VS_PATH%\VC\Auxiliary\Build\vcvars64.bat" (
    echo    Testing vcvars64.bat...
    call "%VS_PATH%\VC\Auxiliary\Build\vcvars64.bat" >nul 2>&1
    if %errorlevel% equ 0 (
        echo    FOUND: VS environment setup works
        
        REM 测试编译器是否可用
        where cl.exe >nul 2>&1
        if %errorlevel% equ 0 (
            echo    FOUND: C++ compiler accessible after VS setup
        ) else (
            echo    WARNING: C++ compiler not accessible
        )
    ) else (
        echo    ERROR: VS environment setup failed
    )
) else (
    echo    ERROR: vcvars64.bat not found
)

echo.
echo ====================================
echo Diagnosis Complete
echo ====================================
echo.

if "%SDK_FOUND%"=="1" (
    echo RECOMMENDATION: Try fix_vs2022_environment.bat
    echo VS2022 should be able to find SDK through vcvars64.bat
) else (
    echo RECOMMENDATION: 
    echo 1. Open Visual Studio Installer
    echo 2. Modify VS2022 installation  
    echo 3. Ensure Windows SDK is checked in Individual Components
    echo 4. Or use setup_minimal_environment.bat to skip dlib
)

echo.
:end
pause