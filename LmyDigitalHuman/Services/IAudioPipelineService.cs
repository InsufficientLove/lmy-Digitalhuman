using LmyDigitalHuman.Models;

namespace LmyDigitalHuman.Services
{
    /// <summary>
    /// 音频处理管道服务接口
    /// </summary>
    public interface IAudioPipelineService
    {
        // 语音识别
        Task<SpeechRecognitionResult> RecognizeSpeechAsync(byte[] audioData, string format = "wav");
        Task<SpeechRecognitionResult> RecognizeSpeechFromFileAsync(string audioPath);
        Task<List<SpeechRecognitionResult>> RecognizeBatchAudioAsync(List<string> audioPaths);

        // 实时语音识别
        Task<string> StartRealtimeSpeechRecognitionAsync();
        Task<SpeechRecognitionResult> ProcessRealtimeAudioChunkAsync(string sessionId, byte[] audioChunk);
        Task<SpeechRecognitionResult> EndRealtimeSpeechRecognitionAsync(string sessionId);

        // 文本转语音
        Task<TTSResult> ConvertTextToSpeechAsync(TTSRequest request);
        Task<List<TTSResult>> ConvertBatchTextToSpeechAsync(List<TTSRequest> requests);

        // 流式TTS
        Task<string> StartStreamingTTSAsync(StreamingTTSRequest request);
        Task<byte[]> GetTTSChunkAsync(string sessionId);
        Task<bool> EndStreamingTTSAsync(string sessionId);

        // 音频格式转换
        Task<AudioConversionResult> ConvertAudioFormatAsync(string inputPath, string outputFormat);
        Task<AudioConversionResult> OptimizeAudioForMuseTalkAsync(string inputPath);
        Task<AudioConversionResult> NormalizeAudioAsync(string inputPath);

        // 音频增强
        Task<AudioEnhancementResult> EnhanceAudioQualityAsync(string inputPath);
        Task<AudioEnhancementResult> RemoveNoiseAsync(string inputPath);
        Task<AudioEnhancementResult> AdjustVolumeAsync(string inputPath, float volumeMultiplier);

        // 音频分析
        Task<AudioAnalysisResult> AnalyzeAudioAsync(string audioPath);
        Task<EmotionDetectionResult> DetectEmotionFromAudioAsync(string audioPath);
        Task<bool> ValidateAudioFormatAsync(string audioPath);

        // 性能优化
        Task<bool> PreloadVoiceModelAsync(string voiceId);
        Task<bool> WarmupAudioProcessingAsync();
        Task<long> GetAudioProcessingQueueLengthAsync();
    }

    /// <summary>
    /// 语音识别结果
    /// </summary>
    public class SpeechRecognitionResult
    {
        public bool Success { get; set; }
        public string Text { get; set; } = string.Empty;
        public float Confidence { get; set; }
        public TimeSpan Duration { get; set; }
        public long ProcessingTime { get; set; }
        public string Language { get; set; } = string.Empty;
        public List<SpeechSegment> Segments { get; set; } = new();
        public string Error { get; set; } = string.Empty;
    }

    /// <summary>
    /// 语音片段
    /// </summary>
    public class SpeechSegment
    {
        public string Text { get; set; } = string.Empty;
        public TimeSpan StartTime { get; set; }
        public TimeSpan EndTime { get; set; }
        public float Confidence { get; set; }
    }

    /// <summary>
    /// TTS请求
    /// </summary>
    public class TTSRequest
    {
        public string Text { get; set; } = string.Empty;
        public string VoiceId { get; set; } = "zh-CN-XiaoxiaoNeural";
        public string OutputFormat { get; set; } = "wav";
        public float Speed { get; set; } = 1.0f;
        public float Pitch { get; set; } = 1.0f;
        public float Volume { get; set; } = 1.0f;
        public string Emotion { get; set; } = "neutral";
        public string? OutputPath { get; set; }
    }

    /// <summary>
    /// TTS结果
    /// </summary>
    public class TTSResult
    {
        public bool Success { get; set; }
        public string AudioPath { get; set; } = string.Empty;
        public string AudioUrl { get; set; } = string.Empty;
        public byte[]? AudioData { get; set; }
        public TimeSpan Duration { get; set; }
        public long ProcessingTime { get; set; }
        public long FileSize { get; set; }
        public string Error { get; set; } = string.Empty;
    }

    /// <summary>
    /// 流式TTS请求
    /// </summary>
    public class StreamingTTSRequest
    {
        public string Text { get; set; } = string.Empty;
        public string VoiceId { get; set; } = "zh-CN-XiaoxiaoNeural";
        public string OutputFormat { get; set; } = "wav";
        public float Speed { get; set; } = 1.0f;
        public int ChunkSize { get; set; } = 1024;
    }

    /// <summary>
    /// 音频转换结果
    /// </summary>
    public class AudioConversionResult
    {
        public bool Success { get; set; }
        public string OutputPath { get; set; } = string.Empty;
        public string OutputFormat { get; set; } = string.Empty;
        public long InputSize { get; set; }
        public long OutputSize { get; set; }
        public TimeSpan Duration { get; set; }
        public long ProcessingTime { get; set; }
        public string Error { get; set; } = string.Empty;
    }

    /// <summary>
    /// 音频增强结果
    /// </summary>
    public class AudioEnhancementResult
    {
        public bool Success { get; set; }
        public string OutputPath { get; set; } = string.Empty;
        public float QualityImprovement { get; set; }
        public float NoiseReduction { get; set; }
        public long ProcessingTime { get; set; }
        public Dictionary<string, object> EnhancementMetrics { get; set; } = new();
        public string Error { get; set; } = string.Empty;
    }

    /// <summary>
    /// 音频分析结果
    /// </summary>
    public class AudioAnalysisResult
    {
        public bool Success { get; set; }
        public TimeSpan Duration { get; set; }
        public int SampleRate { get; set; }
        public int Channels { get; set; }
        public int BitDepth { get; set; }
        public float AverageVolume { get; set; }
        public float PeakVolume { get; set; }
        public float NoiseLevel { get; set; }
        public string Format { get; set; } = string.Empty;
        public long FileSize { get; set; }
        public bool IsSuitableForMuseTalk { get; set; }
        public List<string> Recommendations { get; set; } = new();
    }

    /// <summary>
    /// 情感检测结果
    /// </summary>
    public class EmotionDetectionResult
    {
        public bool Success { get; set; }
        public string PrimaryEmotion { get; set; } = string.Empty;
        public Dictionary<string, float> EmotionScores { get; set; } = new();
        public float Confidence { get; set; }
        public List<EmotionSegment> EmotionSegments { get; set; } = new();
        public long ProcessingTime { get; set; }
        public string Error { get; set; } = string.Empty;
    }

    /// <summary>
    /// 情感片段
    /// </summary>
    public class EmotionSegment
    {
        public TimeSpan StartTime { get; set; }
        public TimeSpan EndTime { get; set; }
        public string Emotion { get; set; } = string.Empty;
        public float Confidence { get; set; }
    }
}