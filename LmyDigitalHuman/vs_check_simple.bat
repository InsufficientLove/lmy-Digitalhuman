@echo off

echo VS2022 Component Check
echo ========================

echo.
echo 1. VS2022 installation:
if exist "C:\Program Files\Microsoft Visual Studio\2022\Community" (
    echo    FOUND: VS2022 Community
    set "VS_OK=1"
) else if exist "C:\Program Files\Microsoft Visual Studio\2022\Professional" (
    echo    FOUND: VS2022 Professional
    set "VS_OK=1"
) else if exist "D:\Program Files\Microsoft Visual Studio\2022\Community" (
    echo    FOUND: VS2022 Community on D drive
    set "VS_OK=1"
) else (
    echo    NOT FOUND
    set "VS_OK=0"
)

echo.
echo 2. MSVC compiler:
if exist "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Tools\MSVC" (
    echo    FOUND
) else if exist "C:\Program Files\Microsoft Visual Studio\2022\Professional\VC\Tools\MSVC" (
    echo    FOUND
) else if exist "D:\Program Files\Microsoft Visual Studio\2022\Community\VC\Tools\MSVC" (
    echo    FOUND
) else (
    echo    NOT FOUND
)

echo.
echo 3. Windows SDK:
if exist "C:\Program Files (x86)\Windows Kits\10" (
    echo    FOUND
) else (
    echo    NOT FOUND
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
echo ========================
echo Check Complete
echo ========================
echo.
echo If all items show FOUND, run: fix_vs2022_environment.bat
echo If any item shows NOT FOUND, install via Visual Studio Installer
echo.
pause