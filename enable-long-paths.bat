@echo off
echo ================================================================================
echo                    Enable Windows Long Path Support
echo ================================================================================
echo.
echo This script will enable Windows Long Path support to fix flash-attn installation
echo.
echo WARNING: This requires Administrator privileges
echo.
pause

echo Checking if running as Administrator...
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ This script must be run as Administrator
    echo Right-click this file and select "Run as administrator"
    pause
    exit /b 1
)

echo ✅ Running as Administrator

echo.
echo Enabling Long Path support in Windows Registry...
reg add "HKLM\SYSTEM\CurrentControlSet\Control\FileSystem" /v LongPathsEnabled /t REG_DWORD /d 1 /f

if %errorlevel% equ 0 (
    echo ✅ Long Path support enabled successfully
    echo.
    echo Please restart your computer for changes to take effect
    echo.
    echo After restart, you can run setup-musetalk-fixed.bat again
) else (
    echo ❌ Failed to enable Long Path support
)

echo.
pause
