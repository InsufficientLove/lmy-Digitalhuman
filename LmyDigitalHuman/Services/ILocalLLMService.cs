using LmyDigitalHuman.Services;
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
        Task<Models.LocalLLMResponse> ChatAsync(Models.LocalLLMRequest request);

        /// <summary>
        /// 生成响应（兼容性方法）
        /// </summary>
        Task<Models.LocalLLMResponse> GenerateResponseAsync(Models.LocalLLMRequest request);

        /// <summary>
        /// 流式对话
        /// </summary>
        IAsyncEnumerable<LocalLLMStreamResponse> ChatStreamAsync(Models.LocalLLMRequest request);

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

    // 模型类已移至 LmyDigitalHuman.Models.UnifiedModels 中统一管理

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

    // ChatMessage 类已移至 LmyDigitalHuman.Models.UnifiedModels 中统一管理

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