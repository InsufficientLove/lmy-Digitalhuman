@echo off
chcp 65001 >nul 2>&1
echo ================================================================================
echo                   VS2022 Debug with Virtual Environment
echo ================================================================================
echo.
echo This script configures virtual environment for VS2022 debugging
echo.

cd /d %~dp0
cd LmyDigitalHuman

echo [1/3] Checking virtual environment...
if not exist "venv_musetalk\Scripts\python.exe" (
    echo ❌ Virtual environment not found
    echo Please run setup-musetalk-basic.bat first
    pause
    exit /b 1
)

echo ✅ Virtual environment found

echo.
echo [2/3] Activating virtual environment...
call venv_musetalk\Scripts\activate.bat

echo.
echo [3/3] Setting environment variables for 4x GPU...
set CUDA_VISIBLE_DEVICES=0,1,2,3
set PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512
set OMP_NUM_THREADS=8

echo.
echo ================================================================================
echo Environment configured for VS2022 debugging with virtual environment
echo ================================================================================
echo.
echo Virtual Environment: ACTIVATED
echo Python: %CD%\venv_musetalk\Scripts\python.exe
echo CUDA GPUs: 0,1,2,3
echo.
echo Now you can:
echo 1. Launch VS2022 from this command window: start devenv.exe LmyDigitalHuman.sln
echo 2. Or manually open VS2022 and the environment will be inherited
echo.
echo Press Enter to launch VS2022, or Ctrl+C to configure manually
pause

echo Launching Visual Studio 2022...
start devenv.exe LmyDigitalHuman.sln