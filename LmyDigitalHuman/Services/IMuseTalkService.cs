using LmyDigitalHuman.Models;

namespace LmyDigitalHuman.Services
{
    public interface IMuseTalkService
    {
        // 基础视频生成
        Task<DigitalHumanResponse> GenerateVideoAsync(DigitalHumanRequest request);
        Task<List<DigitalHumanResponse>> GenerateBatchVideosAsync(List<DigitalHumanRequest> requests);

        // 高性能生成（使用队列）
        Task<string> QueueVideoGenerationAsync(DigitalHumanRequest request);
        Task<DigitalHumanResponse?> GetQueuedVideoResultAsync(string jobId);
        Task<List<QueuedJob>> GetQueueStatusAsync();
        Task<bool> CancelQueuedJobAsync(string jobId);

        // 模板管理
        Task<List<DigitalHumanTemplate>> GetAvailableTemplatesAsync();
        Task<DigitalHumanTemplate> CreateTemplateAsync(CreateTemplateRequest request);
        Task<bool> DeleteTemplateAsync(string templateId);
        Task<bool> ValidateTemplateAsync(string templateId);

        // 预处理与优化
        Task<PreprocessingResult> PreprocessTemplateAsync(string templateId);
        Task<bool> WarmupTemplateAsync(string templateId);
        Task<string> GetOptimalSettingsAsync(string templateId, string quality);

        // 缓存管理
        Task<bool> CacheVideoResultAsync(string cacheKey, DigitalHumanResponse response);
        Task<DigitalHumanResponse?> GetCachedVideoAsync(string cacheKey);
        Task<bool> ClearVideoCache(string? templateId = null);
        Task<CacheStatistics> GetCacheStatisticsAsync();

        // 服务健康与监控
        Task<bool> IsServiceHealthyAsync();
        Task<ServiceMetrics> GetServiceMetricsAsync();
        Task<List<ProcessingJob>> GetActiveJobsAsync();
        Task<bool> ScaleWorkersAsync(int workerCount);

        // 音频优化
        Task<AudioOptimizationResult> OptimizeAudioForGenerationAsync(string audioPath);
        Task<bool> ValidateAudioAsync(string audioPath);

        // 实时生成支持
        Task<string> StartStreamingGenerationAsync(StreamingGenerationRequest request);
        Task<StreamingGenerationChunk?> GetGenerationChunkAsync(string sessionId);
        Task<bool> EndStreamingGenerationAsync(string sessionId);
    }

    public class DigitalHumanRequest
    {
        public string AvatarImagePath { get; set; } = string.Empty;
        public string AudioPath { get; set; } = string.Empty;
        public string Text { get; set; } = string.Empty;
        public string OutputDirectory { get; set; } = string.Empty;
        public int? BboxShift { get; set; }
        public int? Fps { get; set; } = 25;
        public int? BatchSize { get; set; } = 4;
        public string Quality { get; set; } = "medium";
        public bool EnableEmotion { get; set; } = true;
        public string? CacheKey { get; set; }
        public int Priority { get; set; } = 5; // 1-10, 10为最高优先级
        public Dictionary<string, object>? CustomParameters { get; set; }
    }

    public class DigitalHumanResponse
    {
        public bool Success { get; set; }
        public string VideoUrl { get; set; } = string.Empty;
        public string VideoPath { get; set; } = string.Empty;
        public long ProcessingTime { get; set; }
        public string Message { get; set; } = string.Empty;
        public string Error { get; set; } = string.Empty;
        public DigitalHumanMetadata? Metadata { get; set; }
        public string? JobId { get; set; }
        public bool FromCache { get; set; } = false;
        public DateTime CompletedAt { get; set; }
    }

    public class DigitalHumanMetadata
    {
        public string Resolution { get; set; } = string.Empty;
        public int Fps { get; set; }
        public double Duration { get; set; }
        public long FileSize { get; set; }
        public string Quality { get; set; } = string.Empty;
        public string TemplateId { get; set; } = string.Empty;
        public Dictionary<string, object> ProcessingStats { get; set; } = new();
    }

    public class CreateTemplateRequest
    {
        public string Name { get; set; } = string.Empty;
        public string Description { get; set; } = string.Empty;
        public string ImagePath { get; set; } = string.Empty;
        public string Gender { get; set; } = "female";
        public string Style { get; set; } = "professional";
        public Dictionary<string, object>? OptimizationSettings { get; set; }
    }

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
        public int Priority { get; set; }
        public string? Error { get; set; }
        public DigitalHumanResponse? Result { get; set; }
        public long EstimatedProcessingTime { get; set; }
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

    /// <summary>
    /// 预处理结果
    /// </summary>
    public class PreprocessingResult
    {
        public bool Success { get; set; }
        public string TemplateId { get; set; } = string.Empty;
        public Dictionary<string, object> OptimizedSettings { get; set; } = new();
        public long PreprocessingTime { get; set; }
        public List<string> Recommendations { get; set; } = new();
        public string Error { get; set; } = string.Empty;
    }

    /// <summary>
    /// 缓存统计
    /// </summary>
    public class CacheStatistics
    {
        public long TotalCachedItems { get; set; }
        public long TotalCacheSize { get; set; }
        public double CacheHitRate { get; set; }
        public Dictionary<string, int> CacheHitsByTemplate { get; set; } = new();
        public DateTime LastCleanup { get; set; }
    }

    /// <summary>
    /// 服务性能指标
    /// </summary>
    public class ServiceMetrics
    {
        public int ActiveWorkers { get; set; }
        public int QueueLength { get; set; }
        public long AverageProcessingTime { get; set; }
        public double ThroughputPerHour { get; set; }
        public Dictionary<string, object> ResourceUsage { get; set; } = new();
        public List<string> PerformanceWarnings { get; set; } = new();
    }

    /// <summary>
    /// 处理任务
    /// </summary>
    public class ProcessingJob
    {
        public string JobId { get; set; } = string.Empty;
        public string TemplateId { get; set; } = string.Empty;
        public DateTime StartTime { get; set; }
        public long ElapsedTime { get; set; }
        public long EstimatedRemainingTime { get; set; }
        public float Progress { get; set; }
        public string CurrentStep { get; set; } = string.Empty;
    }

    /// <summary>
    /// 音频优化结果
    /// </summary>
    public class AudioOptimizationResult
    {
        public bool Success { get; set; }
        public string OptimizedAudioPath { get; set; } = string.Empty;
        public string OriginalFormat { get; set; } = string.Empty;
        public string OptimizedFormat { get; set; } = string.Empty;
        public long OriginalSize { get; set; }
        public long OptimizedSize { get; set; }
        public float QualityScore { get; set; }
        public List<string> AppliedOptimizations { get; set; } = new();
        public long ProcessingTime { get; set; }
    }

    /// <summary>
    /// 流式生成请求
    /// </summary>
    public class StreamingGenerationRequest
    {
        public string TemplateId { get; set; } = string.Empty;
        public string AudioPath { get; set; } = string.Empty;
        public string Quality { get; set; } = "medium";
        public int ChunkSize { get; set; } = 1024; // KB
        public bool EnableProgressUpdates { get; set; } = true;
    }

    /// <summary>
    /// 流式生成数据块
    /// </summary>
    public class StreamingGenerationChunk
    {
        public byte[] VideoData { get; set; } = Array.Empty<byte>();
        public int ChunkIndex { get; set; }
        public bool IsLastChunk { get; set; }
        public float Progress { get; set; }
        public string CurrentStep { get; set; } = string.Empty;
        public long ElapsedTime { get; set; }
    }
}