@echo off
echo ================================================================================
echo                    Test MuseTalk Python Execution Fix
echo ================================================================================
echo.
echo This script will test the enhanced Python execution with error diagnosis
echo.
pause

echo Starting application with enhanced Python diagnostics...
echo.
echo Expected logs to watch for:
echo [INF] MuseTalk Python路径: [detected path]
echo [INF] MuseTalk脚本路径: [script path]
echo [INF] 执行Python命令: [python path] [arguments]
echo [INF] 工作目录: [working directory]
echo [INF] Python进程退出码: [exit code]
echo [INF] Python标准输出: [output]
echo [INF] Python错误输出: [errors]
echo.
echo If Python path detection fails:
echo [WRN] 未找到有效的Python路径，使用默认值: python
echo.
echo If script file missing:
echo [ERR] MuseTalk脚本文件不存在: [script path]
echo.
echo If Python executable missing:
echo [ERR] Python可执行文件不存在: [python path]
echo.

cd LmyDigitalHuman
dotnet run

pause
