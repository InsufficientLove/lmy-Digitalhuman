@echo off
chcp 65001 >nul
echo ================================================================================
echo                📥 商用级数字人模型下载指南
echo ================================================================================
echo.
echo 此脚本将指导您下载所有必需的AI模型文件
echo.
echo 📊 预计下载大小: 50-80GB
echo ⏱️  预计时间: 30-60分钟 (取决于网络速度)
echo.
echo 🔗 需要下载的模型:
echo   1. 大语言模型: Qwen2.5-14B-Instruct (~28GB)
echo   2. MuseTalk模型: 数字人生成模型 (~15GB)
echo   3. Whisper模型: 语音识别模型 (~3GB)
echo   4. TTS模型: 语音合成模型 (~2GB)
echo   5. 其他依赖模型 (~10GB)
echo.
pause

echo ================================================================================
echo [阶段 1/6] 准备下载环境
echo ================================================================================

echo [1.1] 检查网络连接...
ping -n 1 huggingface.co >nul 2>&1
if %errorlevel% neq 0 (
    echo [⚠️] 无法连接到Hugging Face，请检查网络
    echo [💡] 如果在国内，可能需要配置代理或使用镜像站
    pause
)

echo [1.2] 检查Git LFS...
git lfs version >nul 2>&1
if %errorlevel% neq 0 (
    echo [⚠️] Git LFS未安装，大文件下载可能失败
    echo [📝] 安装Git LFS: git lfs install
    echo [💾] 或下载: https://git-lfs.github.io/
    pause
) else (
    echo [✅] Git LFS可用
)

echo [1.3] 创建模型存储目录...
if not exist "models" mkdir models
if not exist "models\llm" mkdir models\llm
if not exist "models\musetalk" mkdir models\musetalk
if not exist "models\whisper" mkdir models\whisper
if not exist "models\tts" mkdir models\tts
echo [✅] 模型目录创建完成

echo ================================================================================
echo [阶段 2/6] 下载大语言模型 (Qwen2.5-14B-Instruct)
echo ================================================================================

echo [2.1] 检查现有LLM模型...
if exist "models\llm\Qwen2.5-14B-Instruct" (
    echo [✅] Qwen2.5-14B-Instruct已存在，跳过下载
) else (
    echo [📥] 开始下载Qwen2.5-14B-Instruct (~28GB)...
    echo [⏱️] 预计时间: 15-30分钟
    echo.
    echo [命令] 请手动执行以下命令:
    echo.
    echo cd models\llm
    echo git clone https://huggingface.co/Qwen/Qwen2.5-14B-Instruct
    echo cd ..\..
    echo.
    echo [🌐] 国内用户可使用镜像:
    echo git clone https://hf-mirror.com/Qwen/Qwen2.5-14B-Instruct
    echo.
    pause
)

echo ================================================================================
echo [阶段 3/6] 下载MuseTalk模型
echo ================================================================================

echo [3.1] 检查MuseTalk主模型...
if exist "models\musetalk\MuseTalk" (
    echo [✅] MuseTalk主模型已存在
) else (
    echo [📥] 下载MuseTalk主模型 (~10GB)...
    echo.
    echo [命令] 请手动执行:
    echo.
    echo cd models\musetalk
    echo git clone https://github.com/TMElyralab/MuseTalk.git
    echo cd ..\..
    echo.
    pause
)

echo [3.2] MuseTalk预训练权重...
echo [📝] MuseTalk需要额外的预训练权重文件
echo [💾] 下载地址: https://github.com/TMElyralab/MuseTalk/releases
echo.
echo [📋] 需要下载的文件:
echo   - musetalk.json
echo   - pytorch_model.bin
echo   - face_parsing.pth
echo   - DNet.pth
echo.
echo [💡] 这些文件需要放在 models\musetalk\MuseTalk\models\ 目录下
echo.
pause

echo ================================================================================
echo [阶段 4/6] 下载Whisper语音识别模型
echo ================================================================================

echo [4.1] 检查Whisper模型...
if exist "models\whisper\whisper-large-v3" (
    echo [✅] Whisper模型已存在
) else (
    echo [📥] 下载Whisper Large V3 (~3GB)...
    echo.
    echo [命令] 请手动执行:
    echo.
    echo cd models\whisper
    echo git clone https://huggingface.co/openai/whisper-large-v3
    echo cd ..\..
    echo.
    echo [🌐] 国内镜像:
    echo git clone https://hf-mirror.com/openai/whisper-large-v3
    echo.
    pause
)

echo ================================================================================
echo [阶段 5/6] 下载TTS语音合成模型
echo ================================================================================

echo [5.1] Edge-TTS模型...
echo [📝] Edge-TTS使用在线API，无需下载模型文件
echo [✅] 但需要网络连接

echo [5.2] 可选：FastSpeech2离线模型...
echo [💡] 如需离线TTS，可下载FastSpeech2模型
echo.
echo [命令] 可选下载:
echo.
echo cd models\tts
echo git clone https://huggingface.co/microsoft/fastspeech2
echo cd ..\..
echo.

echo ================================================================================
echo [阶段 6/6] 验证下载结果
echo ================================================================================

echo [6.1] 检查模型文件完整性...

set MISSING_MODELS=0

if not exist "models\llm\Qwen2.5-14B-Instruct" (
    echo [❌] Qwen2.5-14B-Instruct缺失
    set /a MISSING_MODELS+=1
) else (
    echo [✅] Qwen2.5-14B-Instruct存在
)

if not exist "models\musetalk\MuseTalk" (
    echo [❌] MuseTalk模型缺失
    set /a MISSING_MODELS+=1
) else (
    echo [✅] MuseTalk模型存在
)

if not exist "models\whisper\whisper-large-v3" (
    echo [❌] Whisper模型缺失
    set /a MISSING_MODELS+=1
) else (
    echo [✅] Whisper模型存在
)

echo.
echo [6.2] 下载结果总结...
if %MISSING_MODELS% equ 0 (
    echo [🎉] 所有必需模型已下载完成！
    echo.
    echo [📊] 模型统计:
    echo   ✅ 大语言模型: Qwen2.5-14B-Instruct
    echo   ✅ 数字人模型: MuseTalk
    echo   ✅ 语音识别: Whisper Large V3
    echo   ✅ 语音合成: Edge-TTS (在线)
    echo.
    echo [🚀] 下一步: 运行部署脚本
    echo   deploy-production-now.bat
    echo.
) else (
    echo [⚠️] 还有 %MISSING_MODELS% 个模型未下载完成
    echo [📝] 请按照上述指南完成剩余模型下载
    echo.
)

echo ================================================================================
echo                    📋 手动下载命令汇总
echo ================================================================================
echo.
echo 如果需要手动下载，请依次执行以下命令:
echo.
echo # 1. 大语言模型
echo cd models\llm
echo git clone https://huggingface.co/Qwen/Qwen2.5-14B-Instruct
echo cd ..\..
echo.
echo # 2. MuseTalk模型
echo cd models\musetalk  
echo git clone https://github.com/TMElyralab/MuseTalk.git
echo cd ..\..
echo.
echo # 3. Whisper模型
echo cd models\whisper
echo git clone https://huggingface.co/openai/whisper-large-v3
echo cd ..\..
echo.
echo # 4. 安装Git LFS (如果未安装)
echo git lfs install
echo.
echo ================================================================================
echo                        📥 国内用户镜像站
echo ================================================================================
echo.
echo 如果访问GitHub/HuggingFace较慢，可使用以下镜像:
echo.
echo # HuggingFace镜像
echo git clone https://hf-mirror.com/Qwen/Qwen2.5-14B-Instruct
echo git clone https://hf-mirror.com/openai/whisper-large-v3
echo.
echo # GitHub镜像 (可选)
echo git clone https://ghproxy.com/https://github.com/TMElyralab/MuseTalk.git
echo.
echo ================================================================================
echo                              下载完成
echo ================================================================================
echo.
echo 💡 重要提示:
echo   1. 确保所有模型都下载完整
echo   2. MuseTalk需要额外的权重文件
echo   3. 下载完成后运行: deploy-production-now.bat
echo   4. 如遇问题，检查网络连接和磁盘空间
echo.
echo 按任意键退出...
pause >nul