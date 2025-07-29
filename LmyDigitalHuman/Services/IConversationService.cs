using LmyDigitalHuman.Models;

namespace LmyDigitalHuman.Services
{
    /// <summary>
    /// 数字人对话服务接口
    /// </summary>
    public interface IConversationService
    {
        // 非实时对话
        Task<ConversationResponse> ProcessTextConversationAsync(TextConversationRequest request);
        Task<ConversationResponse> ProcessAudioConversationAsync(AudioConversationRequest request);

        // 实时对话
        Task<RealtimeConversationResponse> StartRealtimeConversationAsync(StartRealtimeConversationRequest request);
        Task<RealtimeConversationResponse> ProcessRealtimeAudioAsync(ProcessRealtimeAudioRequest request);
        Task<bool> EndRealtimeConversationAsync(string conversationId);

        // 对话上下文管理
        Task<ConversationContext> GetConversationContextAsync(string conversationId);
        Task<bool> UpdateConversationContextAsync(string conversationId, ConversationContext context);
        Task<bool> ClearConversationContextAsync(string conversationId);

        // 批处理对话
        Task<List<ConversationResponse>> ProcessBatchConversationsAsync(List<TextConversationRequest> requests);

        // 对话历史与统计
        Task<List<ConversationHistory>> GetConversationHistoryAsync(string? conversationId = null, int limit = 50);
        Task<ConversationStatistics> GetConversationStatisticsAsync();

        // 性能优化
        Task<bool> PreloadTemplateForConversationAsync(string templateId);
        Task<string> GetOptimalResponseModeAsync(string templateId, ConversationMetrics metrics);
    }

    /// <summary>
    /// 文本对话请求
    /// </summary>
    public class TextConversationRequest
    {
        public string TemplateId { get; set; } = string.Empty;
        public string Text { get; set; } = string.Empty;
        public string? ConversationId { get; set; }
        public string ResponseMode { get; set; } = "fast";
        public string Quality { get; set; } = "medium";
        public string Emotion { get; set; } = "neutral";
        public bool UseCache { get; set; } = true;
        public Dictionary<string, object>? CustomParameters { get; set; }
    }

    /// <summary>
    /// 音频对话请求
    /// </summary>
    public class AudioConversationRequest
    {
        public string TemplateId { get; set; } = string.Empty;
        public string AudioPath { get; set; } = string.Empty;
        public string? ConversationId { get; set; }
        public string ResponseMode { get; set; } = "fast";
        public string Quality { get; set; } = "medium";
        public bool EnableEmotionDetection { get; set; } = true;
        public bool UseCache { get; set; } = true;
        public Dictionary<string, object>? CustomParameters { get; set; }
    }

    /// <summary>
    /// 对话响应
    /// </summary>
    public class ConversationResponse
    {
        public bool Success { get; set; }
        public string Message { get; set; } = string.Empty;
        public string ConversationId { get; set; } = string.Empty;
        public string InputText { get; set; } = string.Empty;
        public string ResponseText { get; set; } = string.Empty;
        public string VideoUrl { get; set; } = string.Empty;
        public string AudioUrl { get; set; } = string.Empty;
        public string DetectedEmotion { get; set; } = string.Empty;
        public long ProcessingTime { get; set; }
        public bool FromCache { get; set; } = false;
        public ConversationMetrics? Metrics { get; set; }
    }

    /// <summary>
    /// 实时对话开始请求
    /// </summary>
    public class StartRealtimeConversationRequest
    {
        public string TemplateId { get; set; } = string.Empty;
        public string Quality { get; set; } = "medium";
        public bool EnableEmotionDetection { get; set; } = true;
        public Dictionary<string, object>? CustomParameters { get; set; }
    }

    /// <summary>
    /// 实时音频处理请求
    /// </summary>
    public class ProcessRealtimeAudioRequest
    {
        public string ConversationId { get; set; } = string.Empty;
        public byte[] AudioData { get; set; } = Array.Empty<byte>();
        public bool IsEndOfSpeech { get; set; } = false;
        public string AudioFormat { get; set; } = "wav";
    }

    /// <summary>
    /// 对话上下文
    /// </summary>
    public class ConversationContext
    {
        public string ConversationId { get; set; } = string.Empty;
        public string TemplateId { get; set; } = string.Empty;
        public List<ConversationTurn> History { get; set; } = new();
        public DateTime StartTime { get; set; }
        public DateTime LastUpdateTime { get; set; }
        public Dictionary<string, object> Metadata { get; set; } = new();
        public ConversationState State { get; set; } = ConversationState.Active;
    }

    /// <summary>
    /// 对话轮次
    /// </summary>
    public class ConversationTurn
    {
        public DateTime Timestamp { get; set; }
        public string UserInput { get; set; } = string.Empty;
        public string BotResponse { get; set; } = string.Empty;
        public string Emotion { get; set; } = string.Empty;
        public long ProcessingTime { get; set; }
        public bool FromCache { get; set; } = false;
    }

    /// <summary>
    /// 对话状态
    /// </summary>
    public enum ConversationState
    {
        Active,
        Paused,
        Ended,
        Error
    }

    /// <summary>
    /// 对话历史
    /// </summary>
    public class ConversationHistory
    {
        public string ConversationId { get; set; } = string.Empty;
        public string TemplateId { get; set; } = string.Empty;
        public DateTime StartTime { get; set; }
        public DateTime EndTime { get; set; }
        public int TurnCount { get; set; }
        public long TotalProcessingTime { get; set; }
        public ConversationState State { get; set; }
    }

    /// <summary>
    /// 对话统计信息
    /// </summary>
    public class ConversationStatistics
    {
        public int TotalConversations { get; set; }
        public int ActiveConversations { get; set; }
        public long AverageProcessingTime { get; set; }
        public long AverageConversationDuration { get; set; }
        public Dictionary<string, int> TemplateUsageCount { get; set; } = new();
        public Dictionary<string, int> EmotionDistribution { get; set; } = new();
        public Dictionary<string, long> DailyConversationCount { get; set; } = new();
    }

    /// <summary>
    /// 对话性能指标
    /// </summary>
    public class ConversationMetrics
    {
        public long AudioProcessingTime { get; set; }
        public long LLMResponseTime { get; set; }
        public long TTSProcessingTime { get; set; }
        public long VideoGenerationTime { get; set; }
        public long TotalProcessingTime { get; set; }
        public double CacheHitRate { get; set; }
        public string QualityUsed { get; set; } = string.Empty;
        public string ResponseModeUsed { get; set; } = string.Empty;
    }
}