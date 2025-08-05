@echo off
REM MuseTalk Engine 启动脚本
REM 启动增强版 MuseTalk 推理服务
REM 
REM 作者: Claude Sonnet
REM 版本: 1.0
REM 兼容: C# MuseTalk 服务

echo ========================================
echo    Enhanced MuseTalk Engine 启动器
echo ========================================
echo.

REM 检查 Python 环境
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未找到 Python，请确保 Python 已安装并添加到 PATH
    pause
    exit /b 1
)

REM 检查必要目录
if not exist "MuseTalkEngine" (
    echo ❌ 错误: MuseTalkEngine 目录不存在
    pause
    exit /b 1
)

if not exist "MuseTalk" (
    echo ❌ 错误: MuseTalk 目录不存在，请确保模型数据目录存在
    pause
    exit /b 1
)

echo ✅ 环境检查通过
echo.

REM 切换到 MuseTalkEngine 目录
cd MuseTalkEngine

echo 🚀 启动选项:
echo 1. 增强推理服务 V4 (推荐)
echo 2. 集成服务 (预处理+推理)
echo 3. 超快实时推理
echo 4. 优化推理 V3
echo 5. 持久化服务
echo 0. 退出
echo.

set /p choice="请选择启动模式 (1-5): "

if "%choice%"=="1" goto start_v4
if "%choice%"=="2" goto start_integrated
if "%choice%"=="3" goto start_ultra_fast
if "%choice%"=="4" goto start_v3
if "%choice%"=="5" goto start_persistent
if "%choice%"=="0" goto end
goto invalid_choice

:start_v4
echo.
echo 🔥 启动增强推理服务 V4...
echo 使用默认参数，兼容 C# 服务接口
echo.
python enhanced_musetalk_inference_v4.py --help
echo.
echo 💡 要启动服务，请使用类似以下命令:
echo python enhanced_musetalk_inference_v4.py --template_id your_template --audio_path input.wav --output_path output.mp4
goto end

:start_integrated
echo.
echo 🔥 启动集成服务...
echo 包含预处理和实时推理功能
echo.
python integrated_musetalk_service.py --help
echo.
echo 💡 要启动服务，请使用类似以下命令:
echo python integrated_musetalk_service.py --mode preprocess --template_video template.mp4
echo python integrated_musetalk_service.py --mode inference --template_id template_001 --audio_path input.wav
goto end

:start_ultra_fast
echo.
echo 🔥 启动超快实时推理...
echo 基于预处理缓存的极速推理
echo.
python ultra_fast_realtime_inference.py --help
echo.
echo 💡 要启动服务，请使用类似以下命令:
echo python ultra_fast_realtime_inference.py --template_id template_001 --audio_path input.wav --output_path output.mp4
goto end

:start_v3
echo.
echo 🔥 启动优化推理 V3...
echo 传统优化版本，稳定可靠
echo.
python optimized_musetalk_inference_v3.py --help
echo.
echo 💡 要启动服务，请使用类似以下命令:
echo python optimized_musetalk_inference_v3.py --template_id template_001 --audio_path input.wav --output_path output.mp4
goto end

:start_persistent
echo.
echo 🔥 启动持久化服务...
echo 长期运行的后台服务
echo.
python start_persistent_service.py
goto end

:invalid_choice
echo ❌ 无效选择，请输入 0-5 之间的数字
pause
goto end

:end
echo.
echo 👋 感谢使用 Enhanced MuseTalk Engine!
cd ..
pause