@echo off
chcp 65001 >nul 2>&1
echo ================================================================================
echo                    Install FFmpeg to System PATH (Required for MuseTalk)
echo ================================================================================
echo.
echo MuseTalk requires FFmpeg for video processing and audio duration detection
echo This script will install FFmpeg to C:\ffmpeg and add it to system PATH
echo.
echo 警告: 这将修改系统环境变量，需要管理员权限
echo.
pause

echo [1/5] Checking administrator privileges...
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ This script requires administrator privileges
    echo Please run as administrator
    pause
    exit /b 1
)

echo ✅ Administrator privileges confirmed

echo.
echo [2/5] Creating FFmpeg directory...
if not exist "C:\ffmpeg" mkdir "C:\ffmpeg"
cd /d "C:\ffmpeg"

echo.
echo [3/5] Downloading FFmpeg...
echo Downloading from: https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip
echo This may take several minutes...

powershell -Command "& {
    $url = 'https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip'
    $output = 'ffmpeg-essentials.zip'
    Write-Host 'Starting download...'
    try {
        $ProgressPreference = 'SilentlyContinue'
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
echo [4/5] Extracting and setting up FFmpeg...
powershell -Command "Expand-Archive -Path 'ffmpeg-essentials.zip' -DestinationPath '.' -Force"

for /d %%i in (ffmpeg-*) do (
    if exist "%%i\bin\ffmpeg.exe" (
        copy "%%i\bin\ffmpeg.exe" .
        copy "%%i\bin\ffprobe.exe" .
        echo ✅ FFmpeg binaries extracted
        goto path_setup
    )
)

echo ❌ FFmpeg extraction failed
pause
exit /b 1

:path_setup
echo.
echo [5/5] Adding FFmpeg to system PATH...

:: 获取当前PATH
for /f "tokens=2*" %%A in ('reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v PATH 2^>nul') do set "CURRENT_PATH=%%B"

:: 检查是否已经在PATH中
echo %CURRENT_PATH% | find /i "C:\ffmpeg" >nul
if %errorlevel% equ 0 (
    echo ✅ FFmpeg already in system PATH
    goto verify_installation
)

:: 添加到PATH
set "NEW_PATH=%CURRENT_PATH%;C:\ffmpeg"
reg add "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v PATH /t REG_EXPAND_SZ /d "%NEW_PATH%" /f >nul

if %errorlevel% equ 0 (
    echo ✅ FFmpeg added to system PATH
) else (
    echo ❌ Failed to add FFmpeg to system PATH
    echo Please manually add C:\ffmpeg to your system PATH
    pause
    exit /b 1
)

:verify_installation
echo.
echo [Verification] Testing FFmpeg installation...
set PATH=%PATH%;C:\ffmpeg
ffmpeg -version | find "ffmpeg version" >nul
if %errorlevel% equ 0 (
    echo ✅ FFmpeg installation successful
    ffmpeg -version | head -1
) else (
    echo ❌ FFmpeg installation verification failed
)

ffprobe -version | find "ffprobe version" >nul
if %errorlevel% equ 0 (
    echo ✅ FFprobe installation successful
) else (
    echo ❌ FFprobe installation verification failed
)

echo.
echo ================================================================================
echo FFmpeg System Installation Complete
echo ================================================================================
echo.
echo Installation location: C:\ffmpeg
echo Added to system PATH: Yes
echo.
echo ⚠️  IMPORTANT: You need to restart your applications for PATH changes to take effect
echo.
echo Next steps:
echo 1. Restart Visual Studio 2022
echo 2. Restart your command prompt/PowerShell
echo 3. Test MuseTalk: test-musetalk-fixed.bat
echo.
echo FFmpeg commands available globally:
echo - ffmpeg -version
echo - ffprobe -version
echo.
pause