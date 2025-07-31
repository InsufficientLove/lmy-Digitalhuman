@echo off
echo ================================================================================
echo                    Test Path Manager for VS Debug and IIS
echo ================================================================================
echo.
echo This script will test the new unified path management system
echo.
pause

echo [1/3] Checking current environment...
echo Current directory: %CD%
echo.
echo Environment detection:
if exist "LmyDigitalHuman\bin\Debug" (
    echo ✅ VS Debug environment detected
    set ENV_TYPE=VS_DEBUG
) else if exist "LmyDigitalHuman\bin\Release" (
    echo ✅ VS Release environment detected  
    set ENV_TYPE=VS_RELEASE
) else (
    echo ✅ IIS/Production environment detected
    set ENV_TYPE=IIS_PROD
)

echo Environment Type: %ENV_TYPE%
echo.

echo [2/3] Checking directory structure...
echo.
echo Expected paths (will be auto-created by PathManager):
echo   ContentRoot: Project root directory
echo   WebRoot: ContentRoot\wwwroot 
echo   Templates: WebRoot\templates
echo   Videos: WebRoot\videos
echo   Temp: ContentRoot\temp
echo   Models: ContentRoot\models
echo   Scripts: ContentRoot (for Python scripts)
echo.

echo Checking current structure:
if exist "LmyDigitalHuman\wwwroot" (
    echo ✅ wwwroot exists
    if exist "LmyDigitalHuman\wwwroot\templates" (
        echo ✅ templates exists
    ) else (
        echo ⚠️ templates missing (will be created)
    )
    if exist "LmyDigitalHuman\wwwroot\videos" (
        echo ✅ videos exists
    ) else (
        echo ⚠️ videos missing (will be created)
    )
) else (
    echo ❌ wwwroot missing - this is a problem!
)

if exist "LmyDigitalHuman\temp" (
    echo ✅ temp exists
) else (
    echo ⚠️ temp missing (will be created)
)

if exist "LmyDigitalHuman\models" (
    echo ✅ models exists
) else (
    echo ⚠️ models missing (will be created)
)

echo.
echo [3/3] Starting application with PathManager...
echo.
echo ================================================================================
echo                           Expected Behavior
echo ================================================================================
echo.
echo With PathManager, you should see these logs on startup:
echo.
echo [INF] 路径管理器初始化完成:
echo [INF]   ContentRoot: C:\workspace\LmyDigitalHuman (or actual path)
echo [INF]   WebRoot: C:\workspace\LmyDigitalHuman\wwwroot
echo [INF]   Templates: C:\workspace\LmyDigitalHuman\wwwroot\templates
echo [INF]   Videos: C:\workspace\LmyDigitalHuman\wwwroot\videos
echo [INF]   Temp: C:\workspace\LmyDigitalHuman\temp
echo [INF]   Models: C:\workspace\LmyDigitalHuman\models
echo [INF]   Scripts: C:\workspace\LmyDigitalHuman
echo.
echo Key benefits:
echo ✅ Works in VS Debug (ContentRoot = project directory)
echo ✅ Works in IIS (ContentRoot = deployment directory)
echo ✅ Automatic directory creation
echo ✅ Consistent path resolution across all services
echo ✅ Python scripts use absolute paths
echo ✅ Audio/video files use correct temp directories
echo.
echo Path resolution examples:
echo - "/templates/image.jpg" → WebRoot\templates\image.jpg
echo - "temp/audio.wav" → ContentRoot\temp\audio.wav
echo - Python script paths → ContentRoot\script.py
echo - Video output → WebRoot\videos\video.mp4
echo.
echo Testing steps:
echo 1. Check startup logs for path initialization
echo 2. Create a template (image upload)
echo 3. Test conversation (TTS file creation)
echo 4. Verify all paths work in both VS and IIS
echo.

cd LmyDigitalHuman
dotnet run

pause