using FlowithRealizationAPI.Models;

namespace FlowithRealizationAPI.Services
{
    /// <summary>
    /// Whisper语音转文本服务接口
    /// </summary>
    public interface IWhisperService
    {
        /// <summary>
        /// 语音转文本
        /// </summary>
        Task<WhisperTranscriptionResult> TranscribeAsync(IFormFile audioFile);

        /// <summary>
        /// 语音转文本（支持多种音频格式）
        /// </summary>
        Task<WhisperTranscriptionResult> TranscribeAsync(Stream audioStream, string fileName);

        /// <summary>
        /// 批量语音转文本
        /// </summary>
        Task<List<WhisperTranscriptionResult>> TranscribeBatchAsync(List<IFormFile> audioFiles);

        /// <summary>
        /// 检查Whisper服务状态
        /// </summary>
        Task<bool> IsServiceHealthyAsync();

        /// <summary>
        /// 获取支持的音频格式
        /// </summary>
        Task<List<string>> GetSupportedFormatsAsync();

        /// <summary>
        /// 获取可用的语言模型
        /// </summary>
        Task<List<string>> GetAvailableModelsAsync();
    }
} 