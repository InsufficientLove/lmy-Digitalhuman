@echo off
chcp 65001 >nul
echo ================================================================================
echo                   Diagnose Python Environment for MuseTalk
echo ================================================================================
echo.
pause

echo [1/3] Checking Python installation...
python --version 2>nul
if %errorlevel% equ 0 (
    echo ✅ Python is accessible
    python --version
) else (
    echo ❌ Python not found
    goto :end
)

echo.
echo [2/3] Checking MuseTalk script...
cd LmyDigitalHuman
if exist "musetalk_service_complete.py" (
    echo ✅ MuseTalk script found
) else (
    echo ❌ MuseTalk script missing
    goto :end
)

echo.
echo [3/3] Checking Python dependencies...
cd ..
python check-python-deps.py

:end
echo.
echo ================================================================================
echo Diagnosis complete. Check the results above.
echo ================================================================================
pause
