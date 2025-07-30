@echo off
echo ================================================================================
echo                   Fix edge-tts Installation Issue
echo ================================================================================
echo.
echo Current issue: edge-tts command not found
echo This will install edge-tts globally for the system
echo.
pause

echo [1/4] Checking current Python installation...
python --version
if %errorlevel% neq 0 (
    echo ERROR: Python not found in PATH
    echo Please ensure Python is installed and added to PATH
    pause
    exit /b 1
)

echo.
echo [2/4] Checking if edge-tts is already installed...
python -c "import edge_tts; print('edge-tts module found')" 2>nul
if %errorlevel% equ 0 (
    echo edge-tts module is installed
) else (
    echo edge-tts module not found, installing...
    pip install edge-tts
)

echo.
echo [3/4] Installing/Upgrading edge-tts...
pip install --upgrade edge-tts

echo.
echo [4/4] Testing edge-tts functionality...

echo Testing Python module access:
python -c "import edge_tts; print('SUCCESS: edge-tts module accessible')"

echo.
echo Testing command line access:
edge-tts --version 2>nul
if %errorlevel% equ 0 (
    echo SUCCESS: edge-tts command line tool working
) else (
    echo WARNING: edge-tts command not in PATH
    echo This is normal on some systems
    echo The application will use 'python -m edge_tts' instead
)

echo.
echo Testing voice synthesis:
python -m edge_tts --voice zh-CN-XiaoxiaoNeural --text "测试语音合成" --write-media test_audio.wav
if exist "test_audio.wav" (
    echo SUCCESS: Test audio file created
    del test_audio.wav
) else (
    echo ERROR: Failed to create test audio file
)

echo.
echo ================================================================================
echo                           Fix Complete
echo ================================================================================
echo.
echo edge-tts should now work with your application
echo The app will try both methods:
echo 1. Direct command: edge-tts
echo 2. Python module: python -m edge_tts
echo.
echo You can now restart your application
echo.
pause