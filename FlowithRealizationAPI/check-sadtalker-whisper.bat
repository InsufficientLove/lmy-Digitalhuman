@echo off
echo 检查SadTalker环境中的Whisper安装情况...
echo.

echo [1] 检查Python环境...
F:\AI\SadTalker\venv\Scripts\python.exe --version

echo.
echo [2] 检查是否已安装whisper...
F:\AI\SadTalker\venv\Scripts\python.exe -m pip show openai-whisper

echo.
echo [3] 测试whisper命令...
F:\AI\SadTalker\venv\Scripts\python.exe -m whisper --help

echo.
echo [4] 如果whisper未安装，运行以下命令安装：
echo F:\AI\SadTalker\venv\Scripts\python.exe -m pip install openai-whisper
echo.
pause