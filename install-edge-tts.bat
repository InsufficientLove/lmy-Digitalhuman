@echo off
echo ================================================================================
echo                     Installing edge-tts
echo ================================================================================
echo.
echo edge-tts is required for text-to-speech functionality
echo.
pause

echo [1/3] Checking Python installation...
python --version
if %errorlevel% neq 0 (
    echo ERROR: Python not found
    echo Please install Python first
    pause
    exit /b 1
)

echo.
echo [2/3] Installing edge-tts...
pip install edge-tts

echo.
echo [3/3] Verifying installation...
edge-tts --version
if %errorlevel% equ 0 (
    echo SUCCESS: edge-tts installed successfully
) else (
    echo WARNING: edge-tts command not found in PATH
    echo Trying alternative installation...
    python -m pip install --upgrade edge-tts
)

echo.
echo Testing edge-tts...
edge-tts --list-voices | head -5
if %errorlevel% equ 0 (
    echo edge-tts is working correctly
) else (
    echo edge-tts installation may have issues
    echo Please check Python and pip configuration
)

echo.
echo Installation completed
pause