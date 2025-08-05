# 🤖 数字人系统 - Enhanced MuseTalk V4

基于AI技术的数字人对话系统，集成增强版MuseTalk V4系统，支持超高速实时推理和面部特征预计算。

## ✨ 功能特性

- 🗣️ **Edge-TTS语音合成** - 高质量语音生成
- 🎤 **语音识别** - 支持实时语音输入  
- 🧠 **Ollama本地LLM** - 本地大语言模型支持
- 🎭 **数字人视频生成** - 唇形同步和面部表情
- 🌐 **Web界面** - 完整的测试和管理界面
- ⚡ **V4增强推理** - 30fps+ 超高速实时推理

## 🆕 Enhanced MuseTalk V4 系统

### 核心优化

基于MuseTalk官方实时推理机制的深入分析，V4系统实现了：

- **🧠 面部特征预计算**：VAE编码、坐标、掩码等预先计算并缓存
- **⚡ 超高速实时推理**：推理过程只涉及UNet和VAE解码器
- **💾 智能缓存机制**：持久化预处理结果，支持重复使用
- **🔄 完全兼容**：与现有C#服务完全兼容，无缝升级

### 性能对比

| 操作阶段 | 传统方式 | V4增强系统 | 优化效果 |
|---------|----------|-----------|----------|
| 面部检测 | 每次推理 | 预处理一次 | ✅ 消除重复 |
| VAE编码 | 每次推理 | 预处理一次 | ✅ 消除重复 |
| 面部解析 | 每次推理 | 预处理一次 | ✅ 消除重复 |
| UNet推理 | 每次推理 | 每次推理 | ⚡ 批处理优化 |
| VAE解码 | 每次推理 | 每次推理 | ⚡ 半精度优化 |
| 总体速度 | 10-15fps | **30fps+** | **2-3倍提升** |

## 🚀 快速部署 (Docker)

### 前置要求
- Windows Server 2019+
- 8GB+ RAM
- Docker Engine

### 安装步骤

1. **手动安装Docker Engine**

**步骤1: 关闭Hyper-V（如果需要）**
```cmd
# 以管理员身份运行PowerShell
Disable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V-All -NoRestart
# 重启服务器
```

**步骤2: 启用容器功能**
```cmd
# 以管理员身份运行PowerShell
Enable-WindowsOptionalFeature -Online -FeatureName Containers -All -NoRestart
```

**步骤3: 安装Chocolatey**
```cmd
# 以管理员身份运行PowerShell
Set-ExecutionPolicy Bypass -Scope Process -Force
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
```

**步骤4: 安装Docker和Docker Compose**
```cmd
choco install docker-engine -y
choco install docker-compose -y
```

**步骤5: 启动Docker服务**
```cmd
Start-Service docker
Set-Service docker -StartupType Automatic
```

2. **部署应用**
```cmd
# 克隆代码
git clone https://github.com/InsufficientLove/lmy-Digitalhuman.git
cd lmy-Digitalhuman

# 部署
deploy-app.bat
```

3. **访问系统**
- 测试界面: http://localhost:5000/digital-human-test.html
- API文档: http://localhost:5000/swagger
- 主页: http://localhost:5000

## 🛠️ 管理命令

```cmd
# 查看日志
docker-compose logs -f

# 停止服务  
docker-compose down

# 重启服务
docker-compose restart

# 查看状态
docker-compose ps
```

## 📁 项目结构

```
lmy-Digitalhuman/
├── LmyDigitalHuman/                      # 主应用程序
│   ├── Controllers/                      # API控制器
│   ├── Services/                        # 业务服务
│   ├── wwwroot/                         # 静态文件
│   └── digital-human-test.html          # 测试页面
├── enhanced_musetalk_inference_v4.py    # V4增强推理脚本（主要接口）
├── enhanced_musetalk_preprocessing.py   # 增强预处理系统
├── ultra_fast_realtime_inference.py     # 超高速实时推理系统
├── integrated_musetalk_service.py       # 集成服务接口
├── optimized_musetalk_inference_v3.py   # V3版本（已修复，向后兼容）
├── ENHANCED_MUSETALK_GUIDE.md          # 增强系统使用指南
├── docker-compose.yml                   # Docker编排
├── Dockerfile                          # Docker镜像
└── deploy-app.bat                      # 应用部署脚本
```

## 🎯 V4系统使用

### 自动模式（推荐）
V4系统具有智能缓存检测，首次使用会自动创建预处理缓存：

```bash
# C#服务会自动调用V4脚本
python enhanced_musetalk_inference_v4.py \
    --template_id "xiaoha" \
    --audio_path "./audio/test.wav" \
    --output_path "./output/result.mp4"
```

### 手动预处理（可选）
如需手动管理缓存：

```bash
# 预处理模板
python integrated_musetalk_service.py \
    --preprocess \
    --template_id "xiaoha" \
    --template_image_path "./wwwroot/templates/xiaoha.jpg"

# 超高速推理
python integrated_musetalk_service.py \
    --inference \
    --template_id "xiaoha" \
    --audio_path "./audio/test.wav" \
    --output_path "./output/result.mp4"
```

更多详细信息请参考：[ENHANCED_MUSETALK_GUIDE.md](ENHANCED_MUSETALK_GUIDE.md)

## 🔧 开发模式

如果需要本地开发调试：

```cmd
# 在VS2022中打开解决方案
# 按F5启动调试
# 访问: http://localhost:5000/digital-human-test.html
```

## 📝 技术栈

- **后端**: ASP.NET Core 8.0
- **AI模型**: Enhanced MuseTalk V4 + Ollama + Edge-TTS
- **推理引擎**: PyTorch + VAE + UNet + Whisper
- **容器**: Docker + Docker Compose
- **前端**: HTML5 + JavaScript + WebRTC
- **实时通信**: SignalR

## 🆘 常见问题

**Q: V4系统性能如何？**
A: 相比传统方式提升2-3倍，理论可达30fps+，首次运行会自动创建缓存

**Q: 与旧版本兼容吗？**  
A: 完全兼容，V4系统会自动检测并回退到兼容模式

**Q: Docker启动失败？**
A: 确保已关闭Hyper-V并重启服务器

**Q: 无法访问测试页面？**  
A: 检查容器是否正常运行：`docker-compose ps`

**Q: Python环境错误？**
A: 容器内已包含完整Python环境，无需额外配置

## 📄 许可证

MIT License