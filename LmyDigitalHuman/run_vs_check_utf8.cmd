@echo off
chcp 65001 >nul 2>&1

echo =============================================
echo VS2022 Component Check
echo =============================================
echo.

echo 1. Checking VS2022 installation...
if exist "C:\Program Files\Microsoft Visual Studio\2022\Community" (
    echo   [OK] VS2022 Community found
    set "VS_PATH=C:\Program Files\Microsoft Visual Studio\2022\Community"
) else if exist "C:\Program Files\Microsoft Visual Studio\2022\Professional" (
    echo   [OK] VS2022 Professional found
    set "VS_PATH=C:\Program Files\Microsoft Visual Studio\2022\Professional"
) else if exist "C:\Program Files\Microsoft Visual Studio\2022\Enterprise" (
    echo   [OK] VS2022 Enterprise found
    set "VS_PATH=C:\Program Files\Microsoft Visual Studio\2022\Enterprise"
) else if exist "D:\Program Files\Microsoft Visual Studio\2022\Community" (
    echo   [OK] VS2022 Community found (D drive)
    set "VS_PATH=D:\Program Files\Microsoft Visual Studio\2022\Community"
) else if exist "D:\Program Files\Microsoft Visual Studio\2022\Professional" (
    echo   [OK] VS2022 Professional found (D drive)
    set "VS_PATH=D:\Program Files\Microsoft Visual Studio\2022\Professional"
) else (
    echo   [FAIL] VS2022 not found
    goto :end
)

echo.
echo 2. Checking MSVC compiler...
if exist "%VS_PATH%\VC\Tools\MSVC" (
    echo   [OK] MSVC compiler installed
) else (
    echo   [FAIL] MSVC compiler not found
)

echo.
echo 3. Checking Windows SDK...
if exist "C:\Program Files (x86)\Windows Kits\10" (
    echo   [OK] Windows SDK installed
) else (
    echo   [FAIL] Windows SDK not found
)

echo.
echo 4. Checking CMake...
cmake --version >nul 2>&1
if %errorlevel% equ 0 (
    echo   [OK] CMake installed
) else (
    echo   [FAIL] CMake not found or not in PATH
)

echo.
echo =============================================
echo Check Complete
echo =============================================
echo.
echo If all items show [OK], you can try compiling dlib
echo If any item shows [FAIL], install missing components via Visual Studio Installer
echo.

:end
echo Press any key to continue...
pause >nul