@echo off
echo ================================================================================
echo                   Test Template Creation Fix
echo ================================================================================
echo.
echo This script will test the template creation and image path fixes
echo.
pause

echo [1/4] Checking current templates directory...
if not exist "LmyDigitalHuman\wwwroot\templates" (
    echo Creating templates directory...
    mkdir "LmyDigitalHuman\wwwroot\templates"
) else (
    echo Templates directory exists
)

echo.
echo [2/4] Checking for default avatar...
if not exist "LmyDigitalHuman\wwwroot\images\default-avatar.svg" (
    echo WARNING: Default avatar not found
    echo This may cause template images to not display
) else (
    echo Default avatar found
)

echo.
echo [3/4] Listing current template files...
if exist "LmyDigitalHuman\wwwroot\templates\*.*" (
    echo Template files:
    dir "LmyDigitalHuman\wwwroot\templates" /b
) else (
    echo No template files found
)

echo.
echo [4/4] Testing application startup...
echo Starting application to test fixes...
echo Check the logs for:
echo - Template loading messages
echo - Image path resolution
echo - Edge-TTS functionality
echo.
echo Press Ctrl+C to stop the application when testing is complete
echo.

cd LmyDigitalHuman
dotnet run

echo.
echo ================================================================================
echo                           Test Complete
echo ================================================================================
echo.
echo Check the application logs for:
echo 1. Successful template loading
echo 2. Correct image path resolution  
echo 3. Edge-TTS audio generation
echo 4. Video generation (if SadTalker is configured)
echo.
pause