@echo off
chcp 65001 >nul 2>&1
echo ================================================================================
echo                   Test Virtual Environment Python Path
echo ================================================================================
echo.
echo This script will test the Python path resolution for virtual environment
echo.
pause

echo [1/3] Checking virtual environment Python path...
cd LmyDigitalHuman
set VENV_PYTHON=%CD%\venv_musetalk\Scripts\python.exe
echo Expected path: %VENV_PYTHON%

if exist "venv_musetalk\Scripts\python.exe" (
    echo ✅ Virtual environment Python found
    echo Testing Python execution...
    venv_musetalk\Scripts\python.exe --version
    if %errorlevel% equ 0 (
        echo ✅ Virtual environment Python works
    ) else (
        echo ❌ Virtual environment Python failed
    )
) else (
    echo ❌ Virtual environment Python not found
    echo Please run setup-musetalk-basic.bat first
    pause
    exit /b 1
)

echo.
echo [2/3] Testing dependency imports in virtual environment...
venv_musetalk\Scripts\python.exe -c "
import sys
print('Python executable:', sys.executable)
print('Virtual environment:', hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix))

# Test critical imports
packages = ['torch', 'cv2', 'numpy', 'PIL', 'librosa']
for pkg in packages:
    try:
        __import__(pkg)
        print(f'✅ {pkg} import successful')
    except ImportError as e:
        print(f'❌ {pkg} import failed: {e}')
"

echo.
echo [3/3] Starting application with enhanced logging...
echo.
echo Expected logs to watch for:
echo [INF] 检查配置的Python路径: venv_musetalk/Scripts/python.exe → [absolute path]
echo [INF] 使用配置的Python路径: [absolute path]
echo [INF] MuseTalk Python路径: [absolute path]
echo.
echo If you see these logs, the virtual environment is being used correctly.
echo.

echo 如果要启动应用请手动运行: dotnet run
echo 或使用: start-with-venv.bat

echo.
echo ================================================================================
echo 测试完成
echo ================================================================================
pause
