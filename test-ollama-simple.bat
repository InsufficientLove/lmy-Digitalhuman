@echo off
echo ================================================================================
echo                    Simple Ollama Test
echo ================================================================================
echo.

echo [1/3] Checking if Ollama is running...
curl -s http://localhost:11434/api/tags >nul 2>&1
if %errorlevel% equ 0 (
    echo SUCCESS: Ollama is running
) else (
    echo Starting Ollama...
    start /b ollama serve
    timeout /t 5 /nobreak >nul
)

echo.
echo [2/3] Listing available models...
curl -s http://localhost:11434/api/tags

echo.
echo [3/3] Testing qwen2.5vl:7b model...
echo Sending test request...
curl -X POST http://localhost:11434/api/generate ^
  -H "Content-Type: application/json" ^
  -d "{\"model\":\"qwen2.5vl:7b\",\"prompt\":\"你好\",\"stream\":false}"

echo.
echo ================================================================================
echo If you see a 404 error above, the model qwen2.5vl:7b is not installed
echo Try: ollama pull qwen2.5vl:7b
echo ================================================================================
pause