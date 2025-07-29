@echo off
chcp 65001 >nul
echo ================================================================================
echo                 🎮 单GPU环境配置 (性能阉割版)
echo ================================================================================
echo.
echo 🎯 适用场景:
echo   - 单张GPU (GTX/RTX系列)
echo   - 开发测试环境
echo   - 资源受限场景
echo   - 演示Demo用途
echo.
echo 📋 性能预期:
echo   - 语音识别: ~200ms
echo   - LLM推理: ~800ms  
echo   - TTS合成: ~150ms
echo   - 视频生成: ~3-5秒
echo   - 总延迟: ~4-6秒 (可接受的演示效果)
echo.
pause

echo ================================================================================
echo [步骤 1/7] 环境检查
echo ================================================================================

echo [1.1] 检查CUDA版本...
nvcc --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] CUDA未安装，请先安装CUDA 12.1
    echo 下载地址: https://developer.nvidia.com/cuda-12-1-0-download-archive
    pause
    goto end
)

echo [1.2] 检查GPU...
nvidia-smi >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] NVIDIA GPU驱动未安装
    pause
    goto end
)

echo [✓] GPU环境检查完成

echo ================================================================================
echo [步骤 2/7] 创建单GPU虚拟环境
echo ================================================================================

if exist "venv_single" (
    echo [信息] 删除旧环境...
    rmdir /s /q venv_single
)

python -m venv venv_single
call venv_single\Scripts\activate.bat
python -m pip install --upgrade pip --quiet

echo [✓] 单GPU虚拟环境创建完成

echo ================================================================================
echo [步骤 3/7] 安装PyTorch (CUDA 12.1优化)
echo ================================================================================

echo [信息] 安装PyTorch CUDA 12.1版本...
pip install torch==2.1.0 torchvision==0.16.0 torchaudio==2.1.0 --index-url https://download.pytorch.org/whl/cu121 --quiet

echo [✓] PyTorch安装完成

echo ================================================================================
echo [步骤 4/7] 安装轻量化AI库
echo ================================================================================

echo [4.1] 安装基础AI库...
pip install --quiet ^
    transformers==4.35.2 ^
    diffusers==0.21.4 ^
    accelerate==0.24.1

echo [4.2] 安装MuseTalk轻量版...
pip install --quiet ^
    opencv-python==4.8.1.78 ^
    pillow==10.0.1 ^
    imageio==2.31.5 ^
    imageio-ffmpeg==0.4.9

echo [4.3] 安装音频处理...
pip install --quiet ^
    librosa==0.10.1 ^
    soundfile==0.12.1 ^
    pydub==0.25.1 ^
    edge-tts==6.1.9

echo [4.4] 安装科学计算...
pip install --quiet ^
    numpy==1.24.3 ^
    scipy==1.11.4 ^
    omegaconf==2.3.0 ^
    einops==0.7.0

echo [✓] 轻量化AI库安装完成

echo ================================================================================
echo [步骤 5/7] 配置单GPU优化
echo ================================================================================

echo [5.1] 创建单GPU配置文件...
mkdir configs\single_gpu 2>nul

echo # 单GPU优化配置 > configs\single_gpu\config.yaml
echo gpu: >> configs\single_gpu\config.yaml
echo   device_count: 1 >> configs\single_gpu\config.yaml
echo   memory_fraction: 0.8 >> configs\single_gpu\config.yaml
echo   batch_size: 1 >> configs\single_gpu\config.yaml
echo. >> configs\single_gpu\config.yaml
echo musetalk: >> configs\single_gpu\config.yaml
echo   resolution: 256  # 降低分辨率提升速度 >> configs\single_gpu\config.yaml
echo   fps: 15         # 降低帧率 >> configs\single_gpu\config.yaml
echo   inference_steps: 10  # 减少推理步数 >> configs\single_gpu\config.yaml
echo   use_float16: true    # 使用半精度 >> configs\single_gpu\config.yaml
echo. >> configs\single_gpu\config.yaml
echo llm: >> configs\single_gpu\config.yaml
echo   max_tokens: 50      # 限制输出长度 >> configs\single_gpu\config.yaml
echo   temperature: 0.7 >> configs\single_gpu\config.yaml
echo. >> configs\single_gpu\config.yaml
echo tts: >> configs\single_gpu\config.yaml
echo   voice: "zh-CN-XiaoxiaoNeural" >> configs\single_gpu\config.yaml
echo   rate: "+0%%" >> configs\single_gpu\config.yaml

echo [✓] 单GPU配置完成

echo ================================================================================
echo [步骤 6/7] 创建WebRTC前端支持
echo ================================================================================

echo [6.1] 安装WebRTC依赖...
pip install --quiet ^
    websockets==12.0 ^
    aiohttp==3.9.1 ^
    python-socketio==5.10.0

echo [6.2] 创建WebRTC配置...
mkdir wwwroot\js 2>nul

echo // WebRTC单GPU配置 > wwwroot\js\webrtc-single.js
echo const singleGPUConfig = { >> wwwroot\js\webrtc-single.js
echo   iceServers: [{ urls: 'stun:stun.l.google.com:19302' }], >> wwwroot\js\webrtc-single.js
echo   video: { >> wwwroot\js\webrtc-single.js
echo     width: { ideal: 640 }, >> wwwroot\js\webrtc-single.js
echo     height: { ideal: 480 }, >> wwwroot\js\webrtc-single.js
echo     frameRate: { ideal: 15 } >> wwwroot\js\webrtc-single.js
echo   }, >> wwwroot\js\webrtc-single.js
echo   audio: { >> wwwroot\js\webrtc-single.js
echo     sampleRate: 16000, >> wwwroot\js\webrtc-single.js
echo     channelCount: 1 >> wwwroot\js\webrtc-single.js
echo   } >> wwwroot\js\webrtc-single.js
echo }; >> wwwroot\js\webrtc-single.js

echo [✓] WebRTC支持配置完成

echo ================================================================================
echo [步骤 7/7] 创建启动脚本
echo ================================================================================

echo @echo off > start-single-gpu.bat
echo chcp 65001 ^>nul >> start-single-gpu.bat
echo echo 🎮 启动单GPU数字人服务... >> start-single-gpu.bat
echo echo 📊 性能模式: 演示级 (4-6秒延迟) >> start-single-gpu.bat
echo echo 🎯 GPU配置: 单卡优化 >> start-single-gpu.bat
echo echo. >> start-single-gpu.bat
echo call venv_single\Scripts\activate.bat >> start-single-gpu.bat
echo set CUDA_VISIBLE_DEVICES=0 >> start-single-gpu.bat
echo set PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:256 >> start-single-gpu.bat
echo cd LmyDigitalHuman >> start-single-gpu.bat
echo dotnet run --configuration Release >> start-single-gpu.bat

echo [✓] 启动脚本创建完成

echo ================================================================================
echo                        🎉 单GPU环境配置完成！
echo ================================================================================
echo.
echo [✅] 配置成功！
echo.
echo 🎮 单GPU性能特点:
echo   ✓ 演示级延迟 (4-6秒)
echo   ✓ 低资源占用 (6-8GB显存)
echo   ✓ 稳定可靠运行
echo   ✓ 适合开发测试
echo.
echo 🚀 启动方式:
echo   start-single-gpu.bat
echo.
echo 🌐 访问地址:
echo   http://localhost:5000 (单GPU优化版)
echo.
echo 💡 优化建议:
echo   - 如需更高性能，使用4GPU版本
echo   - 适合演示和功能验证
echo   - 建议显存8GB以上
echo.

:end
echo 按任意键退出...
pause >nul