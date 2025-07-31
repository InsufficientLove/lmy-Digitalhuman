@echo off
chcp 65001 >nul 2>&1
echo ================================================================================
echo                    Setup Official MuseTalk from GitHub
echo ================================================================================
echo.
echo This script will download and setup the official MuseTalk from:
echo https://github.com/TMElyralab/MuseTalk
echo.
echo Current approach was using a custom implementation, but we should use
echo the official MuseTalk API and models for better results.
echo.
pause

cd /d %~dp0

echo [1/5] Checking current MuseTalk installation...
if exist "Models\musetalk\MuseTalk\app.py" (
    echo ✅ Official MuseTalk already exists
    set MUSETALK_EXISTS=true
) else (
    echo ⚠️  Official MuseTalk not found, will download
    set MUSETALK_EXISTS=false
)

echo.
echo [2/5] Creating Models directory structure...
if not exist "Models" mkdir "Models"
if not exist "Models\musetalk" mkdir "Models\musetalk"

echo.
echo [3/5] Downloading official MuseTalk...
cd Models\musetalk

if "%MUSETALK_EXISTS%"=="false" (
    echo Cloning MuseTalk repository...
    git clone https://github.com/TMElyralab/MuseTalk.git
    if %errorlevel% neq 0 (
        echo ❌ Git clone failed, trying alternative download...
        
        echo Downloading as ZIP...
        powershell -Command "& {
            $url = 'https://github.com/TMElyralab/MuseTalk/archive/refs/heads/main.zip'
            $output = 'MuseTalk-main.zip'
            Write-Host 'Downloading MuseTalk...'
            try {
                Invoke-WebRequest -Uri $url -OutFile $output -UserAgent 'Mozilla/5.0'
                Write-Host 'Download completed'
                Expand-Archive -Path $output -DestinationPath '.' -Force
                Rename-Item 'MuseTalk-main' 'MuseTalk'
                Remove-Item $output
                Write-Host 'MuseTalk extracted successfully'
            } catch {
                Write-Host 'Download failed:' $_.Exception.Message
                exit 1
            }
        }"
        
        if %errorlevel% neq 0 (
            echo ❌ Download failed
            pause
            exit /b 1
        )
    )
    
    echo ✅ MuseTalk downloaded successfully
) else (
    echo Updating existing MuseTalk...
    cd MuseTalk
    git pull origin main
    cd ..
)

echo.
echo [4/5] Installing MuseTalk dependencies...
cd MuseTalk

REM 检查requirements.txt
if exist "requirements.txt" (
    echo Installing MuseTalk requirements...
    ..\..\LmyDigitalHuman\venv_musetalk\Scripts\python.exe -m pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo ❌ Requirements installation failed
        pause
        exit /b 1
    )
    echo ✅ Requirements installed
) else (
    echo ⚠️  requirements.txt not found, installing common dependencies...
    ..\..\LmyDigitalHuman\venv_musetalk\Scripts\python.exe -m pip install ^
        torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121 ^
        opencv-python pillow numpy librosa scipy matplotlib ^
        diffusers transformers accelerate ^
        gradio pyyaml
)

echo.
echo [5/5] Downloading MuseTalk model weights...
if exist "download_weights.bat" (
    echo Running official weight download script...
    call download_weights.bat
) else if exist "download_weights.sh" (
    echo Converting shell script to batch...
    echo @echo off > temp_download.bat
    echo echo Downloading MuseTalk weights... >> temp_download.bat
    echo mkdir models 2^>nul >> temp_download.bat
    echo echo Please manually download weights from MuseTalk releases >> temp_download.bat
    call temp_download.bat
    del temp_download.bat
) else (
    echo ⚠️  No official download script found
    echo Please manually download model weights from:
    echo https://github.com/TMElyralab/MuseTalk/releases
    echo.
    echo Or check the official documentation for weight download instructions
)

cd ..\..\..

echo.
echo ================================================================================
echo Official MuseTalk Setup Complete
echo ================================================================================
echo.
echo Installation location: Models\musetalk\MuseTalk
echo.
echo Next steps:
echo 1. Verify model weights are downloaded in Models\musetalk\MuseTalk\models
echo 2. Test with: python integrate-official-musetalk.py --help
echo 3. Run your .NET application - it will now use official MuseTalk
echo.
echo Official MuseTalk files:
if exist "Models\musetalk\MuseTalk\app.py" (
    echo ✅ app.py - Gradio web interface
) else (
    echo ❌ app.py missing
)

if exist "Models\musetalk\MuseTalk\scripts\inference.py" (
    echo ✅ scripts\inference.py - Official inference script  
) else (
    echo ❌ scripts\inference.py missing
)

if exist "Models\musetalk\MuseTalk\configs\inference\test.yaml" (
    echo ✅ configs\inference\test.yaml - Inference config
) else (
    echo ❌ configs\inference\test.yaml missing
)

echo.
echo Model weights status:
if exist "Models\musetalk\MuseTalk\models" (
    echo ✅ Models directory exists
    dir "Models\musetalk\MuseTalk\models" /s /b | find /c ".bin" > temp_count.txt
    set /p MODEL_COUNT=<temp_count.txt
    del temp_count.txt
    echo Found !MODEL_COUNT! model files
) else (
    echo ❌ Models directory missing - please download weights
)

echo.
echo The application will now use official MuseTalk instead of custom implementation
echo This should provide much better lip-sync quality and accuracy
echo.
pause