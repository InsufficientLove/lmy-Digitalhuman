@echo off
chcp 65001 >nul
echo ================================================================================
echo              🔄 重新下载Qwen2.5-14B-Instruct模型
echo ================================================================================
echo.
echo [🎯] 策略: 删除旧文件，全新下载
echo [📊] 预期大小: 28GB+
echo [⏱️] 预计时间: 30-60分钟
echo.
pause

cd models\llm

echo ================================================================================
echo [步骤 1/4] 清理旧文件
echo ================================================================================

if exist "Qwen2.5-14B-Instruct" (
    echo [🗑️] 删除损坏的Qwen目录...
    rmdir /s /q "Qwen2.5-14B-Instruct"
    echo [✅] 旧文件已清理
) else (
    echo [ℹ️] 没有找到旧文件
)

echo.
echo ================================================================================
echo [步骤 2/4] 重新配置Git环境
echo ================================================================================

echo [🔧] 配置Git LFS和缓冲区...
git lfs install --system
git lfs install --global
git lfs install

git config --global http.postBuffer 2147483648
git config --global http.maxRequestBuffer 100M
git config --global core.compression 0
git config --global lfs.concurrenttransfers 3
git config --global lfs.activitytimeout 600

echo [✅] Git环境配置完成

echo.
echo ================================================================================
echo [步骤 3/4] 开始全新下载
echo ================================================================================

echo [📥] 使用HuggingFace镜像下载...
echo [🔗] 源地址: https://hf-mirror.com/Qwen/Qwen2.5-14B-Instruct
echo.
echo [⏱️] 开始下载，请耐心等待...

git clone https://hf-mirror.com/Qwen/Qwen2.5-14B-Instruct

if %errorlevel% neq 0 (
    echo [❌] 镜像下载失败，尝试官方源...
    git clone https://huggingface.co/Qwen/Qwen2.5-14B-Instruct
)

echo.
echo ================================================================================
echo [步骤 4/4] 验证下载结果
echo ================================================================================

if exist "Qwen2.5-14B-Instruct" (
    cd Qwen2.5-14B-Instruct
    
    echo [📊] 检查目录大小:
    for /f "tokens=3" %%a in ('dir /s /-c ^| find "个文件"') do set file_count=%%a
    echo [📁] 文件数量: %file_count%
    
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
    
    if exist "config.json" (
        echo [✅] 配置文件存在
    ) else (
        echo [❌] 配置文件缺失
    )
    
    if exist "tokenizer.json" (
        echo [✅] 分词器存在
    ) else (
        echo [❌] 分词器缺失
    )
    
    echo.
    echo [📊] 检查总体大小:
    for /f "tokens=3" %%a in ('dir /s /-c ^| find "字节"') do set total_size=%%a
    echo [💾] 总大小: %total_size% bytes
    
    cd ..
) else (
    echo [❌] 下载目录不存在，下载失败
)

cd ..\..

echo.
echo ================================================================================
echo                           下载结果
echo ================================================================================

if exist "models\llm\Qwen2.5-14B-Instruct\pytorch_model-00001-of-00015.bin" (
    echo [🎉] Qwen2.5-14B-Instruct下载成功！
    echo [✅] 模型文件完整
    echo [🚀] 可以继续下载其他模型
    echo.
    echo [💡] 下一步建议:
    echo   1. 运行 download-musetalk-official.bat
    echo   2. 运行 deploy-production-now.bat
) else (
    echo [❌] 下载仍然失败
    echo.
    echo [🔧] 手动下载步骤:
    echo   1. 打开浏览器访问: https://hf-mirror.com/Qwen/Qwen2.5-14B-Instruct
    echo   2. 点击 "Clone repository"
    echo   3. 使用 git clone 命令下载
    echo   4. 或使用 ModelScope 下载工具
    echo.
    echo [📝] ModelScope下载命令:
    echo   pip install modelscope
    echo   python -c "from modelscope import snapshot_download; snapshot_download('qwen/Qwen2.5-14B-Instruct', cache_dir='./models/llm')"
)

echo.
echo 按任意键退出...
pause >nul