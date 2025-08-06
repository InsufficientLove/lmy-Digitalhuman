@echo off
title Ultra Fast Digital Human System
echo.
echo ==========================================
echo 🚀 Ultra Fast Digital Human System
echo ==========================================
echo.

REM 设置环境变量
call set_ultra_fast_env.bat

REM 启动Ultra Fast Python服务
echo 🐍 启动Ultra Fast推理引擎...
cd /d MuseTalkEngine
start "Ultra Fast Service" python ultra_fast_realtime_inference_v2.py --port 28888

REM 等待Python服务启动
echo ⏳ 等待服务初始化...
timeout /t 10 /nobreak

REM 启动C#数字人服务
echo 🎭 启动数字人API服务...
cd /d LmyDigitalHuman
dotnet run

pause
