@echo off
echo ================================================================================
echo                    Test Complete Conversation Flow
echo ================================================================================
echo.
echo This script will test the entire conversation flow:
echo 1. Frontend template selection
echo 2. LLM text generation  
echo 3. TTS audio synthesis
echo 4. Digital human video generation
echo.
pause

echo [1/5] Checking required services...
echo Checking Ollama...
curl -s http://localhost:11434/api/version >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Ollama service running
) else (
    echo ⚠️ Starting Ollama...
    start /b ollama serve
    timeout /t 5 /nobreak >nul
)

echo.
echo Checking edge-tts...
python -c "import edge_tts; print('✅ edge-tts available')" 2>nul
if %errorlevel% neq 0 (
    echo ❌ edge-tts not available
    echo Run: pip install edge-tts
)

echo.
echo [2/5] Testing LLM request format...
echo Testing Ollama with correct request format...
curl -X POST http://localhost:11434/api/generate ^
  -H "Content-Type: application/json" ^
  -d "{\"model\":\"qwen2.5vl:7b\",\"prompt\":\"你是谁？\",\"stream\":false}" ^
  --max-time 30 -s | head -5

echo.
echo [3/5] Testing TTS with absolute path...
set "TEST_TTS_FILE=%CD%\temp\test_conversation_tts.mp3"
if not exist "temp" mkdir temp

echo Testing TTS output to: %TEST_TTS_FILE%
python -m edge_tts --voice zh-CN-XiaoxiaoNeural --text "我是数字人助手，很高兴为您服务" --write-media "%TEST_TTS_FILE%"
if exist "%TEST_TTS_FILE%" (
    echo ✅ TTS test successful
    echo File size: 
    dir "%TEST_TTS_FILE%" | find "test_conversation_tts.mp3"
    del "%TEST_TTS_FILE%"
) else (
    echo ❌ TTS test failed
)

echo.
echo [4/5] Checking temp directories...
if not exist "temp" (
    mkdir temp
    echo Created temp directory
)
if not exist "LmyDigitalHuman\temp" (
    mkdir "LmyDigitalHuman\temp"
    echo Created LmyDigitalHuman\temp directory
)

echo.
echo [5/5] Starting application for testing...
echo.
echo ================================================================================
echo                           Ready for Testing
echo ================================================================================
echo.
echo Next steps:
echo 1. Application will start
echo 2. Open: http://localhost:5001/digital-human-test.html
echo 3. Click on a template (should not show error popup)
echo 4. Type "你是谁？" and send
echo 5. Wait for complete flow: LLM → TTS → Video
echo.
echo Expected results:
echo - Template selection works without errors
echo - LLM responds in 5-15 seconds
echo - TTS generates audio file
echo - Audio plays in browser
echo.
echo Press Ctrl+C to stop when testing is complete
echo.

cd LmyDigitalHuman
dotnet run

pause