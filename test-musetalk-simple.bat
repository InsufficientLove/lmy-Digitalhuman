@echo off
chcp 65001 >nul
echo ================================================================================
echo                   Test MuseTalk Python Execution Fix
echo ================================================================================
echo.
echo This script will test the enhanced Python execution with error diagnosis
echo.
pause

echo Starting application with enhanced Python diagnostics...
echo.
echo Expected logs to watch for:
echo [INF] MuseTalk Python path: [detected path]
echo [INF] MuseTalk script path: [script path]
echo [INF] Execute Python command: [python path] [arguments]
echo [INF] Working directory: [working directory]
echo [INF] Python process exit code: [exit code]
echo [INF] Python standard output: [output]
echo [INF] Python error output: [errors]
echo.
echo If Python path detection fails:
echo [WRN] No valid Python path found, using default: python
echo.
echo If script file missing:
echo [ERR] MuseTalk script file not found: [script path]
echo.
echo If Python executable missing:
echo [ERR] Python executable not found: [python path]
echo.

cd LmyDigitalHuman
dotnet run

pause
