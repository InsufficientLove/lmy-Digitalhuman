@echo off
echo ================================================================================
echo                   Whisper Large Model Download
echo ================================================================================
echo.
echo Model: Whisper Large v3
echo Size: ~2.9GB  
echo Path: LmyDigitalHuman\Models\ggml-large-v3.bin
echo.
echo Press any key to start download...
pause

REM Check if project directory exists
if not exist "LmyDigitalHuman" (
    echo ERROR: LmyDigitalHuman directory not found
    echo Please run this script from project root directory
    pause
    exit /b 1
)

REM Create Models directory
if not exist "LmyDigitalHuman\Models" (
    echo Creating Models directory...
    mkdir "LmyDigitalHuman\Models"
)

REM Change to Models directory
cd LmyDigitalHuman\Models

REM Check if file already exists
if exist "ggml-large-v3.bin" (
    echo File already exists. Checking size...
    for %%I in ("ggml-large-v3.bin") do (
        echo Current size: %%~zI bytes
        if %%~zI gtr 2000000000 (
            echo File size looks good. Download may not be needed.
            set /p overwrite="Download anyway? (y/n): "
            if /i not "!overwrite!"=="y" (
                echo Keeping existing file.
                goto end
            )
        )
    )
)

echo ================================================================================
echo Starting download...
echo ================================================================================

REM Method 1: Try curl
echo Trying curl download...
curl --version >nul 2>&1
if %errorlevel% equ 0 (
    curl -L -o ggml-large-v3.bin https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3.bin
    if %errorlevel% equ 0 (
        echo Curl download completed
        goto verify
    )
)

REM Method 2: Try PowerShell
echo Trying PowerShell download...
powershell -Command "Invoke-WebRequest -Uri 'https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3.bin' -OutFile 'ggml-large-v3.bin'"

:verify
echo ================================================================================
echo Verifying download...
echo ================================================================================

if exist "ggml-large-v3.bin" (
    for %%I in ("ggml-large-v3.bin") do (
        echo Downloaded file size: %%~zI bytes
        if %%~zI gtr 2000000000 (
            echo SUCCESS: Download completed successfully!
        ) else (
            echo WARNING: File size seems small. May be incomplete.
        )
    )
) else (
    echo ERROR: Download failed. File not found.
    echo.
    echo Manual download instructions:
    echo 1. Visit: https://huggingface.co/ggerganov/whisper.cpp/tree/main
    echo 2. Download: ggml-large-v3.bin
    echo 3. Save to: %CD%
)

:end
cd ..\..
echo.
echo Download process completed.
echo Press any key to exit...
pause