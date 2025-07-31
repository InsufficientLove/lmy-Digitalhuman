@echo off
chcp 65001 >nul 2>&1
echo ================================================================================
echo                    数字人项目 - 开发环境启动
echo ================================================================================

echo 🔧 激活Python虚拟环境...
if not exist "venv_musetalk\Scripts\activate.bat" (
    echo ❌ 虚拟环境未找到！请先运行 setup-environment.bat
    pause
    exit /b 1
)

call venv_musetalk\Scripts\activate.bat

echo 🌟 设置GPU环境变量...
set CUDA_VISIBLE_DEVICES=0,1,2,3
set PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512
set OMP_NUM_THREADS=4

echo 🚀 启动.NET开发环境...
cd LmyDigitalHuman
dotnet run --environment Development

echo 开发环境已关闭
pause