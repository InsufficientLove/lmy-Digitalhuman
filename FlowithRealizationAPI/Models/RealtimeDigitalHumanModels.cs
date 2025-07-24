using System.ComponentModel.DataAnnotations;

namespace FlowithRealizationAPI.Models
{
    /// <summary>
    /// 立即响应对话请求
    /// </summary>
    public class InstantChatRequest
    {
        [Required]
        public string Text { get; set; } = string.Empty;

        /// <summary>
        /// 数字人头像ID
        /// </summary>
        public string AvatarId { get; set; } = "default";

        /// <summary>
        /// 响应模式：instant(立即), fast(快速), quality(高质量)
        /// </summary>
        public string ResponseMode { get; set; } = "instant";

        /// <summary>
        /// 视频质量：low, medium, high, ultra
        /// </summary>
        public string Quality { get; set; } = "medium";

        /// <summary>
        /// 是否启用情感表达
        /// </summary>
        public bool EnableEmotion { get; set; } = true;

        /// <summary>
        /// 语音合成参数
        /// </summary>
        public VoiceSettings? VoiceSettings { get; set; }
    }

    /// <summary>
    /// 语音聊天请求
    /// </summary>
    public class VoiceChatRequest
    {
        public IFormFile AudioFile { get; set; }
        public string AvatarId { get; set; }
        public string ResponseMode { get; set; } = "instant";
        public string Quality { get; set; } = "medium";
    }

    /// <summary>
    /// 流式对话请求
    /// </summary>
    public class StreamingChatRequest
    {
        public string Text { get; set; }
        public string AvatarId { get; set; }
        public string Voice { get; set; } = "zh-CN-XiaoxiaoNeural";
        public string Model { get; set; } = "qwen2.5:14b-instruct-q4_0";
        public bool EnableEmotion { get; set; } = true;
        public string Quality { get; set; } = "medium";
        public string SystemPrompt { get; set; }
    }

    /// <summary>
    /// 流式对话响应
    /// </summary>
    public class StreamingChatResponse
    {
        public string Type { get; set; } // "text", "audio", "video", "complete"
        public string TextDelta { get; set; }
        public string AudioChunkUrl { get; set; }
        public byte[] AudioData { get; set; }
        public string VideoUrl { get; set; }
        public bool IsComplete { get; set; }
        public Dictionary<string, object> Metadata { get; set; } = new();
    }

    /// <summary>
    /// TTS流式请求
    /// </summary>
    public class TTSStreamRequest
    {
        public string Text { get; set; }
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
        public byte[] AudioData { get; set; }
        public int ChunkIndex { get; set; }
        public bool IsComplete { get; set; }
        public int TotalDuration { get; set; } // 毫秒
    }

    /// <summary>
    /// 生成视频请求
    /// </summary>
    public class GenerateVideoRequest
    {
        public string AvatarId { get; set; }
        public string AudioUrl { get; set; }
        public byte[] AudioData { get; set; }
        public string Quality { get; set; } = "medium";
        public bool Async { get; set; } = false;
    }

    /// <summary>
    /// 生成视频响应
    /// </summary>
    public class GenerateVideoResponse
    {
        public bool Success { get; set; }
        public string VideoUrl { get; set; }
        public string TaskId { get; set; }
        public string Status { get; set; } // "processing", "completed", "failed"
        public int ProcessingTime { get; set; }
    }

    /// <summary>
    /// 创建头像请求
    /// </summary>
    public class CreateAvatarRequest
    {
        [Required]
        public IFormFile ImageFile { get; set; } = default!;

        [Required]
        public string Name { get; set; } = string.Empty;

        public string Description { get; set; } = string.Empty;

        /// <summary>
        /// 参考音频文件（可选）
        /// </summary>
        public IFormFile? ReferenceAudioFile { get; set; }

        /// <summary>
        /// 参考文本（用于音频训练）
        /// </summary>
        public string? ReferenceText { get; set; }

        /// <summary>
        /// 头像风格：realistic, anime, cartoon
        /// </summary>
        public string Style { get; set; } = "realistic";
    }

    /// <summary>
    /// 语音设置
    /// </summary>
    public class VoiceSettings
    {
        /// <summary>
        /// 语音速度 (0.5-2.0)
        /// </summary>
        public float Speed { get; set; } = 1.0f;

        /// <summary>
        /// 音调 (-20 to 20)
        /// </summary>
        public float Pitch { get; set; } = 0.0f;

        /// <summary>
        /// 音量 (0.0-1.0)
        /// </summary>
        public float Volume { get; set; } = 1.0f;

        /// <summary>
        /// 语音风格：friendly, professional, excited, calm
        /// </summary>
        public string Style { get; set; } = "friendly";
    }

    /// <summary>
    /// 立即响应对话结果
    /// </summary>
    public class InstantChatResponse
    {
        public bool Success { get; set; }
        public string ResponseText { get; set; } = string.Empty;
        public string VideoUrl { get; set; } = string.Empty;
        public string AudioUrl { get; set; } = string.Empty;
        public ResponseMetadata Metadata { get; set; } = new();
    }

    /// <summary>
    /// 响应元数据
    /// </summary>
    public class ResponseMetadata
    {
        /// <summary>
        /// 响应类型：prerendered, realtime, cached
        /// </summary>
        public string ResponseType { get; set; } = string.Empty;

        /// <summary>
        /// 处理时间（毫秒）
        /// </summary>
        public long ProcessingTime { get; set; }

        /// <summary>
        /// 视频时长（秒）
        /// </summary>
        public double VideoDuration { get; set; }

        /// <summary>
        /// 视频质量信息
        /// </summary>
        public VideoQualityInfo Quality { get; set; } = new();

        /// <summary>
        /// 使用的头像ID
        /// </summary>
        public string AvatarId { get; set; } = string.Empty;

        /// <summary>
        /// 情感分析结果
        /// </summary>
        public EmotionAnalysis? Emotion { get; set; }
    }

    /// <summary>
    /// 视频质量信息
    /// </summary>
    public class VideoQualityInfo
    {
        public string Resolution { get; set; } = string.Empty;
        public int Fps { get; set; }
        public int Bitrate { get; set; }
        public string Codec { get; set; } = string.Empty;
        public long FileSize { get; set; }
    }

    /// <summary>
    /// 情感分析结果
    /// </summary>
    public class EmotionAnalysis
    {
        public string PrimaryEmotion { get; set; } = string.Empty;
        public float Confidence { get; set; }
        public Dictionary<string, float> EmotionScores { get; set; } = new();
    }

    /// <summary>
    /// 语音转文本结果
    /// </summary>
    public class WhisperTranscriptionResult
    {
        public string Text { get; set; } = string.Empty;
        public float Confidence { get; set; }
        public string Language { get; set; } = string.Empty;
        public long ProcessingTime { get; set; }
        public List<WordTimestamp> WordTimestamps { get; set; } = new();
    }

    /// <summary>
    /// 词语时间戳
    /// </summary>
    public class WordTimestamp
    {
        public string Word { get; set; } = string.Empty;
        public float Start { get; set; }
        public float End { get; set; }
        public float Confidence { get; set; }
    }

    /// <summary>
    /// 数字人头像信息
    /// </summary>
    public class DigitalHumanAvatar
    {
        public string Id { get; set; } = string.Empty;
        public string Name { get; set; } = string.Empty;
        public string Description { get; set; } = string.Empty;
        public string PreviewImageUrl { get; set; } = string.Empty;
        public string PreviewVideoUrl { get; set; } = string.Empty;
        public string Style { get; set; } = string.Empty;
        public bool IsCustom { get; set; }
        public DateTime CreatedAt { get; set; }
        public AvatarCapabilities Capabilities { get; set; } = new();
    }

    /// <summary>
    /// 头像能力信息
    /// </summary>
    public class AvatarCapabilities
    {
        public bool SupportsEmotion { get; set; } = true;
        public bool SupportsLipSync { get; set; } = true;
        public bool SupportsEyeTracking { get; set; } = false;
        public bool SupportsHeadMovement { get; set; } = true;
        public List<string> SupportedLanguages { get; set; } = new();
        public List<string> SupportedEmotions { get; set; } = new();
    }

    /// <summary>
    /// 创建头像结果
    /// </summary>
    public class CreateAvatarResponse
    {
        public bool Success { get; set; }
        public string AvatarId { get; set; } = string.Empty;
        public string Message { get; set; } = string.Empty;
        public DigitalHumanAvatar? Avatar { get; set; }
        public long ProcessingTime { get; set; }
    }

    /// <summary>
    /// 预渲染视频库状态
    /// </summary>
    public class PrerenderedStatus
    {
        public int TotalVideos { get; set; }
        public int AvailableVideos { get; set; }
        public int ProcessingVideos { get; set; }
        public long TotalStorage { get; set; }
        public long UsedStorage { get; set; }
        public DateTime LastUpdate { get; set; }
        public List<PrerenderedVideo> RecentVideos { get; set; } = new();
    }

    /// <summary>
    /// 预渲染视频信息
    /// </summary>
    public class PrerenderedVideo
    {
        public string Id { get; set; } = string.Empty;
        public string Text { get; set; } = string.Empty;
        public string VideoUrl { get; set; } = string.Empty;
        public string AvatarId { get; set; } = string.Empty;
        public double Duration { get; set; }
        public long FileSize { get; set; }
        public DateTime CreatedAt { get; set; }
        public int UseCount { get; set; }
    }

    /// <summary>
    /// 系统健康状态
    /// </summary>
    public class SystemHealth
    {
        public bool IsHealthy { get; set; }
        public string Status { get; set; } = string.Empty;
        public Dictionary<string, ServiceHealth> Services { get; set; } = new();
        public SystemResources Resources { get; set; } = new();
        public DateTime CheckTime { get; set; }
    }

    /// <summary>
    /// 服务健康状态
    /// </summary>
    public class ServiceHealth
    {
        public bool IsHealthy { get; set; }
        public string Status { get; set; } = string.Empty;
        public long ResponseTime { get; set; }
        public string? ErrorMessage { get; set; }
        public DateTime LastCheck { get; set; }
    }

    /// <summary>
    /// 系统资源状态
    /// </summary>
    public class SystemResources
    {
        public float CpuUsage { get; set; }
        public float MemoryUsage { get; set; }
        public float GpuUsage { get; set; }
        public float DiskUsage { get; set; }
        public long AvailableMemory { get; set; }
        public long TotalMemory { get; set; }
    }
} 