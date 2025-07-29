using LmyDigitalHuman.Models;

namespace LmyDigitalHuman.Services
{
    /// <summary>
    /// 流式TTS服务接口
    /// </summary>
    public interface IStreamingTTSService
    {
        /// <summary>
        /// 开始流式TTS
        /// </summary>
        Task<string> StartStreamingTTSAsync(StreamingTTSRequest request);

        /// <summary>
        /// 获取TTS音频块
        /// </summary>
        Task<byte[]> GetTTSChunkAsync(string sessionId);

        /// <summary>
        /// 结束流式TTS
        /// </summary>
        Task<bool> EndStreamingTTSAsync(string sessionId);

        /// <summary>
        /// 检查会话状态
        /// </summary>
        Task<bool> IsSessionActiveAsync(string sessionId);

        /// <summary>
        /// 获取支持的语音列表
        /// </summary>
        Task<List<VoiceInfo>> GetAvailableVoicesAsync();
    }
}