# 🤖 本地化大模型+数字人系统

## 📋 项目简介

基于.NET 8的本地化大模型+真人数字人系统，实现**模板化数字人管理**、**本地大模型对话**和**真人效果视频生成**。

### ✨ 核心特性

- **🤖 本地大模型** - 基于Ollama的完全本地化部署
- **🎭 数字人模板** - 支持创建、管理、复用数字人模板
- **💬 智能对话** - 集成本地大模型的实时对话功能
- **🎤 语音交互** - 支持语音输入和数字人视频输出
- **⚡ 高性能缓存** - 三层响应策略，最快1秒内响应

## 🚀 快速开始

### 1. 环境准备
- .NET 8 SDK
- Python 3.8+
- Git 和 FFmpeg

### 2. 部署Ollama
```bash
# 安装Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 启动服务
ollama serve

# 下载模型
ollama pull qwen2.5:14b-instruct-q4_0
```

### 3. 部署SadTalker
```bash
# 克隆仓库
git clone https://github.com/OpenTalker/SadTalker.git
cd SadTalker

# 安装依赖
python -m venv venv
source venv/bin/activate
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
pip install -r requirements.txt

# 下载模型
python scripts/download_models.py
```

### 4. 启动应用
```bash
# 克隆项目
git clone <项目地址>
cd FlowithRealizationAPI

# 还原依赖
dotnet restore

# 创建目录
mkdir -p wwwroot/templates wwwroot/videos temp

# 启动应用
dotnet run --urls="http://localhost:5000"
```

## 📚 文档

- 📖 [完整实施指南](IMPLEMENTATION-GUIDE.md) - 详细的部署和配置说明

## 🔧 系统要求

- **操作系统**: Windows 10/11, Linux
- **运行时**: .NET 8 SDK
- **Python**: 3.8+ (用于SadTalker)
- **GPU**: NVIDIA GPU (推荐)
- **内存**: 8GB+ RAM
- **存储**: 20GB+ 可用空间

## 🛠️ 技术栈

- **后端**: .NET 8, ASP.NET Core WebAPI
- **大模型**: Ollama (Qwen2.5, Llama3.1, ChatGLM3)
- **数字人**: SadTalker (真人效果)
- **语音**: Whisper (识别) + Edge-TTS (合成)
- **缓存**: 内存缓存 + 文件缓存

## 📞 技术支持

如果您在使用过程中遇到问题，请：

1. 📋 查看[实施指南](IMPLEMENTATION-GUIDE.md)
2. 🔍 检查API健康状态: `http://localhost:5000/health`
3. 💬 提交GitHub Issue

---

**🎉 开始您的本地化AI数字人之旅！** 🚀 