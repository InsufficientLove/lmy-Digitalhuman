@echo off
chcp 65001 >nul
echo ================================================================================
echo                   Diagnose Python Environment for MuseTalk
echo ================================================================================
echo.
echo This script will diagnose Python environment issues causing [WinError 2]
echo.
pause

echo [1/4] Checking Python installation...
python --version 2>nul
if %errorlevel% equ 0 (
    echo ✅ Python is accessible via 'python' command
    python --version
) else (
    echo ❌ Python not found via 'python' command
)

echo.
echo [2/4] Checking MuseTalk script...
cd LmyDigitalHuman
if exist "musetalk_service_complete.py" (
    echo ✅ Found musetalk_service_complete.py
    for %%F in (musetalk_service_complete.py) do echo File size: %%~zF bytes
) else (
    echo ❌ musetalk_service_complete.py not found
)

echo.
echo [3/4] Testing Python basic execution...
python -c "print('Python execution test: OK')" 2>nul
if %errorlevel% equ 0 (
    echo ✅ Python basic execution works
) else (
    echo ❌ Python basic execution failed
)

echo.
echo [4/4] Checking key Python dependencies...
echo Checking OpenCV...
python -c "import cv2; print('✅ OpenCV installed, version:', cv2.__version__)" 2>nul || echo ❌ OpenCV not installed

echo Checking NumPy...
python -c "import numpy; print('✅ NumPy installed, version:', numpy.__version__)" 2>nul || echo ❌ NumPy not installed

echo Checking PyTorch...
python -c "import torch; print('✅ PyTorch installed, version:', torch.__version__)" 2>nul || echo ❌ PyTorch not installed

echo Checking PIL...
python -c "import PIL; print('✅ PIL installed')" 2>nul || echo ❌ PIL not installed

echo.
echo ================================================================================
echo                          Diagnosis Summary
echo ================================================================================
echo.
echo If dependencies are missing, install them with:
echo pip install opencv-python numpy torch pillow torchaudio librosa scipy matplotlib
echo.
echo For CUDA support (recommended):
echo pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
echo.

pause
