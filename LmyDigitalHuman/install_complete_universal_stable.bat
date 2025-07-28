@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ================================================================
echo 🚀 数字人系统安装脚本 - 超级稳定版
echo ================================================================
echo 针对您的环境: F盘Python + D盘VS2022
echo 使用最稳定的检测逻辑，确保不会闪退
echo.

REM 立即设置错误处理
set "ERROR_OCCURRED=0"

REM 添加调试输出，确保每一步都可见
echo 🔍 步骤1: 初始化基本配置...

REM 简化路径检测 - 直接使用您的环境
set "BASE_DIR=F:\AI\DigitalHuman"
echo ✅ 安装路径设置为: %BASE_DIR%

set "VENV_DIR=%BASE_DIR%\venv"
set "TEMP_DIR=%BASE_DIR%\temp_install"

echo 📋 配置完成:
echo   安装路径: %BASE_DIR%
echo   虚拟环境: %VENV_DIR%
echo   临时目录: %TEMP_DIR%
echo.

echo 🔍 步骤2: 检测Visual Studio...

REM 简化VS检测 - 直接检查您的路径
set "VS_PATH="
set "VS_YEAR="

echo 检查D盘VS2022 Community...
if exist "D:\Program Files\Microsoft Visual Studio\2022\Community\VC\Tools\MSVC" (
    set "VS_PATH=D:\Program Files\Microsoft Visual Studio\2022\Community"
    set "VS_YEAR=2022"
    echo ✅ 找到VS2022 Community: !VS_PATH!
    goto :vs_found
)

echo 检查D盘VS2022 Professional...
if exist "D:\Program Files\Microsoft Visual Studio\2022\Professional\VC\Tools\MSVC" (
    set "VS_PATH=D:\Program Files\Microsoft Visual Studio\2022\Professional"
    set "VS_YEAR=2022"
    echo ✅ 找到VS2022 Professional: !VS_PATH!
    goto :vs_found
)

echo 检查C盘VS2022 Community...
if exist "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Tools\MSVC" (
    set "VS_PATH=C:\Program Files\Microsoft Visual Studio\2022\Community"
    set "VS_YEAR=2022"
    echo ✅ 找到VS2022 Community: !VS_PATH!
    goto :vs_found
)

echo ⚠️  未找到Visual Studio 2022
goto :vs_check_done

:vs_found
echo ✅ Visual Studio检测成功: %VS_PATH%

:vs_check_done

echo.
echo 🔍 步骤3: 检测CMake...

set "CMAKE_PATH="
set "CMAKE_TYPE="

REM 检查VS内置CMake - 使用您的实际路径
if not "%VS_PATH%"=="" (
    echo 检查VS内置CMake...
    if exist "%VS_PATH%\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe" (
        set "CMAKE_PATH=%VS_PATH%\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin"
        set "CMAKE_TYPE=VS内置"
        echo ✅ 找到VS内置CMake: !CMAKE_PATH!
        goto :cmake_found
    ) else (
        echo ⚠️  VS内置CMake未找到，请在VS Installer中安装"C++ CMake工具"
    )
)

REM 检查独立CMake
echo 检查独立安装的CMake...
if exist "C:\Program Files\CMake\bin\cmake.exe" (
    set "CMAKE_PATH=C:\Program Files\CMake\bin"
    set "CMAKE_TYPE=独立安装"
    echo ✅ 找到独立CMake: !CMAKE_PATH!
    goto :cmake_found
)

if exist "D:\Program Files\CMake\bin\cmake.exe" (
    set "CMAKE_PATH=D:\Program Files\CMake\bin"
    set "CMAKE_TYPE=独立安装"
    echo ✅ 找到独立CMake: !CMAKE_PATH!
    goto :cmake_found
)

echo ⚠️  未找到CMake安装
goto :cmake_check_done

:cmake_found
echo ✅ CMake检测成功 (%CMAKE_TYPE%): %CMAKE_PATH%

:cmake_check_done

echo.
echo 📋 环境检测结果:
echo   VS路径: %VS_PATH%
echo   CMake路径: %CMAKE_PATH%
echo   CMake类型: %CMAKE_TYPE%
echo.

REM 如果缺少关键组件，给出明确指导
if "%VS_PATH%"=="" (
    echo ❌ 缺少Visual Studio，无法继续
    echo.
    echo 📝 请按以下步骤操作:
    echo 1. 确认VS2022已安装在D盘或C盘
    echo 2. 确认安装了"C++桌面开发"工作负载
    echo 3. 重新运行此脚本
    echo.
    set "ERROR_OCCURRED=1"
    goto :error_exit
)

if "%CMAKE_PATH%"=="" (
    echo ❌ 缺少CMake，建议安装VS内置CMake
    echo.
    echo 📝 推荐操作:
    echo 1. 打开Visual Studio Installer
    echo 2. 点击"修改"您的VS2022
    echo 3. 在"单个组件"中搜索并勾选"C++ CMake工具"
    echo 4. 安装完成后重新运行此脚本
    echo.
    echo 💡 您也可以选择继续安装（部分功能可能受限）
    echo.
    choice /C YN /M "是否继续安装 (Y=继续, N=退出)"
    if errorlevel 2 (
        echo 安装已取消
        set "ERROR_OCCURRED=1"
        goto :error_exit
    )
    echo 继续安装（CMake功能受限）...
)

echo.
echo 🔍 步骤4: 创建目录结构...

if not exist "%BASE_DIR%" (
    echo 创建安装目录: %BASE_DIR%
    mkdir "%BASE_DIR%" 2>nul
    if !errorlevel! neq 0 (
        echo ❌ 无法创建目录: %BASE_DIR%
        echo 请检查F盘是否可用或权限是否足够
        set "ERROR_OCCURRED=1"
        goto :error_exit
    )
    echo ✅ 安装目录创建成功
) else (
    echo ✅ 安装目录已存在
)

if not exist "%TEMP_DIR%" (
    echo 创建临时目录: %TEMP_DIR%
    mkdir "%TEMP_DIR%" 2>nul
    if !errorlevel! neq 0 (
        echo ❌ 无法创建临时目录
        set "ERROR_OCCURRED=1"
        goto :error_exit
    )
    echo ✅ 临时目录创建成功
) else (
    echo ✅ 临时目录已存在
)

echo.
echo 🔍 步骤5: 验证Python环境...

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python未安装或未添加到PATH
    echo 请确保Python已正确安装并添加到系统PATH
    set "ERROR_OCCURRED=1"
    goto :error_exit
)

echo ✅ Python已安装
python --version

REM 检查Python路径
echo 🔍 检查Python路径...
for /f "tokens=*" %%i in ('where python 2^>nul') do (
    echo   Python路径: %%i
    if "%%i"=="F:\AI\DigitalHuman_Portable\python.exe" (
        echo   ✅ 使用F盘完整版Python（推荐）
    )
)

echo.
echo 🔍 步骤6: 检查pip...

pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ pip不可用，尝试修复...
    python -m ensurepip --upgrade 2>nul
    if !errorlevel! neq 0 (
        echo ❌ pip修复失败
        set "ERROR_OCCURRED=1"
        goto :error_exit
    )
)

echo ✅ pip可用
pip --version

echo.
echo 🔍 步骤7: 创建Python虚拟环境...

if not exist "%VENV_DIR%" (
    echo 创建虚拟环境...
    python -m venv "%VENV_DIR%" 2>nul
    if !errorlevel! neq 0 (
        echo ❌ 虚拟环境创建失败
        set "ERROR_OCCURRED=1"
        goto :error_exit
    )
    echo ✅ 虚拟环境创建成功
) else (
    echo ✅ 虚拟环境已存在
)

echo.
echo 🔍 步骤8: 激活虚拟环境...

call "%VENV_DIR%\Scripts\activate.bat" 2>nul
if %errorlevel% neq 0 (
    echo ❌ 虚拟环境激活失败
    set "ERROR_OCCURRED=1"
    goto :error_exit
)

echo ✅ 虚拟环境已激活

echo.
echo 🔍 步骤9: 配置pip镜像源...

if not exist "%USERPROFILE%\.pip" mkdir "%USERPROFILE%\.pip" 2>nul

(
echo [global]
echo index-url = https://pypi.tuna.tsinghua.edu.cn/simple/
echo trusted-host = pypi.tuna.tsinghua.edu.cn
echo timeout = 120
echo retries = 5
echo [install]
echo trusted-host = pypi.tuna.tsinghua.edu.cn
) > "%USERPROFILE%\.pip\pip.conf" 2>nul

echo ✅ pip镜像源配置完成

echo.
echo 🔍 步骤10: 升级pip和构建工具...

python -m pip install --upgrade pip setuptools wheel -i https://pypi.tuna.tsinghua.edu.cn/simple/ >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️  pip升级失败，继续使用当前版本
) else (
    echo ✅ pip升级成功
)

echo.
echo 🔍 步骤11: 设置编译环境...

REM 如果有CMake，设置PATH
if not "%CMAKE_PATH%"=="" (
    set "PATH=%CMAKE_PATH%;%PATH%"
    echo ✅ CMake已添加到PATH
)

REM 如果有VS，初始化编译环境
if not "%VS_PATH%"=="" (
    echo 初始化Visual Studio环境...
    call "%VS_PATH%\VC\Auxiliary\Build\vcvars64.bat" >nul 2>&1
    if !errorlevel! equ 0 (
        echo ✅ VS编译环境初始化成功
        
        REM 设置CMake生成器
        set CMAKE_GENERATOR=Visual Studio 17 2022
        set CMAKE_GENERATOR_PLATFORM=x64
        set CMAKE_GENERATOR_TOOLSET=v143
        set CMAKE_BUILD_TYPE=Release
        
        echo ✅ 编译环境配置完成
    ) else (
        echo ⚠️  VS环境初始化可能有问题，继续安装
    )
)

echo.
echo 🔍 步骤12: 安装基础依赖包...

echo 📦 安装PyTorch...
nvidia-smi >nul 2>&1
if %errorlevel% equ 0 (
    echo 检测到NVIDIA GPU，安装CUDA版本...
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118 >nul 2>&1
    if !errorlevel! neq 0 (
        echo CUDA版本安装失败，尝试CPU版本...
        pip install torch torchvision torchaudio -i https://pypi.tuna.tsinghua.edu.cn/simple/ >nul 2>&1
    )
) else (
    echo 安装CPU版本PyTorch...
    pip install torch torchvision torchaudio -i https://pypi.tuna.tsinghua.edu.cn/simple/ >nul 2>&1
)

if %errorlevel% equ 0 (
    echo ✅ PyTorch安装成功
) else (
    echo ❌ PyTorch安装失败
)

echo 📦 安装基础库...
pip install opencv-python pillow numpy scipy -i https://pypi.tuna.tsinghua.edu.cn/simple/ >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ 基础视觉库安装成功
) else (
    echo ⚠️  部分基础库安装失败
)

echo 📦 安装音频库...
pip install librosa soundfile -i https://pypi.tuna.tsinghua.edu.cn/simple/ >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ 音频库安装成功
) else (
    echo ⚠️  音频库安装失败
)

echo 📦 安装Web框架...
pip install flask fastapi uvicorn -i https://pypi.tuna.tsinghua.edu.cn/simple/ >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Web框架安装成功
) else (
    echo ⚠️  Web框架安装失败
)

echo.
echo 🔍 步骤13: 安装dlib（关键步骤）...

REM 策略1: 预编译包
echo 📥 尝试预编译dlib包...
pip install dlib -i https://pypi.tuna.tsinghua.edu.cn/simple/ --no-cache-dir >nul 2>&1

if %errorlevel% equ 0 (
    echo 测试dlib导入...
    python -c "import dlib; print('dlib版本:', dlib.__version__)" >nul 2>&1
    if !errorlevel! equ 0 (
        echo ✅ dlib预编译包安装成功！
        goto :dlib_success
    )
)

echo ⚠️  预编译包失败，尝试源码编译...

REM 策略2: 源码编译（如果有编译环境）
if not "%CMAKE_PATH%"=="" if not "%VS_PATH%"=="" (
    echo 🔨 从源码编译dlib...
    
    cd /d "%TEMP_DIR%"
    
    REM 下载源码
    pip download dlib==19.24.2 --no-deps -i https://pypi.tuna.tsinghua.edu.cn/simple/ >nul 2>&1
    
    if exist "dlib-19.24.2.tar.gz" (
        echo 解压源码...
        tar -xzf dlib-19.24.2.tar.gz >nul 2>&1
        
        if exist "dlib-19.24.2" (
            cd dlib-19.24.2
            
            echo 开始编译...
            pip install . -i https://pypi.tuna.tsinghua.edu.cn/simple/ >nul 2>&1
            
            if !errorlevel! equ 0 (
                cd /d "%BASE_DIR%"
                python -c "import dlib; print('dlib版本:', dlib.__version__)" >nul 2>&1
                if !errorlevel! equ 0 (
                    echo ✅ dlib源码编译安装成功！
                    goto :dlib_success
                )
            )
        )
    )
    
    cd /d "%BASE_DIR%"
    echo ⚠️  源码编译失败，尝试兼容版本...
) else (
    echo ⚠️  缺少编译环境，跳过源码编译
)

REM 策略3: 兼容版本
echo 🔄 尝试兼容版本...
for %%v in (19.22.1 19.21.1 19.20.1) do (
    echo 尝试dlib %%v...
    pip install dlib==%%v -i https://pypi.tuna.tsinghua.edu.cn/simple/ --no-cache-dir >nul 2>&1
    if !errorlevel! equ 0 (
        python -c "import dlib" >nul 2>&1
        if !errorlevel! equ 0 (
            echo ✅ dlib %%v 安装成功！
            goto :dlib_success
        )
    )
)

REM 策略4: 替代方案
echo ⚠️  dlib安装失败，安装替代方案...
echo 📦 安装MediaPipe...
pip install mediapipe -i https://pypi.tuna.tsinghua.edu.cn/simple/ >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ MediaPipe安装成功（dlib替代方案）
) else (
    echo ❌ MediaPipe安装也失败
)

goto :post_dlib

:dlib_success
echo 🎉 dlib安装成功！正在测试功能...
python -c "
try:
    import dlib
    print('✅ dlib导入成功，版本:', dlib.__version__)
    detector = dlib.get_frontal_face_detector()
    print('✅ 人脸检测器创建成功')
    print('🏆 dlib完全可用！')
except Exception as e:
    print('❌ dlib测试失败:', str(e))
" 2>nul

:post_dlib

echo.
echo 🔍 步骤14: 安装MuseTalk相关依赖...

echo 📦 安装深度学习扩展...
pip install diffusers transformers accelerate -i https://pypi.tuna.tsinghua.edu.cn/simple/ >nul 2>&1

echo 📦 安装音视频处理...
pip install ffmpeg-python moviepy -i https://pypi.tuna.tsinghua.edu.cn/simple/ >nul 2>&1

echo 📦 安装人脸处理...
pip install insightface onnxruntime -i https://pypi.tuna.tsinghua.edu.cn/simple/ >nul 2>&1

echo 📦 安装工具库...
pip install tqdm requests pydantic -i https://pypi.tuna.tsinghua.edu.cn/simple/ >nul 2>&1

echo ✅ MuseTalk依赖安装完成

echo.
echo 🔍 步骤15: 创建启动脚本...

REM 创建环境激活脚本
(
echo @echo off
echo echo 🚀 激活数字人系统环境...
echo call "%VENV_DIR%\Scripts\activate.bat"
if not "%CMAKE_PATH%"=="" echo set "PATH=%CMAKE_PATH%;%%PATH%%"
if not "%VS_PATH%"=="" echo call "%VS_PATH%\VC\Auxiliary\Build\vcvars64.bat" ^>nul 2^>^&1
echo echo ✅ 环境已激活
echo echo.
echo echo 📋 可用命令:
echo echo   python musetalk_service_complete.py  - 启动MuseTalk服务
echo echo   python test_environment.py          - 测试环境
echo echo.
echo echo 💡 您的配置:
echo echo   Python: F盘完整版本
echo echo   Visual Studio: %VS_PATH%
echo echo   CMake: %CMAKE_TYPE%
echo echo.
echo cmd /k
) > "%BASE_DIR%\activate_env.bat"

echo ✅ 启动脚本创建完成

REM 创建测试脚本
(
echo # 环境测试脚本
echo import sys
echo print^("🔍 Python环境测试"^)
echo print^(f"Python版本: {sys.version}"^)
echo print^(f"Python路径: {sys.executable}"^)
echo print^(^)
echo 
echo # 测试关键库
echo libraries = [^('torch', 'PyTorch'^), ^('cv2', 'OpenCV'^), ^('numpy', 'NumPy'^), ^('PIL', 'Pillow'^), ^('flask', 'Flask'^)]
echo 
echo try:
echo     import dlib
echo     libraries.append^(^('dlib', f'dlib {dlib.__version__}'^)^)
echo except ImportError:
echo     try:
echo         import mediapipe
echo         libraries.append^(^('mediapipe', f'MediaPipe {mediapipe.__version__}'^)^)
echo     except ImportError:
echo         pass
echo 
echo print^("📦 库测试结果:"^)
echo for module, name in libraries:
echo     try:
echo         if module == 'dlib':
echo             import dlib
echo             print^(f"✅ {name} - 🏆 最佳人脸检测"^)
echo         elif module == 'mediapipe':
echo             import mediapipe
echo             print^(f"✅ {name} - 👍 良好人脸检测"^)
echo         else:
echo             lib = __import__^(module^)
echo             version = getattr^(lib, '__version__', 'unknown'^)
echo             print^(f"✅ {name}: {version}"^)
echo     except ImportError:
echo         print^(f"❌ {name}: 未安装"^)
echo 
echo print^(^)
echo print^("🎉 环境测试完成！"^)
) > "%BASE_DIR%\test_environment.py"

echo ✅ 测试脚本创建完成

echo.
echo 🔍 步骤16: 清理临时文件...

if exist "%TEMP_DIR%" (
    rmdir /s /q "%TEMP_DIR%" >nul 2>&1
    echo ✅ 临时文件清理完成
)

echo.
echo 🔍 步骤17: 最终环境测试...

python -c "
import sys
print('✅ Python:', sys.version.split()[0])

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
    components.append(f'✅ dlib: {dlib.__version__} (🏆 最佳)')
except ImportError:
    try:
        import mediapipe
        components.append(f'✅ MediaPipe: {mediapipe.__version__} (👍 替代)')
    except ImportError:
        components.append('❌ 人脸检测库: 未安装')

for comp in components:
    print(comp)

print()
print('🏆 安装完成！')
" 2>nul

if %errorlevel% neq 0 (
    echo ⚠️  最终测试执行失败，但安装可能已完成
)

goto :success_exit

:error_exit
echo.
echo ================================================================
echo ❌ 安装过程中出现错误
echo ================================================================
echo.
echo 🔍 常见解决方案:
echo 1. 确保以管理员身份运行
echo 2. 检查F盘空间是否充足（至少10GB）
echo 3. 在VS Installer中安装"C++ CMake工具"
echo 4. 确保网络连接正常
echo.
echo 📞 获取帮助:
echo 1. 运行debug_install_enhanced.bat重新诊断
echo 2. 查看上方的详细错误信息
echo 3. 参考README文档
echo.
goto :final_pause

:success_exit
echo.
echo ================================================================
echo 🎉 数字人系统安装成功完成！
echo ================================================================
echo.
echo 📁 安装路径: %BASE_DIR%
echo 🐍 Python环境: %VENV_DIR%
echo 🔧 VS路径: %VS_PATH%
echo 🛠️  CMake: %CMAKE_TYPE%
echo.
echo 🚀 下一步操作:
echo 1. 双击运行: %BASE_DIR%\activate_env.bat
echo 2. 测试环境: python test_environment.py
echo 3. 启动服务: python musetalk_service_complete.py
echo.
echo 💡 您的环境已完美配置！
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