# LmyDigitalHuman - 实时数字人系统

## 快速开始

### 方式一：Docker 部署（推荐）

```bash
# 克隆项目
git clone https://github.com/InsufficientLove/lmy-Digitalhuman.git
cd lmy-Digitalhuman/LmyDigitalHuman

# 启动开发环境（支持热重载和远程调试）
docker-compose up lmy-digital-human-dev

# 或启动生产环境
docker-compose up -d lmy-digital-human
```

### 方式二：本地运行

```bash
# 运行环境安装脚本（Windows）
setup-python-env.bat

# 修改配置文件 appsettings.json
# 启动系统
dotnet run
```

### 访问界面
- 实时数字人：http://localhost:5000/realtime-digital-human.html
- 模板管理：http://localhost:5000/templates.html

## 主要功能
- 语音识别（ASR）：基于 Whisper
- 语音合成（TTS）：基于 Edge-TTS
- 数字人视频生成：基于 SadTalker
- 大语言模型对话：基于 Ollama/Qwen2.5
- 实时流式响应

## 系统要求
- .NET 8.0 SDK
- Python 3.8（与 SadTalker 兼容）
- CUDA 11.3（推荐，与 SadTalker 最佳兼容）
- SadTalker 环境（包含所有依赖）

## SadTalker 环境说明
本项目集成了完整的 SadTalker 环境，包括：
- PyTorch 1.12.1 + CUDA 11.3
- 所有 SadTalker 依赖（numpy==1.23.4, kornia==0.6.8 等）
- Edge-TTS 和 Whisper（在同一虚拟环境中）
- 预训练模型支持

## API 端点
- POST `/api/RealtimeDigitalHuman/streaming-chat` - 流式对话
- POST `/api/RealtimeDigitalHuman/create-avatar` - 创建数字人头像
- GET `/api/RealtimeDigitalHuman/voices` - 获取可用语音列表

## 远程调试

### VS Code
1. 安装 Remote-SSH 扩展
2. 连接到服务器：`ssh user@server`
3. 打开项目文件夹
4. F5 启动调试（使用 Docker 配置）

### Visual Studio
1. 调试 -> 附加到进程
2. 连接类型：Docker (Linux Container)
3. 选择容器和进程

详细说明请查看 [Remote-Debug-Guide.md](Remote-Debug-Guide.md)

## Docker 部署优势
- 无需手动安装 CUDA、Python 等依赖
- 环境一致性保证
- 支持 GPU 加速（自动检测）
- 便于横向扩展
- 隔离性好，不影响宿主机