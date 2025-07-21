# Windows环境 Whisper 配置指南

## 🚀 快速解决方案

### 1. **运行安装脚本**
```powershell
# 使用PowerShell（推荐）
.\install-whisper-windows.ps1

# 或使用批处理
.\install-whisper-windows.bat
```

### 2. **手动安装步骤**
```cmd
# 1. 检查Python
F:\AI\Python\python.exe --version

# 2. 升级pip
F:\AI\Python\python.exe -m pip install --upgrade pip

# 3. 安装openai-whisper
F:\AI\Python\python.exe -m pip install openai-whisper

# 4. 验证安装
F:\AI\Python\python.exe -m whisper --help
```

## 🔧 配置文件设置

确认 `appsettings.json` 中的配置正确：
```json
{
  "RealtimeDigitalHuman": {
    "Whisper": {
      "PythonPath": "F:/AI/Python/python.exe",
      "Model": "base",
      "Language": "zh",
      "UseGPU": false,
      "MaxFileSize": 104857600,
      "EnableWordTimestamps": true,
      "Verbose": false,
      "TimeoutMs": 300000
    }
  }
}
```

## 📋 依赖检查清单

### ✅ Python环境
- [ ] Python 3.8+ 已安装
- [ ] Python路径正确：`F:\AI\Python\python.exe`
- [ ] pip工具正常工作

### ✅ Whisper包
- [ ] openai-whisper已安装
- [ ] 可以运行 `python -m whisper --help`

### ✅ FFmpeg（必需）
- [ ] FFmpeg已安装
- [ ] FFmpeg在系统PATH中，或者：
  - 下载：https://ffmpeg.org/download.html
  - 或使用：`winget install ffmpeg`

## 🐛 常见问题解决

### 问题1：`系统找不到指定的文件`
**原因**：whisper命令不在PATH中
**解决**：
```cmd
# 检查是否安装了openai-whisper
F:\AI\Python\python.exe -m pip show openai-whisper

# 如果没有安装
F:\AI\Python\python.exe -m pip install openai-whisper
```

### 问题2：`No module named whisper`
**原因**：Python环境中没有安装whisper模块
**解决**：
```cmd
F:\AI\Python\python.exe -m pip install openai-whisper
```

### 问题3：`python3 命令不存在`
**原因**：Windows下通常是python而不是python3
**解决**：配置文件已经使用正确的路径 `F:/AI/Python/python.exe`

### 问题4：`FFmpeg相关错误`
**原因**：缺少FFmpeg依赖
**解决**：
```cmd
# 方法1：使用winget
winget install ffmpeg

# 方法2：手动下载
# 从 https://ffmpeg.org/download.html 下载
# 解压并添加到系统PATH
```

## 🧪 测试验证

### 1. **基础测试**
```cmd
# 测试Python
F:\AI\Python\python.exe --version

# 测试Whisper模块
F:\AI\Python\python.exe -m whisper --help

# 测试FFmpeg
ffmpeg -version
```

### 2. **完整功能测试**
```cmd
# 创建测试音频（需要安装FFmpeg）
ffmpeg -f lavfi -i "sine=frequency=440:duration=3" -ar 16000 test.wav

# 测试Whisper转录
F:\AI\Python\python.exe -m whisper test.wav --model base --language zh
```

## 📁 目录结构

确保以下目录存在并可写：
```
F:\AICode\FlowithRealization\FlowithRealizationAPI\FlowithRealizationAPI\
├── temp\                    # 临时文件目录
├── wwwroot\videos\         # 输出视频目录
└── logs\                   # 日志目录
```

## ⚙️ 高级配置

### GPU加速（可选）
如果有NVIDIA GPU：
```json
{
  "Whisper": {
    "UseGPU": true
  }
}
```

### 自定义模型路径
```json
{
  "Whisper": {
    "ModelPath": "F:/AI/Models/Whisper"
  }
}
```

## 🆘 获取帮助

如果问题仍未解决：

1. **检查日志**：查看应用程序日志中的详细错误信息
2. **验证路径**：确认所有文件路径都存在且可访问
3. **权限检查**：确保应用程序有足够的文件系统权限
4. **网络连接**：首次运行时Whisper会下载模型文件

---

**更新时间**：2025年7月21日  
**适用环境**：Windows 10/11, Python 3.8+