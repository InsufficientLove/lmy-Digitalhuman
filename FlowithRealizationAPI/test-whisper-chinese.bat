@echo off
echo 测试Whisper中文语言支持...
echo.

echo 检查支持的语言列表...
F:\AI\SadTalker\venv\Scripts\python.exe -c "import whisper; print('支持的语言:'); [print(f'{k}: {v}') for k, v in whisper.tokenizer.LANGUAGES.items() if 'chinese' in v.lower() or 'zh' in k.lower()]"

echo.
echo 当前配置测试：
echo Language: zh
echo Model: base

pause