@echo off
chcp 65001 >nul

echo ================================================================
echo 🔍 数字人系统安装调试脚本
echo ================================================================
echo 此脚本用于诊断安装问题，不会自动关闭
echo.

echo 📋 系统环境检查:
echo.

echo 🖥️  操作系统信息:
ver
echo.

echo 🐍 Python检查:
python --version 2>nul
if %errorlevel% neq 0 (
    echo ❌ Python 未安装或未添加到PATH
    echo 请从 https://www.python.org/downloads/ 下载安装Python
) else (
    echo ✅ Python 已安装
    echo Python路径:
    where python
)
echo.

echo 📦 pip检查:
pip --version 2>nul
if %errorlevel% neq 0 (
    echo ❌ pip 不可用
) else (
    echo ✅ pip 可用
)
echo.

echo 🔧 Visual Studio检查:
set "VS_FOUND=0"
if exist "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Tools\MSVC" (
    echo ✅ VS2022 Community 已安装
    set "VS_FOUND=1"
)
if exist "C:\Program Files\Microsoft Visual Studio\2022\Professional\VC\Tools\MSVC" (
    echo ✅ VS2022 Professional 已安装
    set "VS_FOUND=1"
)
if exist "C:\Program Files\Microsoft Visual Studio\2022\Enterprise\VC\Tools\MSVC" (
    echo ✅ VS2022 Enterprise 已安装
    set "VS_FOUND=1"
)
if exist "C:\Program Files\Microsoft Visual Studio\2019\Community\VC\Tools\MSVC" (
    echo ✅ VS2019 Community 已安装
    set "VS_FOUND=1"
)

if "%VS_FOUND%"=="0" (
    echo ❌ 未找到Visual Studio
    echo 请从 https://visualstudio.microsoft.com/downloads/ 下载安装
)
echo.

echo 🛠️  CMake检查:
cmake --version 2>nul
if %errorlevel% neq 0 (
    echo ❌ CMake 未安装或未添加到PATH
    echo 请从 https://cmake.org/download/ 下载安装CMake
) else (
    echo ✅ CMake 已安装
    echo CMake路径:
    where cmake
)
echo.

echo 💾 磁盘空间检查:
echo C盘可用空间:
dir C:\ | findstr "bytes free"
echo.

echo 🌐 网络连接检查:
ping -n 1 pypi.tuna.tsinghua.edu.cn >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ 可以连接到清华镜像源
) else (
    echo ❌ 无法连接到清华镜像源
    echo 请检查网络连接
)
echo.

echo 👤 用户权限检查:
mkdir "%TEMP%\test_permissions" 2>nul
if %errorlevel% equ 0 (
    echo ✅ 具有创建目录的权限
    rmdir "%TEMP%\test_permissions" 2>nul
) else (
    echo ❌ 权限不足，建议以管理员身份运行
)
echo.

echo ================================================================
echo 📊 诊断结果总结
echo ================================================================
echo.
echo 如果上述检查中有❌标记，请先解决这些问题：
echo.
echo 1. 安装Python: https://www.python.org/downloads/
echo    - 下载Python 3.8或更高版本
echo    - 安装时勾选"Add Python to PATH"
echo.
echo 2. 安装Visual Studio: https://visualstudio.microsoft.com/downloads/
echo    - 选择Community版本（免费）
echo    - 安装时选择"C++桌面开发"工作负载
echo.
echo 3. 安装CMake: https://cmake.org/download/
echo    - 下载Windows x64 Installer
echo    - 安装时选择"Add CMake to PATH"
echo.
echo 4. 检查网络连接和防火墙设置
echo.
echo 5. 以管理员身份运行安装脚本
echo.

echo 解决上述问题后，请运行:
echo   install_complete_universal_fixed.bat
echo.

echo ================================================================
echo 窗口保持打开 - 按任意键关闭
echo ================================================================
pause >nul