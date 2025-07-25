# Python 环境执行问题修复

## 问题分析

从日志发现两个主要问题：

### 1. Edge-TTS 执行效率低
- 尝试了4种方式才成功执行
- 系统 Python 和 python3 都没有安装 edge-tts
- 只有 SadTalker 虚拟环境中安装了 edge-tts

### 2. SadTalker 执行失败
- 错误：`ModuleNotFoundError: No module named 'torch'`
- 原因：使用了系统默认的 `python` 命令，而不是 SadTalker 虚拟环境的 Python

## 解决方案

### 1. 统一使用配置的 Python 路径
所有服务都优先使用 `appsettings.json` 中配置的 Python 路径：
```json
"SadTalker": {
    "PythonPath": "F:/AI/SadTalker/venv/Scripts/python.exe"
}
```

### 2. 修改的文件

#### DigitalHumanTemplateService.cs
- **GenerateVideoWithSadTalkerAsync**: 使用配置的 Python 路径执行 SadTalker
- **TryExecuteEdgeTTSAsync**: 简化逻辑，优先使用配置的 Python 路径

#### EdgeTTSService.cs
- **RunEdgeTTSCommandAsync**: 使用 `python -m edge_tts` 而不是直接调用 `edge-tts`

#### RealtimeDigitalHumanService.cs
- **BuildEdgeTTSCommand**: 构建命令时包含 Python 路径

### 3. 环境检查工具
创建了 `check-environment.bat`，可以检查：
- Python 环境和版本
- Edge-TTS 安装状态
- PyTorch 和 CUDA 支持
- SadTalker 依赖
- 模型文件是否存在

## 使用建议

1. **运行环境检查**
   ```bash
   check-environment.bat
   ```

2. **确保所有依赖都在同一个虚拟环境**
   - SadTalker 虚拟环境应包含：PyTorch、Edge-TTS、Whisper 等所有依赖
   - 避免混用不同的 Python 环境

3. **配置文件设置**
   确保 `appsettings.json` 中的路径正确：
   - `SadTalker:PythonPath`: 指向 SadTalker 虚拟环境的 python.exe
   - `SadTalker:Path`: SadTalker 项目根目录

## 故障排除

如果仍有问题：
1. 检查 Python 路径是否正确
2. 确认虚拟环境已激活
3. 验证所有依赖都已安装
4. 查看详细的错误日志