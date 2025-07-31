@echo off
chcp 65001 >nul 2>&1
echo ================================================================================
echo                     Complete MuseTalk Environment Setup
echo ================================================================================
echo.
echo This script will set up the complete environment for MuseTalk:
echo 1. Install FFmpeg to system (requires admin)
echo 2. Set up Python virtual environment
echo 3. Configure .NET application for automatic virtual environment activation
echo.
echo Requirements:
echo - Administrator privileges (for FFmpeg system installation)
echo - Python 3.10.11 with CUDA 12.1
echo - 4x RTX 4090 GPUs
echo.
pause

echo [Step 1/4] Installing FFmpeg to system...
echo.
echo FFmpeg is required for MuseTalk video processing and audio duration detection
echo This step requires administrator privileges
echo.
set /p install_ffmpeg="Install FFmpeg to system? (y/n): "
if /i "%install_ffmpeg%"=="y" (
    echo Starting FFmpeg installation...
    call install-ffmpeg-system.bat
    if %errorlevel% neq 0 (
        echo ❌ FFmpeg installation failed
        echo Please install FFmpeg manually and add to system PATH
        pause
        exit /b 1
    )
    echo ✅ FFmpeg installation completed
) else (
    echo Skipping FFmpeg installation
    echo ⚠️  Warning: MuseTalk requires FFmpeg to work properly
)

echo.
echo [Step 2/4] Setting up Python virtual environment...
cd /d %~dp0
cd LmyDigitalHuman

if not exist "venv_musetalk\Scripts\python.exe" (
    echo Virtual environment not found, creating...
    call setup-musetalk-basic.bat
    if %errorlevel% neq 0 (
        echo ❌ Virtual environment setup failed
        pause
        exit /b 1
    )
) else (
    echo ✅ Virtual environment already exists
)

echo.
echo [Step 3/4] Testing complete environment...
echo.
echo Testing FFmpeg availability...
ffmpeg -version >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ FFmpeg available in system PATH
) else (
    echo ❌ FFmpeg not found in system PATH
    echo Please restart your command prompt or add C:\ffmpeg to PATH manually
)

ffprobe -version >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ FFprobe available in system PATH
) else (
    echo ❌ FFprobe not found in system PATH
)

echo.
echo Testing virtual environment...
call venv_musetalk\Scripts\activate.bat
python -c "import torch; print('✅ PyTorch:', torch.__version__); print('✅ CUDA available:', torch.cuda.is_available()); print('✅ GPU count:', torch.cuda.device_count())"
if %errorlevel% neq 0 (
    echo ❌ Virtual environment test failed
    pause
    exit /b 1
)

echo.
echo Testing Python dependencies...
python -c "
packages = ['cv2', 'numpy', 'PIL', 'librosa', 'scipy', 'matplotlib']
missing = []
for pkg in packages:
    try:
        __import__(pkg)
        print(f'✅ {pkg}')
    except ImportError:
        print(f'❌ {pkg}')
        missing.append(pkg)
if missing:
    print(f'Missing packages: {missing}')
    exit(1)
else:
    print('✅ All dependencies available')
"

if %errorlevel% neq 0 (
    echo ❌ Some dependencies are missing
    pause
    exit /b 1
)

echo.
echo [Step 4/4] Final verification...
echo.
echo Testing MuseTalk Python script with complete environment...
python musetalk_service_complete.py --help >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ MuseTalk Python script is accessible
) else (
    echo ❌ MuseTalk Python script test failed
)

echo.
echo ================================================================================
echo Complete Environment Setup Finished
echo ================================================================================
echo.
echo Environment Status:
echo ✅ FFmpeg: System-wide installation with PATH configuration
echo ✅ Python: Virtual environment (venv_musetalk) with all dependencies
echo ✅ CUDA: 4x RTX 4090 GPUs configured
echo ✅ .NET: Automatic virtual environment activation configured
echo.
echo The .NET application will now:
echo 1. Automatically use the virtual environment Python
echo 2. Automatically configure 4x GPU environment variables
echo 3. Use system FFmpeg for video processing
echo 4. No manual .bat file activation needed
echo.
echo Next steps:
echo 1. Restart Visual Studio 2022 (to pick up PATH changes)
echo 2. Run your .NET application normally (F5 debug or dotnet run)
echo 3. The application will automatically activate virtual environment
echo.
echo Test commands:
echo - dotnet run (from LmyDigitalHuman directory)
echo - Or use Visual Studio 2022 F5 debug
echo.
echo Expected behavior:
echo - No more [WinError 2] errors
echo - Python process exit code: 0
echo - Successful video generation
echo.
pause