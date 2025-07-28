@echo off
setlocal enabledelayedexpansion

REM 设置控制台编码为UTF-8
chcp 65001 >nul 2>&1

echo ================================================
echo VS2022组件检查工具
echo ================================================
echo 检查dlib编译所需的VS2022组件是否已安装
echo.

REM 查找VS2022安装路径
set "VS2022_PATH="
echo 正在查找VS2022安装路径...

if exist "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Tools\MSVC" (
    set "VS2022_PATH=C:\Program Files\Microsoft Visual Studio\2022\Community"
    echo 找到VS2022 Community: !VS2022_PATH!
    goto :found_vs
)

if exist "C:\Program Files\Microsoft Visual Studio\2022\Professional\VC\Tools\MSVC" (
    set "VS2022_PATH=C:\Program Files\Microsoft Visual Studio\2022\Professional"
    echo 找到VS2022 Professional: !VS2022_PATH!
    goto :found_vs
)

if exist "C:\Program Files\Microsoft Visual Studio\2022\Enterprise\VC\Tools\MSVC" (
    set "VS2022_PATH=C:\Program Files\Microsoft Visual Studio\2022\Enterprise"
    echo 找到VS2022 Enterprise: !VS2022_PATH!
    goto :found_vs
)

if exist "D:\Program Files\Microsoft Visual Studio\2022\Community\VC\Tools\MSVC" (
    set "VS2022_PATH=D:\Program Files\Microsoft Visual Studio\2022\Community"
    echo 找到VS2022 Community: !VS2022_PATH!
    goto :found_vs
)

if exist "D:\Program Files\Microsoft Visual Studio\2022\Professional\VC\Tools\MSVC" (
    set "VS2022_PATH=D:\Program Files\Microsoft Visual Studio\2022\Professional"
    echo 找到VS2022 Professional: !VS2022_PATH!
    goto :found_vs
)

if exist "D:\Program Files\Microsoft Visual Studio\2022\Enterprise\VC\Tools\MSVC" (
    set "VS2022_PATH=D:\Program Files\Microsoft Visual Studio\2022\Enterprise"
    echo 找到VS2022 Enterprise: !VS2022_PATH!
    goto :found_vs
)

echo 未找到VS2022安装
echo 请检查VS2022是否已正确安装
echo.
echo 按任意键退出...
pause >nul
exit /b 1

:found_vs

echo.
echo 检查必需组件...

REM 检查MSVC编译器
if exist "!VS2022_PATH!\VC\Tools\MSVC" (
    echo MSVC编译器: 已安装
    
    REM 查找MSVC版本
    for /f "delims=" %%i in ('dir "!VS2022_PATH!\VC\Tools\MSVC" /b /ad /o-n 2^>nul') do (
        echo    版本: %%i
        set "MSVC_VERSION=%%i"
        goto :msvc_found
    )
    :msvc_found
) else (
    echo MSVC编译器: 未安装
    echo 需要安装: MSVC v143 - VS 2022 C++ x64/x86生成工具
)

REM 检查Windows SDK
set "SDK_FOUND=0"
if exist "!VS2022_PATH!\VC\Auxiliary\Build\Microsoft.VCToolsVersion.default.txt" (
    echo VC工具: 已安装
) else (
    echo VC工具: 未安装
)

REM 检查Windows SDK
if exist "C:\Program Files (x86)\Windows Kits\10\Include" (
    echo Windows SDK: 已安装
    for /f "delims=" %%i in ('dir "C:\Program Files (x86)\Windows Kits\10\Include" /b /ad 2^>nul ^| findstr "10\."') do (
        echo    版本: %%i
        set "SDK_FOUND=1"
    )
) else (
    echo Windows SDK: 未安装
    echo 需要安装: Windows 11 SDK 或 Windows 10 SDK
)

REM 检查CMake
cmake --version >nul 2>&1
if !errorlevel! equ 0 (
    echo CMake: 已安装
    for /f "tokens=3" %%i in ('cmake --version 2^>nul ^| findstr "cmake version"') do (
        echo    版本: %%i
    )
) else (
    echo CMake: 未安装或不在PATH中
    echo 下载地址: https://cmake.org/download/
)

echo.
echo 检查编译环境...

REM 尝试调用VS环境设置
if exist "!VS2022_PATH!\VC\Auxiliary\Build\vcvars64.bat" (
    echo VS环境脚本: 存在
    
    REM 测试环境设置（在子进程中）
    call "!VS2022_PATH!\VC\Auxiliary\Build\vcvars64.bat" >nul 2>&1
    if !errorlevel! equ 0 (
        echo VS环境设置: 成功
    ) else (
        echo VS环境设置: 失败
    )
) else (
    echo VS环境脚本: 不存在
)

echo.
echo ================================================================
echo 检查结果总结
echo ================================================================

set "ALL_OK=1"

if not exist "!VS2022_PATH!\VC\Tools\MSVC" (
    echo 缺少: MSVC编译器
    set "ALL_OK=0"
)

if "!SDK_FOUND!"=="0" (
    echo 缺少: Windows SDK
    set "ALL_OK=0"
)

cmake --version >nul 2>&1
if !errorlevel! neq 0 (
    echo 缺少: CMake
    set "ALL_OK=0"
)

if "!ALL_OK!"=="1" (
    echo.
    echo 所有必需组件都已安装！
    echo 可以尝试运行 fix_vs2022_environment.bat 编译dlib
) else (
    echo.
    echo 发现缺失组件，需要安装
    echo.
    echo 解决方案:
    echo 1. 打开 Visual Studio Installer
    echo 2. 修改 Visual Studio 2022 安装
    echo 3. 在"工作负载"中确保选中:
    echo    - 使用C++的桌面开发
    echo 4. 在"单个组件"中确保选中:
    echo    - MSVC v143 - VS 2022 C++ x64/x86生成工具
    echo    - Windows 11 SDK 或 Windows 10 SDK
    echo    - CMake工具
    echo 5. 点击"修改"完成安装
)

echo.
echo 如果组件齐全但dlib仍编译失败:
echo - 重启命令行/PowerShell
echo - 以管理员身份运行
echo - 或使用 setup_minimal_environment.bat 跳过dlib

echo.
echo 按任意键退出...
pause >nul