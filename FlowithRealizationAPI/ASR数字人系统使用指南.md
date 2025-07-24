# ASR 数字人系统使用指南

## 系统概述

本系统是一个完整的ASR（自动语音识别）数字人对话系统，集成了以下功能：

1. **语音识别（ASR）**：使用 Whisper 进行高精度语音转文本
2. **大语言模型（LLM）**：使用 Ollama 本地部署的 Qwen2.5 模型
3. **语音合成（TTS）**：使用 Edge TTS 进行流式语音合成
4. **数字人视频生成**：使用 SadTalker 生成逼真的数字人视频
5. **实时流式响应**：支持文本、语音、视频的流式生成和播放

## 系统架构

```
用户输入（语音/文本）
    ↓
语音识别（Whisper）
    ↓
大语言模型（Ollama/Qwen2.5）
    ↓
流式文本输出 → 流式TTS（Edge TTS）
    ↓                    ↓
实时文本显示        实时语音播放
    ↓
数字人视频生成（SadTalker）
    ↓
视频播放
```

## 功能特点

### 1. GPU 加速优化
- Whisper 支持 CPU/GPU 自动切换
- 配置文件中可设置 `UseGPU: true/false`
- 自动处理 CUDA 环境检测

### 2. 模板化数字人
- 支持上传自定义数字人头像
- 一次创建，多次使用
- 保存数字人模板供后续调用

### 3. 流式对话模式
- 实时显示 AI 回复文本
- 逐句生成语音并播放
- 同步生成数字人视频

### 4. 多种对话模式
- **普通模式**：完整生成后播放
- **流式模式**：实时生成和播放

## 使用步骤

### 1. 创建数字人模板

1. 访问系统主页：`https://localhost:7135/realtime-digital-human.html`
2. 点击"📤 上传头像"按钮
3. 填写模板信息：
   - 模板名称（必填）
   - 描述信息
   - 性别选择
   - 风格选择
4. 上传头像图片（建议 512x512 像素）
5. 点击"创建模板"

### 2. 选择对话模式

在设置面板中选择：
- **对话模式**：普通模式 或 流式模式（实时语音）
- **TTS语音**：选择喜欢的语音角色
- **启用AI对话**：
  - 启用：AI 智能回答问题
  - 禁用：原样播报输入文本

### 3. 开始对话

#### 文本输入方式：
1. 在文本框输入内容
2. 点击"发送消息"
3. 等待数字人视频生成并播放

#### 语音输入方式：
1. 切换到"🎤 语音输入"标签
2. 点击录音按钮开始录音
3. 再次点击停止录音
4. 系统自动识别语音并显示识别结果
5. 点击"发送识别内容"

### 4. 流式对话体验

启用流式模式后：
1. 输入问题后，AI 回复会实时显示
2. 每完成一句话，自动生成语音并播放
3. 同时生成数字人视频
4. 实现类似真人对话的体验

## 配置说明

### appsettings.json 配置项

```json
{
  "RealtimeDigitalHuman": {
    "Whisper": {
      "PythonPath": "F:/AI/SadTalker/venv/Scripts/python.exe",
      "Model": "base",
      "Language": "zh",
      "InitialPrompt": "这是一个对话场景。",
      "UseGPU": false,  // 设置为 true 启用 GPU 加速
      "TimeoutMs": 300000
    },
    "EdgeTTS": {
      "DefaultVoice": "zh-CN-XiaoxiaoNeural",
      "DefaultRate": "1.0",
      "DefaultPitch": "0Hz",
      "OutputPath": "/workspace/temp"
    },
    "SadTalker": {
      "Path": "F:/AI/SadTalker",
      "PythonPath": "F:/AI/SadTalker/venv/Scripts/python.exe",
      "DefaultQuality": "medium",
      "EnableGPU": true
    }
  },
  "Ollama": {
    "BaseUrl": "http://localhost:11434",
    "Model": "qwen2.5:14b-instruct-q4_0",
    "Temperature": 0.7,
    "Stream": true
  }
}
```

## 性能优化建议

### 1. GPU 加速
- 确保安装了 CUDA Toolkit（如需使用 GPU）
- Whisper 设置 `UseGPU: true`
- SadTalker 设置 `EnableGPU: true`

### 2. 模型选择
- Whisper 模型：
  - `tiny`：最快，精度较低
  - `base`：平衡选择（推荐）
  - `small/medium`：更高精度
  - `large`：最高精度，速度最慢

### 3. 视频质量
- `low`：640x480，生成最快
- `medium`：1280x720，平衡选择
- `high`：1920x1080，高质量
- `ultra`：2560x1440，最高质量

### 4. 响应模式
- `instant`：立即响应（< 1秒）
- `fast`：快速响应（1-3秒）
- `quality`：高质量（3-5秒）

## 常见问题

### 1. Whisper GPU 报错
**问题**：提示 "Failed to launch Triton kernels"
**解决**：
- 检查 CUDA 是否正确安装
- 设置 `UseGPU: false` 使用 CPU
- 安装正确版本的 PyTorch CUDA

### 2. Edge TTS 无法使用
**问题**：edge-tts 命令未找到
**解决**：
```bash
pip install edge-tts
# 或在虚拟环境中
F:\AI\SadTalker\venv\Scripts\pip.exe install edge-tts
```

### 3. 数字人视频生成失败
**问题**：SadTalker 生成视频失败
**解决**：
- 检查 SadTalker 环境是否正确配置
- 确保模型文件已下载
- 查看日志文件了解详细错误

### 4. 流式对话卡顿
**问题**：流式响应不流畅
**解决**：
- 检查网络连接
- 调整 LLM 模型大小
- 优化 TTS 生成参数

## API 端点说明

### 1. 语音识别
```
POST /api/RealtimeDigitalHuman/speech-to-text
Content-Type: multipart/form-data
参数: audioFile (音频文件)
```

### 2. 即时对话
```
POST /api/RealtimeDigitalHuman/instant-chat
Content-Type: application/json
{
  "text": "你好",
  "avatarId": "模板ID",
  "responseMode": "instant",
  "quality": "medium"
}
```

### 3. 流式对话
```
POST /api/RealtimeDigitalHuman/streaming-chat
Content-Type: application/json
{
  "text": "你好",
  "avatarId": "模板ID",
  "voice": "zh-CN-XiaoxiaoNeural",
  "model": "qwen2.5:14b-instruct-q4_0",
  "enableEmotion": true
}
```

### 4. 创建数字人
```
POST /api/RealtimeDigitalHuman/create-avatar
Content-Type: multipart/form-data
参数:
- ImageFile: 头像图片
- TemplateName: 模板名称
- Description: 描述
- Gender: 性别
- Style: 风格
```

## 部署建议

### 开发环境
```bash
# 启动服务
dotnet run

# 访问地址
https://localhost:7135
```

### 生产环境
1. 使用 HTTPS 证书
2. 配置反向代理（Nginx）
3. 启用日志记录
4. 设置定期清理临时文件
5. 监控系统资源使用

## 系统要求

### 最低配置
- CPU: 4核心
- 内存: 8GB
- 硬盘: 50GB
- 显卡: 无（CPU模式）

### 推荐配置
- CPU: 8核心
- 内存: 16GB
- 硬盘: 100GB SSD
- 显卡: NVIDIA RTX 3060 或更高

## 更新日志

### v1.0.0
- 实现基础 ASR 功能
- 集成 Whisper 语音识别
- 支持数字人模板管理
- 实现流式对话功能
- 集成 Edge TTS 语音合成
- 优化 GPU 加速支持