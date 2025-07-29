@echo off
chcp 65001 >nul
echo ================================================================================
echo              🗑️ 清理损坏的Qwen模型文件
echo ================================================================================
echo.
echo [⚠️] 检测到Qwen模型下载不完整:
echo   - 当前大小: 23MB (应该28GB+)
echo   - Git LFS问题导致只下载了元数据
echo   - 占用磁盘空间但无法使用
echo.
echo [💡] 建议改用Ollama管理模型:
echo   ✅ 自动下载和管理
echo   ✅ 优化推理性能  
echo   ✅ 无Git LFS问题
echo   ✅ 量化模型节省空间
echo.
pause

echo ================================================================================
echo [步骤 1/2] 清理损坏的文件
echo ================================================================================

if exist "models\llm\Qwen2.5-14B-Instruct" (
    echo [🔍] 检查当前Qwen目录:
    cd models\llm\Qwen2.5-14B-Instruct
    
    echo [📊] 当前文件统计:
    for /f "tokens=1,3" %%a in ('dir /s /-c ^| find "个文件"') do (
        echo   - 文件数量: %%a 个
        echo   - 总大小: %%b 字节
    )
    
    cd ..\..\..
    
    echo.
    echo [❓] 是否删除损坏的Qwen目录?
    echo [Y] 是 - 删除并释放空间
    echo [N] 否 - 保留现有文件
    echo.
    
    set /p delete_choice="请选择 (Y/N): "
    
    if /i "%delete_choice%"=="Y" (
        echo [🗑️] 正在删除损坏的Qwen目录...
        rmdir /s /q "models\llm\Qwen2.5-14B-Instruct"
        
        if not exist "models\llm\Qwen2.5-14B-Instruct" (
            echo [✅] 清理完成
        ) else (
            echo [❌] 清理失败，可能有文件被占用
        )
    ) else (
        echo [ℹ️] 保留现有文件
    )
) else (
    echo [ℹ️] 没有找到Qwen目录，无需清理
)

echo.
echo ================================================================================
echo [步骤 2/2] 推荐使用Ollama
echo ================================================================================

echo [🦙] Ollama vs 直接下载对比:
echo.
echo [直接下载HuggingFace模型]:
echo   ❌ 需要28GB存储空间
echo   ❌ Git LFS下载问题频繁
echo   ❌ 需要手动管理模型文件
echo   ❌ 推理性能未优化
echo   ❌ 显存占用大
echo.
echo [使用Ollama]:
echo   ✅ 自动下载和管理 (~8GB量化版本)
echo   ✅ 优化的推理引擎
echo   ✅ 支持流式响应
echo   ✅ 无Git LFS问题
echo   ✅ 启动速度快
echo   ✅ 显存占用少
echo.

echo [🚀] 推荐操作:
echo   1. 运行 setup-ollama-qwen.bat
echo   2. 选择 qwen2.5:14b-instruct-q4_0 (量化版本)
echo   3. 享受稳定高效的AI服务
echo.

set /p ollama_choice="是否现在设置Ollama? (Y/N): "

if /i "%ollama_choice%"=="Y" (
    echo [🚀] 启动Ollama设置...
    call setup-ollama-qwen.bat
) else (
    echo [ℹ️] 您可以稍后运行 setup-ollama-qwen.bat
)

echo.
echo ================================================================================
echo                           清理完成
echo ================================================================================

echo [📊] 清理结果:
if not exist "models\llm\Qwen2.5-14B-Instruct" (
    echo   ✅ 损坏的Qwen文件已清理
    echo   ✅ 释放了磁盘空间
) else (
    echo   ℹ️ Qwen文件保留
)

echo.
echo [💡] 下一步建议:
echo   1. 使用 setup-ollama-qwen.bat 安装Ollama版本
echo   2. 继续下载MuseTalk模型
echo   3. 运行 deploy-production-now.bat 部署系统
echo.

echo 按任意键退出...
pause >nul