# Edge TTS 安装故障排除

## 问题描述

当系统提示 `'edge-tts' 不是内部或外部命令` 时，说明 Edge TTS 没有正确安装或没有在系统 PATH 中。

## 解决方案

### 方案 1：在 SadTalker 虚拟环境中安装（推荐）

由于系统使用 SadTalker 的 Python 环境，建议在同一环境中安装 Edge TTS。

1. **使用自动安装脚本**
   ```bash
   install-edge-tts-to-sadtalker-env.bat
   ```

2. **手动安装**
   ```bash
   # 进入 SadTalker 虚拟环境
   F:\AI\SadTalker\venv\Scripts\activate
   
   # 安装 edge-tts
   pip install edge-tts
   
   # 验证安装
   edge-tts --help
   ```

### 方案 2：全局安装 Edge TTS

1. **使用系统 Python**
   ```bash
   pip install edge-tts
   ```

2. **确保 Scripts 目录在 PATH 中**
   - 找到 Python Scripts 目录（通常是 `C:\Users\用户名\AppData\Local\Programs\Python\Python3x\Scripts`）
   - 将该目录添加到系统环境变量 PATH 中
   - 重启命令行窗口

### 方案 3：使用绝对路径

如果安装后仍然无法找到命令，可以在配置文件中指定完整路径。

## 验证安装

### 1. 测试命令
```bash
# 直接测试
edge-tts --help

# 或通过 Python 测试
python -m edge_tts --help

# 生成测试音频
edge-tts --voice zh-CN-XiaoxiaoNeural --text "测试语音合成" --write-media test.mp3
```

### 2. 在代码中测试
```python
import edge_tts
import asyncio

async def test():
    communicate = edge_tts.Communicate("测试文本", "zh-CN-XiaoxiaoNeural")
    await communicate.save("test.mp3")

asyncio.run(test())
```

## 常见问题

### 1. 权限问题
- 使用管理员权限运行安装命令
- 或使用 `--user` 参数：`pip install --user edge-tts`

### 2. 代理问题
- 如果在公司网络，可能需要配置代理
- 使用国内镜像源：`pip install edge-tts -i https://pypi.tuna.tsinghua.edu.cn/simple`

### 3. Python 版本问题
- Edge TTS 需要 Python 3.7 或更高版本
- 检查版本：`python --version`

### 4. 依赖冲突
- 在虚拟环境中安装可以避免依赖冲突
- 如果有冲突，尝试：`pip install --upgrade edge-tts`

## 配置文件设置

在 `appsettings.json` 中，确保 Python 路径正确：

```json
{
  "RealtimeDigitalHuman": {
    "Whisper": {
      "PythonPath": "F:/AI/SadTalker/venv/Scripts/python.exe"
    }
  }
}
```

## 系统支持的执行方式

系统会自动尝试以下方式执行 Edge TTS：

1. 直接执行 `edge-tts` 命令
2. 使用 `python -m edge_tts`
3. 使用 `python3 -m edge_tts`
4. 使用配置文件中指定的 Python 路径

## 日志查看

如果仍有问题，查看日志文件 `logs/realtime-digital-human-*.log` 了解详细错误信息。

## 联系支持

如果以上方法都无法解决问题，请提供以下信息：
- Python 版本
- 操作系统版本
- 完整的错误日志
- `pip list` 的输出结果