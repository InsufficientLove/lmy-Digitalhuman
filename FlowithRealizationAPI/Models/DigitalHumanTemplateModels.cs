using System.ComponentModel.DataAnnotations;

namespace FlowithRealizationAPI.Models
{
    /// <summary>
    /// 数字人模板创建请求
    /// </summary>
    public class CreateDigitalHumanTemplateRequest
    {
        [Required]
        public string TemplateName { get; set; } = string.Empty;

        [Required]
        public IFormFile ImageFile { get; set; } = default!;

        /// <summary>
        /// 模板描述
        /// </summary>
        public string Description { get; set; } = string.Empty;

        /// <summary>
        /// 模板类型：headshot(头像), half_body(半身), full_body(全身)
        /// </summary>
        public string TemplateType { get; set; } = "headshot";

        /// <summary>
        /// 性别：male, female, neutral
        /// </summary>
        public string Gender { get; set; } = "neutral";

        /// <summary>
        /// 年龄范围：child, young, adult, elderly
        /// </summary>
        public string AgeRange { get; set; } = "adult";

        /// <summary>
        /// 风格：professional, casual, friendly
        /// </summary>
        public string Style { get; set; } = "professional";

        /// <summary>
        /// 是否启用情感表达
        /// </summary>
        public bool EnableEmotion { get; set; } = true;

        /// <summary>
        /// 默认语音设置
        /// </summary>
        public VoiceSettings? DefaultVoiceSettings { get; set; }

        /// <summary>
        /// 自定义参数
        /// </summary>
        public Dictionary<string, object>? CustomParameters { get; set; }
    }

    /// <summary>
    /// 数字人模板创建响应
    /// </summary>
    public class CreateDigitalHumanTemplateResponse
    {
        public bool Success { get; set; }
        public string TemplateId { get; set; } = string.Empty;
        public string Message { get; set; } = string.Empty;
        public DigitalHumanTemplate? Template { get; set; }
        public string ProcessingTime { get; set; } = string.Empty;
    }

    /// <summary>
    /// 数字人模板信息
    /// </summary>
    public class DigitalHumanTemplate
    {
        public string TemplateId { get; set; } = string.Empty;
        public string TemplateName { get; set; } = string.Empty;
        public string Description { get; set; } = string.Empty;
        public string TemplateType { get; set; } = string.Empty;
        public string Gender { get; set; } = string.Empty;
        public string AgeRange { get; set; } = string.Empty;
        public string Style { get; set; } = string.Empty;
        public bool EnableEmotion { get; set; }
        public string ImagePath { get; set; } = string.Empty;
        public string PreviewVideoPath { get; set; } = string.Empty;
        public VoiceSettings? DefaultVoiceSettings { get; set; }
        public Dictionary<string, object>? CustomParameters { get; set; }
        public DateTime CreatedAt { get; set; }
        public DateTime UpdatedAt { get; set; }
        public bool IsActive { get; set; } = true;
        public int UsageCount { get; set; } = 0;
        public string Status { get; set; } = "ready"; // ready, processing, error
    }

    /// <summary>
    /// 使用模板生成视频请求
    /// </summary>
    public class GenerateWithTemplateRequest
    {
        [Required]
        public string TemplateId { get; set; } = string.Empty;

        [Required]
        public string Text { get; set; } = string.Empty;

        /// <summary>
        /// 响应模式：instant(立即), fast(快速), quality(高质量)
        /// </summary>
        public string ResponseMode { get; set; } = "fast";

        /// <summary>
        /// 视频质量：low, medium, high, ultra
        /// </summary>
        public string Quality { get; set; } = "medium";

        /// <summary>
        /// 情感表达：neutral, happy, sad, angry, surprised
        /// </summary>
        public string Emotion { get; set; } = "neutral";

        /// <summary>
        /// 语音设置（可覆盖模板默认设置）
        /// </summary>
        public VoiceSettings? VoiceSettings { get; set; }

        /// <summary>
        /// 是否使用预渲染缓存
        /// </summary>
        public bool UseCache { get; set; } = true;
    }

    /// <summary>
    /// 使用模板生成视频响应
    /// </summary>
    public class GenerateWithTemplateResponse
    {
        public bool Success { get; set; }
        public string Message { get; set; } = string.Empty;
        public string VideoUrl { get; set; } = string.Empty;
        public string AudioUrl { get; set; } = string.Empty;
        public string ProcessingTime { get; set; } = string.Empty;
        public string ResponseMode { get; set; } = string.Empty;
        public bool FromCache { get; set; } = false;
        public DigitalHumanTemplate? Template { get; set; }
    }

    /// <summary>
    /// 模板列表请求
    /// </summary>
    public class GetTemplatesRequest
    {
        /// <summary>
        /// 模板类型过滤
        /// </summary>
        public string? TemplateType { get; set; }

        /// <summary>
        /// 性别过滤
        /// </summary>
        public string? Gender { get; set; }

        /// <summary>
        /// 风格过滤
        /// </summary>
        public string? Style { get; set; }

        /// <summary>
        /// 搜索关键词
        /// </summary>
        public string? SearchKeyword { get; set; }

        /// <summary>
        /// 分页参数
        /// </summary>
        public int Page { get; set; } = 1;
        public int PageSize { get; set; } = 20;

        /// <summary>
        /// 排序方式：created_desc, usage_desc, name_asc
        /// </summary>
        public string SortBy { get; set; } = "created_desc";
    }

    /// <summary>
    /// 模板列表响应
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

    /// <summary>
    /// 模板统计信息
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
    /// 批量预渲染请求
    /// </summary>
    public class BatchPreRenderRequest
    {
        [Required]
        public string TemplateId { get; set; } = string.Empty;

        [Required]
        public List<string> TextList { get; set; } = new();

        /// <summary>
        /// 视频质量
        /// </summary>
        public string Quality { get; set; } = "medium";

        /// <summary>
        /// 情感表达列表（与TextList对应）
        /// </summary>
        public List<string>? EmotionList { get; set; }
    }

    /// <summary>
    /// 批量预渲染响应
    /// </summary>
    public class BatchPreRenderResponse
    {
        public bool Success { get; set; }
        public string Message { get; set; } = string.Empty;
        public int TotalCount { get; set; }
        public int SuccessCount { get; set; }
        public int FailedCount { get; set; }
        public List<string> FailedTexts { get; set; } = new();
        public string ProcessingTime { get; set; } = string.Empty;
    }

    /// <summary>
    /// 实时对话请求（使用模板）
    /// </summary>
    public class RealtimeConversationRequest
    {
        [Required]
        public string TemplateId { get; set; } = string.Empty;

        /// <summary>
        /// 输入类型：text, audio
        /// </summary>
        public string InputType { get; set; } = "text";

        /// <summary>
        /// 文本输入
        /// </summary>
        public string? Text { get; set; }

        /// <summary>
        /// 音频输入
        /// </summary>
        public IFormFile? AudioFile { get; set; }

        /// <summary>
        /// 对话上下文ID（用于多轮对话）
        /// </summary>
        public string? ConversationId { get; set; }

        /// <summary>
        /// 响应模式
        /// </summary>
        public string ResponseMode { get; set; } = "fast";

        /// <summary>
        /// 视频质量
        /// </summary>
        public string Quality { get; set; } = "medium";

        /// <summary>
        /// 是否启用情感识别
        /// </summary>
        public bool EnableEmotionDetection { get; set; } = true;
    }

    /// <summary>
    /// 实时对话响应
    /// </summary>
    public class RealtimeConversationResponse
    {
        public bool Success { get; set; }
        public string Message { get; set; } = string.Empty;
        public string ConversationId { get; set; } = string.Empty;
        public string RecognizedText { get; set; } = string.Empty;
        public string ResponseText { get; set; } = string.Empty;
        public string VideoUrl { get; set; } = string.Empty;
        public string AudioUrl { get; set; } = string.Empty;
        public string DetectedEmotion { get; set; } = string.Empty;
        public string ProcessingTime { get; set; } = string.Empty;
        public bool FromCache { get; set; } = false;
        public DigitalHumanTemplate? Template { get; set; }
    }
} 