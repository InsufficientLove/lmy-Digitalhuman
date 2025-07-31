@echo off
chcp 65001 >nul
echo ================================================================================
echo          Setup MuseTalk Virtual Environment - Basic Version
echo ================================================================================
echo.
echo This version installs only essential dependencies for basic functionality
echo Advanced optimizations like flash-attn are skipped to avoid compatibility issues
echo.
pause

echo [1/6] Creating virtual environment...
cd LmyDigitalHuman
if exist "venv_musetalk" (
    echo ⚠️ Virtual environment already exists. Removing old one...
    rmdir /s /q venv_musetalk
)

python -m venv venv_musetalk
call venv_musetalk\Scripts\activate.bat
echo ✅ Virtual environment created and activated

echo.
echo [2/6] Upgrading pip...
python -m pip install --upgrade pip setuptools wheel

echo.
echo [3/6] Installing PyTorch with CUDA 12.1...
pip install torch==2.5.1+cu121 torchvision==0.20.1+cu121 torchaudio==2.5.1+cu121 --index-url https://download.pytorch.org/whl/cu121

echo.
echo [4/6] Installing core dependencies...
pip install opencv-python numpy pillow
pip install librosa soundfile resampy
pip install scipy matplotlib

echo.
echo [5/6] Installing MuseTalk dependencies...
pip install transformers diffusers accelerate
pip install face-alignment
pip install imageio imageio-ffmpeg
pip install omegaconf einops
pip install tqdm requests

echo.
echo [6/6] Testing installation...
python -c "
import torch
print('PyTorch version:', torch.__version__)
print('CUDA available:', torch.cuda.is_available())
if torch.cuda.is_available():
    print('GPU count:', torch.cuda.device_count())
    for i in range(torch.cuda.device_count()):
        print(f'GPU {i}: {torch.cuda.get_device_name(i)}')

# Test core packages
packages = ['cv2', 'numpy', 'PIL', 'librosa', 'transformers']
for pkg in packages:
    try:
        __import__(pkg)
        print(f'✅ {pkg} imported successfully')
    except ImportError as e:
        print(f'❌ {pkg} import failed: {e}')
"

echo.
echo ================================================================================
echo                          Basic Setup Complete
echo ================================================================================
echo.
echo Virtual environment: %CD%\venv_musetalk
echo.
echo This basic installation includes:
echo ✅ PyTorch 2.5.1 with CUDA 12.1
echo ✅ OpenCV, NumPy, Pillow
echo ✅ Audio processing (librosa, soundfile)
echo ✅ Deep learning (transformers, diffusers)
echo ✅ MuseTalk core dependencies
echo.
echo Skipped optimizations (can be added later):
echo ⚠️ XFormers (attention optimization)
echo ⚠️ Flash Attention (memory optimization)
echo ⚠️ DeepSpeed (multi-GPU training)
echo.
echo Next: Use start-with-venv.bat to test the application
echo.
pause
