using System.ComponentModel.DataAnnotations;

namespace LmyDigitalHuman.Models
{
    // ==================== 数字人模板相关 ====================
    
    /// <summary>
    /// 数字人模板
    /// </summary>
    public class DigitalHumanTemplate
    {
        public string TemplateId { get; set; } = string.Empty;
        public string Id { get => TemplateId; set => TemplateId = value; }
        public string TemplateName { get; set; } = string.Empty;
        public string Name { get => TemplateName; set => TemplateName = value; }
        public string Description { get; set; } = string.Empty;
        public string TemplateType { get; set; } = "headshot"; // headshot, half_body, full_body
        public string Gender { get; set; } = "neutral"; // male, female, neutral
        public string AgeRange { get; set; } = "adult"; // child, young, adult, elderly
        public string Style { get; set; } = "professional"; // professional, casual, friendly
        public bool EnableEmotion { get; set; } = true;
        public string ImagePath { get; set; } = string.Empty;
        public string ImageUrl { get; set; } = string.Empty;
        public string PreviewVideoPath { get; set; } = string.Empty;
        public string PreviewImageUrl { get; set; } = string.Empty;
        public VoiceSettings? DefaultVoiceSettings { get; set; }
        public Dictionary<string, object>? CustomParameters { get; set; }
        public DateTime CreatedAt { get; set; }
        public DateTime UpdatedAt { get; set; }
        public bool IsActive { get; set; } = true;
        public int UsageCount { get; set; } = 0;
        public string Status { get; set; } = "ready"; // ready, processing, error
    }

    /// <summary>
    /// 创建模板请求
    /// </summary>
    public class CreateTemplateRequest
    {
        [Required]
        public string TemplateName { get; set; } = string.Empty;
        
        [Required]
        public IFormFile ImageFile { get; set; } = default!;
        
        public string Description { get; set; } = string.Empty;
        public string TemplateType { get; set; } = "headshot";
        public string Gender { get; set; } = "neutral";
        public string AgeRange { get; set; } = "adult";
        public string Style { get; set; } = "professional";
        public bool EnableEmotion { get; set; } = true;
        public VoiceSettings? DefaultVoiceSettings { get; set; }
        public Dictionary<string, object>? CustomParameters { get; set; }
    }

    /// <summary>
    /// 创建模板响应
    /// </summary>
    public class CreateTemplateResponse
    {
        public bool Success { get; set; }
        public string TemplateId { get; set; } = string.Empty;
        public string Message { get; set; } = string.Empty;
        public DigitalHumanTemplate? Template { get; set; }
        public string ProcessingTime { get; set; } = string.Empty;
    }

    /// <summary>
    /// 获取模板列表请求
    /// </summary>
    public class GetTemplatesRequest
    {
        public string? TemplateType { get; set; }
        public string? Gender { get; set; }
        public string? Style { get; set; }
        public string? SearchKeyword { get; set; }
        public string SortBy { get; set; } = "created_desc"; // created_desc, usage_desc, name_asc
        public int Page { get; set; } = 1;
        public int PageSize { get; set; } = 20;
    }

    /// <summary>
    /// 获取模板列表响应
    /// </summary>
    public class GetTemplatesResponse
    {
        public bool Success { get; set; }
        public List<DigitalHumanTemplate> Templates { get; set; } = new();
        public int TotalCount { get; set; }
        public int Page { get; set; }
        public int PageSize { get; set; }
        public int TotalPages { get; set; }
    }

    // ==================== 数字人生成相关 ====================

    /// <summary>
    /// 数字人生成请求
    /// </summary>
    public class DigitalHumanRequest
    {
        [Required]
        public string AvatarImagePath { get; set; } = string.Empty;
        
        [Required]
        public string AudioPath { get; set; } = string.Empty;
        
        public string Quality { get; set; } = "medium"; // low, medium, high, ultra
        public int? Fps { get; set; } = 25;
        public int? BatchSize { get; set; } = 4;
        public float? BboxShift { get; set; }
        public string Priority { get; set; } = "normal"; // low, normal, high
        public bool EnableEmotion { get; set; } = true;
        public string? CacheKey { get; set; }
    }

    /// <summary>
    /// 数字人生成响应
    /// </summary>
    public class DigitalHumanResponse
    {
        public bool Success { get; set; }
        public string VideoUrl { get; set; } = string.Empty;
        public string VideoPath { get; set; } = string.Empty;
        public string Error { get; set; } = string.Empty;
        public long ProcessingTime { get; set; }
        public string Message { get; set; } = string.Empty;
        public DateTime CompletedAt { get; set; }
        public bool FromCache { get; set; }
        public DigitalHumanMetadata? Metadata { get; set; }
    }

    /// <summary>
    /// 数字人元数据
    /// </summary>
    public class DigitalHumanMetadata
    {
        public string Resolution { get; set; } = string.Empty;
        public int Fps { get; set; }
        public long FileSize { get; set; }
        public string Quality { get; set; } = string.Empty;
    }

    /// <summary>
    /// 使用模板生成请求
    /// </summary>
    public class GenerateWithTemplateRequest
    {
        [Required]
        public string TemplateId { get; set; } = string.Empty;
        
        [Required]
        public string Text { get; set; } = string.Empty;
        
        public string Quality { get; set; } = "medium";
        public string Emotion { get; set; } = "neutral";
        public string ResponseMode { get; set; } = "sync"; // sync, async
        public VoiceSettings? VoiceSettings { get; set; }
        public bool UseCache { get; set; } = true;
    }

    /// <summary>
    /// 使用模板生成响应
    /// </summary>
    public class GenerateWithTemplateResponse
    {
        public bool Success { get; set; }
        public string VideoUrl { get; set; } = string.Empty;
        public string AudioUrl { get; set; } = string.Empty;
        public string Message { get; set; } = string.Empty;
        public string ProcessingTime { get; set; } = string.Empty;
        public string ResponseMode { get; set; } = string.Empty;
        public bool FromCache { get; set; }
        public DigitalHumanTemplate? Template { get; set; }
    }

    // ==================== 对话相关 ====================

    /// <summary>
    /// 文本对话请求
    /// </summary>
    public class TextConversationRequest
    {
        [Required]
        public string TemplateId { get; set; } = string.Empty;
        
        [Required]
        public string Text { get; set; } = string.Empty;
        
        public string? ConversationId { get; set; }
        public string Quality { get; set; } = "medium";
        public string ResponseMode { get; set; } = "sync";
        public string Emotion { get; set; } = "neutral";
        public bool EnableEmotionDetection { get; set; } = true;
        public bool UseCache { get; set; } = true;
    }

    /// <summary>
    /// 音频对话请求
    /// </summary>
    public class AudioConversationRequest
    {
        [Required]
        public string TemplateId { get; set; } = string.Empty;
        
        [Required]
        public IFormFile AudioFile { get; set; } = default!;
        
        public string? ConversationId { get; set; }
        public string AudioPath { get; set; } = string.Empty;
        public string Quality { get; set; } = "medium";
        public string ResponseMode { get; set; } = "sync";
        public bool EnableEmotionDetection { get; set; } = true;
        public string Language { get; set; } = "zh";
        public bool UseCache { get; set; } = true;
        public Dictionary<string, object>? CustomParameters { get; set; }
    }

    /// <summary>
    /// 对话响应
    /// </summary>
    public class ConversationResponse
    {
        public bool Success { get; set; }
        public string ConversationId { get; set; } = string.Empty;
        public string InputText { get; set; } = string.Empty;
        public string RecognizedText { get; set; } = string.Empty;
        public string ResponseText { get; set; } = string.Empty;
        public string VideoUrl { get; set; } = string.Empty;
        public string AudioUrl { get; set; } = string.Empty;
        public string DetectedEmotion { get; set; } = "neutral";
        public string ProcessingTime { get; set; } = string.Empty;
        public bool FromCache { get; set; }
        public string Message { get; set; } = string.Empty;
        public ServiceMetrics? Metrics { get; set; }
    }

    /// <summary>
    /// 实时对话请求
    /// </summary>
    public class StartRealtimeConversationRequest
    {
        [Required]
        public string TemplateId { get; set; } = string.Empty;
        
        public string? ConversationId { get; set; }
        public string Quality { get; set; } = "fast";
        public bool EnableEmotionDetection { get; set; } = true;
        public string Language { get; set; } = "zh";
    }

    /// <summary>
    /// 实时音频处理请求
    /// </summary>
    public class ProcessRealtimeAudioRequest
    {
        [Required]
        public string ConversationId { get; set; } = string.Empty;
        
        [Required]
        public byte[] AudioData { get; set; } = Array.Empty<byte>();
        
        public bool IsComplete { get; set; }
        public bool IsEndOfSpeech { get; set; }
        public int ChunkIndex { get; set; }
        public string AudioFormat { get; set; } = "wav";
    }

    // ==================== 语音相关 ====================

    /// <summary>
    /// 语音设置
    /// </summary>
    public class VoiceSettings
    {
        public string Voice { get; set; } = "zh-CN-XiaoxiaoNeural";
        public string VoiceId { get; set; } = "zh-CN-XiaoxiaoNeural";
        public string Rate { get; set; } = "medium";
        public string Pitch { get; set; } = "medium";
        public float Speed { get; set; } = 1.0f;
        public float Volume { get; set; } = 1.0f;
        public string Emotion { get; set; } = "neutral";
    }

    /// <summary>
    /// TTS请求
    /// </summary>
    public class TTSRequest
    {
        public string Text { get; set; } = string.Empty;
        public string Voice { get; set; } = "zh-CN-XiaoxiaoNeural";
        public string VoiceId { get; set; } = "zh-CN-XiaoxiaoNeural";
        public string Rate { get; set; } = "1.0";
        public string Speed { get; set; } = "1.0";
        public string Pitch { get; set; } = "0Hz";
        public string Emotion { get; set; } = "neutral";
        public string OutputFormat { get; set; } = "audio-16khz-128kbitrate-mono-mp3";
        public string OutputPath { get; set; } = string.Empty;
    }

    /// <summary>
    /// TTS响应
    /// </summary>
    public class TTSResponse
    {
        public bool Success { get; set; }
        public string AudioPath { get; set; } = string.Empty;
        public string AudioUrl { get; set; } = string.Empty;
        public int Duration { get; set; }
        public long FileSize { get; set; }
        public int ProcessingTime { get; set; }
    }

    /// <summary>
    /// 语音识别响应
    /// </summary>
    public class SpeechToTextResponse
    {
        public bool Success { get; set; }
        public string Text { get; set; } = string.Empty;
        public string Language { get; set; } = string.Empty;
        public float Confidence { get; set; }
        public TimeSpan Duration { get; set; }
        public long ProcessingTime { get; set; }
        public List<SpeechSegment> Segments { get; set; } = new();
        public string Error { get; set; } = string.Empty;
    }

    /// <summary>
    /// 语音信息
    /// </summary>
    public class VoiceInfo
    {
        public string Name { get; set; } = string.Empty;
        public string DisplayName { get; set; } = string.Empty;
        public string Language { get; set; } = string.Empty;
        public string Gender { get; set; } = string.Empty;
        public string Style { get; set; } = string.Empty;
        public List<string> SupportedStyles { get; set; } = new();
    }

    /// <summary>
    /// 流式TTS请求
    /// </summary>
    public class TTSStreamRequest
    {
        public string Text { get; set; } = string.Empty;
        public string Voice { get; set; } = "zh-CN-XiaoxiaoNeural";
        public string Rate { get; set; } = "1.0";
        public string Pitch { get; set; } = "0Hz";
        public string OutputFormat { get; set; } = "audio-16khz-128kbitrate-mono-mp3";
    }

    /// <summary>
    /// 音频块响应
    /// </summary>
    public class AudioChunkResponse
    {
        public byte[] AudioData { get; set; } = Array.Empty<byte>();
        public int ChunkIndex { get; set; }
        public bool IsComplete { get; set; }
        public int TotalDuration { get; set; }
    }

    // ==================== 大模型相关 ====================

    /// <summary>
    /// 聊天消息
    /// </summary>
    public class ChatMessage
    {
        public string Role { get; set; } = string.Empty; // user, assistant, system
        public string Content { get; set; } = string.Empty;
        public DateTime Timestamp { get; set; } = DateTime.UtcNow;
    }

    /// <summary>
    /// 本地LLM请求
    /// </summary>
    public class LocalLLMRequest
    {
        [Required]
        public string Message { get; set; } = string.Empty;
        
        public string Prompt { get; set; } = string.Empty;
        public string ModelName { get; set; } = "qwen2.5:14b-instruct-q4_0";
        public string? ConversationId { get; set; }
        public float Temperature { get; set; } = 0.7f;
        public float TopP { get; set; } = 0.9f;
        public int TopK { get; set; } = 40;
        public int MaxTokens { get; set; } = 500;
        public string? SystemPrompt { get; set; }
        public bool Stream { get; set; } = false;
        public List<ChatMessage> History { get; set; } = new();
    }

    /// <summary>
    /// 本地LLM响应
    /// </summary>
    public class LocalLLMResponse
    {
        public bool Success { get; set; }
        public string Response { get; set; } = string.Empty;
        public string ResponseText { get; set; } = string.Empty;
        public string Message { get; set; } = string.Empty;
        public string ModelName { get; set; } = string.Empty;
        public string? ConversationId { get; set; }
        public long ProcessingTime { get; set; }
        public int TokensUsed { get; set; }
        public string Error { get; set; } = string.Empty;
        public Dictionary<string, object>? Metadata { get; set; }
    }

    // ==================== 统计和监控相关 ====================

    /// <summary>
    /// 对话指标
    /// </summary>
    public class ConversationMetrics
    {
        public int ActiveWorkers { get; set; }
        public int QueueLength { get; set; }
        public double AverageProcessingTime { get; set; }
        public double ThroughputPerHour { get; set; }
        public Dictionary<string, object> ResourceUsage { get; set; } = new();
        public List<string> PerformanceWarnings { get; set; } = new();
    }

    /// <summary>
    /// 模板统计
    /// </summary>
    public class TemplateStatistics
    {
        public int TotalTemplates { get; set; }
        public int ActiveTemplates { get; set; }
        public int TotalUsage { get; set; }
        public Dictionary<string, int> TemplateTypeCount { get; set; } = new();
        public Dictionary<string, int> GenderCount { get; set; } = new();
        public Dictionary<string, int> StyleCount { get; set; } = new();
        public List<DigitalHumanTemplate> MostUsedTemplates { get; set; } = new();
        public List<DigitalHumanTemplate> RecentTemplates { get; set; } = new();
    }

    /// <summary>
    /// 对话统计
    /// </summary>
    public class ConversationStatistics
    {
        public int TotalConversations { get; set; }
        public int ActiveConversations { get; set; }
        public long AverageResponseTime { get; set; }
        public Dictionary<string, int> LanguageDistribution { get; set; } = new();
        public Dictionary<string, int> EmotionDistribution { get; set; } = new();
        public Dictionary<string, int> QualityDistribution { get; set; } = new();
    }

    /// <summary>
    /// 缓存统计
    /// </summary>
    public class CacheStatistics
    {
        public int TotalCachedItems { get; set; }
        public double CacheHitRate { get; set; }
        public DateTime LastCleanup { get; set; }
        public long CacheSize { get; set; }
        public Dictionary<string, int> CacheHitsByTemplate { get; set; } = new();
    }

    /// <summary>
    /// 服务性能指标
    /// </summary>
    public class ServiceMetrics
    {
        public int ActiveWorkers { get; set; }
        public int QueueLength { get; set; }
        public double AverageProcessingTime { get; set; }
        public double ThroughputPerHour { get; set; }
        public Dictionary<string, object> ResourceUsage { get; set; } = new();
        public List<string> PerformanceWarnings { get; set; } = new();
    }

    // ==================== 任务队列相关 ====================

    /// <summary>
    /// 队列任务
    /// </summary>
    public class QueuedJob
    {
        public string JobId { get; set; } = string.Empty;
        public DigitalHumanRequest Request { get; set; } = new();
        public JobStatus Status { get; set; } = JobStatus.Pending;
        public DateTime QueuedAt { get; set; }
        public DateTime? StartedAt { get; set; }
        public DateTime? CompletedAt { get; set; }
        public string Priority { get; set; } = "normal";
        public long EstimatedProcessingTime { get; set; }
        public DigitalHumanResponse? Result { get; set; }
        public string? Error { get; set; }
    }

    /// <summary>
    /// 处理中任务
    /// </summary>
    public class ProcessingJob
    {
        public string JobId { get; set; } = string.Empty;
        public DateTime StartTime { get; set; }
        public int Progress { get; set; }
        public string CurrentStep { get; set; } = string.Empty;
    }

    /// <summary>
    /// 任务状态
    /// </summary>
    public enum JobStatus
    {
        Pending,
        Processing,
        Completed,
        Failed,
        Cancelled
    }

    // ==================== 批处理相关 ====================

    /// <summary>
    /// 批量预渲染请求
    /// </summary>
    public class BatchPreRenderRequest
    {
        [Required]
        public string TemplateId { get; set; } = string.Empty;
        
        [Required]
        public List<string> TextList { get; set; } = new();
        
        public List<string>? EmotionList { get; set; }
        public string Quality { get; set; } = "medium";
    }

    /// <summary>
    /// 批量预渲染响应
    /// </summary>
    public class BatchPreRenderResponse
    {
        public bool Success { get; set; }
        public int TotalCount { get; set; }
        public int SuccessCount { get; set; }
        public int FailedCount { get; set; }
        public List<string> FailedTexts { get; set; } = new();
        public string ProcessingTime { get; set; } = string.Empty;
        public string Message { get; set; } = string.Empty;
    }

    // ==================== 其他辅助类 ====================

    /// <summary>
    /// 预处理结果
    /// </summary>
    public class PreprocessingResult
    {
        public bool Success { get; set; }
        public string TemplateId { get; set; } = string.Empty;
        public long PreprocessingTime { get; set; }
        public Dictionary<string, object> OptimizedSettings { get; set; } = new();
    }

    /// <summary>
    /// 音频优化结果
    /// </summary>
    public class AudioOptimizationResult
    {
        public bool Success { get; set; }
        public string OptimizedAudioPath { get; set; } = string.Empty;
        public long OriginalSize { get; set; }
        public long OptimizedSize { get; set; }
        public long ProcessingTime { get; set; }
        public List<string> AppliedOptimizations { get; set; } = new();
    }

    /// <summary>
    /// 流式生成请求
    /// </summary>
    public class StreamingGenerationRequest
    {
        public string TemplateId { get; set; } = string.Empty;
        public string Text { get; set; } = string.Empty;
        public string Quality { get; set; } = "fast";
    }

    /// <summary>
    /// 流式生成块
    /// </summary>
    public class StreamingGenerationChunk
    {
        public byte[] VideoData { get; set; } = Array.Empty<byte>();
        public int ChunkIndex { get; set; }
        public bool IsComplete { get; set; }
        public int Progress { get; set; }
    }

    // ==================== 音频处理相关 ====================

    /// <summary>
    /// 语音片段
    /// </summary>
    public class SpeechSegment
    {
        public string Text { get; set; } = string.Empty;
        public TimeSpan StartTime { get; set; }
        public TimeSpan EndTime { get; set; }
        public float Confidence { get; set; }
    }

    /// <summary>
    /// TTS结果
    /// </summary>
    public class TTSResult
    {
        public bool Success { get; set; }
        public string AudioPath { get; set; } = string.Empty;
        public string AudioUrl { get; set; } = string.Empty;
        public byte[]? AudioData { get; set; }
        public TimeSpan Duration { get; set; }
        public long ProcessingTime { get; set; }
        public long FileSize { get; set; }
        public string Error { get; set; } = string.Empty;
    }

    /// <summary>
    /// 音频转换结果
    /// </summary>
    public class AudioConversionResult
    {
        public bool Success { get; set; }
        public string OutputPath { get; set; } = string.Empty;
        public string OutputFormat { get; set; } = string.Empty;
        public long InputSize { get; set; }
        public long OutputSize { get; set; }
        public TimeSpan Duration { get; set; }
        public long ProcessingTime { get; set; }
        public string Error { get; set; } = string.Empty;
    }

    /// <summary>
    /// 音频增强结果
    /// </summary>
    public class AudioEnhancementResult
    {
        public bool Success { get; set; }
        public string OutputPath { get; set; } = string.Empty;
        public float QualityImprovement { get; set; }
        public float NoiseReduction { get; set; }
        public long ProcessingTime { get; set; }
        public Dictionary<string, object> EnhancementMetrics { get; set; } = new();
        public string Error { get; set; } = string.Empty;
    }

    /// <summary>
    /// 音频分析结果
    /// </summary>
    public class AudioAnalysisResult
    {
        public bool Success { get; set; }
        public TimeSpan Duration { get; set; }
        public int SampleRate { get; set; }
        public int Channels { get; set; }
        public int BitDepth { get; set; }
        public float AverageVolume { get; set; }
        public float PeakVolume { get; set; }
        public float NoiseLevel { get; set; }
        public string Format { get; set; } = string.Empty;
        public long FileSize { get; set; }
        public bool IsSuitableForMuseTalk { get; set; }
        public List<string> Recommendations { get; set; } = new();
    }

    /// <summary>
    /// 情感检测结果
    /// </summary>
    public class EmotionDetectionResult
    {
        public bool Success { get; set; }
        public string PrimaryEmotion { get; set; } = string.Empty;
        public Dictionary<string, float> EmotionScores { get; set; } = new();
        public float Confidence { get; set; }
        public List<EmotionSegment> EmotionSegments { get; set; } = new();
        public long ProcessingTime { get; set; }
        public string Error { get; set; } = string.Empty;
    }

    /// <summary>
    /// 情感片段
    /// </summary>
    public class EmotionSegment
    {
        public TimeSpan StartTime { get; set; }
        public TimeSpan EndTime { get; set; }
        public string Emotion { get; set; } = string.Empty;
        public float Confidence { get; set; }
    }

    // ==================== 语音识别相关 ====================

    /// <summary>
    /// 语音识别结果
    /// </summary>
    public class SpeechRecognitionResult
    {
        public bool Success { get; set; }
        public string Text { get; set; } = string.Empty;
        public string Language { get; set; } = string.Empty;
        public float Confidence { get; set; }
        public TimeSpan Duration { get; set; }
        public long ProcessingTime { get; set; }
        public List<SpeechSegment> Segments { get; set; } = new();
        public string Error { get; set; } = string.Empty;
        public Dictionary<string, object>? Metadata { get; set; }
    }

    /// <summary>
    /// 流式TTS请求
    /// </summary>
    public class StreamingTTSRequest
    {
        public string Text { get; set; } = string.Empty;
        public string Voice { get; set; } = "zh-CN-XiaoxiaoNeural";
        public string VoiceId { get; set; } = "zh-CN-XiaoxiaoNeural";
        public string Rate { get; set; } = "1.0";
        public string Speed { get; set; } = "1.0";
        public string Pitch { get; set; } = "0Hz";
        public string OutputFormat { get; set; } = "audio-16khz-128kbitrate-mono-mp3";
        public string SessionId { get; set; } = string.Empty;
        public int ChunkSize { get; set; } = 4096;
    }

    /// <summary>
    /// 实时对话请求
    /// </summary>
    public class RealtimeConversationRequest
    {
        [Required]
        public string TemplateId { get; set; } = string.Empty;
        
        public string? ConversationId { get; set; }
        public string InputType { get; set; } = "text"; // text, audio
        public string Text { get; set; } = string.Empty;
        public IFormFile? AudioFile { get; set; }
        public string Quality { get; set; } = "fast";
        public string ResponseMode { get; set; } = "stream";
        public bool EnableEmotionDetection { get; set; } = true;
        public string Language { get; set; } = "zh";
        public VoiceSettings? VoiceSettings { get; set; }
    }

    /// <summary>
    /// 实时对话响应
    /// </summary>
    public class RealtimeConversationResponse
    {
        public bool Success { get; set; }
        public string ConversationId { get; set; } = string.Empty;
        public string RecognizedText { get; set; } = string.Empty;
        public string ResponseText { get; set; } = string.Empty;
        public string VideoUrl { get; set; } = string.Empty;
        public string AudioUrl { get; set; } = string.Empty;
        public string DetectedEmotion { get; set; } = "neutral";
        public string ProcessingTime { get; set; } = string.Empty;
        public bool FromCache { get; set; }
        public DigitalHumanTemplate? Template { get; set; }
        public string Message { get; set; } = string.Empty;
        public string SessionId { get; set; } = string.Empty;
        public Dictionary<string, object>? ConnectionInfo { get; set; }
    }

    /// <summary>
    /// 创建数字人模板请求
    /// </summary>
    public class CreateDigitalHumanTemplateRequest
    {
        [Required]
        public string TemplateName { get; set; } = string.Empty;
        
        [Required]
        public IFormFile ImageFile { get; set; } = default!;
        
        public string Description { get; set; } = string.Empty;
        public string TemplateType { get; set; } = "headshot";
        public string Gender { get; set; } = "neutral";
        public string AgeRange { get; set; } = "adult";
        public string Style { get; set; } = "professional";
        public bool EnableEmotion { get; set; } = true;
        public VoiceSettings? DefaultVoiceSettings { get; set; }
        public Dictionary<string, object>? CustomParameters { get; set; }
    }

    /// <summary>
    /// 创建数字人模板响应
    /// </summary>
    public class CreateDigitalHumanTemplateResponse
    {
        public bool Success { get; set; }
        public string TemplateId { get; set; } = string.Empty;
        public string Message { get; set; } = string.Empty;
        public DigitalHumanTemplate? Template { get; set; }
        public string ProcessingTime { get; set; } = string.Empty;
        public string PreviewUrl { get; set; } = string.Empty;
    }
}