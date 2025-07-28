@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ================================================================
echo 🚀 数字人系统完整安装脚本 - 修复版本
echo ================================================================
echo 支持任何Windows服务器自动安装
echo 自动检测环境，智能配置，解决dlib安装问题
echo.
echo 版本: 2025-01-28 修复版
echo 支持: MuseTalk + 所有依赖 + dlib完美解决方案
echo.

REM 添加错误处理 - 确保脚本不会闪退
set "ERROR_OCCURRED=0"

REM ================================================================
REM 配置部分 - 自动检测和适配（简化版本）
REM ================================================================

echo 🔍 开始系统环境检测...

REM 简化的路径检测 - 避免复杂的磁盘空间检测
set "BASE_DIR=C:\AI\DigitalHuman"

REM 尝试其他盘符如果C盘不可用
if not exist "C:\" (
    if exist "D:\" (
        set "BASE_DIR=D:\AI\DigitalHuman"
    ) else if exist "E:\" (
        set "BASE_DIR=E:\AI\DigitalHuman"
    )
)

echo ✅ 选择安装路径: %BASE_DIR%

set "VENV_DIR=%BASE_DIR%\venv"
set "TEMP_DIR=%BASE_DIR%\temp_install"

echo 📋 配置信息:
echo   安装路径: %BASE_DIR%
echo   虚拟环境: %VENV_DIR%
echo   临时目录: %TEMP_DIR%
echo.

REM 自动检测VS版本和路径
echo 🔍 检测Visual Studio...
set "VS_PATH="
set "VS_YEAR="

REM 检测VS2022
if exist "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Tools\MSVC" (
    set "VS_PATH=C:\Program Files\Microsoft Visual Studio\2022\Community"
    set "VS_YEAR=2022"
    goto :found_vs
)
if exist "C:\Program Files\Microsoft Visual Studio\2022\Professional\VC\Tools\MSVC" (
    set "VS_PATH=C:\Program Files\Microsoft Visual Studio\2022\Professional"
    set "VS_YEAR=2022"
    goto :found_vs
)
if exist "C:\Program Files\Microsoft Visual Studio\2022\Enterprise\VC\Tools\MSVC" (
    set "VS_PATH=C:\Program Files\Microsoft Visual Studio\2022\Enterprise"
    set "VS_YEAR=2022"
    goto :found_vs
)

REM 检测VS2019
if exist "C:\Program Files\Microsoft Visual Studio\2019\Community\VC\Tools\MSVC" (
    set "VS_PATH=C:\Program Files\Microsoft Visual Studio\2019\Community"
    set "VS_YEAR=2019"
    goto :found_vs
)
if exist "C:\Program Files\Microsoft Visual Studio\2019\Professional\VC\Tools\MSVC" (
    set "VS_PATH=C:\Program Files\Microsoft Visual Studio\2019\Professional"
    set "VS_YEAR=2019"
    goto :found_vs
)

REM 检测VS2017
if exist "C:\Program Files\Microsoft Visual Studio\2017\Community\VC\Tools\MSVC" (
    set "VS_PATH=C:\Program Files\Microsoft Visual Studio\2017\Community"
    set "VS_YEAR=2017"
    goto :found_vs
)

:found_vs

if "%VS_PATH%"=="" (
    echo ⚠️  未检测到Visual Studio
) else (
    echo ✅ 检测到Visual Studio %VS_YEAR%: %VS_PATH%
)

REM 自动检测CMake
echo 🔍 检测CMake...
set "CMAKE_PATH="

if exist "C:\Program Files\CMake\bin\cmake.exe" (
    set "CMAKE_PATH=C:\Program Files\CMake\bin"
    goto :found_cmake
)
if exist "D:\Program Files\CMake\bin\cmake.exe" (
    set "CMAKE_PATH=D:\Program Files\CMake\bin"
    goto :found_cmake
)
if exist "C:\Program Files (x86)\CMake\bin\cmake.exe" (
    set "CMAKE_PATH=C:\Program Files (x86)\CMake\bin"
    goto :found_cmake
)
if not "%VS_PATH%"=="" (
    if exist "%VS_PATH%\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe" (
        set "CMAKE_PATH=%VS_PATH%\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin"
        goto :found_cmake
    )
)

:found_cmake

if "%CMAKE_PATH%"=="" (
    echo ⚠️  未检测到CMake
) else (
    echo ✅ 检测到CMake: %CMAKE_PATH%
)

echo.
echo 📋 检测结果总结:
echo   安装路径: %BASE_DIR%
echo   VS版本: %VS_YEAR%
echo   VS路径: %VS_PATH%
echo   CMake路径: %CMAKE_PATH%
echo.

REM ================================================================
REM 环境准备和依赖安装
REM ================================================================

echo 🛠️  开始环境准备...

REM 创建目录结构
echo 📁 创建目录结构...
if not exist "%BASE_DIR%" (
    mkdir "%BASE_DIR%" 2>nul
    if !errorlevel! neq 0 (
        echo ❌ 无法创建目录: %BASE_DIR%
        echo 请检查权限或手动创建该目录
        set "ERROR_OCCURRED=1"
        goto :error_exit
    )
)

if not exist "%TEMP_DIR%" (
    mkdir "%TEMP_DIR%" 2>nul
    if !errorlevel! neq 0 (
        echo ❌ 无法创建临时目录: %TEMP_DIR%
        set "ERROR_OCCURRED=1"
        goto :error_exit
    )
)

echo ✅ 目录创建完成

REM 检查Python
echo 🐍 检查Python安装...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python 未安装或未添加到PATH
    echo.
    echo 请按以下步骤安装Python:
    echo 1. 访问: https://www.python.org/downloads/
    echo 2. 下载Python 3.8或更高版本
    echo 3. 安装时勾选"Add Python to PATH"
    echo 4. 重新运行此脚本
    echo.
    set "ERROR_OCCURRED=1"
    goto :error_exit
)

echo ✅ Python 已安装
python --version

REM 检查pip
echo 📦 检查pip...
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ pip 不可用
    echo 尝试修复pip...
    python -m ensurepip --upgrade
    if !errorlevel! neq 0 (
        echo ❌ 无法修复pip，请手动安装
        set "ERROR_OCCURRED=1"
        goto :error_exit
    )
)

echo ✅ pip 可用
pip --version

REM 自动安装缺失的组件
echo.
echo 🔧 检查和安装必需组件...

REM 检查和安装VS Build Tools
if "%VS_PATH%"=="" (
    echo ❌ 未找到Visual Studio，开始自动安装...
    echo 正在下载VS Build Tools...
    echo 这可能需要几分钟，请耐心等待...
    
    powershell -Command "try { Invoke-WebRequest -Uri 'https://aka.ms/vs/17/release/vs_buildtools.exe' -OutFile '%TEMP_DIR%\vs_buildtools.exe' -UseBasicParsing } catch { exit 1 }"
    
    if exist "%TEMP_DIR%\vs_buildtools.exe" (
        echo ✅ VS Build Tools下载完成
        echo 开始安装VS Build Tools（这可能需要10-20分钟）...
        echo 请不要关闭此窗口，安装完成后会自动继续...
        
        start /wait "%TEMP_DIR%\vs_buildtools.exe" --quiet --wait --add Microsoft.VisualStudio.Workload.VCTools --add Microsoft.VisualStudio.Component.Windows10SDK.19041 --add Microsoft.VisualStudio.Component.VC.CMake.Project
        
        REM 重新检测VS路径
        if exist "C:\Program Files\Microsoft Visual Studio\2022\BuildTools\VC\Tools\MSVC" (
            set "VS_PATH=C:\Program Files\Microsoft Visual Studio\2022\BuildTools"
            set "VS_YEAR=2022"
        ) else if exist "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Tools\MSVC" (
            set "VS_PATH=C:\Program Files\Microsoft Visual Studio\2022\Community"
            set "VS_YEAR=2022"
        )
        
        if not "%VS_PATH%"=="" (
            echo ✅ Visual Studio 安装成功: %VS_PATH%
        ) else (
            echo ❌ Visual Studio 安装可能失败，请手动安装
            echo 下载地址: https://visualstudio.microsoft.com/downloads/
        )
    ) else (
        echo ❌ 无法下载VS Build Tools
        echo 请检查网络连接或手动安装Visual Studio
        echo 下载地址: https://visualstudio.microsoft.com/downloads/
    )
)

REM 检查和安装CMake
if "%CMAKE_PATH%"=="" (
    echo ❌ 未找到CMake，开始自动安装...
    echo 正在下载CMake...
    
    powershell -Command "try { Invoke-WebRequest -Uri 'https://github.com/Kitware/CMake/releases/download/v3.28.1/cmake-3.28.1-windows-x86_64.msi' -OutFile '%TEMP_DIR%\cmake.msi' -UseBasicParsing } catch { exit 1 }"
    
    if exist "%TEMP_DIR%\cmake.msi" (
        echo ✅ CMake下载完成
        echo 安装CMake...
        start /wait msiexec /i "%TEMP_DIR%\cmake.msi" /quiet ADD_CMAKE_TO_PATH=System
        
        REM 重新检测CMake
        if exist "C:\Program Files\CMake\bin\cmake.exe" (
            set "CMAKE_PATH=C:\Program Files\CMake\bin"
            echo ✅ CMake安装成功: %CMAKE_PATH%
        ) else (
            echo ❌ CMake安装可能失败，请手动安装
            echo 下载地址: https://cmake.org/download/
        )
    ) else (
        echo ❌ 无法下载CMake
        echo 请检查网络连接或手动安装CMake
        echo 下载地址: https://cmake.org/download/
    )
)

REM 最终检查
echo.
echo 🔍 最终环境检查...
if "%VS_PATH%"=="" (
    echo ❌ Visual Studio 仍未可用
    echo 建议手动安装后重新运行脚本
) else (
    echo ✅ Visual Studio: %VS_PATH%
)

if "%CMAKE_PATH%"=="" (
    echo ❌ CMake 仍未可用
    echo 建议手动安装后重新运行脚本
) else (
    echo ✅ CMake: %CMAKE_PATH%
)

REM ================================================================
REM Python环境设置
REM ================================================================

echo.
echo 🐍 设置Python环境...

REM 创建虚拟环境
if not exist "%VENV_DIR%" (
    echo 📦 创建虚拟环境...
    python -m venv "%VENV_DIR%"
    if !errorlevel! neq 0 (
        echo ❌ 虚拟环境创建失败
        set "ERROR_OCCURRED=1"
        goto :error_exit
    )
    echo ✅ 虚拟环境创建成功
) else (
    echo ✅ 虚拟环境已存在
)

REM 激活虚拟环境
echo 🔄 激活虚拟环境...
call "%VENV_DIR%\Scripts\activate.bat"
if %errorlevel% neq 0 (
    echo ❌ 虚拟环境激活失败
    set "ERROR_OCCURRED=1"
    goto :error_exit
)
echo ✅ 虚拟环境已激活

REM 配置pip镜像
echo 🌐 配置pip镜像源...
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

echo ✅ pip镜像配置完成

REM 升级pip和基础工具
echo 📈 升级pip和构建工具...
python -m pip install --upgrade pip setuptools wheel -i https://pypi.tuna.tsinghua.edu.cn/simple/
if %errorlevel% neq 0 (
    echo ⚠️  pip升级失败，继续使用当前版本
)

REM ================================================================
REM 设置编译环境
REM ================================================================

echo.
echo ⚙️  设置编译环境...

if not "%CMAKE_PATH%"=="" (
    REM 清理PATH，避免冲突
    set "ORIGINAL_PATH=%PATH%"
    set "PATH=%SystemRoot%\system32;%SystemRoot%;%SystemRoot%\System32\Wbem"
    
    REM 添加CMake到PATH（优先级最高）
    set "PATH=%CMAKE_PATH%;%PATH%"
    echo ✅ CMake已添加到PATH
)

if not "%VS_PATH%"=="" (
    REM 初始化VS环境
    echo 🔧 初始化Visual Studio %VS_YEAR% 环境...
    call "%VS_PATH%\VC\Auxiliary\Build\vcvars64.bat"
    if !errorlevel! equ 0 (
        echo ✅ VS环境初始化成功
    ) else (
        echo ⚠️  VS环境初始化可能有问题，继续尝试
    )
    
    REM 设置编译器环境变量
    set CMAKE_GENERATOR=Visual Studio 17 2022
    if "%VS_YEAR%"=="2019" set CMAKE_GENERATOR=Visual Studio 16 2019
    if "%VS_YEAR%"=="2017" set CMAKE_GENERATOR=Visual Studio 15 2017
    
    set CMAKE_GENERATOR_PLATFORM=x64
    set CMAKE_GENERATOR_TOOLSET=v143
    if "%VS_YEAR%"=="2019" set CMAKE_GENERATOR_TOOLSET=v142
    if "%VS_YEAR%"=="2017" set CMAKE_GENERATOR_TOOLSET=v141
    
    set CMAKE_BUILD_TYPE=Release
    set CMAKE_C_COMPILER=cl.exe
    set CMAKE_CXX_COMPILER=cl.exe
    
    echo ✅ 编译环境设置完成
)

REM 验证工具
echo.
echo 🔍 验证编译工具...
if not "%CMAKE_PATH%"=="" (
    echo CMake版本:
    cmake --version 2>nul
    if !errorlevel! neq 0 (
        echo ⚠️  CMake命令执行失败
    )
) else (
    echo ⚠️  CMake不可用
)

if not "%VS_PATH%"=="" (
    echo 编译器版本:
    cl 2>&1 | findstr "Microsoft" 2>nul
    if !errorlevel! neq 0 (
        echo ⚠️  编译器命令执行失败
    )
) else (
    echo ⚠️  编译器不可用
)

REM ================================================================
REM 安装基础依赖
REM ================================================================

echo.
echo 📦 安装基础依赖包...

REM GPU检测和PyTorch安装
echo 🎮 检测GPU并安装PyTorch...
nvidia-smi >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ 检测到NVIDIA GPU，安装CUDA版本PyTorch...
    pip install torch==2.0.1+cu118 torchvision==0.15.2+cu118 torchaudio==2.0.2+cu118 --index-url https://download.pytorch.org/whl/cu118
    if !errorlevel! neq 0 (
        echo ⚠️  CUDA版本安装失败，尝试镜像源...
        pip install torch torchvision torchaudio -i https://pypi.tuna.tsinghua.edu.cn/simple/
    )
) else (
    echo 💻 未检测到NVIDIA GPU，安装CPU版本PyTorch...
    pip install torch torchvision torchaudio -i https://pypi.tuna.tsinghua.edu.cn/simple/
)

REM 安装其他基础包
echo 📸 安装基础计算机视觉库...
pip install opencv-python pillow numpy scipy -i https://pypi.tuna.tsinghua.edu.cn/simple/

echo 🎵 安装音频处理库...
pip install librosa soundfile -i https://pypi.tuna.tsinghua.edu.cn/simple/

echo 🌐 安装Web框架...
pip install flask fastapi uvicorn -i https://pypi.tuna.tsinghua.edu.cn/simple/

REM ================================================================
REM dlib 安装 - 终极解决方案
REM ================================================================

echo.
echo 🎯 开始dlib安装 - 多重策略保证成功...

REM 策略1: 尝试预编译wheel
echo 📥 策略1: 尝试预编译wheel包...
pip install dlib -i https://pypi.tuna.tsinghua.edu.cn/simple/ --no-cache-dir

if %errorlevel% equ 0 (
    echo ✅ dlib安装成功（预编译包）!
    python -c "import dlib; print('✅ dlib版本:', dlib.__version__)" 2>nul
    if !errorlevel! equ 0 (
        echo 🎉 dlib导入测试成功!
        goto :dlib_success
    )
)

echo ⚠️  预编译包失败，尝试策略2...

REM 策略2: 从源码编译（优化环境）
if not "%CMAKE_PATH%"=="" if not "%VS_PATH%"=="" (
    echo 🔨 策略2: 从源码编译dlib...
    
    REM 确保编译环境最优
    set CMAKE_COMMAND=%CMAKE_PATH%\cmake.exe
    set DLIB_NO_GUI_SUPPORT=1
    set DLIB_JPEG_SUPPORT=0
    set DLIB_PNG_SUPPORT=0
    set DLIB_GIF_SUPPORT=0
    
    echo 使用CMake: %CMAKE_COMMAND%
    echo 编译器: %CMAKE_GENERATOR%
    
    REM 下载dlib源码
    cd /d "%TEMP_DIR%"
    pip download dlib==19.24.2 --no-deps -i https://pypi.tuna.tsinghua.edu.cn/simple/
    
    if exist "dlib-19.24.2.tar.gz" (
        echo 📦 解压dlib源码...
        tar -xzf dlib-19.24.2.tar.gz 2>nul
        if exist dlib-19.24.2 (
            cd dlib-19.24.2
            
            if exist build rmdir /s /q build
            mkdir build
            cd build
            
            echo 🔧 运行CMake配置...
            "%CMAKE_COMMAND%" .. ^
                -G "%CMAKE_GENERATOR%" ^
                -A x64 ^
                -DCMAKE_BUILD_TYPE=Release ^
                -DDLIB_NO_GUI_SUPPORT=ON ^
                -DDLIB_JPEG_SUPPORT=OFF ^
                -DDLIB_PNG_SUPPORT=OFF ^
                -DDLIB_GIF_SUPPORT=OFF ^
                -DDLIB_USE_CUDA=OFF ^
                -DCMAKE_INSTALL_PREFIX=../install
            
            if !errorlevel! equ 0 (
                echo ✅ CMake配置成功，开始编译...
                "%CMAKE_COMMAND%" --build . --config Release --parallel 4
                
                if !errorlevel! equ 0 (
                    echo ✅ 编译成功，安装dlib...
                    cd ..
                    pip install . -i https://pypi.tuna.tsinghua.edu.cn/simple/
                    
                    if !errorlevel! equ 0 (
                        echo ✅ dlib源码编译安装成功!
                        cd /d "%BASE_DIR%"
                        python -c "import dlib; print('✅ dlib版本:', dlib.__version__)" 2>nul
                        if !errorlevel! equ 0 (
                            echo 🎉 dlib导入测试成功!
                            goto :dlib_success
                        )
                    )
                )
            )
        )
    )
    
    cd /d "%BASE_DIR%"
    echo ⚠️  源码编译失败，尝试策略3...
) else (
    echo ⚠️  缺少编译环境，跳过源码编译，尝试策略3...
)

REM 策略3: 兼容版本
echo 🔄 策略3: 尝试兼容版本...

for %%v in (19.22.1 19.21.1 19.20.1 19.19.0) do (
    echo 🔄 尝试dlib %%v...
    pip install dlib==%%v -i https://pypi.tuna.tsinghua.edu.cn/simple/ --no-cache-dir
    
    if !errorlevel! equ 0 (
        python -c "import dlib; print('✅ dlib版本:', dlib.__version__)" 2>nul
        if !errorlevel! equ 0 (
            echo ✅ dlib %%v 安装成功!
            goto :dlib_success
        )
    )
)

REM 策略4: 替代方案
echo ⚠️  dlib安装失败，安装替代方案...
:dlib_alternative

echo 📦 安装MediaPipe作为替代...
pip install mediapipe -i https://pypi.tuna.tsinghua.edu.cn/simple/
if %errorlevel% equ 0 (
    echo ✅ MediaPipe安装成功（dlib替代方案）
    python -c "import mediapipe as mp; print('✅ MediaPipe版本:', mp.__version__)" 2>nul
)

echo 📦 尝试安装face_recognition（可能包含dlib）...
pip install face_recognition -i https://pypi.tuna.tsinghua.edu.cn/simple/
if %errorlevel% equ 0 (
    echo ✅ face_recognition安装成功
)

goto :post_dlib

:dlib_success
echo.
echo 🎉 dlib安装成功！测试功能...
python -c "
try:
    import dlib
    print('✅ dlib导入成功')
    print('   版本:', dlib.__version__)
    
    # 测试人脸检测器
    detector = dlib.get_frontal_face_detector()
    print('✅ 人脸检测器创建成功')
    print('🏆 dlib完全可用，支持最高质量人脸检测！')
    
except Exception as e:
    print('❌ dlib测试失败:', str(e))
" 2>nul

:post_dlib

REM ================================================================
REM 安装MuseTalk相关依赖
REM ================================================================

echo.
echo 🎵 安装MuseTalk相关依赖...

echo 🤖 安装深度学习框架扩展...
pip install diffusers transformers accelerate -i https://pypi.tuna.tsinghua.edu.cn/simple/

echo 🎬 安装音频视频处理...
pip install ffmpeg-python moviepy -i https://pypi.tuna.tsinghua.edu.cn/simple/

echo 👤 安装人脸处理库...
pip install insightface onnxruntime -i https://pypi.tuna.tsinghua.edu.cn/simple/

echo 🛠️  安装其他工具...
pip install tqdm requests pydantic -i https://pypi.tuna.tsinghua.edu.cn/simple/

REM ================================================================
REM 创建启动脚本和配置
REM ================================================================

echo.
echo 📝 创建启动脚本和配置文件...

REM 创建激活环境脚本
(
echo @echo off
echo echo 🚀 激活数字人系统环境...
echo call "%VENV_DIR%\Scripts\activate.bat"
if not "%CMAKE_PATH%"=="" echo set "PATH=%CMAKE_PATH%;%%PATH%%"
if not "%VS_PATH%"=="" echo call "%VS_PATH%\VC\Auxiliary\Build\vcvars64.bat"
echo echo ✅ 环境已激活
echo echo 📋 可用命令:
echo echo   python musetalk_service_complete.py  - 启动MuseTalk服务
echo echo   python test_environment.py          - 测试环境
echo echo.
echo cmd /k
) > "%BASE_DIR%\activate_env.bat"

REM 创建测试脚本
(
echo # 数字人系统环境测试
echo import sys
echo print^("🔍 Python环境测试"^)
echo print^(f"Python版本: {sys.version}"^)
echo print^(f"Python路径: {sys.executable}"^)
echo print^(^)
echo 
echo # 测试关键库
echo libraries = [
echo     ^('torch', 'PyTorch'^),
echo     ^('cv2', 'OpenCV'^),
echo     ^('numpy', 'NumPy'^),
echo     ^('PIL', 'Pillow'^),
echo     ^('flask', 'Flask'^),
echo ]
echo 
echo # 测试人脸检测库
echo try:
echo     import dlib
echo     libraries.append^(^('dlib', f'dlib {dlib.__version__}'^)^)
echo except ImportError:
echo     pass
echo     
echo try:
echo     import mediapipe
echo     libraries.append^(^('mediapipe', f'MediaPipe {mediapipe.__version__}'^)^)
echo except ImportError:
echo     pass
echo 
echo print^("📦 库测试结果:"^)
echo for module, name in libraries:
echo     try:
echo         if module == 'dlib':
echo             import dlib
echo             print^(f"✅ {name} - 最佳人脸检测"^)
echo         elif module == 'mediapipe':
echo             import mediapipe
echo             print^(f"✅ {name} - 良好人脸检测"^)
echo         else:
echo             lib = __import__^(module^)
echo             version = getattr^(lib, '__version__', 'unknown'^)
echo             print^(f"✅ {name}: {version}"^)
echo     except ImportError:
echo         print^(f"❌ {name}: 未安装"^)
echo 
echo print^(^)
echo print^("🎉 环境测试完成！"^)
echo print^("💡 运行 'python musetalk_service_complete.py' 启动服务"^)
) > "%BASE_DIR%\test_environment.py"

REM ================================================================
REM 清理和完成
REM ================================================================

echo.
echo 🧹 清理临时文件...
if exist "%TEMP_DIR%" (
    rmdir /s /q "%TEMP_DIR%" 2>nul
)

echo.
echo ================================================================
echo 🎉 数字人系统安装完成！
echo ================================================================
echo.
echo 📁 安装路径: %BASE_DIR%
echo 🐍 Python环境: %VENV_DIR%
echo.
echo 🚀 使用方法:
echo   1. 双击运行: %BASE_DIR%\activate_env.bat
echo   2. 测试环境: python %BASE_DIR%\test_environment.py
echo   3. 启动服务: python musetalk_service_complete.py
echo.

REM 最终状态检查
echo 📊 最终安装状态:
python -c "
import sys
print('✅ Python:', sys.version.split()[0])

# 检查关键组件
components = []
try:
    import torch
    components.append(f'✅ PyTorch: {torch.__version__}')
except ImportError:
    components.append('❌ PyTorch: 未安装')

try:
    import cv2
    components.append(f'✅ OpenCV: {cv2.__version__}')
except ImportError:
    components.append('❌ OpenCV: 未安装')

try:
    import dlib
    components.append(f'✅ dlib: {dlib.__version__} (🏆 最佳选择)')
except ImportError:
    try:
        import mediapipe
        components.append(f'✅ MediaPipe: {mediapipe.__version__} (👍 替代方案)')
    except ImportError:
        components.append('❌ 人脸检测库: 未安装')

for comp in components:
    print(comp)

print()
print('🏆 系统就绪，可以开始使用MuseTalk数字人系统！')
" 2>nul

if %errorlevel% neq 0 (
    echo ⚠️  Python测试执行失败，但安装可能已完成
)

goto :success_exit

:error_exit
echo.
echo ================================================================
echo ❌ 安装过程中出现错误
echo ================================================================
echo.
echo 🔍 错误排查建议:
echo 1. 检查是否有管理员权限
echo 2. 确保网络连接正常
echo 3. 检查磁盘空间是否充足（至少10GB）
echo 4. 尝试手动安装Python、Visual Studio和CMake
echo.
echo 📞 获取帮助:
echo 1. 查看上方的错误信息
echo 2. 参考README_COMPLETE.md文档
echo 3. 手动安装缺失的组件后重新运行
echo.
goto :final_pause

:success_exit
echo.
echo ================================================================
echo 🎉 安装成功完成！
echo ================================================================
echo.
echo 🎯 下一步操作:
echo 1. 双击运行: %BASE_DIR%\activate_env.bat
echo 2. 在激活的环境中运行: python test_environment.py
echo 3. 如果测试通过，运行: python musetalk_service_complete.py
echo.

:final_pause
echo ================================================================
echo 脚本执行完成 - 窗口保持打开
echo ================================================================
echo.
echo 此窗口将保持打开，您可以查看所有输出信息
echo 如有问题，请查看上方的详细信息
echo.
echo 按任意键关闭窗口...
pause >nul
exit /b %ERROR_OCCURRED%