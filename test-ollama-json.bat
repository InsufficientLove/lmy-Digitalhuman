@echo off
echo ================================================================================
echo                    Test Ollama JSON Parsing Fix
echo ================================================================================
echo.
echo This script will test the Ollama JSON response parsing fix
echo.
pause

echo [1/3] Testing Ollama service...
curl -s http://localhost:11434/api/version >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Ollama service is running
) else (
    echo ⚠️ Starting Ollama service...
    start /b ollama serve
    timeout /t 5 /nobreak >nul
)

echo.
echo [2/3] Testing Ollama API response format...
echo Sending test request to get actual JSON format...
curl -X POST http://localhost:11434/api/generate ^
  -H "Content-Type: application/json" ^
  -d "{\"model\":\"qwen2.5vl:7b\",\"prompt\":\"你好\",\"stream\":false}" ^
  --max-time 30

echo.
echo.
echo [3/3] Starting application to test JSON parsing...
echo.
echo ================================================================================
echo                           Expected Log Output
echo ================================================================================
echo.
echo With the JSON parsing fix, you should now see:
echo.
echo [INF] Ollama原始响应: {"model":"qwen2.5vl:7b","response":"你好！我是通义千问...",...}
echo [INF] Ollama解析结果: Response=你好！我是通义千问..., Done=True
echo [INF] LLM响应结果: Success=True, ResponseText长度=XX, Error=
echo [INF] 开始TTS转换: ResponseText=你好！我是通义千问..., Voice=zh-CN-XiaoxiaoNeural
echo.
echo Key changes:
echo - Response field should now contain the actual response text
echo - ResponseText长度 should be > 0 (not 0)
echo - TTS should receive actual text (not empty string)
echo.
echo Testing steps:
echo 1. Select a template
echo 2. Type "你是谁？"
echo 3. Check logs for proper JSON parsing
echo 4. Verify TTS processes actual response text
echo.

cd LmyDigitalHuman
dotnet run

pause