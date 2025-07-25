# LmyDigitalHuman - 实时数字人系统

## 系统介绍
LmyDigitalHuman 是一个集成了语音识别、语音合成、大语言模型对话和数字人视频生成的实时交互系统。基于 SadTalker、Whisper、Edge-TTS 等技术，提供流畅的数字人对话体验。

## 主要功能
- **语音识别（ASR）**：基于 OpenAI Whisper，支持多语言识别
- **语音合成（TTS）**：基于 Edge-TTS，支持多种中文语音
- **数字人视频生成**：基于 SadTalker，支持实时唇形同步
- **大语言模型对话**：支持 Ollama/Qwen2.5 等模型
- **实时流式响应**：文本、音频、视频流式输出
- **模板管理**：支持自定义数字人形象

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
# 1. 运行环境安装脚本（Windows）
setup-python-env.bat

# 2. 运行环境检查工具
check-environment.bat

# 3. 修改配置文件 appsettings.json
# 设置正确的 Python 路径和 SadTalker 路径

# 4. 启动系统
dotnet run
```

### 访问界面
- 实时数字人：http://localhost:5000/realtime-digital-human.html
- 模板管理：http://localhost:5000/templates.html

## 系统要求

### 软件环境
- **操作系统**：Windows 10/11, Ubuntu 20.04+
- **.NET SDK**：8.0 或更高版本
- **Python**：3.8（与 SadTalker 兼容）
- **CUDA**：11.3（推荐，最佳兼容性）
- **显卡驱动**：NVIDIA 470.63+

### 硬件要求
- **GPU**：NVIDIA 显卡（至少 8GB 显存）
- **内存**：16GB 或以上
- **硬盘**：至少 20GB 可用空间

## 环境配置

### 1. Python 环境
所有组件使用同一个虚拟环境（SadTalker venv）：
```bash
# 创建虚拟环境
python -m venv sadtalker_venv

# 激活虚拟环境
# Windows: sadtalker_venv\Scripts\activate
# Linux: source sadtalker_venv/bin/activate

# 安装依赖
pip install torch==1.12.1+cu113 torchvision==0.13.1+cu113 torchaudio==0.12.1 --extra-index-url https://download.pytorch.org/whl/cu113
pip install -r requirements.txt
```

### 2. SadTalker 模型
下载预训练模型：
- [百度网盘](https://pan.baidu.com/s/1tb0pBh2vZO5YD5vRNe_ZXg)（提取码：sadt）
- [Google Drive](https://drive.google.com/drive/folders/1Wd88VDoLhVzYsQ30_qDVluQHjqQHrmYKr)

放置到对应目录：
- SadTalker 模型 → `checkpoints/`
- GFPGAN 模型 → `gfpgan/weights/`

### 3. 配置文件
修改 `appsettings.json`：
```json
{
  "RealtimeDigitalHuman": {
    "SadTalker": {
      "Path": "F:/AI/SadTalker",
      "PythonPath": "F:/AI/SadTalker/venv/Scripts/python.exe",
      "EnableGPU": true,
      "EnableEnhancer": false,  // 关闭增强器以提高速度
      "TimeoutSeconds": 120     // 超时时间（秒）
    }
  }
}
```

## API 端点

### 实时数字人
- `POST /api/RealtimeDigitalHuman/streaming-chat` - 流式对话
- `POST /api/RealtimeDigitalHuman/instant-chat` - 即时响应
- `POST /api/RealtimeDigitalHuman/create-avatar` - 创建数字人
- `GET /api/RealtimeDigitalHuman/avatars` - 获取头像列表

### 语音服务
- `GET /api/RealtimeDigitalHuman/voices` - 获取可用语音
- `POST /api/RealtimeDigitalHuman/tts-stream` - 流式语音合成

## 故障排除

### 常见问题

1. **Edge-TTS 找不到**
   - 确保在 SadTalker 虚拟环境中安装：`pip install edge-tts`
   
2. **PyTorch 未找到**
   - 检查配置的 Python 路径是否指向虚拟环境
   - 运行 `check-environment.bat` 检查环境

3. **CUDA 错误**
   - 确认安装 CUDA 11.3
   - 检查显卡驱动版本
   - 验证 PyTorch CUDA 支持：`python -c "import torch; print(torch.cuda.is_available())"`

4. **中文乱码**
   - 系统已配置 UTF-8 编码
   - 确保终端支持 UTF-8

5. **视频生成太慢**
   - 在配置中设置 `"EnableEnhancer": false` 禁用增强器
   - 首次运行需要加载模型，后续会更快
   - 检查 GPU 是否正常工作
   - 考虑调整 `TimeoutSeconds` 超时时间

### 环境检查
运行 `check-environment.bat` 可以检查：
- Python 环境和版本
- 所有依赖安装状态
- CUDA 和 GPU 支持
- SadTalker 模型文件

## 开发指南

### 项目结构
```
LmyDigitalHuman/
├── Controllers/        # API 控制器
├── Services/          # 业务逻辑服务
├── Models/            # 数据模型
├── wwwroot/           # 静态文件和前端
├── appsettings.json   # 配置文件
├── setup-python-env.bat # 环境安装脚本
└── check-environment.bat # 环境检查工具
```

### 远程调试
支持 VS Code 和 Visual Studio 远程调试：
1. 使用 Docker 开发容器
2. 通过 SSH 连接调试
3. 详见 `.vscode/launch.json` 配置

## 许可证
本项目基于 MIT 许可证开源。注意：
- SadTalker 有其自己的许可条款
- 商业使用请确认所有组件的许可证

## 联系方式
- GitHub: [InsufficientLove/lmy-Digitalhuman](https://github.com/InsufficientLove/lmy-Digitalhuman)
- Issues: 欢迎提交问题和建议