@echo off
chcp 65001 >nul
echo ================================================================================
echo              🎭 MuseTalk官方权重文件下载工具
echo ================================================================================
echo.
echo 基于MuseTalk官方仓库的下载方法
echo 参考: https://github.com/TMElyralab/MuseTalk
echo.
pause

echo ================================================================================
echo [步骤 1/4] 下载MuseTalk源码
echo ================================================================================

if not exist "models\musetalk" mkdir models\musetalk
cd models\musetalk

if exist "MuseTalk" (
    echo [⚠️] MuseTalk目录已存在
    set /p cleanup_choice="是否删除重新下载? (y/n): "
    if /i "%cleanup_choice%"=="y" (
        rmdir /s /q "MuseTalk"
    ) else (
        cd MuseTalk
        goto download_weights
    )
)

echo [📥] 克隆MuseTalk官方仓库...
git clone https://github.com/TMElyralab/MuseTalk.git
cd MuseTalk

:download_weights
echo.
echo ================================================================================
echo [步骤 2/4] 运行官方权重下载脚本
echo ================================================================================

echo [🔍] 检查官方下载脚本...
if exist "download_weights.bat" (
    echo [✅] 找到官方Windows下载脚本
    echo.
    echo [📥] 运行官方下载脚本...
    echo [⏱️] 这可能需要较长时间，请耐心等待...
    echo.
    
    call download_weights.bat
    
    if %errorlevel% equ 0 (
        echo [✅] 官方脚本执行完成
    ) else (
        echo [⚠️] 官方脚本执行可能有问题，但继续检查文件
    )
) else (
    echo [❌] 未找到官方下载脚本
    echo [💡] 可能需要手动下载权重文件
)

echo.
echo ================================================================================
echo [步骤 3/4] 验证权重文件
echo ================================================================================

echo [🔍] 检查models目录结构...
if exist "models" (
    echo [✅] models目录存在
    dir models /b
    
    echo.
    echo [🔍] 检查关键权重文件...
    
    if exist "models\musetalk\musetalk.json" (
        echo [✅] musetalk.json 存在
    ) else (
        echo [❌] musetalk.json 缺失
    )
    
    if exist "models\musetalk\pytorch_model.bin" (
        echo [✅] pytorch_model.bin 存在
        for %%I in ("models\musetalk\pytorch_model.bin") do echo [📊] 大小: %%~zI bytes
    ) else (
        echo [❌] pytorch_model.bin 缺失
    )
    
    if exist "models\musetalkV15\unet.pth" (
        echo [✅] unet.pth (v1.5) 存在
        for %%I in ("models\musetalkV15\unet.pth") do echo [📊] 大小: %%~zI bytes
    ) else (
        echo [❌] unet.pth (v1.5) 缺失
    )
    
    echo.
    echo [🔍] 检查其他必需模型...
    if exist "models\sd-vae" echo [✅] sd-vae 存在
    if exist "models\whisper" echo [✅] whisper 存在
    if exist "models\dwpose" echo [✅] dwpose 存在
    if exist "models\face-parse-bisent" echo [✅] face-parse-bisent 存在
    
) else (
    echo [❌] models目录不存在，下载可能失败
)

echo.
echo ================================================================================
echo [步骤 4/4] 手动下载指导（如果需要）
echo ================================================================================

echo [📝] 如果自动下载失败，请手动下载以下文件:
echo.
echo 🔗 下载链接 (需要从官方文档获取):
echo   1. MuseTalk主模型权重
echo   2. sd-vae-ft-mse 模型
echo   3. whisper 模型  
echo   4. dwpose 模型
echo   5. face-parse-bisent 模型
echo.
echo 📁 期望的目录结构:
echo   ./models/
echo   ├── musetalk/
echo   │   ├── musetalk.json
echo   │   └── pytorch_model.bin
echo   ├── musetalkV15/
echo   │   ├── musetalk.json  
echo   │   └── unet.pth
echo   ├── sd-vae/
echo   │   ├── config.json
echo   │   └── diffusion_pytorch_model.bin
echo   ├── whisper/
echo   │   ├── config.json
echo   │   ├── pytorch_model.bin
echo   │   └── preprocessor_config.json
echo   ├── dwpose/
echo   │   └── dw-ll_ucoco_384.pth
echo   └── face-parse-bisent/
echo       ├── 79999_iter.pth
echo       └── resnet18-5c106cde.pth
echo.

echo [💡] 官方下载说明:
echo   - 查看 MuseTalk README.md 获取最新下载链接
echo   - 有些模型可能需要从Hugging Face下载
echo   - 确保网络连接稳定，文件较大
echo.

cd ..\..\..\

echo ================================================================================
echo                              下载完成
echo ================================================================================
echo.

set total_files=0
set found_files=0

echo [📊] 最终检查结果:

if exist "models\musetalk\MuseTalk\models\musetalk\pytorch_model.bin" (
    echo [✅] MuseTalk主模型: 已下载
    set /a found_files+=1
) else (
    echo [❌] MuseTalk主模型: 未找到
)
set /a total_files+=1

if exist "models\musetalk\MuseTalk\models\sd-vae\diffusion_pytorch_model.bin" (
    echo [✅] SD-VAE模型: 已下载
    set /a found_files+=1
) else (
    echo [❌] SD-VAE模型: 未找到
)
set /a total_files+=1

if exist "models\musetalk\MuseTalk\models\whisper\pytorch_model.bin" (
    echo [✅] Whisper模型: 已下载
    set /a found_files+=1
) else (
    echo [❌] Whisper模型: 未找到
)
set /a total_files+=1

echo.
echo [📊] 下载进度: %found_files%/%total_files% 个主要模型

if %found_files% equ %total_files% (
    echo [🎉] 所有MuseTalk模型下载完成！
    echo [🚀] 下一步: 运行 deploy-production-now.bat
) else (
    echo [⚠️] 部分模型未下载完成
    echo [📝] 请检查网络连接或查看MuseTalk官方文档
    echo [🔗] https://github.com/TMElyralab/MuseTalk#download-weights
)

echo.
echo 按任意键退出...
pause >nul