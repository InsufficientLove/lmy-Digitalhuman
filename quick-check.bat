@echo off
chcp 65001 >nul 2>&1
echo ========================================
echo Quick Environment Check
echo ========================================
echo.

echo [Python Environment]
python --version 2>nul && echo ✅ Python OK || echo ❌ Python NOT FOUND
python -c "import edge_tts" 2>nul && echo ✅ edge_tts OK || echo ❌ edge_tts NOT FOUND
echo.

echo [Virtual Environment]  
if exist "venv_musetalk\Scripts\python.exe" (
    echo ✅ Virtual env exists
    venv_musetalk\Scripts\python.exe --version 2>nul
    venv_musetalk\Scripts\python.exe -c "import edge_tts" 2>nul && echo ✅ venv edge_tts OK || echo ❌ venv edge_tts FAILED
) else (
    echo ❌ Virtual env NOT FOUND
)
echo.

echo [.NET Environment]
dotnet --version 2>nul && echo ✅ .NET SDK OK || echo ❌ .NET SDK NOT FOUND
echo.

echo [Services]
curl -f http://localhost:11434/api/version >nul 2>&1 && echo ✅ Ollama Running || echo ❌ Ollama Not Running
docker --version >nul 2>&1 && echo ✅ Docker Available || echo ❌ Docker Not Available
echo.

echo [Project Files]
if exist "LmyDigitalHuman\LmyDigitalHuman.csproj" (echo ✅ Main project found) else (echo ❌ Main project NOT FOUND)
if exist "docker-compose.yml" (echo ✅ Docker config found) else (echo ❌ Docker config NOT FOUND)
echo.

echo ========================================
echo Check Complete
echo ========================================
echo.
echo Next Steps:
echo   1. VS Debug: Open solution in VS2022 and press F5
echo   2. Docker Deploy: run deploy-docker.bat
echo   3. Test API: http://localhost:5000/api/diagnostics/python-environments
echo.
pause