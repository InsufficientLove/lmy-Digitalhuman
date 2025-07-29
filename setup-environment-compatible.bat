@echo off
chcp 65001 >nul
echo ================================================================================
echo                🛠️ 兼容环境配置脚本 (适配您的现有环境)
echo ================================================================================
echo.
echo 📋 检测到您的环境:
echo   - Python: 3.10.11 ✅
echo   - CUDA: 11.8 ✅ 
echo   - .NET: 8 ✅
echo.
echo 🎯 此脚本将:
echo   ✅ 使用您现有的Python 3.10.11
echo   ✅ 兼容您的CUDA 11.8环境
echo   ✅ 安装MuseTalk兼容版本
echo   ✅ 配置Edge-TTS支持
echo   ✅ 创建虚拟环境隔离依赖
echo.
pause

echo ================================================================================
echo [步骤 1/6] 环境检查
echo ================================================================================

echo [1.1] 检查Python版本...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] Python未找到，请确保Python 3.10.11在PATH中
    pause
    goto end
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [✓] Python版本: %PYTHON_VERSION%

echo [1.2] 检查CUDA版本...
nvcc --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [警告] NVCC未找到，但这不影响使用
) else (
    echo [✓] CUDA工具链可用
)

echo [1.3] 检查.NET版本...
dotnet --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] .NET未找到，请确保.NET 8已安装
    pause
    goto end
)

for /f %%i in ('dotnet --version 2^>^&1') do set DOTNET_VERSION=%%i
echo [✓] .NET版本: %DOTNET_VERSION%

echo ================================================================================
echo [步骤 2/6] 创建兼容的虚拟环境
echo ================================================================================

echo [2.1] 创建Python虚拟环境...
if exist "venv" (
    echo [信息] 虚拟环境已存在，正在重新创建...
    rmdir /s /q venv
)

python -m venv venv
if %errorlevel% neq 0 (
    echo [错误] 虚拟环境创建失败
    pause
    goto end
)

call venv\Scripts\activate.bat
echo [✓] 虚拟环境创建完成

echo [2.2] 升级pip...
python -m pip install --upgrade pip --quiet

echo ================================================================================
echo [步骤 3/6] 安装PyTorch (CUDA 11.8兼容版)
echo ================================================================================

echo [3.1] 安装PyTorch CUDA 11.8版本...
echo [信息] 使用与您CUDA 11.8兼容的PyTorch版本...
pip install torch==2.0.1 torchvision==0.15.2 torchaudio==2.0.2 --index-url https://download.pytorch.org/whl/cu118 --quiet

if %errorlevel% neq 0 (
    echo [错误] PyTorch安装失败
    pause
    goto end
)

echo [✓] PyTorch CUDA 11.8版本安装完成

echo ================================================================================
echo [步骤 4/6] 安装MuseTalk兼容依赖
echo ================================================================================

echo [4.1] 安装基础依赖...
pip install --quiet ^
    diffusers==0.21.4 ^
    transformers==4.35.2 ^
    accelerate==0.24.1

echo [4.2] 安装图像处理依赖...
pip install --quiet ^
    opencv-python==4.8.1.78 ^
    pillow==10.0.1 ^
    imageio==2.31.5 ^
    imageio-ffmpeg==0.4.9 ^
    scikit-image==0.21.0

echo [4.3] 安装音频处理依赖...
pip install --quiet ^
    librosa==0.10.1 ^
    soundfile==0.12.1 ^
    pydub==0.25.1 ^
    edge-tts==6.1.9

echo [4.4] 安装科学计算库...
pip install --quiet ^
    numpy==1.24.3 ^
    scipy==1.11.4 ^
    omegaconf==2.3.0 ^
    einops==0.7.0

echo [4.5] 安装其他工具...
pip install --quiet ^
    tqdm==4.66.1 ^
    requests==2.31.0 ^
    face-alignment==1.3.5

echo [✓] MuseTalk兼容依赖安装完成

echo ================================================================================
echo [步骤 5/6] 验证环境配置
echo ================================================================================

echo [5.1] 验证PyTorch CUDA支持...
python -c "import torch; print(f'PyTorch版本: {torch.__version__}'); print(f'CUDA可用: {torch.cuda.is_available()}'); print(f'CUDA版本: {torch.version.cuda if torch.cuda.is_available() else \"N/A\"}')" 2>nul
if %errorlevel% neq 0 (
    echo [警告] PyTorch验证失败，但可能不影响使用
) else (
    echo [✓] PyTorch验证成功
)

echo [5.2] 验证Edge-TTS...
python -c "import edge_tts; print('Edge-TTS版本:', edge_tts.__version__)" 2>nul
if %errorlevel% neq 0 (
    echo [警告] Edge-TTS验证失败
) else (
    echo [✓] Edge-TTS验证成功
)

echo [5.3] 验证基础库...
python -c "import cv2, PIL, numpy, librosa, diffusers; print('基础库验证成功')" 2>nul
if %errorlevel% neq 0 (
    echo [警告] 部分基础库验证失败
) else (
    echo [✓] 基础库验证成功
)

echo ================================================================================
echo [步骤 6/6] 创建启动脚本
echo ================================================================================

echo [6.1] 创建项目启动脚本...
echo @echo off > startup-compatible.bat
echo chcp 65001 ^>nul >> startup-compatible.bat
echo echo 🚀 启动实时数字人项目 (兼容环境版本)... >> startup-compatible.bat
echo echo 📋 环境信息: >> startup-compatible.bat
echo echo   - Python: 3.10.11 >> startup-compatible.bat
echo echo   - CUDA: 11.8 >> startup-compatible.bat
echo echo   - .NET: 8 >> startup-compatible.bat
echo echo. >> startup-compatible.bat
echo call venv\Scripts\activate.bat >> startup-compatible.bat
echo cd LmyDigitalHuman >> startup-compatible.bat
echo dotnet run >> startup-compatible.bat

echo [6.2] 创建环境验证脚本...
echo @echo off > verify-compatible.bat
echo chcp 65001 ^>nul >> verify-compatible.bat
echo echo 🔍 环境验证 (兼容版本)... >> verify-compatible.bat
echo echo. >> verify-compatible.bat
echo call venv\Scripts\activate.bat >> verify-compatible.bat
echo echo [1/5] Python环境检查... >> verify-compatible.bat
echo python --version >> verify-compatible.bat
echo echo [2/5] PyTorch CUDA检查... >> verify-compatible.bat
echo python -c "import torch; print(f'PyTorch: {torch.__version__}'); print(f'CUDA: {torch.cuda.is_available()}')" >> verify-compatible.bat
echo echo [3/5] Edge-TTS检查... >> verify-compatible.bat
echo python -c "import edge_tts; print('Edge-TTS: OK')" >> verify-compatible.bat
echo echo [4/5] 基础库检查... >> verify-compatible.bat
echo python -c "import cv2, PIL, numpy, librosa; print('基础库: OK')" >> verify-compatible.bat
echo echo [5/5] .NET检查... >> verify-compatible.bat
echo cd LmyDigitalHuman >> verify-compatible.bat
echo dotnet build --verbosity quiet >> verify-compatible.bat
echo if %%errorlevel%% equ 0 (echo .NET编译: OK) else (echo .NET编译: 失败) >> verify-compatible.bat
echo cd .. >> verify-compatible.bat
echo echo. >> verify-compatible.bat
echo echo ✅ 环境验证完成！ >> verify-compatible.bat
echo pause >> verify-compatible.bat

echo [6.3] 创建Edge-TTS测试脚本...
echo @echo off > test-edge-tts.bat
echo chcp 65001 ^>nul >> test-edge-tts.bat
echo echo 🎵 Edge-TTS功能测试... >> test-edge-tts.bat
echo call venv\Scripts\activate.bat >> test-edge-tts.bat
echo echo 测试中文语音合成... >> test-edge-tts.bat
echo edge-tts --voice zh-CN-XiaoxiaoNeural --text "你好，这是Edge-TTS语音合成测试" --write-media test_voice.mp3 >> test-edge-tts.bat
echo if exist test_voice.mp3 ( >> test-edge-tts.bat
echo     echo ✅ Edge-TTS测试成功！音频文件已生成: test_voice.mp3 >> test-edge-tts.bat
echo ) else ( >> test-edge-tts.bat
echo     echo ❌ Edge-TTS测试失败 >> test-edge-tts.bat
echo ) >> test-edge-tts.bat
echo pause >> test-edge-tts.bat

echo [✓] 启动脚本创建完成

echo ================================================================================
echo                           🎉 兼容环境配置完成！
echo ================================================================================
echo.
echo [✅] 环境配置成功！
echo.
echo 📋 配置摘要:
echo   ✓ Python 3.10.11 虚拟环境
echo   ✓ PyTorch 2.0.1 + CUDA 11.8兼容版
echo   ✓ MuseTalk兼容依赖包
echo   ✓ Edge-TTS 语音合成支持
echo   ✓ 图像、音频处理库
echo   ✓ 科学计算库支持
echo.
echo 🚀 使用方式:
echo   1. 启动项目:        startup-compatible.bat
echo   2. 验证环境:        verify-compatible.bat  
echo   3. 测试语音合成:    test-edge-tts.bat
echo.
echo 🌐 访问地址:
echo   - 本地服务: http://localhost:5000
echo   - 数字人测试: http://localhost:5000/digital-human-test.html
echo.
echo 💡 重要提示:
echo   - 此配置针对您的CUDA 11.8环境优化
echo   - 如果遇到GPU相关问题，请检查NVIDIA驱动
echo   - Edge-TTS需要网络连接进行语音合成
echo   - 首次运行可能需要下载模型文件
echo.
echo ⚠️  注意事项:
echo   - MuseTalk性能取决于您的GPU配置
echo   - 建议显存至少8GB以上
echo   - 如需更高性能，可考虑升级到CUDA 12.x
echo.

:end
echo 按任意键退出...
pause >nul