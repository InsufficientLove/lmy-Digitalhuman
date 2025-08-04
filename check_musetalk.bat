@echo off
chcp 65001 > nul
echo.
echo ================================================
echo          MuseTalk目录结构检查工具
echo ================================================
echo.

cd /d "C:\Users\Administrator\Desktop\digitalhuman\lmy-Digitalhuman"

echo 当前目录: %CD%
echo.

REM 检查MuseTalk目录是否存在
if not exist "MuseTalk" (
    echo ❌ MuseTalk目录不存在！
    echo 路径: %CD%\MuseTalk
    echo.
    echo 请确保MuseTalk目录位于: C:\Users\Administrator\Desktop\digitalhuman\lmy-Digitalhuman\MuseTalk
    pause
    exit /b 1
)

echo ✅ MuseTalk目录存在
echo.

REM 检查虚拟环境
if exist "venv_musetalk\Scripts\python.exe" (
    echo ✅ 虚拟环境存在: venv_musetalk
    echo.
    echo 使用虚拟环境Python运行检查脚本...
    echo.
    venv_musetalk\Scripts\python.exe LmyDigitalHuman\check_musetalk_structure.py
) else (
    echo ❌ 虚拟环境不存在: venv_musetalk\Scripts\python.exe
    echo.
    echo 尝试使用系统Python...
    python LmyDigitalHuman\check_musetalk_structure.py
)

echo.
echo ================================================
echo                检查完成
echo ================================================
pause