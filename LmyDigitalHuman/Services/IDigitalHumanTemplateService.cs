using LmyDigitalHuman.Models;

namespace LmyDigitalHuman.Services
{
    public interface IDigitalHumanTemplateService
    {
        // 基础模板管理
        Task<CreateDigitalHumanTemplateResponse> CreateTemplateAsync(CreateDigitalHumanTemplateRequest request);
        Task<GetTemplatesResponse> GetTemplatesAsync(GetTemplatesRequest request);
        Task<DigitalHumanTemplate?> GetTemplateByIdAsync(string templateId);
        Task<bool> DeleteTemplateAsync(string templateId);
        Task<bool> UpdateTemplateAsync(string templateId, CreateDigitalHumanTemplateRequest request);

        // 模板生成与对话
        Task<GenerateWithTemplateResponse> GenerateWithTemplateAsync(GenerateWithTemplateRequest request);
        Task<RealtimeConversationResponse> RealtimeConversationAsync(RealtimeConversationRequest request);

        // 批处理与预渲染
        Task<BatchPreRenderResponse> BatchPreRenderAsync(BatchPreRenderRequest request);
        Task<List<string>> GetPreRenderedVideosAsync(string templateId);
        Task<bool> ClearPreRenderedCacheAsync(string templateId);

        // 统计与监控
        Task<TemplateStatistics> GetStatisticsAsync();
        Task<bool> IncrementUsageCountAsync(string templateId);

        // 性能优化
        Task<bool> ValidateTemplateAsync(string templateId);
        Task<string> GetOptimalQualitySettingAsync(string templateId, string responseMode);
        Task<bool> WarmupTemplateAsync(string templateId);

        // 并发处理
        Task<List<GenerateWithTemplateResponse>> ProcessBatchRequestsAsync(List<GenerateWithTemplateRequest> requests);
        Task<bool> IsTemplateAvailableForProcessingAsync(string templateId);
        
        // 缓存管理
        Task<bool> RefreshTemplateCacheAsync(string? templateId = null);
        Task<long> GetCacheSizeAsync();
        Task<bool> ClearExpiredCacheAsync();
    }

    /// <summary>
    /// 更新数字人模板请求
    /// </summary>
    public class UpdateDigitalHumanTemplateRequest
    {
        public string? TemplateName { get; set; }
        public string? Description { get; set; }
        public bool? EnableEmotion { get; set; }
        public VoiceSettings? DefaultVoiceSettings { get; set; }
        public Dictionary<string, object>? CustomParameters { get; set; }
        public bool? IsActive { get; set; }
    }
} 