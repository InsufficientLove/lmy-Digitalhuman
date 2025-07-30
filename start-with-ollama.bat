@echo off
echo ================================================================================
echo                🚀 启动数字人系统 (含Ollama检查)
echo ================================================================================
echo.

echo [1/4] 检查Ollama服务状态...
curl -s http://localhost:11434/api/version >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Ollama服务运行正常
    curl -s http://localhost:11434/api/version
) else (
    echo ⚠️ Ollama服务未启动，正在启动...
    start /b ollama serve
    echo 等待服务启动...
    timeout /t 10 /nobreak >nul
    
    curl -s http://localhost:11434/api/version >nul 2>&1
    if %errorlevel% equ 0 (
        echo ✅ Ollama服务启动成功
    ) else (
        echo ❌ Ollama服务启动失败
        echo 请检查Ollama是否正确安装
        pause
        exit /b 1
    )
)

echo.
echo [2/4] 检查模型可用性...
ollama list | findstr "qwen2.5vl:7b" >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ qwen2.5vl:7b 模型已安装
) else (
    echo ⚠️ qwen2.5vl:7b 模型未找到
    echo 可用模型:
    ollama list
    echo.
    echo 提示: 如果需要安装模型，运行: ollama pull qwen2.5vl:7b
)

echo.
echo [3/4] 检查edge-tts...
python -c "import edge_tts; print('✅ edge-tts 可用')" 2>nul
if %errorlevel% neq 0 (
    echo ⚠️ edge-tts 未安装或不可用
    echo 运行 fix-edge-tts.bat 来修复
)

echo.
echo [4/4] 启动.NET应用程序...
echo 配置信息:
echo - Ollama超时: 120秒
echo - 模型: qwen2.5vl:7b
echo - 端口: http://localhost:5001
echo.
echo 🌐 访问地址: http://localhost:5001/digital-human-test.html
echo.

cd LmyDigitalHuman
dotnet run

echo.
echo 应用程序已退出
pause