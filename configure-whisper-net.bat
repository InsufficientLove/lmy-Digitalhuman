@echo off
chcp 65001 >nul
echo ================================================================================
echo              🎤 配置Whisper.NET语音识别模型
echo ================================================================================
echo.
echo [📋] Whisper.NET模型选项:
echo   - Tiny:   39MB,  快速但准确率较低 (适合实时)
echo   - Base:   142MB, 平衡速度和准确率 (默认推荐)
echo   - Small:  466MB, 更高准确率
echo   - Medium: 1.5GB, 高准确率
echo   - Large:  2.9GB, 最高准确率 (识别率最好)
echo.
echo [💡] 重要说明:
echo   - 模型只需下载一次，保存在本地
echo   - 程序启动时会自动检查，存在则不重复下载
echo   - 推荐Large模型获得最佳识别效果
echo.
pause

echo ================================================================================
echo [步骤 1/3] 选择模型大小
echo ================================================================================

echo 请选择Whisper.NET模型:
echo [1] Tiny   (39MB)  - 最快速度，适合实时场景
echo [2] Base   (142MB) - 平衡选择 (当前默认)
echo [3] Small  (466MB) - 更好准确率
echo [4] Medium (1.5GB) - 高准确率
echo [5] Large  (2.9GB) - 最佳识别率 (推荐)
echo.

set /p model_choice="请输入选择 (1-5): "

if "%model_choice%"=="1" (
    set model_size=Tiny
    set model_file=ggml-tiny.bin
    set model_desc=最快速度
) else if "%model_choice%"=="2" (
    set model_size=Base
    set model_file=ggml-base.bin
    set model_desc=平衡选择
) else if "%model_choice%"=="3" (
    set model_size=Small
    set model_file=ggml-small.bin
    set model_desc=更好准确率
) else if "%model_choice%"=="4" (
    set model_size=Medium
    set model_file=ggml-medium.bin
    set model_desc=高准确率
) else if "%model_choice%"=="5" (
    set model_size=Large
    set model_file=ggml-large-v3.bin
    set model_desc=最佳识别率
) else (
    echo [⚠️] 无效选择，使用默认Base模型
    set model_size=Base
    set model_file=ggml-base.bin
    set model_desc=平衡选择
)

echo.
echo [✅] 已选择: %model_size% 模型 (%model_desc%)

echo.
echo ================================================================================
echo [步骤 2/3] 创建配置文件
echo ================================================================================

echo [🔧] 创建Whisper.NET配置...

if not exist "LmyDigitalHuman\Models" mkdir "LmyDigitalHuman\Models"

echo [📝] 更新appsettings.json配置...

set config_content={
set config_content=%config_content%  "RealtimeDigitalHuman": {
set config_content=%config_content%    "WhisperNet": {
set config_content=%config_content%      "ModelSize": "%model_size%",
set config_content=%config_content%      "ModelPath": "Models/%model_file%"
set config_content=%config_content%    }
set config_content=%config_content%  }
set config_content=%config_content%}

echo [💡] 建议的appsettings.json配置:
echo %config_content%

echo.
echo ================================================================================
echo [步骤 3/3] 预下载模型 (可选)
echo ================================================================================

echo [❓] 是否现在预下载模型? 
echo [Y] 是 - 立即下载，避免首次启动等待
echo [N] 否 - 程序首次启动时自动下载
echo.

set /p download_choice="请选择 (Y/N): "

if /i "%download_choice%"=="Y" (
    echo.
    echo [📥] 开始下载 %model_size% 模型...
    echo [🔗] 下载地址: https://huggingface.co/ggerganov/whisper.cpp/resolve/main/%model_file%
    echo.
    
    if not exist "LmyDigitalHuman\Models\%model_file%" (
        echo [⏳] 正在下载，请稍候...
        
        powershell -Command "& {
            $url = 'https://huggingface.co/ggerganov/whisper.cpp/resolve/main/%model_file%'
            $output = 'LmyDigitalHuman\Models\%model_file%'
            Write-Host '[📊] 开始下载...'
            try {
                $webClient = New-Object System.Net.WebClient
                $webClient.DownloadFile($url, $output)
                Write-Host '[✅] 下载完成!'
            } catch {
                Write-Host '[❌] 下载失败:' $_.Exception.Message
            }
        }"
        
        if exist "LmyDigitalHuman\Models\%model_file%" (
            for %%I in ("LmyDigitalHuman\Models\%model_file%") do echo [✅] 模型文件: %%~zI bytes
        ) else (
            echo [❌] 下载失败，程序启动时会自动重试
        )
    ) else (
        echo [ℹ️] 模型文件已存在，无需重复下载
        for %%I in ("LmyDigitalHuman\Models\%model_file%") do echo [✅] 现有文件: %%~zI bytes
    )
) else (
    echo [ℹ️] 跳过预下载，程序启动时会自动下载
)

echo.
echo ================================================================================
echo                           配置完成
echo ================================================================================

echo [📊] 配置摘要:
echo   - 模型类型: %model_size%
echo   - 文件名: %model_file%
echo   - 特点: %model_desc%
echo   - 位置: LmyDigitalHuman\Models\%model_file%
echo.

echo [💡] 使用说明:
echo   1. 模型只需下载一次，永久保存
echo   2. 程序启动时自动检查，存在则直接使用
echo   3. Large模型识别率最高，推荐用于生产环境
echo   4. 如需更换模型，删除旧文件重新配置即可
echo.

echo [🚀] 下一步:
echo   - 继续等待Qwen和MuseTalk下载完成
echo   - 运行 deploy-production-now.bat 部署系统
echo.

echo 按任意键退出...
pause >nul