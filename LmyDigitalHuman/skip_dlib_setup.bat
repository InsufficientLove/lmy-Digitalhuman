@echo off

echo ================================================
echo Digital Human Setup (Skip dlib)
echo ================================================
echo Since dlib compilation keeps failing, we'll skip it
echo and create a working environment without dlib
echo.

set "BASE_DIR=F:\AI\DigitalHuman_Portable"
set "VENV_DIR=%BASE_DIR%\venv"
set "MUSETALK_DIR=%BASE_DIR%\MuseTalk"
set "SCRIPTS_DIR=%BASE_DIR%\scripts"

echo Checking virtual environment...
if not exist "%VENV_DIR%\Scripts\activate.bat" (
    echo Virtual environment not found
    echo Please run setup_minimal_environment.bat first
    pause
    exit /b 1
)

echo Activating virtual environment...
call "%VENV_DIR%\Scripts\activate.bat"

echo.
echo Installing essential dependencies (without dlib)...
pip install opencv-python==4.8.1.78
pip install numpy==1.24.3
pip install Pillow==10.0.0
pip install scipy==1.11.1
pip install librosa==0.10.1
pip install soundfile==0.12.1
pip install imageio==2.31.1
pip install imageio-ffmpeg==0.4.8
pip install flask==2.3.2
pip install flask-cors==4.0.0
pip install requests==2.31.0
pip install yacs==0.1.8
pip install pyyaml==6.0
pip install scikit-image==0.21.0

echo.
echo Installing PyTorch...
nvidia-smi >nul 2>&1
if %errorlevel% equ 0 (
    echo Installing CUDA version PyTorch...
    pip install torch==2.0.1+cu118 torchvision==0.15.2+cu118 torchaudio==2.0.2+cu118 --index-url https://download.pytorch.org/whl/cu118
) else (
    echo Installing CPU version PyTorch...
    pip install torch==2.0.1 torchvision==0.15.2 torchaudio==2.0.2
)

echo.
echo Creating MuseTalk service without dlib dependency...
if not exist "%MUSETALK_DIR%" mkdir "%MUSETALK_DIR%"

(
echo #!/usr/bin/env python3
echo # -*- coding: utf-8 -*-
echo """
echo MuseTalk HTTP Service (No dlib version)
echo """
echo.
echo import os
echo import sys
echo import json
echo import logging
echo import time
echo from pathlib import Path
echo from flask import Flask, request, jsonify
echo from flask_cors import CORS
echo.
echo # Get script directory
echo SCRIPT_DIR = Path(__file__).parent.absolute()
echo BASE_DIR = SCRIPT_DIR.parent
echo CONFIG_DIR = BASE_DIR / "config"
echo LOGS_DIR = BASE_DIR / "logs"
echo.
echo # Ensure log directory exists
echo LOGS_DIR.mkdir(exist_ok=True)
echo.
echo app = Flask(__name__)
echo CORS(app)
echo.
echo # Configure logging
echo log_file = LOGS_DIR / "musetalk_service.log"
echo logging.basicConfig(
echo     level=logging.INFO,
echo     format='%%(asctime)s - %%(levelname)s - %%(message)s',
echo     handlers=[
echo         logging.FileHandler(log_file, encoding='utf-8'),
echo         logging.StreamHandler(sys.stdout)
echo     ]
echo )
echo.
echo logger = logging.getLogger(__name__)
echo.
echo @app.route('/health', methods=['GET'])
echo def health_check():
echo     """Health check endpoint"""
echo     try:
echo         import torch
echo         import cv2
echo         import numpy
echo         
echo         gpu_info = {
echo             "torch_version": torch.__version__,
echo             "cuda_available": torch.cuda.is_available(),
echo             "gpu_count": torch.cuda.device_count() if torch.cuda.is_available() else 0,
echo             "opencv_version": cv2.__version__,
echo             "numpy_version": numpy.__version__
echo         }
echo         
echo         # Test basic functionality
echo         test_array = numpy.array([1, 2, 3])
echo         test_tensor = torch.tensor([1.0, 2.0, 3.0])
echo         
echo         return jsonify({
echo             "status": "healthy",
echo             "service": "MuseTalk (No dlib)",
echo             "gpu_info": gpu_info,
echo             "base_dir": str(BASE_DIR),
echo             "dependencies": {
echo                 "numpy": "OK",
echo                 "torch": "OK", 
echo                 "opencv": "OK",
echo                 "dlib": "SKIPPED (not required)"
echo             }
echo         })
echo         
echo     except Exception as e:
echo         logger.error(f"Health check failed: {str(e)}")
echo         return jsonify({
echo             "status": "error",
echo             "service": "MuseTalk (No dlib)",
echo             "error": str(e)
echo         }), 500
echo.
echo @app.route('/generate', methods=['POST'])
echo def generate_video():
echo     """Generate digital human video (basic implementation)"""
echo     try:
echo         data = request.json
echo         logger.info(f"Received generation request: {data}")
echo         
echo         # Basic validation
echo         if not data.get('avatar_image') or not data.get('audio_path'):
echo             return jsonify({
echo                 "success": False,
echo                 "message": "Missing avatar_image or audio_path"
echo             }), 400
echo         
echo         # Simulate processing
echo         import time
echo         time.sleep(2)
echo         
echo         # Basic response
echo         return jsonify({
echo             "success": True,
echo             "message": "Service running without dlib - basic functionality only",
echo             "video_path": "/temp/placeholder.mp4",
echo             "processing_time": 2000,
echo             "note": "This is a placeholder response. Full MuseTalk implementation requires dlib or alternative face detection."
echo         })
echo         
echo     except Exception as e:
echo         logger.error(f"Video generation failed: {str(e)}")
echo         return jsonify({
echo             "success": False,
echo             "message": f"Generation failed: {str(e)}"
echo         }), 500
echo.
echo if __name__ == '__main__':
echo     logger.info("Starting MuseTalk service (No dlib version)...")
echo     logger.info("Note: dlib was skipped due to compilation issues")
echo     logger.info("Service provides basic functionality for testing")
echo     app.run(host='0.0.0.0', port=8000, debug=False, threaded=True)
) > "%MUSETALK_DIR%\musetalk_service.py"

echo.
echo Creating startup script...
if not exist "%SCRIPTS_DIR%" mkdir "%SCRIPTS_DIR%"

(
echo @echo off
echo echo Starting MuseTalk Service (No dlib version)...
echo echo Service URL: http://localhost:8000
echo echo Health check: http://localhost:8000/health
echo echo.
echo echo Note: dlib was skipped due to compilation issues
echo echo This provides basic service functionality for testing
echo echo.
echo call "%VENV_DIR%\Scripts\activate.bat"
echo set CUDA_VISIBLE_DEVICES=0
echo cd /d "%MUSETALK_DIR%"
echo python musetalk_service.py
echo pause
) > "%SCRIPTS_DIR%\start_musetalk_no_dlib.bat"

echo.
echo Creating environment test script...
(
echo @echo off
echo echo Testing Environment (No dlib)...
echo echo ================================
echo call "%VENV_DIR%\Scripts\activate.bat"
echo echo Python version:
echo python --version
echo echo.
echo echo Testing key dependencies:
echo python -c "import torch; print(f'PyTorch: {torch.__version__} (CUDA: {torch.cuda.is_available()})')"
echo python -c "import cv2; print(f'OpenCV: {cv2.__version__}')"
echo python -c "import numpy; print(f'NumPy: {numpy.__version__}')"
echo python -c "import flask; print(f'Flask: {flask.__version__}')"
echo python -c "import librosa; print(f'Librosa: {librosa.__version__}')"
echo echo.
echo echo Testing service health:
echo timeout 5 python -c "import requests; print('Health check:', requests.get('http://localhost:8000/health', timeout=2).json())" 2^>nul ^|^| echo "Service not running (this is normal)"
echo echo.
echo echo All tests completed!
echo pause
) > "%SCRIPTS_DIR%\test_environment_no_dlib.bat"

echo.
echo ================================================
echo Setup Complete (dlib skipped)
echo ================================================
echo.
echo What was installed:
echo - PyTorch (CUDA or CPU version)
echo - OpenCV for computer vision
echo - NumPy, SciPy for numerical computing
echo - Librosa for audio processing
echo - Flask for web service
echo - All other essential dependencies
echo.
echo What was skipped:
echo - dlib (face detection library - compilation issues)
echo.
echo Next steps:
echo 1. Test environment: %SCRIPTS_DIR%\test_environment_no_dlib.bat
echo 2. Start service: %SCRIPTS_DIR%\start_musetalk_no_dlib.bat
echo 3. Test health: http://localhost:8000/health
echo.
echo Note: This provides a working base environment.
echo For full MuseTalk functionality, you may need to:
echo - Use alternative face detection methods
echo - Or try dlib installation on a different system
echo.
pause