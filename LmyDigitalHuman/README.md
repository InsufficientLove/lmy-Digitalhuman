# 🤖 数字人对话系统 (Digital Human Conversation System)

基于 .NET 8 和 MuseTalk 的高性能数字人对话系统，支持文本对话、语音对话和实时对话，提供完整的数字人模板管理和视频生成能力。

## ✨ 核心特性

### 🎯 主要功能
- **数字人模板管理**: 创建、编辑、删除和复用数字人模板
- **多模态对话**: 支持文本对话、音频对话和实时语音对话
- **高质量语音合成**: Edge-TTS + Azure Speech 双重保障
- **智能语音识别**: Whisper.NET 本地化部署
- **大模型集成**: 支持 Ollama 本地大模型
- **实时通信**: SignalR 支持实时音视频交互

### ⚡ 性能特点
- **高并发支持**: 200+ 并发用户，50+ 实时对话
- **低延迟响应**: 文本对话 < 3秒，语音对话 < 5秒
- **智能缓存**: 多级缓存策略，提升响应速度
- **资源优化**: 动态资源分配和负载均衡

## 🏗️ 技术架构

### 技术栈
- **后端框架**: ASP.NET Core 8.0
- **语音识别**: Whisper.NET (C# 原生)
- **语音合成**: Edge-TTS + Azure Speech Service
- **大语言模型**: Ollama + 本地模型
- **数字人生成**: MuseTalk (Python 集成)
- **实时通信**: SignalR
- **音频处理**: FFMpegCore + NAudio
- **缓存系统**: IMemoryCache + 文件缓存
- **日志系统**: Serilog

### 架构设计
```
┌─────────────────┬─────────────────┬─────────────────────────┐
│   Web界面       │   移动端APP     │    第三方集成           │
│ (H5/React)      │  (iOS/Android)  │   (API调用)             │
└─────────────────┴─────────────────┴─────────────────────────┘
                              │
                    ┌─────────┴─────────┐
                    │    API网关层       │
                    │  (ASP.NET Core)   │
                    └─────────┬─────────┘
                              │
┌─────────────────────────────┴─────────────────────────────┐
│                   应用服务层                               │
├─────────────┬─────────────┬─────────────┬─────────────────┤
│ 对话服务    │ 模板服务    │ 音频服务    │   MuseTalk服务  │
└─────────────┴─────────────┴─────────────┴─────────────────┘
```

## 🚀 快速开始

### 环境要求
- **.NET 8 SDK**: [下载地址](https://dotnet.microsoft.com/download)
- **Python 3.8+**: [下载地址](https://python.org/downloads)
- **FFmpeg**: [下载地址](https://ffmpeg.org/download.html)
- **内存**: 推荐 32GB 以上
- **存储**: 推荐 500GB SSD

### 一键启动

#### Windows
```bash
# 双击运行或命令行执行
startup.bat
```

#### Linux/Mac
```bash
# 添加执行权限并运行
chmod +x startup.sh
./startup.sh
```

### 手动启动
```bash
# 1. 安装 Python 依赖
pip install edge-tts torch torchvision torchaudio opencv-python

# 2. 恢复 .NET 包
dotnet restore

# 3. 构建项目
dotnet build -c Release

# 4. 运行项目
dotnet run -c Release
```

## 🌐 访问地址

启动成功后，您可以通过以下地址访问系统：

- **主服务**: https://localhost:7135
- **API 文档**: https://localhost:7135/swagger
- **测试页面**: https://localhost:7135/digital-human-test.html
- **健康检查**: https://localhost:7135/health

## 📖 API 文档

### 数字人模板管理
```http
GET    /api/templates              # 获取模板列表
POST   /api/templates              # 创建模板
GET    /api/templates/{id}         # 获取模板详情
PUT    /api/templates/{id}         # 更新模板
DELETE /api/templates/{id}         # 删除模板
```

### 对话接口
```http
POST   /api/conversation/text      # 文本对话
POST   /api/conversation/audio     # 语音对话
POST   /api/conversation/realtime  # 实时对话
GET    /api/conversation/{id}      # 获取对话状态
```

### 系统监控
```http
GET    /api/system/health          # 健康检查
GET    /api/system/metrics         # 性能指标
GET    /api/system/statistics      # 使用统计
```

## 🔧 配置说明

### 主要配置项 (appsettings.json)
```json
{
  "DigitalHuman": {
    "MaxConcurrentConversations": 200,    // 最大并发对话数
    "MaxRealtimeConversations": 50,       // 最大实时对话数
    "MaxVideoGeneration": 10,             // 最大视频生成并发数
    "CacheExpirationHours": 4,            // 缓存过期时间
    "MuseTalk": {
      "PythonPath": "python",             // Python 路径
      "ScriptPath": "./musetalk_service_complete.py",
      "TimeoutSeconds": 120               // 生成超时时间
    }
  },
  "AudioProcessing": {
    "MaxConcurrentJobs": 20,              // 音频处理并发数
    "SampleRate": 16000,                  // 采样率
    "Channels": 1                         // 声道数
  }
}
```

## 📁 项目结构

```
LmyDigitalHuman/
├── Controllers/                 # API 控制器
│   ├── ConversationController.cs
│   └── DigitalHumanTemplateController.cs
├── Services/                    # 业务服务
│   ├── ConversationService.cs
│   ├── DigitalHumanTemplateService.cs
│   ├── MuseTalkService.cs
│   ├── AudioPipelineService.cs
│   ├── WhisperNetService.cs
│   ├── EdgeTTSService.cs
│   └── OllamaService.cs
├── Models/                      # 数据模型
│   └── UnifiedModels.cs
├── wwwroot/                     # 静态文件
│   ├── digital-human-test.html
│   ├── videos/                  # 生成的视频
│   └── images/                  # 静态图片
├── temp/                        # 临时文件
├── musetalk_service_complete.py # MuseTalk Python 脚本
├── startup.bat                  # Windows 启动脚本
├── startup.sh                   # Linux/Mac 启动脚本
├── 架构设计方案.md              # 架构设计文档
├── 技术实现方案.md              # 技术实现文档
└── README.md                    # 项目说明
```

## 🎮 使用示例

### 创建数字人模板
```csharp
var request = new CreateTemplateRequest
{
    TemplateName = "AI助手小美",
    Description = "专业的AI客服助手",
    Gender = "female",
    Style = "professional",
    ImageFile = imageFile // IFormFile
};

var response = await templateService.CreateTemplateAsync(request);
```

### 文本对话
```csharp
var request = new TextConversationRequest
{
    TemplateId = "template-001",
    Text = "你好，请介绍一下你自己",
    Quality = "medium"
};

var response = await conversationService.ProcessTextConversationAsync(request);
```

### 实时对话 (SignalR)
```javascript
// 连接到 SignalR Hub
const connection = new signalR.HubConnectionBuilder()
    .withUrl("/conversationHub")
    .build();

// 开始实时对话
await connection.invoke("StartRealtimeConversation", "template-001");

// 发送音频数据
await connection.invoke("SendAudioChunk", conversationId, audioData, false);
```

## 📊 性能指标

### 基准性能
- **文本对话响应时间**: < 3秒
- **语音对话响应时间**: < 5秒
- **视频生成时间**: < 30秒
- **最大并发用户**: 200人
- **实时对话支持**: 50人
- **系统可用性**: 99.9%

### 资源使用
- **CPU 使用率**: < 80%
- **内存使用率**: < 85%
- **磁盘 IO**: < 70%

## 🔍 故障排除

### 常见问题

#### 1. Python 环境问题
```bash
# 检查 Python 版本
python --version

# 安装缺失依赖
pip install edge-tts torch opencv-python
```

#### 2. 端口占用
```bash
# 检查端口占用
netstat -ano | findstr :7135

# 修改端口配置
# 编辑 appsettings.json 中的 urls 配置
```

#### 3. 内存不足
- 增加系统内存到 32GB+
- 调整 appsettings.json 中的并发配置
- 启用磁盘缓存减少内存占用

## 📈 性能优化

### 系统级优化
- 使用 SSD 存储提升 IO 性能
- 配置足够的内存避免交换
- 使用多核 CPU 提升并发能力

### 应用级优化
- 启用缓存减少重复计算
- 调整并发参数适应硬件配置
- 使用 GPU 加速 AI 模型推理

## 🤝 贡献指南

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 📞 支持与反馈

如果您在使用过程中遇到问题或有改进建议，请通过以下方式联系我们：

- 提交 [Issue](https://github.com/your-repo/issues)
- 发送邮件至：support@example.com
- 加入技术交流群：[QQ群号]

## 🙏 致谢

感谢以下开源项目的支持：
- [MuseTalk](https://github.com/TMElyralab/MuseTalk) - 数字人生成
- [Whisper.NET](https://github.com/sandrohanea/whisper.net) - 语音识别
- [Edge-TTS](https://github.com/rany2/edge-tts) - 语音合成
- [Ollama](https://ollama.ai/) - 本地大模型
- [FFMpegCore](https://github.com/rosenbjerg/FFMpegCore) - 音频处理

---

⭐ 如果这个项目对您有帮助，请给我们一个星标！