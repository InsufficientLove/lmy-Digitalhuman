@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ================================================================
echo 🔍 数字人系统安装调试脚本 - 增强版
echo ================================================================
echo 此脚本用于诊断安装问题，支持D盘VS和VS内置CMake
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
) else (
    echo ✅ Python 已安装
    echo Python版本和路径:
    where python
    echo.
    echo 🔍 Python详细信息:
    for /f "tokens=*" %%i in ('where python') do (
        echo   路径: %%i
        if "%%i" == "C:\Users\Administrator\AppData\Local\Microsoft\WindowsApps\python.exe" (
            echo   类型: Windows Store版本 ^(功能受限^)
        ) else (
            echo   类型: 完整版本 ^(推荐使用^)
        )
    )
)
echo.

echo 📦 pip检查:
pip --version 2>nul
if %errorlevel% neq 0 (
    echo ❌ pip 不可用
) else (
    echo ✅ pip 可用
    pip --version
)
echo.

echo 🔧 Visual Studio检查 ^(支持C盘和D盘^):
set "VS_FOUND=0"
set "VS_PATH="
set "VS_YEAR="

REM 检查C盘VS安装
for %%v in (2022 2019 2017) do (
    for %%e in (Community Professional Enterprise BuildTools) do (
        if exist "C:\Program Files\Microsoft Visual Studio\%%v\%%e\VC\Tools\MSVC" (
            echo ✅ VS%%v %%e 已安装 ^(C盘^): C:\Program Files\Microsoft Visual Studio\%%v\%%e
            set "VS_FOUND=1"
            set "VS_PATH=C:\Program Files\Microsoft Visual Studio\%%v\%%e"
            set "VS_YEAR=%%v"
        )
    )
)

REM 检查D盘VS安装
for %%v in (2022 2019 2017) do (
    for %%e in (Community Professional Enterprise BuildTools) do (
        if exist "D:\Program Files\Microsoft Visual Studio\%%v\%%e\VC\Tools\MSVC" (
            echo ✅ VS%%v %%e 已安装 ^(D盘^): D:\Program Files\Microsoft Visual Studio\%%v\%%e
            set "VS_FOUND=1"
            set "VS_PATH=D:\Program Files\Microsoft Visual Studio\%%v\%%e"
            set "VS_YEAR=%%v"
        )
    )
)

REM 检查其他可能的路径
for %%d in (E F G) do (
    for %%v in (2022 2019 2017) do (
        for %%e in (Community Professional Enterprise BuildTools) do (
            if exist "%%d:\Program Files\Microsoft Visual Studio\%%v\%%e\VC\Tools\MSVC" (
                echo ✅ VS%%v %%e 已安装 ^(%%d盘^): %%d:\Program Files\Microsoft Visual Studio\%%v\%%e
                set "VS_FOUND=1"
                set "VS_PATH=%%d:\Program Files\Microsoft Visual Studio\%%v\%%e"
                set "VS_YEAR=%%v"
            )
        )
    )
)

if "%VS_FOUND%"=="0" (
    echo ❌ 未找到Visual Studio
    echo 请从 https://visualstudio.microsoft.com/downloads/ 下载安装
) else (
    echo.
    echo 🎯 推荐使用的VS路径: %VS_PATH%
    echo 🔍 检查VS组件:
    if exist "%VS_PATH%\VC\Tools\MSVC" (
        echo   ✅ C++ 编译器工具已安装
    ) else (
        echo   ❌ C++ 编译器工具未安装
    )
    if exist "%VS_PATH%\Common7\IDE\CommonExtensions\Microsoft\CMake" (
        echo   ✅ VS内置CMake工具已安装
    ) else (
        echo   ❌ VS内置CMake工具未安装
    )
)
echo.

echo 🛠️  CMake检查 ^(独立安装 + VS内置^):
set "CMAKE_FOUND=0"
set "CMAKE_PATH="
set "CMAKE_TYPE="

REM 检查独立安装的CMake
cmake --version 2>nul
if %errorlevel% equ 0 (
    echo ✅ 独立CMake已安装并在PATH中
    set "CMAKE_FOUND=1"
    set "CMAKE_TYPE=独立安装"
    where cmake
) else (
    echo ⚠️  独立CMake未在PATH中或未安装
)

REM 检查VS内置CMake
if not "%VS_PATH%"=="" (
    if exist "%VS_PATH%\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe" (
        echo ✅ VS内置CMake已安装: %VS_PATH%\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe
        set "CMAKE_FOUND=1"
        if "%CMAKE_TYPE%"=="" set "CMAKE_TYPE=VS内置"
        set "CMAKE_PATH=%VS_PATH%\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin"
        
        echo 🔍 测试VS内置CMake:
        "%VS_PATH%\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe" --version 2>nul
        if !errorlevel! equ 0 (
            echo   ✅ VS内置CMake可正常执行
        ) else (
            echo   ❌ VS内置CMake执行失败
        )
    )
)

REM 检查其他可能的CMake路径
for %%d in (C D E F G) do (
    if exist "%%d:\Program Files\CMake\bin\cmake.exe" (
        if "%CMAKE_FOUND%"=="0" (
            echo ✅ 发现CMake安装: %%d:\Program Files\CMake\bin\cmake.exe
            set "CMAKE_FOUND=1"
            set "CMAKE_PATH=%%d:\Program Files\CMake\bin"
            set "CMAKE_TYPE=独立安装"
        )
    )
)

if "%CMAKE_FOUND%"=="0" (
    echo ❌ 未找到任何CMake安装
    echo 建议: 在VS Installer中安装"C++ CMake工具"组件
)
echo.

echo 💾 磁盘空间检查:
echo C盘可用空间:
dir C:\ | findstr "bytes free"
echo F盘可用空间:
dir F:\ | findstr "bytes free" 2>nul
if %errorlevel% neq 0 (
    echo F盘不存在或无法访问
)
echo.

echo 🌐 网络连接检查:
ping -n 1 pypi.tuna.tsinghua.edu.cn >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ 可以连接到清华镜像源
) else (
    echo ❌ 无法连接到清华镜像源
    echo 请检查网络连接
)

ping -n 1 github.com >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ 可以连接到GitHub
) else (
    echo ❌ 无法连接到GitHub
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
echo 📊 详细诊断结果
echo ================================================================
echo.

if "%VS_FOUND%"=="1" if "%CMAKE_FOUND%"=="1" (
    echo 🎉 恭喜！您的环境基本满足要求
    echo.
    echo 📋 推荐配置:
    echo   Python: 使用F盘的完整版本
    echo   Visual Studio: %VS_PATH%
    if not "%CMAKE_PATH%"=="" (
        echo   CMake: %CMAKE_TYPE% - %CMAKE_PATH%
    ) else (
        echo   CMake: %CMAKE_TYPE%
    )
    echo.
    echo 🚀 可以直接运行: install_complete_universal_fixed.bat
    echo.
) else (
    echo ⚠️  环境需要完善
    echo.
    if "%VS_FOUND%"=="0" (
        echo ❌ 需要安装Visual Studio:
        echo   1. 访问: https://visualstudio.microsoft.com/downloads/
        echo   2. 下载Community版本^(免费^)
        echo   3. 安装时选择"C++桌面开发"工作负载
        echo   4. 确保勾选"C++ CMake工具"组件
        echo.
    )
    if "%CMAKE_FOUND%"=="0" (
        echo ❌ 需要安装CMake:
        echo   选项1^(推荐^): 在VS Installer中安装"C++ CMake工具"
        echo   选项2: 独立安装CMake from https://cmake.org/download/
        echo.
    )
)

echo 💡 关于Python路径的说明:
echo   F盘Python: %~1 完整功能版本^(推荐^)
echo   C盘Python: Windows Store版本^(功能受限，不推荐用于开发^)
echo   建议: 确保F盘Python在PATH中优先级更高
echo.

echo 🔧 如果需要修复Python PATH优先级:
echo   1. 按Win+R，输入sysdm.cpl
echo   2. 点击"环境变量"
echo   3. 在系统变量中找到PATH
echo   4. 将F:\AI\DigitalHuman_Portable移到最前面
echo.

echo ================================================================
echo 🎯 下一步行动建议
echo ================================================================
echo.

if "%VS_FOUND%"=="1" if "%CMAKE_FOUND%"=="1" (
    echo ✅ 环境就绪，可以开始安装:
    echo   运行: install_complete_universal_fixed.bat
) else (
    echo 📝 需要完成以下步骤:
    if "%VS_FOUND%"=="0" (
        echo   1. 安装Visual Studio 2022 Community
        echo      - 选择"C++桌面开发"工作负载
        echo      - 确保包含"C++ CMake工具"
    )
    if "%CMAKE_FOUND%"=="0" if "%VS_FOUND%"=="1" (
        echo   1. 在VS Installer中添加"C++ CMake工具"组件
    )
    echo   2. 重新运行此诊断脚本确认
    echo   3. 运行: install_complete_universal_fixed.bat
)

echo.
echo ================================================================
echo 窗口保持打开 - 按任意键关闭
echo ================================================================
pause >nul