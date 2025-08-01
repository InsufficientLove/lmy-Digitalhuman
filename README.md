# 🤖 数字人系统

基于AI技术的数字人对话系统，支持语音识别、自然语言处理和实时视频生成。

## ✨ 功能特性

- 🗣️ **Edge-TTS语音合成** - 高质量语音生成
- 🎤 **语音识别** - 支持实时语音输入  
- 🧠 **Ollama本地LLM** - 本地大语言模型支持
- 🎭 **数字人视频生成** - 唇形同步和面部表情
- 🌐 **Web界面** - 完整的测试和管理界面

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
├── LmyDigitalHuman/          # 主应用程序
│   ├── Controllers/          # API控制器
│   ├── Services/            # 业务服务
│   ├── wwwroot/             # 静态文件
│   └── digital-human-test.html  # 测试页面
├── docker-compose.yml       # Docker编排
├── Dockerfile              # Docker镜像

└── deploy-app.bat          # 应用部署脚本
```

## 🔧 开发模式

如果需要本地开发调试：

```cmd
# 在VS2022中打开解决方案
# 按F5启动调试
# 访问: http://localhost:5000/digital-human-test.html
```

## 📝 技术栈

- **后端**: ASP.NET Core 8.0
- **AI模型**: Ollama + MuseTalk + Edge-TTS
- **容器**: Docker + Docker Compose
- **前端**: HTML5 + JavaScript + WebRTC
- **实时通信**: SignalR

## 🆘 常见问题

**Q: Docker启动失败？**
A: 确保已关闭Hyper-V并重启服务器

**Q: 无法访问测试页面？**  
A: 检查容器是否正常运行：`docker-compose ps`

**Q: Python环境错误？**
A: 容器内已包含完整Python环境，无需额外配置

## 📄 许可证

MIT License