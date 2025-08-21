using LmyDigitalHuman.Services;
using LmyDigitalHuman.Models;

namespace LmyDigitalHuman.Services
{
    /// <summary>
    /// TTS服务接口
    /// </summary>
    public interface ITTSService
    {
        /// <summary>
        /// 文本转语音
        /// </summary>
        Task<TTSResponse> TextToSpeechAsync(TTSRequest request);

        /// <summary>
        /// 获取可用的语音列表
        /// </summary>
        Task<List<VoiceSettings>> GetAvailableVoicesAsync();
    }
}