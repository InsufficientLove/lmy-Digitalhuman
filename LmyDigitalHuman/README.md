# LmyDigitalHuman - 实时数字人系统

## 快速开始

### 1. 环境准备
```bash
# 运行环境安装脚本
setup-python-env.bat
```

### 2. 配置文件
修改 `appsettings.json` 中的路径配置：
- `SadTalker:Path` - SadTalker 安装路径
- `Whisper:PythonPath` - Python 解释器路径
- `Whisper:UseGPU` - 是否使用 GPU（已设置为 true）

### 3. 启动系统
```bash
dotnet run
```

### 4. 访问界面
- 实时数字人：https://localhost:7135/realtime-digital-human.html
- 模板管理：https://localhost:7135/templates.html

## 主要功能
- 语音识别（ASR）：基于 Whisper
- 语音合成（TTS）：基于 Edge-TTS
- 数字人视频生成：基于 SadTalker
- 大语言模型对话：基于 Ollama/Qwen2.5
- 实时流式响应

## 系统要求
- .NET 8.0 SDK
- Python 3.8+
- SadTalker 环境
- CUDA（可选，用于 GPU 加速）

## API 端点
- POST `/api/RealtimeDigitalHuman/streaming-chat` - 流式对话
- POST `/api/RealtimeDigitalHuman/create-avatar` - 创建数字人头像
- GET `/api/RealtimeDigitalHuman/voices` - 获取可用语音列表