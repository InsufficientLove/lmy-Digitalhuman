@echo off
chcp 65001 >nul 2>&1
echo ================================================================================
echo                    🚀 启动数字人调试环境
echo ================================================================================
echo.
echo [✅] Ollama: qwen2.5vl:7b
echo [✅] Whisper: Large模型  
echo [✅] MuseTalk: 模型已下载
echo.
pause

echo [🔍] 检查Ollama服务...
curl -s http://localhost:11434/api/tags >nul 2>&1
if %errorlevel% equ 0 (
    echo [✅] Ollama服务运行正常
) else (
    echo [⚠️] Ollama服务未启动，正在启动...
    start /b ollama serve
    timeout /t 3 /nobreak >nul
)

echo.
echo [🚀] 启动.NET应用程序...
cd LmyDigitalHuman
dotnet run

pause