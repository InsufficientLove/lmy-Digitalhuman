@echo off
chcp 65001 >nul 2>&1
echo ========================================
echo Docker Installation Verification
echo ========================================
echo.

echo [1] Checking Docker Version...
docker --version 2>nul
if %errorLevel% equ 0 (
    echo ✅ Docker installed successfully
) else (
    echo ❌ Docker not found or not running
    echo Please ensure Docker Desktop is installed and running
    goto :error
)

echo.
echo [2] Checking Docker Compose...
docker-compose --version 2>nul
if %errorLevel% equ 0 (
    echo ✅ Docker Compose available
) else (
    echo ❌ Docker Compose not available
)

echo.
echo [3] Checking Docker Service...
docker info >nul 2>&1
if %errorLevel% equ 0 (
    echo ✅ Docker service is running
) else (
    echo ❌ Docker service not running
    echo Please start Docker Desktop
    goto :error
)

echo.
echo [4] Testing Docker with Hello World...
echo Running: docker run hello-world
docker run hello-world
if %errorLevel% equ 0 (
    echo ✅ Docker test successful
) else (
    echo ❌ Docker test failed
    goto :error
)

echo.
echo ========================================
echo ✅ Docker Installation Verified!
echo ========================================
echo.
echo Next Steps:
echo   1. Run: deploy-docker.bat
echo   2. Wait for build and startup
echo   3. Access: http://localhost:5000
echo.
goto :end

:error
echo.
echo ========================================
echo ❌ Docker Installation Issues Found
echo ========================================
echo.
echo Troubleshooting Steps:
echo   1. Ensure Hyper-V is enabled
echo   2. Restart Docker Desktop
echo   3. Run as Administrator
echo   4. Check Windows Updates
echo.

:end
pause