@echo off
chcp 65001 > nul
echo.
echo ================================================
echo          MuseTalk目录结构修复工具
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
    echo 请先创建或下载MuseTalk目录
    pause
    exit /b 1
)

echo ✅ MuseTalk目录存在，开始检查和修复...
echo.

REM 使用虚拟环境Python运行修复脚本
if exist "venv_musetalk\Scripts\python.exe" (
    echo 使用虚拟环境Python...
    venv_musetalk\Scripts\python.exe fix_musetalk_structure.py
) else (
    echo 虚拟环境不存在，使用系统Python...
    python fix_musetalk_structure.py
)

echo.
echo ================================================
echo                修复完成
echo ================================================