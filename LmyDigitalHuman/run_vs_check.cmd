@echo off
echo =============================================
echo VS2022组件快速检查
echo =============================================
echo.

echo 1. 检查VS2022安装...
if exist "C:\Program Files\Microsoft Visual Studio\2022\Community" (
    echo   ✓ VS2022 Community 已安装
    set "VS_PATH=C:\Program Files\Microsoft Visual Studio\2022\Community"
) else if exist "C:\Program Files\Microsoft Visual Studio\2022\Professional" (
    echo   ✓ VS2022 Professional 已安装  
    set "VS_PATH=C:\Program Files\Microsoft Visual Studio\2022\Professional"
) else if exist "D:\Program Files\Microsoft Visual Studio\2022\Community" (
    echo   ✓ VS2022 Community 已安装 (D盘)
    set "VS_PATH=D:\Program Files\Microsoft Visual Studio\2022\Community"
) else (
    echo   ✗ 未找到VS2022安装
    goto :end
)

echo.
echo 2. 检查MSVC编译器...
if exist "%VS_PATH%\VC\Tools\MSVC" (
    echo   ✓ MSVC编译器已安装
) else (
    echo   ✗ MSVC编译器未安装
)

echo.
echo 3. 检查Windows SDK...
if exist "C:\Program Files (x86)\Windows Kits\10" (
    echo   ✓ Windows SDK已安装
) else (
    echo   ✗ Windows SDK未安装
)

echo.
echo 4. 检查CMake...
cmake --version >nul 2>&1
if %errorlevel% equ 0 (
    echo   ✓ CMake已安装
) else (
    echo   ✗ CMake未安装或不在PATH中
)

echo.
echo =============================================
echo 检查完成
echo =============================================
echo.
echo 如果所有组件都显示 ✓，可以尝试编译dlib
echo 如果有 ✗ 项目，需要通过Visual Studio Installer安装
echo.

:end
echo 按任意键继续...
pause >nul