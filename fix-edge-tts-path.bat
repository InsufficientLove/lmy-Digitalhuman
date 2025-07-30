@echo off
echo ================================================================================
echo                    Fix Edge-TTS Path Issue
echo ================================================================================
echo.
echo Current issue: FileNotFoundError: No such file or directory
echo This is caused by path handling problems in edge-tts
echo.
pause

echo [1/5] Checking temp directory...
if not exist "temp" (
    echo Creating temp directory...
    mkdir temp
) else (
    echo Temp directory exists
)

if not exist "LmyDigitalHuman\temp" (
    echo Creating LmyDigitalHuman\temp directory...
    mkdir "LmyDigitalHuman\temp"
) else (
    echo LmyDigitalHuman\temp directory exists
)

echo.
echo [2/5] Testing edge-tts with absolute path...
set "TEST_FILE=%CD%\temp\test_edge_tts.mp3"
echo Testing with file: %TEST_FILE%

python -m edge_tts --voice zh-CN-XiaoxiaoNeural --text "测试语音合成" --write-media "%TEST_FILE%"
if exist "%TEST_FILE%" (
    echo SUCCESS: Edge-TTS works with absolute path
    del "%TEST_FILE%"
) else (
    echo ERROR: Edge-TTS failed with absolute path
)

echo.
echo [3/5] Testing edge-tts with relative path...
cd temp
python -m edge_tts --voice zh-CN-XiaoxiaoNeural --text "测试语音合成" --write-media "test_relative.mp3"
if exist "test_relative.mp3" (
    echo SUCCESS: Edge-TTS works with relative path
    del "test_relative.mp3"
) else (
    echo ERROR: Edge-TTS failed with relative path
)
cd ..

echo.
echo [4/5] Testing edge-tts version and installation...
python -c "import edge_tts; print('Edge-TTS version:', edge_tts.__version__)" 2>nul
if %errorlevel% equ 0 (
    echo Edge-TTS module is properly installed
) else (
    echo WARNING: Edge-TTS module issue detected
    echo Reinstalling edge-tts...
    pip install --upgrade --force-reinstall edge-tts
)

echo.
echo [5/5] Testing with escaped paths...
set "ESCAPED_FILE=%CD%\temp\test_escaped.mp3"
python -m edge_tts --voice zh-CN-XiaoxiaoNeural --text "路径测试" --write-media "%ESCAPED_FILE%"
if exist "%ESCAPED_FILE%" (
    echo SUCCESS: Escaped paths work
    del "%ESCAPED_FILE%"
    echo File cleaned up
) else (
    echo ERROR: Escaped paths don't work
)

echo.
echo ================================================================================
echo                           Fix Complete
echo ================================================================================
echo.
echo Recommendations:
echo 1. Use absolute paths for edge-tts output files
echo 2. Ensure temp directories exist before calling edge-tts
echo 3. Handle path escaping properly for Windows
echo.
echo The application should now work better with edge-tts
echo.
pause