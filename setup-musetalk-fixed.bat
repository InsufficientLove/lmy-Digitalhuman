@echo off
chcp 65001 >nul
echo ================================================================================
echo          Setup MuseTalk Virtual Environment - Fixed Version
echo ================================================================================
echo.
echo System Configuration:
echo - Python: 3.10.11
echo - CUDA: 12.1
echo - GPUs: 4x RTX4090
echo - Target: Commercial-grade low latency performance
echo.
pause

echo [1/7] Creating virtual environment...
cd LmyDigitalHuman
if exist "venv_musetalk" (
    echo ⚠️ Virtual environment already exists. Removing old one...
    rmdir /s /q venv_musetalk
)

python -m venv venv_musetalk
if %errorlevel% neq 0 (
    echo ❌ Failed to create virtual environment
    pause
    exit /b 1
)
echo ✅ Virtual environment created

echo.
echo [2/7] Activating virtual environment...
call venv_musetalk\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo ❌ Failed to activate virtual environment
    pause
    exit /b 1
)
echo ✅ Virtual environment activated

echo.
echo [3/7] Upgrading pip and installing basic tools...
python -m pip install --upgrade pip setuptools wheel
echo ✅ Basic tools upgraded

echo.
echo [4/7] Installing PyTorch with CUDA 12.1 support (fixed versions)...
echo Installing compatible PyTorch versions...
pip install torch==2.5.1+cu121 torchvision==0.20.1+cu121 torchaudio==2.5.1+cu121 --index-url https://download.pytorch.org/whl/cu121
if %errorlevel% neq 0 (
    echo ❌ Failed to install PyTorch
    pause
    exit /b 1
)
echo ✅ PyTorch with CUDA 12.1 installed

echo.
echo [5/7] Installing core dependencies...
echo Installing OpenCV, NumPy, Pillow...
pip install opencv-python numpy pillow
if %errorlevel% neq 0 (
    echo ❌ Failed to install core dependencies
    pause
    exit /b 1
)

echo Installing audio processing libraries...
pip install librosa soundfile resampy
if %errorlevel% neq 0 (
    echo ❌ Failed to install audio libraries
    pause
    exit /b 1
)

echo Installing scientific computing libraries...
pip install scipy matplotlib
if %errorlevel% neq 0 (
    echo ❌ Failed to install scientific libraries
    pause
    exit /b 1
)

echo.
echo [6/7] Installing MuseTalk specific dependencies...
echo Installing deep learning and computer vision libraries...
pip install transformers diffusers accelerate
pip install face-alignment
pip install imageio imageio-ffmpeg
pip install omegaconf einops
pip install tqdm requests

echo Installing performance optimization libraries...
echo Installing XFormers (compatible with PyTorch 2.5.1)...
pip install xformers==0.0.28.post3 --index-url https://download.pytorch.org/whl/cu121

echo Skipping flash-attn due to Windows long path issues...
echo (flash-attn is optional and not critical for basic functionality)

echo Installing multi-GPU support...
pip install deepspeed

echo.
echo [7/7] Verification...
echo ================================================================================
echo                          Verification
echo ================================================================================
echo.
echo Testing PyTorch CUDA installation...
python -c "
import torch
import sys
print('='*50)
print('Python version:', sys.version)
print('PyTorch version:', torch.__version__)
print('CUDA available:', torch.cuda.is_available())
if torch.cuda.is_available():
    print('CUDA version:', torch.version.cuda)
    print('GPU count:', torch.cuda.device_count())
    for i in range(torch.cuda.device_count()):
        print(f'GPU {i}: {torch.cuda.get_device_name(i)}')
        print(f'GPU {i} Memory: {torch.cuda.get_device_properties(i).total_memory / 1024**3:.1f} GB')
else:
    print('❌ CUDA not available!')
print('='*50)
"

echo.
echo Testing core dependencies...
python ..\check-python-deps.py

echo.
echo ================================================================================
echo                          Setup Complete
echo ================================================================================
echo.
echo Virtual environment created at: %CD%\venv_musetalk
echo.
echo Python path for appsettings.json:
echo   "%CD%\venv_musetalk\Scripts\python.exe"
echo.
echo To activate this environment manually:
echo   cd LmyDigitalHuman
echo   call venv_musetalk\Scripts\activate.bat
echo.
echo Known limitations:
echo - flash-attn skipped due to Windows long path issues
echo - This is optional and won't affect core functionality
echo.
echo Next steps:
echo 1. Use start-with-venv.bat to run the application
echo 2. Test with a simple conversation
echo 3. Monitor GPU usage with nvidia-smi
echo.

echo Press any key to continue...
pause >nul
