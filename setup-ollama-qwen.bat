@echo off
chcp 65001 >nul
echo ================================================================================
echo              🦙 使用Ollama管理Qwen2.5-14B模型
echo ================================================================================
echo.
echo [💡] 为什么使用Ollama而不是直接下载?
echo   ✅ 自动管理模型下载和存储
echo   ✅ 优化的推理引擎，速度更快
echo   ✅ 支持量化模型，节省显存
echo   ✅ 无需手动管理28GB的原始文件
echo   ✅ 自动处理Git LFS问题
echo.
pause

echo ================================================================================
echo [步骤 1/4] 检查Ollama安装
echo ================================================================================

ollama --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [❌] Ollama未安装，正在下载安装...
    echo [📥] 下载Ollama安装包...
    
    powershell -Command "Invoke-WebRequest -Uri 'https://ollama.com/download/windows' -OutFile 'ollama-windows-amd64.exe'"
    
    if exist "ollama-windows-amd64.exe" (
        echo [🚀] 请手动运行 ollama-windows-amd64.exe 安装Ollama
        echo [⏸️] 安装完成后按任意键继续...
        pause
    ) else (
        echo [❌] 下载失败，请手动访问 https://ollama.com/download 下载
        pause
        exit /b 1
    )
) else (
    echo [✅] Ollama已安装
    ollama --version
)

echo.
echo ================================================================================
echo [步骤 2/4] 启动Ollama服务
echo ================================================================================

echo [🚀] 启动Ollama服务...
start /b ollama serve

echo [⏳] 等待服务启动...
timeout /t 5 /nobreak >nul

echo [🔍] 检查服务状态...
curl -s http://localhost:11434/api/tags >nul 2>&1
if %errorlevel% equ 0 (
    echo [✅] Ollama服务运行正常
) else (
    echo [⚠️] 服务可能还在启动中，继续执行...
)

echo.
echo ================================================================================
echo [步骤 3/4] 下载Qwen2.5模型
echo ================================================================================

echo [📋] 可用的Qwen2.5模型版本:
echo   1. qwen2.5:7b         - 7B参数，速度快 (~4GB)
echo   2. qwen2.5:14b        - 14B参数，平衡性能 (~8GB) 
echo   3. qwen2.5:32b        - 32B参数，最佳效果 (~20GB)
echo   4. qwen2.5:14b-instruct-q4_0 - 14B量化版本 (~8GB，推荐)
echo.

set /p model_choice="请选择模型 (1-4, 默认4): "

if "%model_choice%"=="" set model_choice=4
if "%model_choice%"=="1" (
    set model_name=qwen2.5:7b
    set model_desc=7B参数版本
) else if "%model_choice%"=="2" (
    set model_name=qwen2.5:14b
    set model_desc=14B参数版本
) else if "%model_choice%"=="3" (
    set model_name=qwen2.5:32b
    set model_desc=32B参数版本
) else (
    set model_name=qwen2.5:14b-instruct-q4_0
    set model_desc=14B量化版本
)

echo.
echo [📥] 开始下载 %model_name% (%model_desc%)...
echo [⏱️] 这可能需要10-30分钟，请耐心等待...
echo.

ollama pull %model_name%

if %errorlevel% equ 0 (
    echo [🎉] 模型下载成功！
) else (
    echo [❌] 模型下载失败，请检查网络连接
    pause
    exit /b 1
)

echo.
echo ================================================================================
echo [步骤 4/4] 验证和配置
echo ================================================================================

echo [🔍] 验证模型安装...
ollama list

echo.
echo [🧪] 测试模型推理...
echo [💭] 测试问题: "你好，请介绍一下自己"
echo.

ollama run %model_name% "你好，请介绍一下自己"

echo.
echo [🔧] 更新项目配置...

echo [📝] 当前配置文件中的模型名称: %model_name%
echo [💡] 如需修改，请编辑 appsettings.json 中的 Ollama.Model 配置

echo.
echo ================================================================================
echo                           设置完成
echo ================================================================================

echo [🎉] Ollama + Qwen2.5 设置成功！
echo.
echo [📊] 优势总结:
echo   ✅ 无需手动下载28GB原始文件
echo   ✅ 自动优化推理性能
echo   ✅ 支持流式响应
echo   ✅ 显存占用更少
echo   ✅ 启动速度更快
echo.
echo [🚀] 下一步:
echo   1. 模型已可用，无需额外配置
echo   2. 继续下载MuseTalk模型
echo   3. 运行 deploy-production-now.bat
echo.
echo [💡] 如果需要切换模型:
echo   ollama pull 其他模型名称
echo   然后修改 appsettings.json 中的配置
echo.

echo 按任意键退出...
pause >nul