using LmyDigitalHuman.Services;
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
        
        // 极速实时推理（使用预处理结果）
        Task<DigitalHumanResponse> SimulateRealtimeInference(DigitalHumanRequest request);
    }

    // DTO模型已移至UnifiedModels.cs中统一管理
}