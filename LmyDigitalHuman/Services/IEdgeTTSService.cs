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

    /// <summary>
    /// TTS请求
    /// </summary>
    public class TTSRequest
    {
        public string Text { get; set; } = string.Empty;
        public string Voice { get; set; } = "zh-CN-XiaoxiaoNeural";
        public string Rate { get; set; } = "1.0";
        public string Pitch { get; set; } = "0Hz";
        public string OutputFormat { get; set; } = "audio-16khz-128kbitrate-mono-mp3";
        public string OutputPath { get; set; } = string.Empty;
    }

    /// <summary>
    /// TTS响应
    /// </summary>
    public class TTSResponse
    {
        public bool Success { get; set; }
        public string AudioPath { get; set; } = string.Empty;
        public string AudioUrl { get; set; } = string.Empty;
        public int Duration { get; set; } // 毫秒
        public long FileSize { get; set; } // 字节
        public int ProcessingTime { get; set; } // 毫秒
    }

    /// <summary>
    /// 语音信息
    /// </summary>
    public class VoiceInfo
    {
        public string Name { get; set; } = string.Empty;
        public string DisplayName { get; set; } = string.Empty;
        public string Language { get; set; } = string.Empty;
        public string Gender { get; set; } = string.Empty;
        public string Style { get; set; } = string.Empty;
        public List<string> SupportedStyles { get; set; } = new();
    }

    /// <summary>
    /// 流式TTS请求
    /// </summary>
    public class TTSStreamRequest
    {
        public string Text { get; set; } = string.Empty;
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
        public byte[] AudioData { get; set; } = Array.Empty<byte>();
        public int ChunkIndex { get; set; }
        public bool IsComplete { get; set; }
        public int TotalDuration { get; set; }
    }
}