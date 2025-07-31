@echo off
chcp 65001 >nul 2>&1
echo ================================================================================
echo                          Install FFmpeg for Audio Optimization
echo ================================================================================
echo.
echo This script will install FFmpeg to enable audio optimization in MuseTalk
echo 音频优化可以提高MuseTalk的处理质量，但不是必需的
echo.
echo Options:
echo 1. Download and install FFmpeg automatically (Recommended)
echo 2. Manual installation guide
echo 3. Skip FFmpeg (use --no_optimize, current default)
echo.
set /p choice="请选择 (1-3): "

if "%choice%"=="1" goto auto_install
if "%choice%"=="2" goto manual_guide
if "%choice%"=="3" goto skip_ffmpeg
echo Invalid choice. Exiting...
pause
exit /b 1

:auto_install
echo.
echo [1/4] Creating FFmpeg directory...
if not exist "ffmpeg" mkdir ffmpeg
cd ffmpeg

echo.
echo [2/4] Downloading FFmpeg...
echo Downloading from: https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip
echo This may take a few minutes...

powershell -Command "& {
    $url = 'https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip'
    $output = 'ffmpeg-essentials.zip'
    Write-Host 'Starting download...'
    try {
        Invoke-WebRequest -Uri $url -OutFile $output -UserAgent 'Mozilla/5.0'
        Write-Host 'Download completed successfully'
    } catch {
        Write-Host 'Download failed:' $_.Exception.Message
        exit 1
    }
}"

if not exist "ffmpeg-essentials.zip" (
    echo ❌ Download failed
    pause
    exit /b 1
)

echo ✅ Download completed

echo.
echo [3/4] Extracting FFmpeg...
powershell -Command "Expand-Archive -Path 'ffmpeg-essentials.zip' -DestinationPath '.' -Force"

echo.
echo [4/4] Setting up FFmpeg...
for /d %%i in (ffmpeg-*) do (
    if exist "%%i\bin\ffmpeg.exe" (
        copy "%%i\bin\ffmpeg.exe" .
        copy "%%i\bin\ffprobe.exe" .
        echo ✅ FFmpeg setup completed
        goto setup_complete
    )
)

echo ❌ FFmpeg setup failed
pause
exit /b 1

:setup_complete
cd ..
echo.
echo ================================================================================
echo FFmpeg Installation Completed
echo ================================================================================
echo.
echo FFmpeg location: %CD%\ffmpeg\ffmpeg.exe
echo.
echo To enable audio optimization:
echo 1. Add %CD%\ffmpeg to your system PATH, or
echo 2. The application will automatically use the local ffmpeg.exe
echo.
echo Now you can remove --no_optimize from MuseTalkService to enable audio optimization
echo.
goto end

:manual_guide
echo.
echo ================================================================================
echo Manual FFmpeg Installation Guide
echo ================================================================================
echo.
echo 1. Visit: https://ffmpeg.org/download.html
echo 2. Download FFmpeg for Windows
echo 3. Extract to a folder (e.g., C:\ffmpeg)
echo 4. Add the bin folder to your system PATH
echo 5. Restart your application
echo.
echo Alternative: Place ffmpeg.exe in the application directory
echo.
goto end

:skip_ffmpeg
echo.
echo ================================================================================
echo Skipping FFmpeg Installation
echo ================================================================================
echo.
echo Audio optimization is disabled (--no_optimize is used)
echo MuseTalk will use the original audio files without preprocessing
echo This is fine for most use cases.
echo.
echo If you want to enable audio optimization later, run this script again.
echo.

:end
echo.
echo ================================================================================
echo Setup Complete
echo ================================================================================
pause