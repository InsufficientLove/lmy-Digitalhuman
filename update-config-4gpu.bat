@echo off
chcp 65001 >nul
echo ================================================================================
echo              Update Configuration for 4x GPU High Performance
echo ================================================================================
echo.
echo This script will update appsettings.json for optimal 4x RTX4090 performance
echo.
pause

cd LmyDigitalHuman

echo Backing up current configuration...
copy appsettings.json appsettings.json.backup
echo ✅ Configuration backed up

echo.
echo Updating Python path to use virtual environment...
set VENV_PYTHON=%CD%\venv_musetalk\Scripts\python.exe

echo.
echo ================================================================================
echo Manual Configuration Updates Required:
echo ================================================================================
echo.
echo Please update the following in appsettings.json:
echo.
echo 1. Python Path:
echo    "DigitalHuman": {
echo      "MuseTalk": {
echo        "PythonPath": "%VENV_PYTHON%",
echo        "TimeoutMinutes": 30,
echo        "MaxRetries": 3
echo      }
echo    }
echo.
echo 2. GPU Configuration:
echo    "MuseTalk": {
echo      "Commercial": {
echo        "UseFloat16": true,
echo        "BatchSize": 8,
echo        "NumInferenceSteps": 20,
echo        "Resolution": 512,
echo        "Fps": 30,
echo        "GPUDevices": "0,1,2,3"
echo      },
echo      "Realtime": {
echo        "UseFloat16": true,
echo        "BatchSize": 4,
echo        "NumInferenceSteps": 10,
echo        "Resolution": 256,
echo        "Fps": 30,
echo        "TargetLatency": 200
echo      }
echo    }
echo.
echo 3. Performance Settings:
echo    "DigitalHuman": {
echo      "MaxVideoGeneration": 16,
echo      "EnablePerformanceOptimization": true,
echo      "EnableBatchProcessing": true,
echo      "DefaultResponseMode": "fast"
echo    }
echo.
echo 4. Environment Variables to set:
echo    CUDA_VISIBLE_DEVICES=0,1,2,3
echo    PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512
echo    OMP_NUM_THREADS=8
echo.

pause
