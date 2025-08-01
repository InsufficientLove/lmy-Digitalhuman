@echo off
echo 测试Python环境和edge-tts包...
echo.

echo [1] 测试系统Python:
python --version
python -c "import edge_tts; print('✅ edge_tts导入成功')"
echo.

echo [2] 测试虚拟环境Python:
venv_musetalk\Scripts\python.exe --version
venv_musetalk\Scripts\python.exe -c "import edge_tts; print('✅ edge_tts导入成功')"
echo.

echo [3] 测试相对路径解析:
echo 当前目录: %cd%
echo 虚拟环境路径: %cd%\venv_musetalk\Scripts\python.exe
if exist "venv_musetalk\Scripts\python.exe" (
    echo ✅ 虚拟环境Python存在
) else (
    echo ❌ 虚拟环境Python不存在
)

pause