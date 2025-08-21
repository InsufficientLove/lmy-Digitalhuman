# 数字人伪实时对话实施方案

## 系统架构

### 核心组件
1. **C#服务端（主控）**: ASR + LLM + TTS + 业务逻辑
2. **Python服务（加速）**: MuseTalk推理加速
3. **前端**: 实时视频播放 + WebSocket通信

### 数据流
```
用户语音 → WhisperNet(ASR) → Ollama(LLM) → EdgeTTS → MuseTalk(Python) → 视频流
                                    ↓
                              流式文本输出
                                    ↓
                              分段TTS+视频生成
```

## 伪实时实现策略

### 1. 流式处理管道
- **LLM流式输出**: 每句话立即处理，不等待完整回答
- **音频分段**: 1-2秒小片段，快速生成
- **视频并行**: 多段同时处理，队列播放

### 2. 性能优化
```python
# 动态批处理策略
if audio_duration <= 1.0:  # 1秒以内
    batch_size = 25
    skip_frames = 1  # 不跳帧
elif audio_duration <= 2.0:  # 2秒以内
    batch_size = 25
    skip_frames = 2  # 隔帧处理
```

### 3. 模型优化
- 模型预加载到GPU
- torch.compile加速
- 半精度推理（fp16）
- 模板特征缓存

## API接口设计

### Python端API（FastAPI）
```python
POST /api/initialize          # 初始化模型
POST /api/preprocess_template  # 预处理模板
POST /api/start_session       # 开始会话
POST /api/process_segment     # 处理音频片段
POST /api/end_session         # 结束会话
GET  /api/status             # 服务状态
GET  /health                 # 健康检查
```

### C#端调用流程
```csharp
// 1. 启动时初始化
await museTalkApi.InitializeAsync();

// 2. 创建模板
await museTalkApi.PreprocessTemplateAsync(templateId, imagePath);

// 3. 流式对话
var sessionId = await museTalkApi.StartSessionAsync(templateId);
foreach (var audioSegment in audioSegments)
{
    var videoPath = await museTalkApi.ProcessSegmentAsync(
        sessionId, 
        audioSegment
    );
    // 推送给前端播放
    await hubContext.SendAsync("VideoReady", videoPath);
}
await museTalkApi.EndSessionAsync(sessionId);
```

## 关键代码位置

### C#端
```
LmyDigitalHuman/
├── Services/
│   ├── Streaming/
│   │   ├── StreamingOllamaService.cs    # LLM流式
│   │   └── StreamingPipelineService.cs  # 管道协调
│   └── MuseTalkApiService.cs            # Python API调用
├── Controllers/
│   └── DigitalHumanController.cs        # HTTP接口
└── Hubs/
    └── DigitalHumanHub.cs              # WebSocket推送
```

### Python端
```
MuseTalkEngine/
├── streaming/
│   ├── api_service.py          # FastAPI服务
│   ├── segment_processor.py    # 音频分段处理
│   └── realtime_processor.py   # 实时处理器
└── offline/
    └── batch_inference.py       # 核心推理引擎
```

## 性能指标

### 离线模式
- 10秒音频：20-30秒生成
- 质量：最高
- 用途：录播、宣传片

### 伪实时模式
- 首句延迟：2-3秒
- 持续输出：每2-3秒一段
- 用途：客服、实时对话

## 部署配置

### Docker Compose
```yaml
services:
  musetalk-python:
    image: musetalk-python:latest
    environment:
      - CUDA_VISIBLE_DEVICES=0,1
      - STREAMING_MODE=integrated
      - SEGMENT_DURATION=1.0
      - SKIP_FRAMES=2
    ports:
      - "28888:28888"
    volumes:
      - ./models:/opt/musetalk/repo/MuseTalk/models
      - ./template_cache:/opt/musetalk/template_cache
```

### 环境要求
- GPU: NVIDIA RTX 3090/4090（24GB显存）
- CUDA: 11.8+
- Python: 3.10
- .NET: 8.0

## 调试和监控

### 健康检查
```bash
# 检查Python服务
curl http://localhost:28888/health

# 查看服务状态
curl http://localhost:28888/api/status
```

### 性能监控
- GPU使用率：`nvidia-smi`
- 内存占用：`docker stats`
- 日志查看：`docker logs musetalk-python`

## 常见问题

### 1. 依赖冲突
- MMCV版本必须是1.7.0（不是1.7.1）
- Diffusers使用0.18.2（兼容huggingface-hub 0.16.4）

### 2. GPU内存不足
- 减小batch_size
- 启用skip_frames
- 使用fp16推理

### 3. 视频片段不连续
- 检查音频分段是否有重叠
- 调整segment_duration参数
- 使用帧插值平滑过渡