@echo off
chcp 65001 >nul
echo ================================================================================
echo              🎭 检查MuseTalk模型下载状态
echo ================================================================================
echo.
pause

if not exist "models\musetalk\MuseTalk\models" (
    echo [❌] MuseTalk模型目录不存在
    echo [💡] 请确保MuseTalk下载已完成
    pause
    exit /b 1
)

cd models\musetalk\MuseTalk\models

echo ================================================================================
echo [检查] MuseTalk核心模型
echo ================================================================================

echo [📊] 当前models目录内容:
dir /b

echo.
echo [🔍] 检查各个模型目录:

REM 检查musetalk目录
if exist "musetalk" (
    echo [✅] musetalk目录存在
    cd musetalk
    echo [📋] musetalk目录内容:
    dir /b
    if exist "musetalk.json" echo [✅] musetalk.json
    if exist "pytorch_model.bin" (
        echo [✅] pytorch_model.bin
        for %%I in ("pytorch_model.bin") do echo [📊] 大小: %%~zI bytes
    ) else (
        echo [❌] pytorch_model.bin 缺失
    )
    cd ..
) else (
    echo [❌] musetalk目录缺失
)

echo.

REM 检查musetalkV15目录
if exist "musetalkV15" (
    echo [✅] musetalkV15目录存在
    cd musetalkV15
    echo [📋] musetalkV15目录内容:
    dir /b
    if exist "musetalk.json" echo [✅] musetalk.json
    if exist "unet.pth" (
        echo [✅] unet.pth
        for %%I in ("unet.pth") do echo [📊] 大小: %%~zI bytes
    ) else (
        echo [❌] unet.pth 缺失
    )
    cd ..
) else (
    echo [❌] musetalkV15目录缺失
)

echo.

REM 检查其他必需模型
echo [🔍] 检查其他必需模型:

if exist "sd-vae" (
    echo [✅] sd-vae目录存在
    cd sd-vae
    if exist "diffusion_pytorch_model.bin" (
        echo [✅] diffusion_pytorch_model.bin
        for %%I in ("diffusion_pytorch_model.bin") do echo [📊] 大小: %%~zI bytes
    )
    cd ..
) else (
    echo [❌] sd-vae目录缺失
)

if exist "whisper" (
    echo [✅] whisper目录存在
    cd whisper
    if exist "pytorch_model.bin" (
        echo [✅] whisper pytorch_model.bin
        for %%I in ("pytorch_model.bin") do echo [📊] 大小: %%~zI bytes
    )
    cd ..
) else (
    echo [❌] whisper目录缺失
)

if exist "dwpose" (
    echo [✅] dwpose目录存在
    cd dwpose
    if exist "dw-ll_ucoco_384.pth" (
        echo [✅] dw-ll_ucoco_384.pth
        for %%I in ("dw-ll_ucoco_384.pth") do echo [📊] 大小: %%~zI bytes
    )
    cd ..
) else (
    echo [❌] dwpose目录缺失
)

if exist "face-parse-bisent" (
    echo [✅] face-parse-bisent目录存在
    cd face-parse-bisent
    if exist "79999_iter.pth" (
        echo [✅] 79999_iter.pth
        for %%I in ("79999_iter.pth") do echo [📊] 大小: %%~zI bytes
    )
    if exist "resnet18-5c106cde.pth" (
        echo [✅] resnet18-5c106cde.pth
        for %%I in ("resnet18-5c106cde.pth") do echo [📊] 大小: %%~zI bytes
    )
    cd ..
) else (
    echo [❌] face-parse-bisent目录缺失
)

echo.
echo ================================================================================
echo [总结] 模型完整性检查
echo ================================================================================

set complete_count=0
set total_count=6

if exist "musetalk\pytorch_model.bin" set /a complete_count+=1
if exist "musetalkV15\unet.pth" set /a complete_count+=1
if exist "sd-vae\diffusion_pytorch_model.bin" set /a complete_count+=1
if exist "whisper\pytorch_model.bin" set /a complete_count+=1
if exist "dwpose\dw-ll_ucoco_384.pth" set /a complete_count+=1
if exist "face-parse-bisent\79999_iter.pth" set /a complete_count+=1

echo [📊] 模型完整性: %complete_count%/%total_count%

if %complete_count% equ %total_count% (
    echo [🎉] 所有MuseTalk模型下载完成！
    echo [✅] 可以开始使用数字人功能
) else (
    echo [⚠️] 部分模型缺失，功能可能受限
    echo [💡] 如需补充下载，请运行官方下载脚本
)

cd ..\..\..\..

echo.
echo ================================================================================
echo                           检查完成
echo ================================================================================

echo [🚀] 下一步建议:
if %complete_count% equ %total_count% (
    echo   1. 所有模型已就绪
    echo   2. 可以运行 deploy-production-now.bat 部署系统
    echo   3. 或先测试各个组件功能
) else (
    echo   1. 等待剩余模型下载完成
    echo   2. 或手动补充缺失的模型文件
    echo   3. 重新运行此检查脚本验证
)

echo.
echo 按任意键退出...
pause >nul