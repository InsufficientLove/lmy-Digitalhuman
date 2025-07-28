@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ================================================
echo Quick Installation Error Check
echo ================================================
echo Looking for common installation issues...
echo.

set "BASE_DIR=F:\AI\DigitalHuman_Portable"
set "VENV_DIR=%BASE_DIR%\venv"

if not exist "%VENV_DIR%\Scripts\activate.bat" (
    echo ❌ CRITICAL: Virtual environment not found!
    echo    Location checked: %VENV_DIR%
    echo    You need to run a setup script first.
    echo.
    pause
    exit /b 1
)

echo ✅ Virtual environment found
call "%VENV_DIR%\Scripts\activate.bat"

echo.
echo ================================================
echo Critical Component Quick Check
echo ================================================

echo Checking dlib...
python -c "
try:
    import dlib
    print('✅ SUCCESS: dlib is installed and working!')
    print('   Version:', dlib.__version__)
    print('   🏆 You have the BEST face detection quality!')
    dlib_ok = True
except ImportError:
    print('❌ dlib not installed (compilation may have failed)')
    dlib_ok = False
except Exception as e:
    print('⚠️ dlib installed but has issues:', str(e))
    dlib_ok = False
" 2>nul

echo.
echo Checking MediaPipe...
python -c "
try:
    import mediapipe as mp
    print('✅ SUCCESS: MediaPipe is installed and working!')
    print('   Version:', mp.__version__)
    print('   🥈 You have GOOD face detection quality!')
    mp_ok = True
except ImportError:
    print('❌ MediaPipe not installed')
    mp_ok = False
except Exception as e:
    print('⚠️ MediaPipe installed but has issues:', str(e))
    mp_ok = False
" 2>nul

echo.
echo Checking PyTorch...
python -c "
try:
    import torch
    print('✅ SUCCESS: PyTorch is installed!')
    print('   Version:', torch.__version__)
    print('   CUDA available:', torch.cuda.is_available())
    torch_ok = True
except ImportError:
    print('❌ PyTorch not installed')
    torch_ok = False
except Exception as e:
    print('⚠️ PyTorch installed but has issues:', str(e))
    torch_ok = False
" 2>nul

echo.
echo Checking OpenCV...
python -c "
try:
    import cv2
    print('✅ SUCCESS: OpenCV is installed!')
    print('   Version:', cv2.__version__)
    cv_ok = True
except ImportError:
    print('❌ OpenCV not installed')
    cv_ok = False
except Exception as e:
    print('⚠️ OpenCV installed but has issues:', str(e))
    cv_ok = False
" 2>nul

echo.
echo ================================================
echo Overall Status
echo ================================================

python -c "
# Quick overall assessment
components = []
quality = 'none'

try:
    import dlib
    components.append('dlib')
    quality = 'excellent'
except:
    pass

try:
    import mediapipe
    components.append('MediaPipe')
    if quality == 'none':
        quality = 'good'
except:
    pass

try:
    import cv2
    components.append('OpenCV')
    if quality == 'none':
        quality = 'basic'
except:
    pass

try:
    import torch
    components.append('PyTorch')
except:
    pass

print('Installed components:', ', '.join(components) if components else 'None')
print()

if quality == 'excellent':
    print('🎉 EXCELLENT STATUS!')
    print('   dlib is working - you have the best possible setup!')
    print('   Ready to use full MuseTalk service.')
elif quality == 'good':
    print('👍 GOOD STATUS!')
    print('   MediaPipe is working - very good quality setup!')
    print('   Ready to use no-dlib MuseTalk service.')
elif quality == 'basic':
    print('⚠️ BASIC STATUS')
    print('   Only OpenCV available - limited quality.')
    print('   Consider running setup scripts again.')
else:
    print('❌ CRITICAL ISSUES!')
    print('   No face detection available.')
    print('   Setup scripts failed - need to investigate.')

print()
if 'torch' in [c.lower() for c in components]:
    print('✅ PyTorch OK - Deep learning ready')
else:
    print('❌ PyTorch missing - Critical for AI functions')
"

echo.
echo ================================================
echo Common Error Patterns
echo ================================================

echo Checking for typical dlib compilation errors...
if exist "%USERPROFILE%\.pip\pip.conf" (
    echo ✅ Pip mirrors configured (should speed up downloads)
) else (
    echo ⚠️ No pip mirrors - downloads may be slow
)

python -c "
import sys
import os

# Check if we're in the right Python environment
expected_path = r'F:\AI\DigitalHuman_Portable\venv\Scripts\python.exe'
current_path = sys.executable

print('Python environment check:')
print('   Current:', current_path)
print('   Expected:', expected_path)

if expected_path.lower() in current_path.lower():
    print('✅ Using correct virtual environment')
else:
    print('⚠️ May not be using the intended virtual environment')

# Check for common missing components
print()
print('Missing component analysis:')
missing = []
try:
    import dlib
except ImportError:
    missing.append('dlib (requires VS2022 + CMake compilation)')

try:
    import mediapipe
except ImportError:
    missing.append('MediaPipe (should install easily)')

try:
    import torch
except ImportError:
    missing.append('PyTorch (large download, may timeout)')

if missing:
    print('❌ Missing:', ', '.join(missing))
    print()
    print('Recommendations:')
    if 'dlib' in str(missing):
        print('   For dlib: Use setup_without_dlib_d_drive.bat (skip compilation issues)')
    if 'MediaPipe' in str(missing):
        print('   For MediaPipe: pip install mediapipe -i https://pypi.tuna.tsinghua.edu.cn/simple/')
    if 'PyTorch' in str(missing):
        print('   For PyTorch: Check internet connection, use mirrors')
else:
    print('✅ All major components found!')
"

echo.
echo ================================================
echo Quick Fix Recommendations
echo ================================================

echo Based on the checks above:
echo.
echo If you see "EXCELLENT" or "GOOD":
echo   ✅ Your installation worked! 
echo   ✅ Run: verify_installation_status.bat for full details
echo   ✅ Start service and test
echo.
echo If you see "BASIC" or "CRITICAL":
echo   🔧 Recommended fix: setup_without_dlib_d_drive.bat
echo   🔧 This skips dlib compilation issues
echo   🔧 Provides stable MediaPipe-based solution
echo.
echo If specific components failed:
echo   📦 dlib failed: Expected with complex compilation
echo   📦 MediaPipe failed: Check internet connection
echo   📦 PyTorch failed: Large download, try again
echo.

echo ================================================
echo Quick Check Complete!
echo ================================================
echo.
echo For detailed analysis: verify_installation_status.bat
echo This window stays open for review.
echo.
pause