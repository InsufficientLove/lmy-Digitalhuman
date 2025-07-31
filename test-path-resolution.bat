@echo off
echo ================================================================================
echo                    Test Path Resolution Debug
echo ================================================================================
echo.
echo This script will test the enhanced path resolution with detailed logging
echo.
pause

echo Starting application with enhanced path debugging...
echo.
echo Expected logs to watch for:
echo [INF] 路径管理器初始化完成:
echo [INF]   ContentRoot: [actual path]
echo [INF]   Templates: [actual path]
echo [INF]   Temp: [actual path]
echo.
echo When testing conversation:
echo [INF] 路径解析结果:
echo [INF]   原始图片路径: /templates/xxx.jpg
echo [INF]   解析图片路径: [actual path]
echo [INF]   图片文件存在: True/False
echo.
echo If file not found, will try alternative paths:
echo [WRN] 图片文件不存在，尝试其他路径解析方式...
echo [INF]   尝试备用路径: [alternative path]
echo.

cd LmyDigitalHuman
dotnet run

pause
