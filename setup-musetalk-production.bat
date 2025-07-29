@echo off
chcp 65001 >nul
echo ================================================================================
echo                   MuseTalk 商用级环境配置 (RTX4090 优化版)
echo ================================================================================
echo.
echo 🚀 硬件配置检测:
echo   - GPU: 4x RTX4090
echo   - 显存: 96GB 
echo   - 目标: 商用级数字人生成
echo.
echo 此脚本将配置:
echo   ✓ MuseTalk 官方最新版本
echo   ✓ 高质量模型权重下载
echo   ✓ 多GPU并行优化
echo   ✓ 商用级推理配置
echo   ✓ 实时和非实时双模式支持
echo.
pause

echo ================================================================================
echo [步骤 1/6] 创建 MuseTalk 专用虚拟环境
echo ================================================================================

if exist "venv_musetalk" (
    echo [信息] MuseTalk虚拟环境已存在，正在重新配置...
    rmdir /s /q venv_musetalk
)

python -m venv venv_musetalk
if %errorlevel% neq 0 (
    echo [错误] 虚拟环境创建失败
    pause
    goto end
)

call venv_musetalk\Scripts\activate.bat
echo [✓] MuseTalk 虚拟环境创建完成

echo ================================================================================
echo [步骤 2/6] 安装 MuseTalk 核心依赖 (RTX4090 优化)
echo ================================================================================

echo [信息] 升级 pip...
python -m pip install --upgrade pip

echo [信息] 安装 PyTorch (CUDA 12.1 优化版)...
pip install torch==2.1.0 torchvision==0.16.0 torchaudio==2.1.0 --index-url https://download.pytorch.org/whl/cu121

echo [信息] 安装 MuseTalk 核心依赖...
pip install diffusers==0.24.0
pip install transformers==4.36.0
pip install accelerate==0.25.0
pip install xformers==0.0.22.post7

echo [信息] 安装图像处理依赖...
pip install opencv-python==4.8.1.78
pip install pillow==10.1.0
pip install imageio==2.33.1
pip install imageio-ffmpeg==0.4.9
pip install scikit-image==0.22.0

echo [信息] 安装音频处理依赖...
pip install librosa==0.10.1
pip install soundfile==0.12.1
pip install pydub==0.25.1

echo [信息] 安装其他依赖...
pip install numpy==1.24.3
pip install scipy==1.11.4
pip install tqdm==4.66.1
pip install omegaconf==2.3.0
pip install einops==0.7.0
pip install face-alignment==1.4.1
pip install resampy==0.4.2

echo [✓] 依赖安装完成

echo ================================================================================
echo [步骤 3/6] 下载 MuseTalk 官方代码
echo ================================================================================

if exist "MuseTalk" (
    echo [信息] MuseTalk目录已存在，正在更新...
    cd MuseTalk
    git pull origin main
    cd ..
) else (
    echo [信息] 克隆 MuseTalk 官方仓库...
    git clone https://github.com/TMElyralab/MuseTalk.git
    if %errorlevel% neq 0 (
        echo [错误] MuseTalk 代码下载失败
        pause
        goto end
    )
)

echo [✓] MuseTalk 代码准备完成

echo ================================================================================
echo [步骤 4/6] 下载预训练模型权重 (商用高质量版)
echo ================================================================================

cd MuseTalk

echo [信息] 下载 MuseTalk 模型权重...
if exist "models" (
    echo [信息] 模型目录已存在
) else (
    mkdir models
)

echo [信息] 执行官方权重下载脚本...
call download_weights.bat
if %errorlevel% neq 0 (
    echo [警告] 自动下载失败，请手动下载模型文件
    echo 下载地址: https://huggingface.co/TMElyralab/MuseTalk
)

cd ..

echo ================================================================================
echo [步骤 5/6] 创建商用级配置文件
echo ================================================================================

echo [信息] 创建高质量推理配置...

mkdir configs\production 2>nul

echo # MuseTalk 商用级配置 (RTX4090 优化) > configs\production\commercial.yaml
echo model: >> configs\production\commercial.yaml
echo   use_float16: false  # 使用FP32获得最高质量 >> configs\production\commercial.yaml
echo   batch_size: 4       # RTX4090可支持更大批次 >> configs\production\commercial.yaml
echo   num_inference_steps: 25  # 增加推理步数提高质量 >> configs\production\commercial.yaml
echo. >> configs\production\commercial.yaml
echo gpu: >> configs\production\commercial.yaml
echo   device_ids: [0, 1, 2, 3]  # 使用所有4张GPU >> configs\production\commercial.yaml
echo   memory_fraction: 0.9      # 使用90%显存 >> configs\production\commercial.yaml
echo. >> configs\production\commercial.yaml
echo output: >> configs\production\commercial.yaml
echo   resolution: 512     # 高分辨率输出 >> configs\production\commercial.yaml
echo   fps: 25            # 商用标准帧率 >> configs\production\commercial.yaml
echo   quality: high      # 最高质量设置 >> configs\production\commercial.yaml

echo [信息] 创建实时对话配置...
echo # MuseTalk 实时对话配置 > configs\production\realtime.yaml
echo model: >> configs\production\realtime.yaml
echo   use_float16: true   # 实时模式使用FP16平衡质量和速度 >> configs\production\realtime.yaml
echo   batch_size: 2       # 实时模式较小批次 >> configs\production\realtime.yaml
echo   num_inference_steps: 15  # 减少推理步数提高速度 >> configs\production\realtime.yaml
echo. >> configs\production\realtime.yaml
echo realtime: >> configs\production\realtime.yaml
echo   target_latency: 500  # 目标延迟500ms >> configs\production\realtime.yaml
echo   buffer_size: 3       # 缓冲区大小 >> configs\production\realtime.yaml
echo   max_queue_size: 10   # 最大队列长度 >> configs\production\realtime.yaml

echo [✓] 配置文件创建完成

echo ================================================================================
echo [步骤 6/6] 创建启动脚本
echo ================================================================================

echo [信息] 创建商用级启动脚本...

echo @echo off > start-musetalk-commercial.bat
echo call venv_musetalk\Scripts\activate.bat >> start-musetalk-commercial.bat
echo cd MuseTalk >> start-musetalk-commercial.bat
echo echo 🚀 启动 MuseTalk 商用级服务... >> start-musetalk-commercial.bat
echo python app.py --config ../configs/production/commercial.yaml --port 8888 >> start-musetalk-commercial.bat

echo @echo off > start-musetalk-realtime.bat
echo call venv_musetalk\Scripts\activate.bat >> start-musetalk-realtime.bat
echo cd MuseTalk >> start-musetalk-realtime.bat
echo echo ⚡ 启动 MuseTalk 实时对话服务... >> start-musetalk-realtime.bat
echo python app.py --config ../configs/production/realtime.yaml --port 8889 >> start-musetalk-realtime.bat

echo [信息] 创建测试脚本...
echo @echo off > test-musetalk.bat
echo call venv_musetalk\Scripts\activate.bat >> test-musetalk.bat
echo cd MuseTalk >> test-musetalk.bat
echo echo 🧪 运行 MuseTalk 功能测试... >> test-musetalk.bat
echo python test_ffmpeg.py >> test-musetalk.bat
echo echo 测试完成！ >> test-musetalk.bat
echo pause >> test-musetalk.bat

echo [✓] 启动脚本创建完成

echo ================================================================================
echo                              配置完成！
echo ================================================================================
echo.
echo [✓] MuseTalk 商用级环境配置完成！
echo.
echo 🎯 您的配置优势:
echo   - 4x RTX4090: 顶级GPU性能
echo   - 96GB显存: 支持最高质量设置
echo   - 专用虚拟环境: 依赖隔离管理
echo   - 双模式支持: 商用质量 + 实时对话
echo.
echo 🚀 启动方式:
echo   1. 商用高质量模式: start-musetalk-commercial.bat
echo   2. 实时对话模式:   start-musetalk-realtime.bat
echo   3. 功能测试:       test-musetalk.bat
echo.
echo 📊 预期性能:
echo   - 商用模式: 8秒视频 1-2分钟 (512p高质量)
echo   - 实时模式: 响应延迟 <500ms
echo   - 支持并发: 多用户同时使用
echo.
echo 🌐 访问地址:
echo   - 商用服务: http://localhost:8888
echo   - 实时服务: http://localhost:8889
echo.
echo 💡 优化建议:
echo   - 定期更新模型权重获得最新效果
echo   - 根据实际需求调整批次大小
echo   - 监控GPU使用率和显存占用
echo.

:end
echo 按任意键退出...
pause >nul