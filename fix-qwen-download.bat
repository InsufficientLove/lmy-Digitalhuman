@echo off
chcp 65001 >nul
echo ================================================================================
echo              🔧 修复Qwen2.5-14B-Instruct模型下载
echo ================================================================================
echo.
echo [❌] 检测到Git LFS下载不完整
echo [🎯] 当前问题: 只有23MB，应该有28GB+
echo.
pause

cd models\llm\Qwen2.5-14B-Instruct

echo ================================================================================
echo [步骤 1/5] 检查当前状态
echo ================================================================================

echo [📊] 当前目录大小:
dir /s | find "个文件"

echo.
echo [🔍] 检查Git LFS状态:
git lfs ls-files

echo.
echo [🔍] 检查Git LFS跟踪:
git lfs track

echo.
echo ================================================================================
echo [步骤 2/5] 重新配置Git LFS
echo ================================================================================

echo [🔧] 重新初始化Git LFS...
git lfs install --force
git lfs install --local

echo [🔧] 增加Git缓冲区大小...
git config http.postBuffer 2147483648
git config http.maxRequestBuffer 100M
git config core.compression 0

echo [🔧] 设置LFS并发下载...
git config lfs.concurrenttransfers 3
git config lfs.activitytimeout 300

echo.
echo ================================================================================
echo [步骤 3/5] 强制拉取LFS文件
echo ================================================================================

echo [📥] 强制拉取所有LFS文件...
git lfs pull --all

if %errorlevel% neq 0 (
    echo [⚠️] LFS pull失败，尝试fetch...
    git lfs fetch --all
    git lfs checkout
)

echo.
echo ================================================================================
echo [步骤 4/5] 验证下载结果
echo ================================================================================

echo [📊] 重新检查目录大小:
dir /s | find "个文件"

echo.
echo [🔍] 检查关键模型文件:
if exist "pytorch_model-00001-of-00015.bin" (
    for %%I in ("pytorch_model-00001-of-00015.bin") do echo [✅] 第1个分片: %%~zI bytes
) else (
    echo [❌] 第1个分片缺失
)

if exist "pytorch_model-00015-of-00015.bin" (
    for %%I in ("pytorch_model-00015-of-00015.bin") do echo [✅] 最后分片: %%~zI bytes
) else (
    echo [❌] 最后分片缺失
)

if exist "model.safetensors.index.json" (
    echo [✅] 索引文件存在
) else (
    echo [❌] 索引文件缺失
)

echo.
echo ================================================================================
echo [步骤 5/5] 备用下载方案
echo ================================================================================

echo [💡] 如果上述方法仍然失败，请尝试以下备用方案:
echo.
echo [方案A] 使用HuggingFace镜像重新下载:
echo   cd ..
echo   rmdir /s /q Qwen2.5-14B-Instruct
echo   git clone https://hf-mirror.com/Qwen/Qwen2.5-14B-Instruct
echo.
echo [方案B] 使用ModelScope下载:
echo   pip install modelscope
echo   python -c "from modelscope import snapshot_download; snapshot_download('qwen/Qwen2.5-14B-Instruct', cache_dir='.')"
echo.
echo [方案C] 分步下载:
echo   git clone --filter=blob:none https://hf-mirror.com/Qwen/Qwen2.5-14B-Instruct
echo   cd Qwen2.5-14B-Instruct
echo   git lfs pull
echo.

cd ..\..\..

echo ================================================================================
echo                           修复完成
echo ================================================================================

echo [📊] 最终检查:
if exist "models\llm\Qwen2.5-14B-Instruct\pytorch_model-00001-of-00015.bin" (
    echo [✅] Qwen模型修复成功
    for %%I in ("models\llm\Qwen2.5-14B-Instruct\pytorch_model-00001-of-00015.bin") do (
        if %%~zI gtr 1000000000 (
            echo [🎉] 文件大小正常: %%~zI bytes
        ) else (
            echo [⚠️] 文件大小异常: %%~zI bytes
        )
    )
) else (
    echo [❌] Qwen模型仍然缺失
    echo [💡] 请考虑使用备用下载方案
)

echo.
echo 按任意键退出...
pause >nul