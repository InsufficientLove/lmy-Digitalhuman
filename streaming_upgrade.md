# 伪实时服务升级方案

## 核心实现

基于之前的伪实时方案，主要需要修复以下服务：

### 1. StreamingPipelineService
```csharp
// 修复方法调用
// TTS调用
var result = await _ttsService.ConvertTextToSpeechAsync(text, voice);

// MuseTalk调用
var request = new DigitalHumanRequest
{
    TemplateId = templateId,
    AudioPath = audioPath,
    Text = text
};
var response = await _museTalkService.GenerateVideoAsync(request);
```

### 2. StreamingOllamaService
```csharp
// 修复yield return在try-catch中的问题
string pendingSentence = null;
try
{
    // 处理逻辑
    pendingSentence = sentence;
}
catch (Exception ex)
{
    // 错误处理
}

// 在try外yield
if (!string.IsNullOrEmpty(pendingSentence))
{
    yield return pendingSentence;
}
```

### 3. 并行管道设计
- TextChannel: LLM输出文本
- AudioChannel: TTS生成音频
- VideoChannel: MuseTalk生成视频

三个管道并行处理，实现流式输出。
