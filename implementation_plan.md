# 实施计划：分层架构，保护现有成果

## 一、保留的代码（不需要改动）

### 1. 模型预加载 ✅
**文件**: `MuseTalkEngine/ultra_fast_realtime_inference_v2.py`
```python
def initialize_models():
    # 保留：启动时加载模型到GPU
    # 保留：torch.compile优化
    # 这些对两种模式都有用
```
**理由**: 无论离线还是流式，都需要预加载

### 2. 模板预处理 ✅
**文件**: `MuseTalkEngine/template_manager.py`
```python
def preprocess_template():
    # 保留：模板特征提取和缓存
    # 两种模式都需要
```
**理由**: 模板缓存对所有场景都有效

### 3. 批量优化 ✅
**文件**: `MuseTalkEngine/ultra_fast_realtime_inference_v2.py`
```python
def execute_4gpu_parallel_inference():
    # 保留：双GPU并行
    # 保留：batch_size自动优化
    # 离线场景继续使用
```
**理由**: 离线生成仍需要这些优化

## 二、需要新增的代码

### 1. 流式Ollama服务
**新文件**: `LmyDigitalHuman/Services/Streaming/StreamingOllamaService.cs`
```csharp
public class StreamingOllamaService : IOllamaService
{
    // 继承基础OllamaService
    // 添加流式方法
    public async IAsyncEnumerable<string> GenerateStreamAsync(string prompt)
    {
        // 实现流式输出
        // 每句话yield return
    }
}
```
**原因**: 需要流式获取LLM回答，减少等待

### 2. 分段处理器
**新文件**: `MuseTalkEngine/streaming/segment_processor.py`
```python
class SegmentProcessor:
    def __init__(self, base_service):
        # 复用现有的模型和优化
        self.service = base_service
    
    def process_segment(self, audio_path, template_id):
        # 处理1-2秒片段
        # 复用现有推理逻辑
        # 但是batch_size=25-50
```
**原因**: 小片段快速处理，复用现有优化

### 3. SignalR Hub
**新文件**: `LmyDigitalHuman/Hubs/StreamingHub.cs`
```csharp
public class StreamingHub : Hub
{
    public async Task StartConversation(string templateId, string text)
    {
        // 流式处理
        await foreach(var segment in ProcessStream(text))
        {
            await Clients.Caller.SendAsync("SegmentReady", segment);
        }
    }
}
```
**原因**: WebSocket推送视频片段，无需轮询

## 三、需要修改的代码（最小改动）

### 1. 添加模式切换
**修改**: `LmyDigitalHuman/Controllers/DigitalHumanController.cs`
```csharp
[HttpPost("process")]
public async Task<IActionResult> Process(
    string templateId, 
    string text,
    bool streaming = false)  // 新增参数
{
    if (streaming)
    {
        // 调用流式服务
        return Ok(await streamingService.ProcessAsync(templateId, text));
    }
    else
    {
        // 保持原有逻辑
        return Ok(await offlineService.ProcessAsync(templateId, text));
    }
}
```
**理由**: 同一接口支持两种模式

### 2. Python端添加分段入口
**修改**: `MuseTalkEngine/ultra_fast_realtime_inference_v2.py`
```python
# 在现有类中添加方法
def process_segment(self, template_id, audio_path, max_frames=50):
    """分段处理入口，复用现有逻辑"""
    # 检测音频长度
    if frames_count <= max_frames:
        # 直接用现有方法，但batch_size小
        return self.ultra_fast_inference_parallel(
            template_id, audio_path, 
            batch_size=frames_count
        )
```
**理由**: 最大程度复用现有代码

## 四、实施顺序（2天计划）

### Day 1 - 上午（4小时）
1. ✅ 创建目录结构
2. ✅ 实现StreamingOllamaService
3. ✅ 测试流式LLM输出

### Day 1 - 下午（4小时）
1. ✅ 实现分段TTS
2. ✅ Python添加segment_processor
3. ✅ 测试分段视频生成

### Day 2 - 上午（4小时）
1. ✅ 实现SignalR Hub
2. ✅ 前端视频队列
3. ✅ 测试端到端流式

### Day 2 - 下午（4小时）
1. ✅ 性能调优
2. ✅ 边界情况处理
3. ✅ 部署测试

## 五、风险控制

### 1. 不影响现有功能
- 所有修改都在新文件或新方法中
- 通过参数控制使用哪种模式
- 离线功能完全不受影响

### 2. 代码复用最大化
- 模型加载：100%复用
- 推理逻辑：90%复用
- 只是改变调用方式

### 3. 可回滚
- 每步都可独立测试
- 问题可快速定位
- 最坏情况回退到离线模式

## 六、验证指标

### 离线模式（保持不变）
- 10秒音频：20-30秒生成
- 质量：最高
- 适用：录播、宣传片

### 流式模式（新增）
- 首句延迟：2-3秒
- 持续输出：每2-3秒一段
- 适用：客服、对话

## 七、具体代码示例

### StreamingOllamaService.cs
```csharp
public class StreamingOllamaService : OllamaService
{
    public async IAsyncEnumerable<SentenceResult> GenerateStreamAsync(
        string prompt, 
        [EnumeratorCancellation] CancellationToken ct = default)
    {
        var request = new
        {
            model = "qwen2.5:latest",
            prompt = prompt,
            stream = true
        };

        using var response = await httpClient.PostAsStreamAsync(
            "/api/generate", 
            JsonContent.Create(request), 
            ct);
            
        using var reader = new StreamReader(await response.Content.ReadAsStreamAsync());
        
        var buffer = new StringBuilder();
        string line;
        
        while ((line = await reader.ReadLineAsync()) != null)
        {
            if (string.IsNullOrWhiteSpace(line)) continue;
            
            var json = JsonSerializer.Deserialize<OllamaStreamResponse>(line);
            buffer.Append(json.Response);
            
            // 检测句子结束
            if (IsSentenceEnd(json.Response))
            {
                var sentence = buffer.ToString();
                buffer.Clear();
                
                yield return new SentenceResult
                {
                    Text = sentence,
                    Index = sentenceIndex++,
                    Timestamp = DateTime.Now
                };
            }
            
            if (json.Done) break;
        }
        
        // 处理剩余文本
        if (buffer.Length > 0)
        {
            yield return new SentenceResult
            {
                Text = buffer.ToString(),
                Index = sentenceIndex++,
                IsFinal = true
            };
        }
    }
    
    private bool IsSentenceEnd(string text)
    {
        return text.EndsWith("。") || 
               text.EndsWith("！") || 
               text.EndsWith("？") ||
               text.EndsWith(".") ||
               text.EndsWith("!") ||
               text.EndsWith("?");
    }
}
```

### segment_processor.py
```python
from ultra_fast_realtime_inference_v2 import UltraFastMuseTalkService

class SegmentProcessor:
    """分段处理器，复用现有服务"""
    
    def __init__(self, base_service: UltraFastMuseTalkService):
        self.service = base_service
        self.template_cache = {}
        
    def process_audio_segment(
        self, 
        template_id: str,
        audio_path: str,
        segment_index: int
    ) -> dict:
        """处理单个音频片段"""
        
        # 1. 检测音频长度
        import librosa
        audio, sr = librosa.load(audio_path, sr=16000)
        duration = len(audio) / sr
        
        # 2. 计算帧数
        fps = 25
        num_frames = int(duration * fps)
        
        # 3. 优化参数
        if num_frames <= 25:  # 1秒以内
            batch_size = num_frames
            skip_frames = 1  # 不跳帧
        elif num_frames <= 50:  # 2秒以内
            batch_size = 25
            skip_frames = 2  # 隔帧处理
        else:
            # 超过2秒，只处理前2秒
            num_frames = 50
            batch_size = 25
            skip_frames = 2
            
        # 4. 调用现有推理（复用所有优化）
        output_path = f"/temp/segment_{template_id}_{segment_index}.mp4"
        
        success = self.service.ultra_fast_inference_parallel(
            template_id=template_id,
            audio_path=audio_path,
            output_path=output_path,
            batch_size=batch_size,
            skip_frames=skip_frames
        )
        
        return {
            "success": success,
            "path": output_path,
            "duration": duration,
            "frames": num_frames,
            "index": segment_index
        }
```

这样的分层设计：
1. ✅ 保护现有成果
2. ✅ 最大化代码复用
3. ✅ 风险可控
4. ✅ 可独立测试