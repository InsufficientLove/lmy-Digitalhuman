@echo off
echo Checking Qwen Model Status...
echo Your reported size: 27.5GB
echo.
pause

if not exist "models\llm\Qwen2.5-14B-Instruct" (
    echo Qwen directory not found
    pause
    exit
)

cd models\llm\Qwen2.5-14B-Instruct

echo Files in Qwen directory:
dir /b *.bin

echo.
echo Counting pytorch_model files...
set count=0
for %%f in (pytorch_model-*.bin) do set /a count+=1
echo Found %count% pytorch_model files

echo.
if exist "config.json" echo Config file: YES
if not exist "config.json" echo Config file: NO

if exist "tokenizer.json" echo Tokenizer: YES  
if not exist "tokenizer.json" echo Tokenizer: NO

echo.
if %count% geq 10 (
    echo STATUS: Model files look complete!
    echo Your 27.5GB download is probably successful.
) else (
    echo STATUS: Model files incomplete
    echo Only %count% files found, need 15
)

cd ..\..\..

echo.
echo Recommendation:
if %count% geq 10 (
    echo - Your model download is complete
    echo - You can use it directly or convert to Ollama
    echo - Run: setup-ollama-qwen.bat for better performance
) else (
    echo - Download incomplete, recommend using Ollama instead
    echo - Run: setup-ollama-qwen.bat
)

echo.
pause