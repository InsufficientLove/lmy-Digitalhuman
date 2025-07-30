@echo off
echo ================================================================================
echo         Manual Whisper Large Model Download Guide
echo ================================================================================
echo.
echo You are manually downloading the Whisper Large model.
echo Here are the CORRECT file locations:
echo.
echo WRONG Location: models\whisper\
echo CORRECT Location: LmyDigitalHuman\Models\
echo.
echo File Details:
echo - File Name: ggml-large-v3.bin
echo - File Size: ~2.9GB
echo - Download URL: https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3.bin
echo.
pause

echo Creating correct directory structure...
if not exist "LmyDigitalHuman" (
    echo ERROR: LmyDigitalHuman directory not found
    echo Please run this script from project root directory
    pause
    exit
)

if not exist "LmyDigitalHuman\Models" (
    echo Creating Models directory...
    mkdir "LmyDigitalHuman\Models"
)

echo.
echo ================================================================================
echo STEP 1: Download Instructions
echo ================================================================================
echo.
echo Please download the file to this EXACT location:
echo %CD%\LmyDigitalHuman\Models\ggml-large-v3.bin
echo.
echo Download Methods:
echo 1. Direct download: https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3.bin
echo 2. Visit: https://huggingface.co/ggerganov/whisper.cpp/tree/main
echo    Then click on: ggml-large-v3.bin
echo    Then click: Download
echo.
echo IMPORTANT: Save the file as "ggml-large-v3.bin" (not .bin.bin)
echo.
pause

echo ================================================================================
echo STEP 2: Verification
echo ================================================================================
echo.
echo After download, press any key to verify...
pause

if exist "LmyDigitalHuman\Models\ggml-large-v3.bin" (
    echo SUCCESS: File found!
    for %%I in ("LmyDigitalHuman\Models\ggml-large-v3.bin") do (
        echo File size: %%~zI bytes
        if %%~zI gtr 2000000000 (
            echo File size looks correct (over 2GB)
            echo Whisper Large model is ready!
        ) else (
            echo WARNING: File size seems small
            echo Expected: ~2.9GB
            echo Actual: %%~zI bytes
        )
    )
) else (
    echo File not found. Please check:
    echo 1. File is saved in correct location
    echo 2. File name is exactly: ggml-large-v3.bin
    echo 3. Download completed successfully
    echo.
    echo Expected location: %CD%\LmyDigitalHuman\Models\ggml-large-v3.bin
)

echo.
echo ================================================================================
echo STEP 3: Configuration Check
echo ================================================================================
echo.
echo The configuration files already point to the correct location:
echo appsettings.json: "ModelPath": "Models/ggml-large-v3.bin"
echo.
echo When you start the application, it will automatically use this model.
echo.
echo Next steps:
echo 1. Complete MuseTalk model download
echo 2. Run deployment script
echo 3. Test the application
echo.
pause