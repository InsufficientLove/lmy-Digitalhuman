@echo off
echo ================================================================================
echo                    Diagnose Ollama Timeout Issue
echo ================================================================================
echo.
echo Current issue: 30-second timeout when calling Ollama
echo This usually means:
echo 1. Ollama service not running
echo 2. Model not installed
echo 3. Model loading takes too long (first time)
echo.
pause

echo [1/7] Checking if Ollama is installed...
where ollama >nul 2>&1
if %errorlevel% equ 0 (
    echo SUCCESS: Ollama found
    ollama --version
) else (
    echo ERROR: Ollama not found
    echo Please install Ollama from: https://ollama.ai/download
    pause
    exit /b 1
)

echo.
echo [2/7] Checking Ollama service status...
curl -s http://localhost:11434/api/version >nul 2>&1
if %errorlevel% equ 0 (
    echo SUCCESS: Ollama service is running
    curl -s http://localhost:11434/api/version
) else (
    echo WARNING: Ollama service not responding
    echo Starting Ollama service...
    start /b ollama serve
    echo Waiting for service to start...
    timeout /t 10 /nobreak >nul
    
    REM Check again
    curl -s http://localhost:11434/api/version >nul 2>&1
    if %errorlevel% equ 0 (
        echo SUCCESS: Ollama service started
    ) else (
        echo ERROR: Failed to start Ollama service
        echo Please check if port 11434 is available
        pause
        exit /b 1
    )
)

echo.
echo [3/7] Listing installed models...
echo Available models:
ollama list
if %errorlevel% neq 0 (
    echo ERROR: Could not list models
)

echo.
echo [4/7] Checking if qwen2.5vl:7b is installed...
ollama list | findstr "qwen2.5vl:7b" >nul 2>&1
if %errorlevel% equ 0 (
    echo SUCCESS: qwen2.5vl:7b is installed
) else (
    echo WARNING: qwen2.5vl:7b not found
    echo Available alternatives:
    ollama list | findstr "qwen"
    
    echo.
    echo Do you want to install qwen2.5vl:7b? (This may take a while)
    echo Press Y to install, N to try with existing model
    choice /c YN /n
    if errorlevel 2 goto :skip_install
    
    echo Installing qwen2.5vl:7b (this may take 10-30 minutes)...
    ollama pull qwen2.5vl:7b
    if %errorlevel% equ 0 (
        echo SUCCESS: Model installed
    ) else (
        echo ERROR: Failed to install model
        pause
        exit /b 1
    )
)

:skip_install
echo.
echo [5/7] Testing model with simple prompt (60s timeout)...
echo This test may take 30-60 seconds for first load...
echo Testing qwen2.5vl:7b...

timeout 60 curl -X POST http://localhost:11434/api/generate ^
  -H "Content-Type: application/json" ^
  -d "{\"model\":\"qwen2.5vl:7b\",\"prompt\":\"Hello\",\"stream\":false}" 2>nul

if %errorlevel% equ 0 (
    echo SUCCESS: Model responded
) else (
    echo WARNING: Model test failed or timed out
    echo Trying alternative models...
    
    for %%m in ("qwen2.5:7b" "qwen2.5:latest" "qwen:latest" "llama3:latest") do (
        echo Testing %%m...
        ollama list | findstr "%%~m" >nul 2>&1
        if !errorlevel! equ 0 (
            timeout 30 curl -X POST http://localhost:11434/api/generate ^
              -H "Content-Type: application/json" ^
              -d "{\"model\":\"%%~m\",\"prompt\":\"Hello\",\"stream\":false}" >nul 2>&1
            if !errorlevel! equ 0 (
                echo SUCCESS: %%m works
                set "WORKING_MODEL=%%~m"
                goto :found_working
            )
        )
    )
    
    :found_working
    if defined WORKING_MODEL (
        echo Found working model: %WORKING_MODEL%
        echo Updating configuration...
        powershell -Command "(Get-Content 'LmyDigitalHuman/appsettings.json') -replace '\"Model\": \".*\"', '\"Model\": \"%WORKING_MODEL%\"' | Set-Content 'LmyDigitalHuman/appsettings.json'"
    )
)

echo.
echo [6/7] Checking system resources...
echo Memory usage:
wmic OS get TotalVisibleMemorySize,FreePhysicalMemory /format:list | find "="

echo.
echo GPU status (if available):
nvidia-smi --query-gpu=name,memory.used,memory.total --format=csv,noheader,nounits 2>nul
if %errorlevel% neq 0 (
    echo No NVIDIA GPU detected or nvidia-smi not available
)

echo.
echo [7/7] Recommendations...
echo.
echo Based on the diagnosis:
echo.
echo If model loading is slow:
echo - First model load can take 30-60 seconds
echo - Consider using a smaller model like qwen2.5:7b
echo - Ensure sufficient RAM (8GB+ recommended)
echo.
echo If timeout persists:
echo - Increase timeout in appsettings.json
echo - Use GPU acceleration if available
echo - Try a smaller model
echo.
echo Configuration suggestions:
echo - Timeout: 60-120 seconds for large models
echo - Model: qwen2.5:7b (smaller, faster) vs qwen2.5vl:7b (larger, slower)
echo.

echo ================================================================================
echo                           Diagnosis Complete
echo ================================================================================
echo.
echo Next steps:
echo 1. If model is working, restart your application
echo 2. If timeout persists, increase timeout in config
echo 3. Consider using a smaller/faster model
echo.
pause