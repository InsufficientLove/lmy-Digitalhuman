@echo off
echo ================================================================================
echo                    Fix Ollama Configuration Issue
echo ================================================================================
echo.
echo Current issue: Model name mismatch
echo - Code expects: qwen2.5:14b-instruct-q4_0
echo - Config has: qwen2.5vl:7b
echo - Need to check what's actually installed
echo.
pause

echo [1/5] Checking if Ollama is installed...
where ollama >nul 2>&1
if %errorlevel% equ 0 (
    echo SUCCESS: Ollama found
    ollama --version
) else (
    echo ERROR: Ollama not found
    echo Please install Ollama first:
    echo https://ollama.ai/download
    pause
    exit /b 1
)

echo.
echo [2/5] Starting Ollama service...
start /b ollama serve
timeout /t 3 /nobreak >nul

echo.
echo [3/5] Checking available models...
echo Available models:
ollama list
if %errorlevel% neq 0 (
    echo WARNING: Could not list models
)

echo.
echo [4/5] Testing qwen2.5vl:7b model...
curl -s -X POST http://localhost:11434/api/generate -H "Content-Type: application/json" -d "{\"model\":\"qwen2.5vl:7b\",\"prompt\":\"Hello\",\"stream\":false}" >nul 2>&1
if %errorlevel% equ 0 (
    echo SUCCESS: qwen2.5vl:7b is available
    set "WORKING_MODEL=qwen2.5vl:7b"
) else (
    echo WARNING: qwen2.5vl:7b not working, trying alternatives...
    
    REM Try common model names
    for %%m in ("qwen2.5:7b" "qwen2.5:14b" "qwen2.5:latest" "qwen:latest") do (
        echo Testing %%m...
        curl -s -X POST http://localhost:11434/api/generate -H "Content-Type: application/json" -d "{\"model\":%%m,\"prompt\":\"Hello\",\"stream\":false}" >nul 2>&1
        if !errorlevel! equ 0 (
            echo SUCCESS: %%m is available
            set "WORKING_MODEL=%%m"
            goto :found_model
        )
    )
    
    :found_model
    if not defined WORKING_MODEL (
        echo ERROR: No working model found
        echo Please install a model:
        echo ollama pull qwen2.5vl:7b
        pause
        exit /b 1
    )
)

echo.
echo [5/5] Updating configuration...
echo Working model: %WORKING_MODEL%

REM Update appsettings.json
powershell -Command "(Get-Content 'LmyDigitalHuman/appsettings.json') -replace '\"Model\": \".*\"', '\"Model\": \"%WORKING_MODEL%\"' | Set-Content 'LmyDigitalHuman/appsettings.json'"

REM Update appsettings.Production.json
if exist "LmyDigitalHuman/appsettings.Production.json" (
    powershell -Command "(Get-Content 'LmyDigitalHuman/appsettings.Production.json') -replace '\"DefaultModel\": \".*\"', '\"DefaultModel\": \"%WORKING_MODEL%\"' | Set-Content 'LmyDigitalHuman/appsettings.Production.json'"
)

echo.
echo ================================================================================
echo                           Fix Complete
echo ================================================================================
echo.
echo Configuration updated to use: %WORKING_MODEL%
echo.
echo Next steps:
echo 1. Restart your application
echo 2. Test text conversation
echo 3. Check logs for successful model loading
echo.
pause