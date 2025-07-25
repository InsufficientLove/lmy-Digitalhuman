namespace LmyDigitalHuman.Services
{
    /// <summary>
    /// 本地化大模型服务接口
    /// </summary>
    public interface ILocalLLMService
    {
        /// <summary>
        /// 获取支持的模型列表
        /// </summary>
        Task<List<LocalLLMModel>> GetAvailableModelsAsync();

        /// <summary>
        /// 文本对话
        /// </summary>
        Task<LocalLLMResponse> ChatAsync(LocalLLMRequest request);

        /// <summary>
        /// 流式对话
        /// </summary>
        IAsyncEnumerable<LocalLLMStreamResponse> ChatStreamAsync(LocalLLMRequest request);

        /// <summary>
        /// 检查模型状态
        /// </summary>
        Task<ModelStatus> GetModelStatusAsync(string modelName);

        /// <summary>
        /// 加载模型
        /// </summary>
        Task<bool> LoadModelAsync(string modelName);

        /// <summary>
        /// 卸载模型
        /// </summary>
        Task<bool> UnloadModelAsync(string modelName);

        /// <summary>
        /// 获取模型性能统计
        /// </summary>
        Task<ModelPerformanceStats> GetModelPerformanceAsync(string modelName);

        /// <summary>
        /// 健康检查
        /// </summary>
        Task<bool> HealthCheckAsync();
    }

    /// <summary>
    /// 本地LLM模型信息
    /// </summary>
    public class LocalLLMModel
    {
        public string Name { get; set; } = string.Empty;
        public string DisplayName { get; set; } = string.Empty;
        public string Description { get; set; } = string.Empty;
        public string Version { get; set; } = string.Empty;
        public string Size { get; set; } = string.Empty;
        public string Language { get; set; } = string.Empty;
        public List<string> Capabilities { get; set; } = new();
        public bool IsLoaded { get; set; } = false;
        public string Status { get; set; } = "unloaded";
        public Dictionary<string, object> Parameters { get; set; } = new();
    }

    /// <summary>
    /// 本地LLM请求
    /// </summary>
    public class LocalLLMRequest
    {
        public string ModelName { get; set; } = "default";
        public string Message { get; set; } = string.Empty;
        public List<ChatMessage> History { get; set; } = new();
        public string SystemPrompt { get; set; } = string.Empty;
        public float Temperature { get; set; } = 0.7f;
        public int MaxTokens { get; set; } = 1000;
        public float TopP { get; set; } = 0.9f;
        public int TopK { get; set; } = 40;
        public bool Stream { get; set; } = false;
        public string ConversationId { get; set; } = string.Empty;
    }

    /// <summary>
    /// 本地LLM响应
    /// </summary>
    public class LocalLLMResponse
    {
        public bool Success { get; set; }
        public string Message { get; set; } = string.Empty;
        public string Response { get; set; } = string.Empty;
        public string ModelName { get; set; } = string.Empty;
        public string ConversationId { get; set; } = string.Empty;
        public int TokensUsed { get; set; }
        public string ProcessingTime { get; set; } = string.Empty;
        public Dictionary<string, object> Metadata { get; set; } = new();
    }

    /// <summary>
    /// 流式响应
    /// </summary>
    public class LocalLLMStreamResponse
    {
        public string Delta { get; set; } = string.Empty;
        public bool IsComplete { get; set; } = false;
        public string ConversationId { get; set; } = string.Empty;
        public int TokenIndex { get; set; } = 0;
    }

    /// <summary>
    /// 聊天消息
    /// </summary>
    public class ChatMessage
    {
        public string Role { get; set; } = "user"; // user, assistant, system
        public string Content { get; set; } = string.Empty;
        public DateTime Timestamp { get; set; } = DateTime.Now;
    }

    /// <summary>
    /// 模型状态
    /// </summary>
    public class ModelStatus
    {
        public string ModelName { get; set; } = string.Empty;
        public bool IsLoaded { get; set; } = false;
        public bool IsReady { get; set; } = false;
        public string Status { get; set; } = string.Empty;
        public long MemoryUsage { get; set; } = 0;
        public DateTime LoadedAt { get; set; }
        public string Error { get; set; } = string.Empty;
    }

    /// <summary>
    /// 模型性能统计
    /// </summary>
    public class ModelPerformanceStats
    {
        public string ModelName { get; set; } = string.Empty;
        public int TotalRequests { get; set; } = 0;
        public double AverageResponseTime { get; set; } = 0.0;
        public int AverageTokensPerSecond { get; set; } = 0;
        public long TotalTokensGenerated { get; set; } = 0;
        public DateTime LastRequestTime { get; set; }
        public double SuccessRate { get; set; } = 0.0;
        public Dictionary<string, object> AdditionalMetrics { get; set; } = new();
    }
} 