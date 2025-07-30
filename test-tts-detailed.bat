@echo off
echo ================================================================================
echo                    Detailed TTS Testing
echo ================================================================================
echo.
echo This script will test TTS functionality step by step
echo.
pause

echo [1/6] Checking Python and edge-tts...
python --version
if %errorlevel% neq 0 (
    echo ERROR: Python not found
    pause
    exit /b 1
)

python -c "import edge_tts; print('✅ edge-tts version:', edge_tts.__version__)" 2>nul
if %errorlevel% neq 0 (
    echo WARNING: edge-tts not available, installing...
    pip install edge-tts
)

echo.
echo [2/6] Testing edge-tts command line...
set "TEST_FILE=%CD%\temp\test_cli.mp3"
if not exist "temp" mkdir temp

echo Testing: python -m edge_tts --voice zh-CN-XiaoxiaoNeural --text "测试语音合成" --write-media "%TEST_FILE%"
python -m edge_tts --voice zh-CN-XiaoxiaoNeural --text "测试语音合成" --write-media "%TEST_FILE%"

if exist "%TEST_FILE%" (
    echo ✅ CLI test successful
    echo File size: 
    dir "%TEST_FILE%" | find "test_cli.mp3"
    del "%TEST_FILE%"
) else (
    echo ❌ CLI test failed
)

echo.
echo [3/6] Testing with different path formats...
set "TEST_FILE2=%CD%/temp/test_forward_slash.mp3"
echo Testing with forward slashes: %TEST_FILE2%
python -m edge_tts --voice zh-CN-XiaoxiaoNeural --text "正斜杠路径测试" --write-media "%TEST_FILE2%"

if exist "%CD%\temp\test_forward_slash.mp3" (
    echo ✅ Forward slash path works
    del "%CD%\temp\test_forward_slash.mp3"
) else (
    echo ❌ Forward slash path failed
)

echo.
echo [4/6] Testing Chinese text with special characters...
set "TEST_FILE3=%CD%\temp\test_chinese.mp3"
python -m edge_tts --voice zh-CN-XiaoxiaoNeural --text "我是来自阿里云的大规模语言模型，我叫通义千问。" --write-media "%TEST_FILE3%"

if exist "%TEST_FILE3%" (
    echo ✅ Chinese text test successful
    echo File size: 
    dir "%TEST_FILE3%" | find "test_chinese.mp3"
    del "%TEST_FILE3%"
) else (
    echo ❌ Chinese text test failed
)

echo.
echo [5/6] Testing with Rate and Pitch parameters...
set "TEST_FILE4=%CD%\temp\test_params.mp3"
python -m edge_tts --voice zh-CN-XiaoxiaoNeural --rate medium --pitch +0Hz --text "参数测试" --write-media "%TEST_FILE4%"

if exist "%TEST_FILE4%" (
    echo ✅ Parameters test successful
    del "%TEST_FILE4%"
) else (
    echo ❌ Parameters test failed
)

echo.
echo [6/6] Starting application to test integration...
echo.
echo ================================================================================
echo                           Testing Results
echo ================================================================================
echo.
echo Now test the application:
echo 1. Start the application
echo 2. Select a template
echo 3. Type: "我是来自阿里云的大规模语言模型，我叫通义千问。"
echo 4. Check the logs for detailed TTS processing
echo 5. Verify audio file is created in temp directory
echo.
echo Expected logs should show:
echo - "开始TTS转换: ResponseText=..."
echo - "TTS请求参数: Text长度=..."  
echo - "开始文本转语音: ..."
echo - "TTS输出文件路径: ..."
echo - "TTS转换结果: Success=True"
echo.

cd LmyDigitalHuman
dotnet run

pause