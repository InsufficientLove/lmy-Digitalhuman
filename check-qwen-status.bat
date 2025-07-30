@echo off
chcp 65001 >nul
echo ================================================================================
echo              🔍 检查Qwen2.5-14B模型真实状态
echo ================================================================================
echo.
echo [📊] 您报告的大小: 27.5GB - 这接近预期的28GB！
echo [🎉] 可能下载已经成功完成
echo.
pause

if not exist "models\llm" (
    echo [❌] models\llm 目录不存在
    pause
    exit /b 1
)

echo ================================================================================
echo [步骤 1/3] 检查目录大小和文件数量
echo ================================================================================

cd models\llm

echo [📊] 当前llm目录内容:
dir /b

echo.
echo [📊] 详细大小统计:
for /d %%d in (*) do (
    if exist "%%d" (
        echo [📁] 检查目录: %%d
        cd "%%d"
        for /f "tokens=3" %%s in ('dir /s /-c ^| find "字节"') do echo [📊] 大小: %%s bytes
        for /f "tokens=1" %%f in ('dir /s /-c ^| find "个文件"') do echo [📁] 文件数: %%f 个
        cd ..
        echo.
    )
)

cd ..\..

echo ================================================================================
echo [步骤 2/3] 检查Qwen模型文件完整性
echo ================================================================================

if exist "models\llm\Qwen2.5-14B-Instruct" (
    cd models\llm\Qwen2.5-14B-Instruct
    
    echo [🔍] 检查关键模型文件:
    
    REM 检查pytorch_model分片文件
    set shard_count=0
    for %%f in (pytorch_model-*.bin) do (
        if exist "%%f" (
            set /a shard_count+=1
            echo [✅] %%f
        )
    )
    echo [📊] 找到 %shard_count% 个pytorch_model分片文件
    
    REM 检查safetensors文件
    if exist "model.safetensors.index.json" (
        echo [✅] model.safetensors.index.json
    ) else (
        echo [❌] model.safetensors.index.json 缺失
    )
    
    REM 检查配置文件
    if exist "config.json" (
        echo [✅] config.json
    ) else (
        echo [❌] config.json 缺失
    )
    
    if exist "tokenizer.json" (
        echo [✅] tokenizer.json
    ) else (
        echo [❌] tokenizer.json 缺失
    )
    
    if exist "tokenizer_config.json" (
        echo [✅] tokenizer_config.json
    ) else (
        echo [❌] tokenizer_config.json 缺失
    )
    
    echo.
    echo [📊] 文件完整性评估:
    if %shard_count% geq 10 (
        echo [🎉] pytorch_model分片文件数量正常 (%shard_count%个)
        if exist "config.json" (
            if exist "tokenizer.json" (
                echo [✅] 模型文件完整，可以使用！
                set model_complete=1
            ) else (
                echo [⚠️] 分词器文件缺失
                set model_complete=0
            )
        ) else (
            echo [⚠️] 配置文件缺失
            set model_complete=0
        )
    ) else (
        echo [❌] pytorch_model分片文件不足 (需要15个)
        set model_complete=0
    )
    
    cd ..\..\..
) else (
    echo [❌] Qwen2.5-14B-Instruct目录不存在
    set model_complete=0
)

echo.
echo ================================================================================
echo [步骤 3/3] 给出使用建议
echo ================================================================================

if "%model_complete%"=="1" (
    echo [🎉] 恭喜！Qwen2.5-14B模型下载完成！
    echo.
    echo [💡] 使用方式建议:
    echo   选项A: 直接使用HuggingFace模型
    echo   - 适合: 需要完整模型功能
    echo   - 缺点: 占用28GB空间，推理较慢
    echo.
    echo   选项B: 转换为Ollama使用 (推荐)
    echo   - 适合: 生产环境，高性能需求
    echo   - 优点: 优化推理，节省空间，更快启动
    echo   - 命令: ollama create qwen2.5-14b -f Modelfile
    echo.
    
    set /p choice="建议使用哪种方式? (A-直接使用/B-转换Ollama): "
    
    if /i "%choice%"=="B" (
        echo [🚀] 推荐选择！Ollama性能更优
        echo [💡] 可以运行: setup-ollama-qwen.bat
    ) else (
        echo [ℹ️] 直接使用HuggingFace模型
        echo [💡] 模型路径: models\llm\Qwen2.5-14B-Instruct
    )
    
) else (
    echo [⚠️] 模型文件不完整，建议:
    echo.
    echo [选项1] 继续等待Git LFS下载
    echo [选项2] 重新下载: redownload-qwen-fresh.bat  
    echo [选项3] 使用Ollama: setup-ollama-qwen.bat (推荐)
    echo.
    echo [💡] 如果27.5GB已经稳定不变，说明Git LFS可能有问题
    echo [🦙] 建议直接使用Ollama，避免Git LFS问题
)

echo.
echo ================================================================================
echo                           检查完成
echo ================================================================================

echo [📊] 总结:
echo   - 目录大小: 27.5GB (接近预期28GB)
if "%model_complete%"=="1" (
    echo   - 文件状态: ✅ 完整
    echo   - 可用性: ✅ 可以使用
) else (
    echo   - 文件状态: ⚠️ 需要验证
    echo   - 建议: 使用Ollama替代
)

echo.
echo 按任意键退出...
pause >nul