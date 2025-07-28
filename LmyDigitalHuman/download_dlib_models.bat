@echo off

echo ================================================
echo Download dlib Pre-trained Models
echo ================================================
echo Downloading face landmark detection models for dlib
echo.

set "BASE_DIR=F:\AI\DigitalHuman_Portable"
set "MODELS_DIR=%BASE_DIR%\models\dlib"

if not exist "%MODELS_DIR%" mkdir "%MODELS_DIR%"

echo Models directory: %MODELS_DIR%
echo.

echo Downloading shape_predictor_68_face_landmarks.dat...
echo This model detects 68 facial landmarks for precise face analysis
echo File size: ~95MB

curl -L -o "%MODELS_DIR%\shape_predictor_68_face_landmarks.dat" "http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2"

if %errorlevel% equ 0 (
    echo Download successful, extracting...
    
    REM Extract bz2 file (requires 7zip or similar)
    if exist "C:\Program Files\7-Zip\7z.exe" (
        "C:\Program Files\7-Zip\7z.exe" x "%MODELS_DIR%\shape_predictor_68_face_landmarks.dat.bz2" -o"%MODELS_DIR%"
        del "%MODELS_DIR%\shape_predictor_68_face_landmarks.dat.bz2"
        echo Model extracted successfully!
    ) else (
        echo 7-Zip not found. Please manually extract the .bz2 file
        echo Location: %MODELS_DIR%\shape_predictor_68_face_landmarks.dat.bz2
    )
) else (
    echo Download failed, trying alternative source...
    
    echo Trying GitHub mirror...
    curl -L -o "%MODELS_DIR%\shape_predictor_68_face_landmarks.dat.bz2" "https://github.com/italojs/facial-landmarks-recognition/raw/master/shape_predictor_68_face_landmarks.dat.bz2"
    
    if %errorlevel% equ 0 (
        echo Alternative download successful!
    ) else (
        echo All downloads failed. Manual download required.
        echo.
        echo Please download manually from:
        echo http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2
        echo.
        echo Save to: %MODELS_DIR%\
    )
)

echo.
echo ================================================
echo Model Download Summary
echo ================================================

if exist "%MODELS_DIR%\shape_predictor_68_face_landmarks.dat" (
    echo ✓ shape_predictor_68_face_landmarks.dat - Ready
    
    REM Get file size
    for %%A in ("%MODELS_DIR%\shape_predictor_68_face_landmarks.dat") do (
        echo   File size: %%~zA bytes
    )
    
    echo.
    echo dlib models are ready for use!
    echo Model path: %MODELS_DIR%\shape_predictor_68_face_landmarks.dat
    
) else (
    echo ✗ shape_predictor_68_face_landmarks.dat - Missing
    echo.
    echo Manual download required:
    echo 1. Download: http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2
    echo 2. Extract the .bz2 file
    echo 3. Place shape_predictor_68_face_landmarks.dat in: %MODELS_DIR%\
)

echo.
pause