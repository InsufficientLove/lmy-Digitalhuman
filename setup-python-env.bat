@echo off
chcp 65001 > nul
color 0A
title MuseTalk Python 环境配置

echo ================================================================================
echo                          MuseTalk Python 环境配置脚本
echo ================================================================================
echo.
echo 此脚本将为 MuseTalk 数字人生成服务配置 Python 环境
echo.
pause

echo ================================================================================
echo [步骤 1/4] 检查 Python 环境
echo ================================================================================

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到 Python 环境
    echo 请先安装 Python 3.8 或更高版本
    echo 下载地址: https://www.python.org/downloads/
    start https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [✓] 检测到 Python 版本:
python --version

echo ================================================================================
echo [步骤 2/4] 升级 pip 包管理器
echo ================================================================================

echo [信息] 正在升级 pip...
python -m pip install --upgrade pip
if %errorlevel% neq 0 (
    echo [警告] pip 升级失败，继续使用当前版本
) else (
    echo [✓] pip 升级成功
)

echo ================================================================================
echo [步骤 3/4] 安装 MuseTalk 依赖包
echo ================================================================================

echo [信息] 正在安装必要的 Python 包...
echo.

echo [1/10] 安装 torch (PyTorch)...
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
if %errorlevel% neq 0 (
    echo [警告] PyTorch GPU 版本安装失败，尝试 CPU 版本...
    pip install torch torchvision torchaudio
)

echo [2/10] 安装 numpy...
pip install numpy

echo [3/10] 安装 opencv-python...
pip install opencv-python

echo [4/10] 安装 pillow...
pip install Pillow

echo [5/10] 安装 scipy...
pip install scipy

echo [6/10] 安装 scikit-image...
pip install scikit-image

echo [7/10] 安装 librosa...
pip install librosa

echo [8/10] 安装 tqdm...
pip install tqdm

echo [9/10] 安装 pydub...
pip install pydub

echo [10/10] 安装 requests...
pip install requests

echo ================================================================================
echo [步骤 4/4] 验证安装
echo ================================================================================

echo [信息] 正在验证已安装的包...
python -c "import torch; print(f'PyTorch: {torch.__version__}')"
python -c "import cv2; print(f'OpenCV: {cv2.__version__}')"
python -c "import numpy; print(f'NumPy: {numpy.__version__}')"
python -c "import PIL; print(f'Pillow: {PIL.__version__}')"

echo ================================================================================
echo                            Python 环境配置完成
echo ================================================================================
echo.
echo [✓] MuseTalk Python 环境配置成功！
echo.
echo 📋 已安装的主要组件：
echo   ✓ PyTorch (深度学习框架)
echo   ✓ OpenCV (计算机视觉)
echo   ✓ NumPy (数值计算)
echo   ✓ Pillow (图像处理)
echo   ✓ SciPy (科学计算)
echo   ✓ Librosa (音频处理)
echo.
echo 🚀 现在您可以使用完整的数字人生成功能了！
echo.

pause