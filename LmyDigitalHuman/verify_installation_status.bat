@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ================================================
echo Digital Human Installation Verification
echo ================================================
echo Checking all components and their status...
echo.

REM Environment paths
set "BASE_DIR=F:\AI\DigitalHuman_Portable"
set "VENV_DIR=%BASE_DIR%\venv"
set "VS2022_PATH=D:\Program Files\Microsoft Visual Studio\2022\Community"
set "CMAKE_PATH=D:\Program Files\CMake\bin"

echo ===========================================
echo 1. Environment Setup Check
echo ===========================================

echo Checking virtual environment...
if exist "%VENV_DIR%\Scripts\activate.bat" (
    echo ✅ Virtual environment found: %VENV_DIR%
) else (
    echo ❌ Virtual environment missing: %VENV_DIR%
    echo.
    echo You need to run one of the setup scripts first!
    pause
    exit /b 1
)

echo Checking D drive tools...
if exist "%VS2022_PATH%\VC\Tools\MSVC" (
    echo ✅ VS2022 found: %VS2022_PATH%
) else (
    echo ⚠️ VS2022 not found at: %VS2022_PATH%
)

if exist "%CMAKE_PATH%\cmake.exe" (
    echo ✅ CMake found: %CMAKE_PATH%
    "%CMAKE_PATH%\cmake.exe" --version | findstr "cmake version"
) else (
    echo ⚠️ CMake not found at: %CMAKE_PATH%
)

echo.
echo Activating Python environment...
call "%VENV_DIR%\Scripts\activate.bat"

echo.
echo ===========================================
echo 2. Python Environment Check
echo ===========================================

echo Python version and location:
python --version
echo Python path: 
python -c "import sys; print(sys.executable)"

echo.
echo Pip configuration:
if exist "%USERPROFILE%\.pip\pip.conf" (
    echo ✅ Pip mirrors configured
    type "%USERPROFILE%\.pip\pip.conf"
) else (
    echo ⚠️ No pip mirrors configured
)

echo.
echo ===========================================
echo 3. Core Dependencies Check
echo ===========================================

echo Checking PyTorch...
python -c "
try:
    import torch
    print('✅ PyTorch:', torch.__version__)
    print('   CUDA available:', torch.cuda.is_available())
    if torch.cuda.is_available():
        print('   GPU count:', torch.cuda.device_count())
        for i in range(torch.cuda.device_count()):
            print(f'   GPU {i}:', torch.cuda.get_device_name(i))
    else:
        print('   Running on CPU')
except ImportError as e:
    print('❌ PyTorch not installed:', str(e))
"

echo.
echo Checking OpenCV...
python -c "
try:
    import cv2
    print('✅ OpenCV:', cv2.__version__)
    print('   Build info available')
except ImportError as e:
    print('❌ OpenCV not installed:', str(e))
"

echo.
echo Checking NumPy...
python -c "
try:
    import numpy as np
    print('✅ NumPy:', np.__version__)
except ImportError as e:
    print('❌ NumPy not installed:', str(e))
"

echo.
echo ===========================================
echo 4. Face Detection Libraries Check
echo ===========================================

echo Checking dlib...
python -c "
try:
    import dlib
    print('✅ dlib:', dlib.__version__)
    
    # Test face detector
    detector = dlib.get_frontal_face_detector()
    print('   Face detector: OK')
    
    # Test landmark predictor (if available)
    try:
        predictor = dlib.shape_predictor('shape_predictor_68_face_landmarks.dat')
        print('   68-point landmarks: OK')
    except:
        print('   68-point landmarks: Model file missing (download needed)')
    
    print('   🏆 BEST QUALITY: dlib provides highest accuracy')
    dlib_status = 'excellent'
    
except ImportError as e:
    print('❌ dlib not available:', str(e))
    dlib_status = 'missing'
except Exception as e:
    print('⚠️ dlib import error:', str(e))
    dlib_status = 'error'
"

echo.
echo Checking MediaPipe...
python -c "
try:
    import mediapipe as mp
    print('✅ MediaPipe:', mp.__version__)
    
    # Test face detection
    mp_face_detection = mp.solutions.face_detection
    face_detection = mp_face_detection.FaceDetection(model_selection=0, min_detection_confidence=0.5)
    print('   Face detection: OK')
    print('   🥈 GOOD QUALITY: Fast and accurate')
    mediapipe_status = 'good'
    
except ImportError as e:
    print('❌ MediaPipe not available:', str(e))
    mediapipe_status = 'missing'
except Exception as e:
    print('⚠️ MediaPipe error:', str(e))
    mediapipe_status = 'error'
"

echo.
echo Checking face_recognition...
python -c "
try:
    import face_recognition
    print('✅ face_recognition: Available')
    print('   Based on dlib, good for recognition tasks')
except ImportError as e:
    print('❌ face_recognition not available:', str(e))
"

echo.
echo ===========================================
echo 5. Web Service Dependencies Check
echo ===========================================

echo Checking Flask...
python -c "
try:
    import flask
    print('✅ Flask:', flask.__version__)
except ImportError as e:
    print('❌ Flask not installed:', str(e))
"

echo Checking Flask-CORS...
python -c "
try:
    import flask_cors
    print('✅ Flask-CORS: Available')
except ImportError as e:
    print('❌ Flask-CORS not installed:', str(e))
"

echo Checking requests...
python -c "
try:
    import requests
    print('✅ requests:', requests.__version__)
except ImportError as e:
    print('❌ requests not installed:', str(e))
"

echo.
echo ===========================================
echo 6. Audio/Video Processing Check
echo ===========================================

echo Checking librosa...
python -c "
try:
    import librosa
    print('✅ librosa:', librosa.__version__)
except ImportError as e:
    print('❌ librosa not installed:', str(e))
"

echo Checking soundfile...
python -c "
try:
    import soundfile
    print('✅ soundfile:', soundfile.__version__)
except ImportError as e:
    print('❌ soundfile not installed:', str(e))
"

echo Checking imageio...
python -c "
try:
    import imageio
    print('✅ imageio:', imageio.__version__)
except ImportError as e:
    print('❌ imageio not installed:', str(e))
"

echo.
echo ===========================================
echo 7. Service Files Check
echo ===========================================

if exist "%BASE_DIR%\MuseTalk\musetalk_service.py" (
    echo ✅ MuseTalk service (with dlib support): Found
) else (
    echo ⚠️ MuseTalk service (with dlib support): Missing
)

if exist "%BASE_DIR%\MuseTalk\musetalk_service_no_dlib.py" (
    echo ✅ MuseTalk service (no dlib): Found
) else (
    echo ⚠️ MuseTalk service (no dlib): Missing
)

if exist "%BASE_DIR%\scripts\start_musetalk_d_drive.bat" (
    echo ✅ Startup script (D drive): Found
) else (
    echo ⚠️ Startup script (D drive): Missing
)

if exist "%BASE_DIR%\scripts\start_musetalk_no_dlib.bat" (
    echo ✅ Startup script (no dlib): Found
) else (
    echo ⚠️ Startup script (no dlib): Missing
)

echo.
echo ===========================================
echo 8. Overall Status Summary
echo ===========================================

python -c "
import sys

# Check face detection capabilities
face_detection_methods = []
quality_level = 'none'

try:
    import dlib
    face_detection_methods.append('dlib (best quality)')
    quality_level = 'excellent'
except ImportError:
    pass

try:
    import mediapipe
    if quality_level != 'excellent':
        quality_level = 'good'
    face_detection_methods.append('MediaPipe (good quality)')
except ImportError:
    pass

try:
    import cv2
    if quality_level == 'none':
        quality_level = 'basic'
    face_detection_methods.append('OpenCV (basic quality)')
except ImportError:
    pass

# Check core dependencies
core_deps = []
try:
    import torch
    core_deps.append('PyTorch')
except ImportError:
    pass

try:
    import cv2
    core_deps.append('OpenCV')
except ImportError:
    pass

try:
    import numpy
    core_deps.append('NumPy')
except ImportError:
    pass

try:
    import flask
    core_deps.append('Flask')
except ImportError:
    pass

print('Face Detection Available:', ', '.join(face_detection_methods) if face_detection_methods else 'None')
print('Quality Level:', quality_level.upper())
print('Core Dependencies:', ', '.join(core_deps) if core_deps else 'Missing critical dependencies')
print()

if quality_level == 'excellent':
    print('🎉 EXCELLENT: You have dlib! Best possible quality.')
    print('   Recommendation: Use the full MuseTalk service')
elif quality_level == 'good':
    print('👍 GOOD: MediaPipe available. Very good quality.')
    print('   Recommendation: Use no-dlib MuseTalk service')
elif quality_level == 'basic':
    print('⚠️ BASIC: Only OpenCV available. Limited quality.')
    print('   Recommendation: Try to install MediaPipe or dlib')
else:
    print('❌ CRITICAL: No face detection available!')
    print('   Recommendation: Run setup scripts again')

print()
if len(core_deps) >= 4:
    print('✅ READY: Core dependencies satisfied')
    print('   You can start the MuseTalk service')
else:
    print('❌ NOT READY: Missing core dependencies')
    print('   Run setup scripts to install missing components')
"

echo.
echo ===========================================
echo 9. Service Test (if running)
echo ===========================================

echo Testing if MuseTalk service is running...
python -c "
import requests
import json

try:
    response = requests.get('http://localhost:8000/health', timeout=3)
    if response.status_code == 200:
        health_data = response.json()
        print('✅ SERVICE RUNNING:')
        print('   Status:', health_data.get('status', 'unknown'))
        print('   Service:', health_data.get('service', 'unknown'))
        print('   Face detection:', health_data.get('environment', {}).get('face_detection', 'unknown'))
        print('   GPU available:', health_data.get('gpu_info', {}).get('cuda_available', 'unknown'))
    else:
        print('⚠️ Service responding but with error:', response.status_code)
except requests.exceptions.ConnectionError:
    print('⚠️ Service not running (connection refused)')
    print('   Start with: start_musetalk_d_drive.bat or start_musetalk_no_dlib.bat')
except Exception as e:
    print('⚠️ Service test failed:', str(e))
"

echo.
echo ===========================================
echo 10. Next Steps Recommendations
echo ===========================================

echo Based on the checks above:
echo.
echo If you see "EXCELLENT" or "GOOD" quality:
echo   ✅ 1. Start service: %BASE_DIR%\scripts\start_musetalk_*.bat
echo   ✅ 2. Test health: http://localhost:8000/health
echo   ✅ 3. Integrate with your .NET application
echo.
echo If you see "BASIC" or "CRITICAL":
echo   🔧 1. Run: setup_without_dlib_d_drive.bat (for stable MediaPipe)
echo   🔧 2. Or try: fix_dlib_ultimate_d_drive.bat (for best quality)
echo.
echo If services are missing:
echo   📁 1. Check if setup scripts completed successfully
echo   📁 2. Look for error messages in the installation logs
echo.

echo ===========================================
echo Verification Complete!
echo ===========================================
echo.
echo This window will NOT close automatically.
echo You can scroll up to review all detailed results.
echo All information remains visible for your analysis.
echo.
echo Press any key when you're ready to close...
pause >nul