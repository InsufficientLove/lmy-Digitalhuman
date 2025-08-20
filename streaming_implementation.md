# 流式数字人实现方案（基于现有代码）

## 改动清单（1-2天工作量）

### 1. C# 端（LmyDigitalHuman）- 半天

#### A. 修改 OllamaService.cs
```csharp
// 当前：等待完整回答
var response = await ollamaClient.Generate(request);

// 改为：流式处理
public async IAsyncEnumerable<string> GenerateStreamAsync(string prompt)
{
    var request = new { 
        model = "qwen2.5:latest",
        prompt = prompt,
        stream = true  // 启用流式
    };
    
    using var stream = await httpClient.PostAsStreamAsync("/api/generate", request);
    using var reader = new StreamReader(stream);
    
    var sentence = "";
    while (!reader.EndOfStream)
    {
        var line = await reader.ReadLineAsync();
        var token = ParseToken(line);
        sentence += token;
        
        // 检测句子结束（。！？）
        if (IsSentenceEnd(token))
        {
            yield return sentence;
            sentence = "";
        }
    }
}
```

#### B. 修改 DigitalHumanTemplateService.cs
```csharp
public async Task<string> ProcessTextStreamAsync(string templateId, string text)
{
    var videoSegments = new List<string>();
    
    // 流式获取LLM回答
    await foreach (var sentence in ollamaService.GenerateStreamAsync(text))
    {
        // 每句话独立处理
        var audioPath = await ttsService.SynthesizeAsync(sentence);
        var videoPath = await museTalkService.GenerateVideoAsync(
            templateId, 
            audioPath,
            outputPath: $"/videos/segment_{Guid.NewGuid()}.mp4"
        );
        
        videoSegments.Add(videoPath);
        
        // 立即推送给前端播放
        await hubContext.Clients.All.SendAsync("VideoSegmentReady", videoPath);
    }
    
    // 后台合并所有片段
    return await MergeVideosAsync(videoSegments);
}
```

### 2. Python 端（MuseTalkEngine）- 半天

#### A. 添加分段处理接口
```python
# ultra_fast_realtime_inference_v2.py

def process_audio_segment(self, template_id, audio_path, segment_index):
    """处理1-2秒音频片段"""
    
    # 1. 音频特征提取（0.5秒）
    audio_features = self.extract_audio_features_fast(audio_path)
    
    # 2. 帧数计算（1-2秒 = 25-50帧）
    num_frames = len(audio_features)
    
    # 3. 小批量推理（2-3秒）
    if num_frames <= 50:  # 2秒以内
        batch_size = num_frames  # 一次处理完
    else:
        batch_size = 25  # 分两批
    
    # 4. 生成视频片段
    output_path = f"/videos/segment_{template_id}_{segment_index}.mp4"
    success = self.ultra_fast_inference_parallel(
        template_id=template_id,
        audio_path=audio_path,
        output_path=output_path,
        batch_size=batch_size,
        skip_frames=2  # 隔帧处理，2倍速
    )
    
    return output_path
```

#### B. 优化批处理大小
```python
# 根据音频长度动态调整
if audio_duration <= 1.0:  # 1秒以内
    batch_size = 25
    skip_frames = 1  # 不跳帧，保证质量
elif audio_duration <= 2.0:  # 2秒以内
    batch_size = 25
    skip_frames = 2  # 隔帧，加速
else:  # 超过2秒，分段
    # 自动分段处理
    return self.process_long_audio(audio_path)
```

### 3. 前端改动 - 半天

```javascript
// 接收视频片段并立即播放
connection.on("VideoSegmentReady", function(videoPath) {
    // 添加到播放队列
    videoQueue.push(videoPath);
    
    // 如果是第一个片段，立即播放
    if (videoQueue.length === 1) {
        playNextSegment();
    }
});

function playNextSegment() {
    if (videoQueue.length > 0) {
        const video = videoQueue.shift();
        videoPlayer.src = video;
        videoPlayer.play();
        
        // 视频结束时播放下一段
        videoPlayer.onended = playNextSegment;
    }
}
```

## 性能预期

### 原方案（串行）
```
用户提问 → 等待30秒 → 看到完整回答
```

### 新方案（流式）
```
用户提问 → 3秒 → 看到第一句回答
        → 6秒 → 看到第二句
        → 9秒 → 看到第三句
        ... 持续输出
```

### 用户体验
- **首次响应**：3秒（vs 30秒）
- **持续输出**：每2-3秒一段
- **完整对话**：总时间不变，但体验好10倍

## 实施步骤

### Day 1 上午
1. 修改 OllamaService 支持流式
2. 修改 DigitalHumanTemplateService 分段处理
3. 测试 C# 流式输出

### Day 1 下午
1. 修改 Python 添加分段接口
2. 优化小批量处理性能
3. 测试分段视频生成

### Day 2 上午
1. 前端添加视频队列播放
2. 处理片段间过渡
3. 添加加载动画

### Day 2 下午
1. 集成测试
2. 性能调优
3. 边界情况处理

## 关键代码位置

```
C# 需要修改：
├── Services/
│   ├── OllamaService.cs          # 添加流式接口
│   ├── DigitalHumanTemplateService.cs  # 分段处理
│   └── OptimizedMuseTalkService.cs     # 调用分段API

Python 需要修改：
├── ultra_fast_realtime_inference_v2.py  # 添加分段处理
└── template_manager.py                  # 优化缓存策略

前端需要修改：
├── wwwroot/js/
│   └── digitalHuman.js  # 视频队列播放
```

## 风险点

1. **视频片段衔接**：可能有轻微跳动
   - 解决：添加淡入淡出过渡

2. **音频同步**：分段可能导致音频不连续
   - 解决：服务端合并音频后再分段

3. **网络传输**：多个小视频增加请求数
   - 解决：使用 WebSocket 推送

## 总结

- **改动量**：中等（20-30%代码）
- **开发时间**：1-2天
- **效果提升**：10倍体验提升
- **风险**：低（不影响现有功能）