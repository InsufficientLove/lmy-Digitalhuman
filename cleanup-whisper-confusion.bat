@echo off
chcp 65001 >nul
echo ================================================================================
echo              🧹 清理Whisper模型混淆问题
echo ================================================================================
echo.
echo [📋] 问题说明:
echo   - C# Whisper.NET 使用 whisper.cpp 格式模型 (.bin)
echo   - MuseTalk 使用 Python Whisper 模型 (HuggingFace格式)
echo   - 两种格式不兼容，不需要同时下载
echo.
pause

echo ================================================================================
echo [步骤 1/3] 检查当前Whisper模型状态
echo ================================================================================

echo [🔍] 检查C# Whisper.NET模型:
if exist "LmyDigitalHuman\Models\ggml-base.bin" (
    for %%I in ("LmyDigitalHuman\Models\ggml-base.bin") do echo [✅] C# Whisper模型: %%~zI bytes
) else (
    echo [❌] C# Whisper模型不存在 (会自动下载)
)

echo.
echo [🔍] 检查MuseTalk Python Whisper模型:
if exist "models\musetalk\MuseTalk\models\whisper" (
    echo [✅] MuseTalk Whisper模型目录存在
    dir "models\musetalk\MuseTalk\models\whisper" /b
) else (
    echo [❌] MuseTalk Whisper模型不存在
)

echo.
echo [🔍] 检查其他可能的Whisper模型:
if exist "models\whisper" (
    echo [⚠️] 发现额外的whisper目录
    dir "models\whisper" /b
) else (
    echo [✅] 没有额外的whisper目录
)

echo.
echo ================================================================================
echo [步骤 2/3] 模型使用说明
echo ================================================================================

echo [📝] Whisper.NET (C#) 模型说明:
echo   - 格式: whisper.cpp (.bin文件)
echo   - 位置: LmyDigitalHuman\Models\ggml-base.bin
echo   - 大小: ~142MB (base模型)
echo   - 下载: 程序启动时自动下载
echo   - 用途: C#语音识别服务
echo.

echo [📝] MuseTalk Whisper (Python) 模型说明:
echo   - 格式: HuggingFace transformers
echo   - 位置: models\musetalk\MuseTalk\models\whisper\
echo   - 大小: ~1GB+
echo   - 下载: MuseTalk官方脚本下载
echo   - 用途: MuseTalk音频特征提取
echo.

echo ================================================================================
echo [步骤 3/3] 清理建议
echo ================================================================================

echo [💡] 建议的清理操作:
echo.
echo [选项A] 保持两套模型 (推荐):
echo   - 保留C# Whisper.NET模型 (用于实时语音识别)
echo   - 保留MuseTalk Whisper模型 (用于数字人生成)
echo   - 两者功能不同，都需要
echo.
echo [选项B] 只保留C# Whisper.NET:
echo   - 删除MuseTalk中的Whisper模型
echo   - 可能影响MuseTalk的音频处理质量
echo   - 节省约1GB空间
echo.
echo [选项C] 优化C# Whisper.NET模型大小:
echo   - 使用tiny模型 (~39MB) 替代base模型 (~142MB)
echo   - 速度更快但准确率略低
echo   - 适合实时应用
echo.

set /p user_choice="请选择操作 (A/B/C/跳过): "

if /i "%user_choice%"=="A" (
    echo [✅] 保持现状，两套模型都保留
    echo [💡] 这是最佳选择，功能完整
    goto end
)

if /i "%user_choice%"=="B" (
    echo [⚠️] 删除MuseTalk Whisper模型...
    if exist "models\musetalk\MuseTalk\models\whisper" (
        rmdir /s /q "models\musetalk\MuseTalk\models\whisper"
        echo [✅] 已删除MuseTalk Whisper模型
    )
    goto end
)

if /i "%user_choice%"=="C" (
    echo [🔧] 配置使用tiny模型...
    echo.
    echo [📝] 请在appsettings.json中添加:
    echo {
    echo   "RealtimeDigitalHuman": {
    echo     "WhisperNet": {
    echo       "ModelSize": "Tiny",
    echo       "ModelPath": "Models/ggml-tiny.bin"
    echo     }
    echo   }
    echo }
    echo.
    pause
    goto end
)

echo [ℹ️] 跳过清理操作

:end
echo.
echo ================================================================================
echo                           清理完成
echo ================================================================================

echo [📊] 最终建议:
echo   1. C# Whisper.NET模型会自动管理，无需手动下载
echo   2. MuseTalk的Whisper模型通过官方脚本下载
echo   3. 两套模型服务不同功能，建议都保留
echo   4. 如需节省空间，可使用tiny模型
echo.

echo 按任意键退出...
pause >nul