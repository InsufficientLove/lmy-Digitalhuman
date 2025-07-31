@echo off
chcp 65001 >nul
echo Starting MuseTalk with Virtual Environment - 4x GPU
echo.

echo Setting up environment variables...
set CUDA_VISIBLE_DEVICES=0,1,2,3
set PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512
set OMP_NUM_THREADS=8

echo Checking virtual environment...
cd LmyDigitalHuman
if not exist "venv_musetalk\Scripts\python.exe" (
    echo Virtual environment not found! Please run setup-musetalk-venv.bat first
    pause
    exit /b 1
)

echo Starting application...
dotnet run
pause
