@echo off
echo ================================================================================
echo                    Test MuseTalk Path Resolution Fix
echo ================================================================================
echo.
echo This script will test the MuseTalk path resolution fixes
echo.
pause

echo [1/4] Checking current directory structure...
echo Current directory: %CD%
echo.
echo Checking wwwroot structure:
if exist "LmyDigitalHuman\wwwroot" (
    echo ✅ wwwroot directory exists
    if exist "LmyDigitalHuman\wwwroot\templates" (
        echo ✅ templates directory exists
        echo Templates found:
        dir "LmyDigitalHuman\wwwroot\templates\*.jpg" /b 2>nul
        dir "LmyDigitalHuman\wwwroot\templates\*.png" /b 2>nul
    ) else (
        echo ❌ templates directory missing
    )
    
    if exist "LmyDigitalHuman\wwwroot\temp" (
        echo ✅ temp directory exists
    ) else (
        echo ⚠️ temp directory missing (will be created automatically)
        mkdir "LmyDigitalHuman\wwwroot\temp" 2>nul
    )
) else (
    echo ❌ wwwroot directory missing
)

echo.
echo [2/4] Checking template files...
if exist "LmyDigitalHuman\wwwroot\templates\*.json" (
    echo JSON template files:
    for %%f in ("LmyDigitalHuman\wwwroot\templates\*.json") do (
        echo   - %%~nxf
    )
) else (
    echo ⚠️ No JSON template files found
)

echo.
echo [3/4] Testing path resolution scenarios...
echo.
echo The MuseTalk service will now handle these path formats:
echo.
echo 1. Web paths: "/templates/image.jpg" 
echo    → Resolves to: %CD%\LmyDigitalHuman\wwwroot\templates\image.jpg
echo.
echo 2. Relative paths: "templates/image.jpg"
echo    → Resolves to: %CD%\LmyDigitalHuman\wwwroot\templates\image.jpg  
echo.
echo 3. Direct filenames: "image.jpg"
echo    → Searches in: %CD%\LmyDigitalHuman\wwwroot\templates\image.jpg
echo.
echo 4. Audio paths: "/temp/audio.wav"
echo    → Resolves to: %CD%\LmyDigitalHuman\temp\audio.wav
echo.
echo 5. Absolute paths: "C:\full\path\file.jpg"
echo    → Uses as-is: C:\full\path\file.jpg
echo.

echo [4/4] Starting application to test path resolution...
echo.
echo ================================================================================
echo                           Expected Behavior
echo ================================================================================
echo.
echo With the path resolution fix, you should see:
echo.
echo ✅ BEFORE (Error):
echo [ERR] 头像图片不存在: /templates/image.jpg
echo.
echo ✅ AFTER (Success):  
echo [INF] 开始生成数字人视频: Avatar=/templates/image.jpg, Audio=temp/audio.wav
echo [INF] 头像图片路径解析: /templates/image.jpg → C:\workspace\LmyDigitalHuman\wwwroot\templates\image.jpg
echo [INF] 音频文件路径解析: temp/audio.wav → C:\workspace\LmyDigitalHuman\temp\audio.wav
echo [INF] MuseTalk处理开始...
echo.
echo Key improvements:
echo - Web paths (/templates/xxx) correctly resolve to wwwroot/templates/xxx
echo - Relative paths work with proper directory resolution
echo - Direct filenames search in templates directory
echo - Audio paths correctly resolve to temp directory
echo - Detailed error messages show both original and resolved paths
echo.
echo Testing steps:
echo 1. Select a template (should work now)
echo 2. Type a message to trigger TTS
echo 3. Check logs for proper path resolution
echo 4. Verify video generation starts without path errors
echo.

cd LmyDigitalHuman
dotnet run

pause