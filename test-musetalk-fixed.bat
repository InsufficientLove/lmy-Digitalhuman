@echo off
chcp 65001 >nul 2>&1
echo ================================================================================
echo                      Test MuseTalk with Audio Optimization Fix
echo ================================================================================
echo.
echo This script tests the MuseTalk fix with --no_optimize parameter
echo.

cd /d %~dp0
cd LmyDigitalHuman

echo [1/3] Activating virtual environment...
if not exist "venv_musetalk\Scripts\python.exe" (
    echo ❌ Virtual environment not found
    echo Please run setup-musetalk-basic.bat first
    pause
    exit /b 1
)

call venv_musetalk\Scripts\activate.bat

echo.
echo [2/3] Testing Python script directly...
echo Testing with --no_optimize parameter to skip FFmpeg dependency

set TEST_AVATAR=wwwroot\templates\Template_20250730_14_b2cbd859fb654911a9e14c50f025ecb7.jpg
set TEST_AUDIO=temp\test_audio.wav
set TEST_OUTPUT=temp\test_output.mp4

if not exist "%TEST_AVATAR%" (
    echo ❌ Test avatar not found: %TEST_AVATAR%
    echo Please create a template first
    pause
    exit /b 1
)

echo Creating test audio file...
echo This is a test > temp\test.txt
if exist "venv_musetalk\Scripts\edge-tts.exe" (
    venv_musetalk\Scripts\edge-tts.exe --voice "zh-CN-XiaoxiaoNeural" --text "这是一个测试音频" --write-media "%TEST_AUDIO%"
) else (
    echo ❌ edge-tts not found, creating dummy audio file
    copy /b NUL "%TEST_AUDIO%" >nul 2>&1
)

echo.
echo Testing MuseTalk Python script with --no_optimize...
python musetalk_service_complete.py ^
    --avatar "%TEST_AVATAR%" ^
    --audio "%TEST_AUDIO%" ^
    --output "%TEST_OUTPUT%" ^
    --fps 25 ^
    --batch_size 4 ^
    --quality medium ^
    --no_optimize ^
    --verbose

echo.
echo [3/3] Test completed!
echo.
echo Expected results:
echo ✅ No FFmpeg errors (audio optimization skipped)
echo ✅ CUDA detected with 4 GPUs
echo ✅ All dependencies loaded successfully
echo ✅ MuseTalk processing starts without [WinError 2]
echo.
echo If you see these results, the fix is working correctly.
echo.

if exist "%TEST_OUTPUT%" (
    echo ✅ Test video generated: %TEST_OUTPUT%
    echo File size: 
    dir "%TEST_OUTPUT%" | find ".mp4"
) else (
    echo ❌ Test video not generated
    echo Check the output above for errors
)

echo.
echo ================================================================================
echo Test Complete
echo ================================================================================
echo.
echo Next steps:
echo 1. If test passed: Run your application normally
echo 2. If test failed: Check the error messages above
echo 3. Optional: Run install-ffmpeg.bat to enable audio optimization
echo.
pause