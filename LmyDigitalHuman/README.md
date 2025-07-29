# 🤖 数字人系统 - 高并发AI数字人对话平台

## 📋 项目简介

基于 .NET 8 + MuseTalk 的高性能数字人对话系统，支持 **200人并发**，提供文本对话、语音对话和实时语音交互功能。

### ✨ 核心特性

- 🚀 **高并发**: 支持200人同时使用，50人实时对话
- 🎭 **多模态交互**: 文本、语音、实时语音对话
- 🎨 **数字人模板**: 可复用的数字人角色管理
- ⚡ **智能缓存**: 多级缓存策略，提升响应速度
- 🔧 **一键部署**: Windows/Linux 自动化启动脚本
- 📱 **可视化界面**: 完整的H5测试平台
- 🌐 **RESTful API**: 标准化接口，支持第三方集成

### 🛠️ 技术栈

- **后端**: .NET 8 Web API + SignalR
- **AI引擎**: MuseTalk (数字人生成)
- **语音识别**: Whisper.NET (C# 原生)
- **语音合成**: Edge TTS + Azure Speech
- **音频处理**: FFMpegCore + NAudio
- **队列管理**: System.Threading.Channels
- **缓存**: IMemoryCache + 文件缓存

## 🚀 快速开始

### 环境要求

- .NET 8 SDK
- Python 3.8+
- FFmpeg (推荐)
- Windows 10+ / Linux / macOS

### 一键启动

**Windows:**
```bash
startup.bat
```

**Linux/Mac:**
```bash
chmod +x startup.sh
./startup.sh
```

### 访问地址

启动成功后，访问以下地址：

- 🌐 **测试平台**: https://localhost:7135/digital-human-test.html
- 📚 **API文档**: https://localhost:7135/swagger
- ❤️ **健康检查**: https://localhost:7135/health

## 📖 功能说明

### 1. 文本对话
```http
POST /api/conversation/text
Content-Type: application/json

{
  "templateId": "template_001",
  "text": "你好，我是数字人助手",
  "emotion": "friendly",
  "quality": "medium"
}
```

### 2. 语音对话
```http
POST /api/conversation/audio
Content-Type: multipart/form-data

templateId: template_001
audioFile: [音频文件]
quality: medium
```

### 3. 实时对话
使用 SignalR WebSocket 连接 `/conversationHub` 进行实时语音交互。

### 4. 模板管理
```http
GET /api/digitalhumantemplate/list     # 获取模板列表
POST /api/digitalhumantemplate/create  # 创建新模板
```

## 🏗️ 项目结构

```
LmyDigitalHuman/
├── Controllers/           # API控制器
│   ├── ConversationController.cs
│   ├── DigitalHumanTemplateController.cs
│   └── LocalLLMController.cs
├── Services/             # 业务服务层
│   ├── ConversationService.cs
│   ├── AudioPipelineService.cs
│   ├── MuseTalkService.cs
│   └── ...
├── Models/              # 数据模型
├── wwwroot/            # 静态资源
│   └── digital-human-test.html
├── musetalk_service_complete.py  # MuseTalk Python服务
├── startup.bat         # Windows启动脚本
├── startup.sh          # Linux/Mac启动脚本
└── 架构设计方案.md      # 详细技术方案
```

## ⚡ 性能配置

系统支持高度可配置的并发参数（`appsettings.json`）：

```json
{
  "DigitalHuman": {
    "MaxConcurrentConversations": 200,
    "MaxRealtimeConversations": 50,
    "MaxAudioProcessing": 20,
    "MaxTTSProcessing": 15,
    "MaxVideoGeneration": 10
  }
}
```

## 🔧 开发指南

### 本地开发

```bash
# 恢复依赖
dotnet restore

# 运行项目
dotnet run

# 构建发布版本
dotnet build --configuration Release
```

### API集成

所有接口都提供标准的RESTful API，支持：
- JSON响应格式
- 统一错误处理
- 请求验证
- 异步处理
- 缓存支持

详细API文档请访问：https://localhost:7135/swagger

## 📊 监控与日志

- **实时监控**: 系统状态、并发数、处理时间
- **详细日志**: Serilog结构化日志
- **性能指标**: 缓存命中率、错误率统计
- **健康检查**: 服务可用性监控

## 🤝 技术支持

如遇问题，请提供：
1. 错误日志 (`logs/` 目录)
2. 系统环境信息
3. 复现步骤

## 📄 许可证

本项目仅供学习和研究使用。

---

**🌟 开始体验高性能数字人对话系统！**