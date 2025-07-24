using FlowithRealizationAPI.Models;

namespace FlowithRealizationAPI.Services
{
    /// <summary>
    /// 实时数字人服务接口
    /// </summary>
    public interface IRealtimeDigitalHumanService
    {
        /// <summary>
        /// 处理立即响应对话
        /// </summary>
        Task<InstantChatResponse> ProcessInstantChatAsync(InstantChatRequest request);

        /// <summary>
        /// 创建自定义数字人头像
        /// </summary>
        Task<CreateAvatarResponse> CreateAvatarAsync(CreateAvatarRequest request);

        /// <summary>
        /// 获取可用的数字人头像列表
        /// </summary>
        Task<List<DigitalHumanAvatar>> GetAvailableAvatarsAsync();

        /// <summary>
        /// 获取预渲染视频库状态
        /// </summary>
        Task<PrerenderedStatus> GetPrerenderedStatusAsync();

        /// <summary>
        /// 获取系统健康状态
        /// </summary>
        Task<SystemHealth> GetSystemHealthAsync();

        /// <summary>
        /// 预渲染常用对话视频
        /// </summary>
        Task<bool> PreRenderCommonPhrasesAsync(string avatarId, List<string> phrases);

        /// <summary>
        /// 清理过期的预渲染视频
        /// </summary>
        Task<bool> CleanupExpiredVideosAsync();

        /// <summary>
        /// 获取视频缓存统计
        /// </summary>
        Task<Dictionary<string, object>> GetCacheStatisticsAsync();

        /// <summary>
        /// 流式对话处理
        /// </summary>
        IAsyncEnumerable<StreamingChatResponse> ProcessStreamingChatAsync(StreamingChatRequest request);

        /// <summary>
        /// 生成实时数字人视频（基于音频流）
        /// </summary>
        Task<GenerateVideoResponse> GenerateRealtimeVideoAsync(GenerateVideoRequest request);

        /// <summary>
        /// 流式文本转语音
        /// </summary>
        IAsyncEnumerable<AudioChunkResponse> TextToSpeechStreamAsync(TTSStreamRequest request);
    }
} 