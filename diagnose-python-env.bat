@echo off
echo ================================================================================
echo                    Diagnose Python Environment for MuseTalk
echo ================================================================================
echo.
echo This script will diagnose Python environment issues causing [WinError 2]
echo.
pause

echo [1/5] Checking Python installation...
python --version 2>nul
if %errorlevel% equ 0 (
    echo ✅ Python is accessible via 'python' command
    python --version
) else (
    echo ❌ Python not found via 'python' command
    echo Trying 'py' command...
    py --version 2>nul
    if %errorlevel% equ 0 (
        echo ✅ Python is accessible via 'py' command
        py --version
    ) else (
        echo ❌ Python not found via 'py' command either
        echo Please install Python or add it to PATH
    )
)

echo.
echo [2/5] Checking Python path in current directory...
echo Current directory: %CD%
if exist "python.exe" (
    echo ✅ Found python.exe in current directory
) else (
    echo ⚠️ No python.exe in current directory
)

echo.
echo [3/5] Checking MuseTalk script...
cd LmyDigitalHuman
if exist "musetalk_service_complete.py" (
    echo ✅ Found musetalk_service_complete.py
    echo File size: 
    dir musetalk_service_complete.py | find "musetalk_service_complete.py"
) else (
    echo ❌ musetalk_service_complete.py not found
    echo Current directory: %CD%
    echo Files in directory:
    dir *.py
)

echo.
echo [4/5] Testing Python script execution...
echo Testing basic Python execution...
python -c "print('Python works')" 2>nul
if %errorlevel% equ 0 (
    echo ✅ Python basic execution works
) else (
    echo ❌ Python basic execution failed
)

echo.
echo Testing script file access...
python -c "import os; print('Script exists:', os.path.exists('musetalk_service_complete.py'))" 2>nul

echo.
echo [5/5] Checking Python dependencies...
echo Checking required packages...
python -c "
try:
    import cv2
    print('✅ cv2 (OpenCV) installed')
except ImportError:
    print('❌ cv2 (OpenCV) not installed')

try:
    import numpy
    print('✅ numpy installed')
except ImportError:
    print('❌ numpy not installed')

try:
    import torch
    print('✅ PyTorch installed')
    print('PyTorch version:', torch.__version__)
except ImportError:
    print('❌ PyTorch not installed')

try:
    import PIL
    print('✅ PIL (Pillow) installed')
except ImportError:
    print('❌ PIL (Pillow) not installed')

try:
    import torchaudio
    print('✅ torchaudio installed')
except ImportError:
    print('❌ torchaudio not installed')

try:
    import librosa
    print('✅ librosa installed')
except ImportError:
    print('❌ librosa not installed')
" 2>nul

echo.
echo ================================================================================
echo                           Diagnosis Summary
echo ================================================================================
echo.
echo Common causes of [WinError 2]:
echo 1. Python not in PATH
echo 2. Wrong Python path in configuration
echo 3. Missing Python dependencies
echo 4. Script file not found or inaccessible
echo 5. Working directory issues
echo.
echo Solutions:
echo 1. Install Python and add to PATH
echo 2. Update Python path in appsettings.json
echo 3. Install missing dependencies: pip install opencv-python numpy torch pillow torchaudio librosa
echo 4. Ensure musetalk_service_complete.py exists and is readable
echo 5. Check file permissions
echo.

pause
