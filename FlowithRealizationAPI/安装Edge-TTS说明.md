# Edge TTS 安装说明

Edge TTS 是微软提供的免费文本转语音服务，支持多种语言和语音。

## 安装步骤

### 1. 安装 Python（如果尚未安装）
确保已安装 Python 3.8 或更高版本。

### 2. 安装 edge-tts
在命令行中运行：

```bash
pip install edge-tts
```

或者在已激活的虚拟环境中：

```bash
# Windows
F:\AI\SadTalker\venv\Scripts\pip.exe install edge-tts

# Linux/Mac
/path/to/venv/bin/pip install edge-tts
```

### 3. 验证安装
运行以下命令验证安装：

```bash
edge-tts --help
```

应该显示 edge-tts 的帮助信息。

### 4. 测试语音合成
测试中文语音合成：

```bash
edge-tts --voice zh-CN-XiaoxiaoNeural --text "你好，我是晓晓" --write-media test.mp3
```

## 支持的中文语音

- **女声**：
  - zh-CN-XiaoxiaoNeural（晓晓-友好）
  - zh-CN-XiaoyiNeural（晓伊-专业）
  - zh-CN-XiaochenNeural（晓辰-活泼）
  - zh-CN-XiaohanNeural（晓涵-温柔）
  - zh-CN-XiaomoNeural（晓墨-成熟）
  - zh-CN-XiaoruiNeural（晓睿-知性）
  - zh-CN-XiaoshuangNeural（晓双-可爱）
  - zh-CN-XiaoxuanNeural（晓萱-温暖）
  - zh-CN-XiaoyouNeural（晓悠-舒缓）

- **男声**：
  - zh-CN-YunxiNeural（云希-专业）
  - zh-CN-YunyangNeural（云扬-阳光）
  - zh-CN-YunfengNeural（云枫-沉稳）
  - zh-CN-YunhaoNeural（云皓-活力）
  - zh-CN-YunjianNeural（云健-成熟）

## 故障排除

### 1. 命令未找到
如果运行 `edge-tts` 时提示命令未找到，请检查：
- Python Scripts 目录是否在 PATH 环境变量中
- 或使用完整路径运行：`python -m edge_tts`

### 2. 网络问题
Edge TTS 需要连接到微软服务器，请确保：
- 网络连接正常
- 防火墙未阻止连接
- 代理设置正确（如果使用代理）

### 3. 权限问题
如果遇到权限错误，请：
- 使用管理员权限运行
- 或安装到用户目录：`pip install --user edge-tts`

## 使用示例

### Python 代码使用
```python
import asyncio
import edge_tts

async def main():
    voice = "zh-CN-XiaoxiaoNeural"
    text = "你好，欢迎使用Edge TTS服务"
    output_file = "output.mp3"
    
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_file)

asyncio.run(main())
```

### 命令行使用
```bash
# 基本使用
edge-tts --voice zh-CN-XiaoxiaoNeural --text "你好世界" --write-media hello.mp3

# 调整语速
edge-tts --voice zh-CN-XiaoxiaoNeural --rate "+20%" --text "这是加快的语音" --write-media fast.mp3

# 调整音调
edge-tts --voice zh-CN-XiaoxiaoNeural --pitch "+5Hz" --text "这是高音调的语音" --write-media high.mp3

# 列出所有可用语音
edge-tts --list-voices
```

## 配置建议

在 `appsettings.json` 中已配置默认语音：

```json
"EdgeTTS": {
    "DefaultVoice": "zh-CN-XiaoxiaoNeural",
    "DefaultRate": "1.0",
    "DefaultPitch": "0Hz",
    "OutputPath": "/workspace/temp"
}
```

可根据需要修改默认配置。