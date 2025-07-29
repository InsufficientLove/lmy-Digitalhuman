# 🤖 数字人系统 (LMY Digital Human)

一个基于 .NET 8.0 和 MuseTalk 的智能数字人对话系统，支持实时语音交互、文本转语音、数字人视频生成等功能。

## ✨ 主要功能

- 🎯 **实时语音对话** - 支持语音识别和实时响应
- 🗣️ **多语言TTS** - 基于 EdgeTTS 的高质量语音合成
- 🎭 **数字人生成** - 基于 MuseTalk 的数字人视频生成
- 🧠 **本地LLM集成** - 支持 Ollama 等本地大语言模型
- 📱 **Web界面** - 现代化的Web管理界面
- 🔄 **流式处理** - 支持实时流式音频和视频处理

## 🚀 快速开始

### 方法一：一键部署（推荐）

1. **下载项目**
   ```bash
   git clone https://github.com/InsufficientLove/lmy-Digitalhuman.git
   cd lmy-Digitalhuman
   ```

2. **运行一键环境配置**
   ```bash
   # Windows
   setup-environment.bat
   
   # Linux/macOS  
   ./setup-environment.sh
   ```

3. **启动系统**
   ```bash
   # 生产环境启动
   startup.bat          # Windows
   ./startup.sh         # Linux/macOS
   
   # 开发环境启动（支持热重载）
   dev-start.bat        # Windows
   ./dev-start.sh       # Linux/macOS
   ```

### 方法二：手动配置

#### 前置要求

- **.NET 8.0 SDK** - [下载地址](https://dotnet.microsoft.com/download/dotnet/8.0)
- **Python 3.8+** - [下载地址](https://www.python.org/downloads/)
- **Git** - [下载地址](https://git-scm.com/)
- **Visual Studio 2022** 或 **VS Code**（可选）

#### 安装步骤

1. **克隆仓库**
   ```bash
   git clone https://github.com/InsufficientLove/lmy-Digitalhuman.git
   cd lmy-Digitalhuman
   ```

2. **配置 Python 环境**
   ```bash
   # Windows
   setup-python-env.bat
   
   # Linux/macOS
   pip install torch torchvision torchaudio numpy opencv-python pillow scipy scikit-image librosa tqdm pydub requests
   ```

3. **还原 .NET 依赖**
   ```bash
   dotnet restore LmyDigitalHuman/LmyDigitalHuman.csproj
   ```

4. **编译项目**
   ```bash
   dotnet build LmyDigitalHuman/LmyDigitalHuman.csproj --configuration Release
   ```

5. **启动系统**
   ```bash
   cd LmyDigitalHuman
   dotnet run --urls "https://localhost:7001;http://localhost:5001"
   ```

## 📋 可用脚本

| 脚本名称 | 功能说明 | 适用平台 |
|---------|----------|----------|
| `setup-environment.bat` | 一键环境部署和配置 | Windows |
| `setup-python-env.bat` | Python环境专用配置 | Windows |
| `startup.bat` | 生产环境启动 | Windows |
| `dev-start.bat` | 开发环境启动（热重载） | Windows |
| `docker-start.bat` | Docker容器启动 | Windows |
| `fix-build-errors.bat` | 编译错误诊断和修复 | Windows |
| `startup.sh` | 生产环境启动 | Linux/macOS |
| `dev-start.sh` | 开发环境启动（热重载） | Linux/macOS |

## 🌐 访问地址

启动成功后，通过以下地址访问系统：

- **HTTPS**: https://localhost:7001
- **HTTP**: http://localhost:5001
- **Docker**: http://localhost:8080

## 🏗️ 项目结构

```
LmyDigitalHuman/
├── Controllers/              # Web API 控制器
│   ├── ConversationController.cs
│   ├── DigitalHumanTemplateController.cs
│   └── LocalLLMController.cs
├── Services/                 # 核心服务层
│   ├── AudioPipelineService.cs      # 音频处理管道
│   ├── ConversationService.cs       # 对话服务
│   ├── DigitalHumanTemplateService.cs # 数字人模板服务
│   ├── EdgeTTSService.cs           # TTS 服务
│   ├── MuseTalkService.cs          # MuseTalk 数字人生成
│   ├── OllamaService.cs            # 本地 LLM 服务
│   ├── StreamingTTSService.cs      # 流式 TTS
│   └── WhisperNetService.cs        # 语音识别服务
├── Models/                   # 数据模型
│   └── UnifiedModels.cs      # 统一模型定义
├── wwwroot/                  # 静态资源
└── appsettings.json         # 配置文件
```

## ⚙️ 配置说明

### 主要配置文件

- `appsettings.json` - 开发环境配置
- `appsettings.Production.json` - 生产环境配置

### 关键配置项

```json
{
  "RealtimeDigitalHuman": {
    "MaxConcurrentUsers": 200,
    "WhisperNet": {
      "ModelPath": "Models/ggml-base.bin",
      "ModelSize": "Base"
    },
    "MuseTalk": {
      "PythonPath": "python",
      "ScriptPath": "musetalk_service_complete.py"
    }
  },
  "Azure": {
    "Speech": {
      "Key": "your-azure-speech-key",
      "Region": "your-region"
    }
  }
}
```

## 🔧 开发指南

### 添加新功能

1. **创建服务接口** - 在 `Services/` 目录下定义接口
2. **实现服务类** - 实现具体的业务逻辑
3. **添加控制器** - 在 `Controllers/` 目录下创建 API 端点
4. **更新模型** - 在 `Models/UnifiedModels.cs` 中添加新的数据模型

### 调试技巧

1. **使用开发模式**
   ```bash
   dev-start.bat  # 支持热重载
   ```

2. **查看详细日志**
   ```bash
   dotnet run --verbosity diagnostic
   ```

3. **编译错误诊断**
   ```bash
   fix-build-errors.bat
   ```

## 🐛 故障排除

### 常见问题

1. **编译错误**
   - 运行 `fix-build-errors.bat` 进行诊断
   - 检查 .NET SDK 版本是否为 8.0+
   - 确保所有 NuGet 包已正确还原

2. **端口占用**
   - 修改 `appsettings.json` 中的端口配置
   - 或停止占用端口的其他应用程序

3. **Python 依赖问题**
   - 运行 `setup-python-env.bat` 重新配置
   - 确保 Python 版本为 3.8 或更高

4. **模型文件缺失**
   - 检查 `Models/` 目录下的 AI 模型文件
   - 按需下载 Whisper 模型文件

### 获取帮助

- 📖 查看 [启动指南](STARTUP_GUIDE.md)
- 📝 查看 [更新日志](CHANGELOG.md)
- 🐛 [提交问题](https://github.com/InsufficientLove/lmy-Digitalhuman/issues)

## 📊 性能特性

- ⚡ **高并发支持** - 支持200+用户同时在线
- 🎯 **低延迟响应** - 音频处理延迟 < 500ms
- 💾 **智能缓存** - 减少重复计算，提升响应速度
- 🔄 **流式处理** - 实时音频/视频流处理
- 📈 **水平扩展** - 支持分布式部署

## 🤝 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目基于 MIT 许可证开源 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [MuseTalk](https://github.com/TMElyralab/MuseTalk) - 数字人生成技术
- [Whisper.NET](https://github.com/sandrohanea/whisper.net) - 语音识别
- [EdgeTTS](https://github.com/rany2/edge-tts) - 文本转语音
- [Ollama](https://ollama.ai/) - 本地大语言模型

---

<p align="center">
  <b>🌟 如果这个项目对您有帮助，请给个 Star！</b>
</p>