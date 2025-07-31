# 🎯 数字人项目 - 官方MuseTalk集成

基于.NET 8和官方MuseTalk的数字人交互系统，支持语音对话和视频生成。

## ✨ 核心特性

- 🗣️ **Edge-TTS语音合成** - 微软Azure级别的语音质量
- 🧠 **Ollama本地LLM** - 支持qwen2.5vl:7b等模型
- 🎬 **官方MuseTalk** - 腾讯开源的顶级数字人技术
- 🌐 **Web界面** - 简洁易用的数字人交互界面
- ⚡ **多GPU支持** - 4x RTX4090优化配置

## 📋 环境要求

### ✅ 已验证兼容
- **Python**: 3.10.11 ✓
- **CUDA**: 12.1 ✓ (官方要求11.7+)
- **.NET**: 8.0
- **操作系统**: Windows 10/11

### 🔧 必需软件
- Git (用于下载MuseTalk)
- FFmpeg (MuseTalk依赖)
- Ollama (本地LLM服务)

## 🚀 快速开始

### 1️⃣ 一键环境安装
```bash
# 下载代码
git clone https://github.com/InsufficientLove/lmy-Digitalhuman.git
cd lmy-Digitalhuman

# 安装所有依赖和官方MuseTalk
setup-environment.bat
```

### 2️⃣ 启动开发环境
```bash
# 启动开发服务器
start-development.bat

# 访问: http://localhost:5001
```

### 3️⃣ 生产环境部署
```bash
# 部署到IIS
deploy-production-now.bat

# 访问: http://localhost/digitalhuman
```

## 🛠️ 项目结构

```
lmy-Digitalhuman/
├── 🔧 核心脚本
│   ├── setup-environment.bat       # 一键环境安装
│   ├── start-development.bat       # 开发启动
│   └── deploy-production-now.bat   # 生产部署
├── 🏗️ .NET项目
│   └── LmyDigitalHuman/
│       ├── Services/               # 核心服务层
│       ├── Controllers/            # Web API
│       ├── Models/                 # 数据模型
│       └── wwwroot/               # 静态资源
├── 🐍 Python环境
│   └── venv_musetalk/             # 虚拟环境
└── 🤖 官方MuseTalk
    └── MuseTalk/                  # 官方GitHub仓库
```

## 🎯 核心服务

### 🗣️ 语音合成 (Edge-TTS)
- 支持多种语音和语言
- 可调节语速和音调
- 高质量音频输出

### 🧠 大语言模型 (Ollama)
- 本地部署，数据安全
- 支持多种开源模型
- 快速响应，低延迟

### 🎬 数字人生成 (MuseTalk)
- 官方最新版本
- 高质量唇形同步
- 支持静态图片输入

## 📊 性能配置

### 🎮 单GPU模式 (演示)
```json
{
  "MuseTalk": {
    "BatchSize": 2,
    "UseFloat16": true,
    "Fps": 25
  }
}
```

### 🚀 4GPU模式 (商用)
```json
{
  "MuseTalk": {
    "BatchSize": 8,
    "UseFloat16": true,
    "Fps": 30,
    "GpuIds": "0,1,2,3"
  }
}
```

## 🔧 配置说明

### appsettings.json (开发环境)
```json
{
  "DigitalHuman": {
    "MuseTalk": {
      "PythonPath": "venv_musetalk/Scripts/python.exe"
    }
  },
  "Ollama": {
    "BaseUrl": "http://localhost:11434",
    "Timeout": 120
  }
}
```

### appsettings.Production.json (生产环境)
```json
{
  "DigitalHuman": {
    "MuseTalk": {
      "PythonPath": "C:/inetpub/wwwroot/digitalhuman/venv_musetalk/Scripts/python.exe"
    }
  }
}
```

## 🐛 常见问题

### Q: MuseTalk模型下载失败？
A: 手动下载到 `MuseTalk/models/` 目录

### Q: Python虚拟环境激活失败？
A: 确保Python 3.10+已正确安装

### Q: IIS部署后找不到Python？
A: 修改 `appsettings.Production.json` 中的绝对路径

### Q: CUDA版本兼容性？
A: 你的CUDA 12.1完全兼容官方要求的11.7+

## 🎉 更新日志

- **v2.0** - 集成官方MuseTalk，简化项目结构
- **v1.5** - 添加虚拟环境支持，优化路径管理
- **v1.0** - 初始版本，基础数字人功能

## 📄 许可证

MIT许可证 - 支持商用部署

---

**🚀 从环境安装到生产部署，三个脚本搞定一切！**