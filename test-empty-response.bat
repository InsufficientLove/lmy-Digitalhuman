@echo off
echo ================================================================================
echo                    Test Empty Response Handling
echo ================================================================================
echo.
echo This script will test how the application handles empty LLM responses
echo.
pause

echo [1/4] Testing Ollama directly...
echo Sending test request to Ollama...
curl -X POST http://localhost:11434/api/generate ^
  -H "Content-Type: application/json" ^
  -d "{\"model\":\"qwen2.5vl:7b\",\"prompt\":\"你是谁？\",\"stream\":false}" ^
  --max-time 30

echo.
echo.
echo [2/4] Testing edge-tts with empty text...
echo This should fail gracefully...
python -m edge_tts --voice zh-CN-XiaoxiaoNeural --text "" --write-media "temp/test_empty.mp3" 2>&1
if exist "temp/test_empty.mp3" (
    echo WARNING: Empty text created audio file
    del "temp/test_empty.mp3"
) else (
    echo EXPECTED: Empty text failed to create audio file
)

echo.
echo [3/4] Testing edge-tts with space-only text...
python -m edge_tts --voice zh-CN-XiaoxiaoNeural --text "   " --write-media "temp/test_spaces.mp3" 2>&1
if exist "temp/test_spaces.mp3" (
    echo WARNING: Space-only text created audio file
    del "temp/test_spaces.mp3"
) else (
    echo EXPECTED: Space-only text failed to create audio file
)

echo.
echo [4/4] Starting application to test empty response handling...
echo.
echo ================================================================================
echo                           Testing Instructions
echo ================================================================================
echo.
echo When the application starts:
echo 1. Select a template
echo 2. Type any question like "你是谁？"
echo 3. Check the logs for:
echo    - "Ollama原始响应: ..."
echo    - "Ollama解析结果: Response=..."
echo    - "LLM响应结果: Success=..., ResponseText长度=..."
echo    - If ResponseText长度=0, should see "LLM返回空响应，使用默认回复"
echo.
echo Expected behavior:
echo - If LLM returns empty response, use default message
echo - TTS should process default message instead of empty text
echo - No more "Edge TTS生成音频失败" due to empty text
echo.

cd LmyDigitalHuman
dotnet run

pause