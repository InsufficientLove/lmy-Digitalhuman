@echo off
chcp 65001 >nul
echo ================================================================================
echo          Setup MuseTalk Virtual Environment - High Performance 4x GPU
echo ================================================================================
echo.
echo System Configuration:
echo - Python: 3.10.11
echo - CUDA: 12.1
echo - GPUs: 4x RTX4090
echo - Target: Commercial-grade low latency performance
echo.
pause

echo [1/6] Creating virtual environment...
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
echo [2/6] Activating virtual environment...
call venv_musetalk\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo ❌ Failed to activate virtual environment
    pause
    exit /b 1
)
echo ✅ Virtual environment activated

echo.
echo [3/6] Upgrading pip and installing basic tools...
python -m pip install --upgrade pip setuptools wheel
echo ✅ Basic tools upgraded

echo.
echo [4/6] Installing PyTorch with CUDA 12.1 support...
echo Installing PyTorch optimized for CUDA 12.1...
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
if %errorlevel% neq 0 (
    echo ❌ Failed to install PyTorch
    pause
    exit /b 1
)
echo ✅ PyTorch with CUDA 12.1 installed

echo.
echo [5/6] Installing core dependencies...
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
echo [6/6] Installing MuseTalk specific dependencies...
echo Installing deep learning and computer vision libraries...
pip install transformers diffusers accelerate
pip install face-alignment
pip install imageio imageio-ffmpeg
pip install omegaconf einops
pip install tqdm requests

echo Installing performance optimization libraries...
pip install xformers --index-url https://download.pytorch.org/whl/cu121
pip install flash-attn --no-build-isolation

echo Installing multi-GPU support...
pip install deepspeed

echo.
echo ================================================================================
echo                          Verification
echo ================================================================================
echo.
echo Testing PyTorch CUDA installation...
python -c "
import torch
print(f'PyTorch version: {torch.__version__}')
print(f'CUDA available: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'CUDA version: {torch.version.cuda}')
    print(f'GPU count: {torch.cuda.device_count()}')
    for i in range(torch.cuda.device_count()):
        print(f'GPU {i}: {torch.cuda.get_device_name(i)}')
else:
    print('❌ CUDA not available!')
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
echo To activate this environment in the future:
echo   cd LmyDigitalHuman
echo   call venv_musetalk\Scripts\activate.bat
echo.
echo To update appsettings.json with the new Python path:
echo   "DigitalHuman:MuseTalk:PythonPath": "%CD%\venv_musetalk\Scripts\python.exe"
echo.

pause
