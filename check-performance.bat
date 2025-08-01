@echo off
chcp 65001 >nul 2>&1
echo ========================================
echo 数字人系统 - 性能检查
echo ========================================
echo.

echo 检查虚拟环境激活状态...
if exist "venv_musetalk\Scripts\python.exe" (
    echo 测试虚拟环境Python:
    venv_musetalk\Scripts\python.exe --version
    venv_musetalk\Scripts\python.exe -c "import edge_tts; print('edge_tts: OK')" 2>nul || echo "edge_tts: 未安装"
    venv_musetalk\Scripts\python.exe -c "import torch; print(f'torch: {torch.__version__} GPU: {torch.cuda.is_available()}')" 2>nul || echo "torch: 未安装"
) else (
    echo 警告: venv_musetalk 不存在
)
echo.

echo 检查系统Python:
python --version 2>nul || echo "系统Python未找到"
python -c "import edge_tts; print('edge_tts: OK')" 2>nul || echo "系统Python缺少edge_tts"
echo.

echo 检查GPU状态:
nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total --format=csv,noheader,nounits 2>nul || echo "GPU信息获取失败"
echo.

echo 检查文件路径:
echo Templates目录: 
dir "LmyDigitalHuman\wwwroot\templates" /b 2>nul | findstr /i ".jpg .png" | head -3
echo.
echo Temp目录:
dir "LmyDigitalHuman\temp" /b 2>nul | head -3
echo.

echo 建议优化:
echo 1. 确保使用虚拟环境: venv_musetalk\Scripts\python.exe
echo 2. 检查GPU驱动和CUDA版本匹配
echo 3. 确保模板文件在正确位置
echo 4. 监控GPU利用率避免过载
echo.
pause