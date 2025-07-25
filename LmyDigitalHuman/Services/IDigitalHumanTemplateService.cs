using LmyDigitalHuman.Models;

namespace LmyDigitalHuman.Services
{
    /// <summary>
    /// 数字人模板管理服务接口
    /// </summary>
    public interface IDigitalHumanTemplateService
    {
        /// <summary>
        /// 创建数字人模板
        /// </summary>
        Task<CreateDigitalHumanTemplateResponse> CreateTemplateAsync(CreateDigitalHumanTemplateRequest request);

        /// <summary>
        /// 获取模板列表
        /// </summary>
        Task<GetTemplatesResponse> GetTemplatesAsync(GetTemplatesRequest request);

        /// <summary>
        /// 根据ID获取模板详情
        /// </summary>
        Task<DigitalHumanTemplate?> GetTemplateByIdAsync(string templateId);

        /// <summary>
        /// 更新模板信息
        /// </summary>
        Task<bool> UpdateTemplateAsync(string templateId, CreateDigitalHumanTemplateRequest request);

        /// <summary>
        /// 删除模板
        /// </summary>
        Task<bool> DeleteTemplateAsync(string templateId);

        /// <summary>
        /// 使用模板生成视频
        /// </summary>
        Task<GenerateWithTemplateResponse> GenerateWithTemplateAsync(GenerateWithTemplateRequest request);

        /// <summary>
        /// 批量预渲染常用内容
        /// </summary>
        Task<BatchPreRenderResponse> BatchPreRenderAsync(BatchPreRenderRequest request);

        /// <summary>
        /// 实时对话（使用模板）
        /// </summary>
        Task<RealtimeConversationResponse> RealtimeConversationAsync(RealtimeConversationRequest request);

        /// <summary>
        /// 获取模板统计信息
        /// </summary>
        Task<TemplateStatistics> GetTemplateStatisticsAsync();

        /// <summary>
        /// 验证模板是否可用
        /// </summary>
        Task<bool> ValidateTemplateAsync(string templateId);

        /// <summary>
        /// 获取模板预览视频
        /// </summary>
        Task<string?> GetTemplatePreviewAsync(string templateId);

        /// <summary>
        /// 复制模板
        /// </summary>
        Task<CreateDigitalHumanTemplateResponse> CloneTemplateAsync(string templateId, string newName);

        /// <summary>
        /// 导出模板配置
        /// </summary>
        Task<byte[]> ExportTemplateAsync(string templateId);

        /// <summary>
        /// 导入模板配置
        /// </summary>
        Task<CreateDigitalHumanTemplateResponse> ImportTemplateAsync(IFormFile configFile);

        /// <summary>
        /// 获取模板缓存状态
        /// </summary>
        Task<Dictionary<string, object>> GetTemplateCacheStatusAsync(string templateId);

        /// <summary>
        /// 清理模板缓存
        /// </summary>
        Task<bool> ClearTemplateCacheAsync(string templateId);
    }
} 