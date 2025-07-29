@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul

echo.
echo ================================================================================
echo                📥 数字人模型分步下载工具
echo ================================================================================
echo.
echo 此工具将逐步指导您下载所有AI模型文件
echo 解决Git LFS和大文件下载问题
echo.

:main_menu
echo.
echo 📋 请选择操作:
echo   1. 检查和修复Git LFS
echo   2. 下载Qwen2.5-14B-Instruct大语言模型 (~28GB)
echo   3. 下载MuseTalk数字人模型 (~15GB)
echo   4. 下载Whisper语音识别模型 (~3GB)
echo   5. 检查所有模型下载状态
echo   6. 清理和重新开始
echo   0. 退出
echo.
set /p choice="请输入选项 (0-6): "

if "%choice%"=="1" goto fix_git_lfs
if "%choice%"=="2" goto download_qwen
if "%choice%"=="3" goto download_musetalk
if "%choice%"=="4" goto download_whisper
if "%choice%"=="5" goto check_models
if "%choice%"=="6" goto cleanup
if "%choice%"=="0" goto end
goto main_menu

:fix_git_lfs
echo.
echo ================================================================================
echo [步骤 1] 检查和修复Git LFS
echo ================================================================================
echo.

echo [1.1] 检查Git版本...
git --version
if %errorlevel% neq 0 (
    echo [❌] Git未安装，请先安装Git
    echo [💾] 下载地址: https://git-scm.com/
    pause
    goto main_menu
)

echo.
echo [1.2] 检查Git LFS状态...
git lfs version
if %errorlevel% neq 0 (
    echo [❌] Git LFS未正确安装
    echo.
    echo [🔧] 正在尝试安装Git LFS...
    git lfs install
    if %errorlevel% neq 0 (
        echo [❌] Git LFS安装失败
        echo [💾] 请手动下载安装: https://git-lfs.github.io/
        pause
        goto main_menu
    )
) else (
    echo [✅] Git LFS已安装
)

echo.
echo [1.3] 配置Git LFS...
git lfs install --system
git lfs install --global
git lfs install

echo.
echo [1.4] 设置Git配置...
git config --global http.postBuffer 524288000
git config --global http.maxRequestBuffer 100M
git config --global core.compression 0

echo.
echo [✅] Git LFS配置完成！
echo.
pause
goto main_menu

:download_qwen
echo.
echo ================================================================================
echo [步骤 2] 下载Qwen2.5-14B-Instruct大语言模型
echo ================================================================================
echo.

if not exist "models" mkdir models
if not exist "models\llm" mkdir models\llm

echo [2.1] 检查现有模型...
if exist "models\llm\Qwen2.5-14B-Instruct" (
    echo [⚠️] 发现现有模型目录，可能下载不完整
    echo.
    set /p cleanup_choice="是否删除重新下载? (y/n): "
    if /i "!cleanup_choice!"=="y" (
        echo [🗑️] 删除现有目录...
        rmdir /s /q "models\llm\Qwen2.5-14B-Instruct"
    ) else (
        goto main_menu
    )
)

echo.
echo [2.2] 开始下载Qwen2.5-14B-Instruct...
echo [📊] 大小: ~28GB
echo [⏱️] 预计时间: 15-30分钟
echo.

cd models\llm

echo [🌐] 选择下载源:
echo   1. 官方源 (国外用户推荐)
echo   2. 镜像源 (国内用户推荐)
echo.
set /p source_choice="请选择 (1/2): "

if "%source_choice%"=="2" (
    echo [📥] 使用镜像源下载...
    git clone https://hf-mirror.com/Qwen/Qwen2.5-14B-Instruct
) else (
    echo [📥] 使用官方源下载...
    git clone https://huggingface.co/Qwen/Qwen2.5-14B-Instruct
)

cd ..\..

if exist "models\llm\Qwen2.5-14B-Instruct\config.json" (
    echo [✅] Qwen模型下载成功！
) else (
    echo [❌] Qwen模型下载失败
    echo [💡] 请检查网络连接或尝试镜像源
)

echo.
pause
goto main_menu

:download_musetalk
echo.
echo ================================================================================
echo [步骤 3] 下载MuseTalk数字人模型 (最复杂)
echo ================================================================================
echo.

if not exist "models" mkdir models
if not exist "models\musetalk" mkdir models\musetalk

echo [3.1] 下载MuseTalk主代码...
cd models\musetalk

if exist "MuseTalk" (
    echo [⚠️] MuseTalk目录已存在
    set /p cleanup_choice="是否删除重新下载? (y/n): "
    if /i "!cleanup_choice!"=="y" (
        rmdir /s /q "MuseTalk"
    ) else (
        cd ..\..
        goto download_weights
    )
)

echo [📥] 下载MuseTalk源码...
git clone https://github.com/TMElyralab/MuseTalk.git

cd ..\..

:download_weights
echo.
echo [3.2] 下载MuseTalk预训练权重 (关键步骤!)...
echo.
echo [📝] MuseTalk需要以下权重文件:
echo   1. musetalk.json (配置文件)
echo   2. pytorch_model.bin (主模型, ~8GB)
echo   3. face_parsing.pth (人脸解析, ~50MB)
echo   4. DNet.pth (深度网络, ~200MB)
echo.

if not exist "models\musetalk\MuseTalk\models" mkdir "models\musetalk\MuseTalk\models"

echo [🔍] 检查现有权重文件...
set missing_files=0

if not exist "models\musetalk\MuseTalk\models\musetalk.json" (
    echo [❌] musetalk.json 缺失
    set /a missing_files+=1
)

if not exist "models\musetalk\MuseTalk\models\pytorch_model.bin" (
    echo [❌] pytorch_model.bin 缺失
    set /a missing_files+=1
)

if not exist "models\musetalk\MuseTalk\models\face_parsing.pth" (
    echo [❌] face_parsing.pth 缺失
    set /a missing_files+=1
)

if not exist "models\musetalk\MuseTalk\models\DNet.pth" (
    echo [❌] DNet.pth 缺失
    set /a missing_files+=1
)

if %missing_files% equ 0 (
    echo [✅] 所有MuseTalk权重文件已存在！
    pause
    goto main_menu
)

echo.
echo [📥] 需要下载 %missing_files% 个权重文件
echo.
echo [🔧] 下载方式选择:
echo   1. 自动下载 (推荐)
echo   2. 手动下载指导
echo.
set /p download_method="请选择 (1/2): "

if "%download_method%"=="2" goto manual_weights

echo.
echo [🤖] 自动下载MuseTalk权重...
echo.

REM 创建临时Python脚本来下载
echo import requests > download_musetalk.py
echo import os >> download_musetalk.py
echo from tqdm import tqdm >> download_musetalk.py
echo. >> download_musetalk.py
echo def download_file(url, filename): >> download_musetalk.py
echo     try: >> download_musetalk.py
echo         response = requests.get(url, stream=True) >> download_musetalk.py
echo         total_size = int(response.headers.get('content-length', 0)) >> download_musetalk.py
echo         with open(filename, 'wb') as file, tqdm( >> download_musetalk.py
echo             desc=os.path.basename(filename), >> download_musetalk.py
echo             total=total_size, >> download_musetalk.py
echo             unit='B', >> download_musetalk.py
echo             unit_scale=True, >> download_musetalk.py
echo             unit_divisor=1024, >> download_musetalk.py
echo         ) as bar: >> download_musetalk.py
echo             for chunk in response.iter_content(chunk_size=8192): >> download_musetalk.py
echo                 if chunk: >> download_musetalk.py
echo                     file.write(chunk) >> download_musetalk.py
echo                     bar.update(len(chunk)) >> download_musetalk.py
echo         print(f"✅ {filename} 下载完成") >> download_musetalk.py
echo     except Exception as e: >> download_musetalk.py
echo         print(f"❌ {filename} 下载失败: {e}") >> download_musetalk.py
echo. >> download_musetalk.py
echo # MuseTalk权重文件下载链接 >> download_musetalk.py
echo base_path = "models/musetalk/MuseTalk/models/" >> download_musetalk.py
echo os.makedirs(base_path, exist_ok=True) >> download_musetalk.py
echo. >> download_musetalk.py
echo # 这些是示例链接，实际链接需要从官方获取 >> download_musetalk.py
echo print("⚠️  需要手动获取MuseTalk权重文件下载链接") >> download_musetalk.py
echo print("📝 请访问: https://github.com/TMElyralab/MuseTalk/releases") >> download_musetalk.py

python download_musetalk.py
del download_musetalk.py

goto manual_weights

:manual_weights
echo.
echo ================================================================================
echo [手动下载MuseTalk权重文件指导]
echo ================================================================================
echo.
echo [📝] 请按以下步骤手动下载:
echo.
echo 1. 打开浏览器访问: https://github.com/TMElyralab/MuseTalk/releases
echo.
echo 2. 找到最新版本，下载以下文件:
echo    - musetalk.json
echo    - pytorch_model.bin (大文件，~8GB)
echo    - face_parsing.pth  
echo    - DNet.pth
echo.
echo 3. 将下载的文件放到以下目录:
echo    %CD%\models\musetalk\MuseTalk\models\
echo.
echo [💡] 如果GitHub下载慢，可以尝试:
echo    - 使用代理
echo    - 使用GitHub镜像站
echo    - 使用下载工具 (如IDM)
echo.
echo [⚠️] 注意: pytorch_model.bin 文件很大(~8GB)，请确保网络稳定
echo.

echo 下载完成后按任意键继续...
pause >nul

echo.
echo [🔍] 验证权重文件...
if exist "models\musetalk\MuseTalk\models\musetalk.json" (
    echo [✅] musetalk.json 存在
) else (
    echo [❌] musetalk.json 缺失
)

if exist "models\musetalk\MuseTalk\models\pytorch_model.bin" (
    echo [✅] pytorch_model.bin 存在
) else (
    echo [❌] pytorch_model.bin 缺失
)

if exist "models\musetalk\MuseTalk\models\face_parsing.pth" (
    echo [✅] face_parsing.pth 存在
) else (
    echo [❌] face_parsing.pth 缺失
)

if exist "models\musetalk\MuseTalk\models\DNet.pth" (
    echo [✅] DNet.pth 存在
) else (
    echo [❌] DNet.pth 缺失
)

echo.
pause
goto main_menu

:download_whisper
echo.
echo ================================================================================
echo [步骤 4] 下载Whisper语音识别模型
echo ================================================================================
echo.

if not exist "models" mkdir models
if not exist "models\whisper" mkdir models\whisper

cd models\whisper

if exist "whisper-large-v3" (
    echo [⚠️] Whisper模型目录已存在
    set /p cleanup_choice="是否删除重新下载? (y/n): "
    if /i "!cleanup_choice!"=="y" (
        rmdir /s /q "whisper-large-v3"
    ) else (
        cd ..\..
        goto main_menu
    )
)

echo [📥] 下载Whisper Large V3模型...
echo [📊] 大小: ~3GB
echo.

echo [🌐] 选择下载源:
echo   1. 官方源 (国外用户推荐)
echo   2. 镜像源 (国内用户推荐)
echo.
set /p source_choice="请选择 (1/2): "

if "%source_choice%"=="2" (
    echo [📥] 使用镜像源下载...
    git clone https://hf-mirror.com/openai/whisper-large-v3
) else (
    echo [📥] 使用官方源下载...
    git clone https://huggingface.co/openai/whisper-large-v3
)

cd ..\..

if exist "models\whisper\whisper-large-v3\config.json" (
    echo [✅] Whisper模型下载成功！
) else (
    echo [❌] Whisper模型下载失败
)

echo.
pause
goto main_menu

:check_models
echo.
echo ================================================================================
echo [检查] 所有模型下载状态
echo ================================================================================
echo.

set total_models=0
set downloaded_models=0

echo [🔍] 检查Qwen2.5-14B-Instruct...
set /a total_models+=1
if exist "models\llm\Qwen2.5-14B-Instruct\config.json" (
    echo [✅] Qwen2.5-14B-Instruct: 已下载
    set /a downloaded_models+=1
) else (
    echo [❌] Qwen2.5-14B-Instruct: 未下载
)

echo [🔍] 检查MuseTalk模型...
set /a total_models+=1
if exist "models\musetalk\MuseTalk\app.py" (
    echo [✅] MuseTalk源码: 已下载
    set /a downloaded_models+=1
) else (
    echo [❌] MuseTalk源码: 未下载
)

echo [🔍] 检查MuseTalk权重文件...
set musetalk_weights=0
if exist "models\musetalk\MuseTalk\models\musetalk.json" set /a musetalk_weights+=1
if exist "models\musetalk\MuseTalk\models\pytorch_model.bin" set /a musetalk_weights+=1
if exist "models\musetalk\MuseTalk\models\face_parsing.pth" set /a musetalk_weights+=1
if exist "models\musetalk\MuseTalk\models\DNet.pth" set /a musetalk_weights+=1

echo [📊] MuseTalk权重文件: %musetalk_weights%/4 个

echo [🔍] 检查Whisper模型...
set /a total_models+=1
if exist "models\whisper\whisper-large-v3\config.json" (
    echo [✅] Whisper Large V3: 已下载
    set /a downloaded_models+=1
) else (
    echo [❌] Whisper Large V3: 未下载
)

echo.
echo [📊] 下载进度: %downloaded_models%/%total_models% 个主要模型
echo.

if %downloaded_models% equ %total_models% (
    if %musetalk_weights% equ 4 (
        echo [🎉] 所有模型下载完成！可以运行部署脚本了
        echo [🚀] 下一步: deploy-production-now.bat
    ) else (
        echo [⚠️] MuseTalk权重文件不完整，请完成下载
    )
) else (
    echo [⚠️] 还有模型未下载完成
)

echo.
pause
goto main_menu

:cleanup
echo.
echo ================================================================================
echo [清理] 删除所有模型文件
echo ================================================================================
echo.
echo [⚠️] 这将删除所有已下载的模型文件！
echo.
set /p confirm="确认删除? (输入 'DELETE' 确认): "

if "%confirm%"=="DELETE" (
    echo [🗑️] 删除模型文件...
    if exist "models" rmdir /s /q "models"
    echo [✅] 清理完成
) else (
    echo [取消] 未执行清理操作
)

echo.
pause
goto main_menu

:end
echo.
echo 感谢使用模型下载工具！
echo.
pause
exit /b 0