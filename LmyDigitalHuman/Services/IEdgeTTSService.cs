using LmyDigitalHuman.Models;

namespace LmyDigitalHuman.Services
{
    /// <summary>
    /// Edge TTS 语音合成服务接口
    /// </summary>
    public interface IEdgeTTSService
    {
        /// <summary>
        /// 文本转语音（完整）
        /// </summary>
        Task<TTSResponse> TextToSpeechAsync(TTSRequest request);

        /// <summary>
        /// 生成音频（兼容性方法）
        /// </summary>
        Task<byte[]> GenerateAudioAsync(TTSRequest request);

        /// <summary>
        /// 转换文本为语音（兼容性方法）
        /// </summary>
        Task<TTSResponse> ConvertTextToSpeechAsync(string text, string voice = "zh-CN-XiaoxiaoNeural");

        /// <summary>
        /// 流式文本转语音
        /// </summary>
        IAsyncEnumerable<AudioChunkResponse> TextToSpeechStreamAsync(TTSStreamRequest request);

        /// <summary>
        /// 获取可用的语音列表
        /// </summary>
        Task<List<VoiceInfo>> GetAvailableVoicesAsync();

        /// <summary>
        /// 获取指定语言的语音列表
        /// </summary>
        Task<List<VoiceInfo>> GetVoicesByLanguageAsync(string language);

        /// <summary>
        /// 健康检查
        /// </summary>
        Task<bool> IsHealthyAsync();
    }

    // DTO模型已移至UnifiedModels.cs中统一管理
}