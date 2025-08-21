using LmyDigitalHuman.Services;
using LmyDigitalHuman.Models;

namespace LmyDigitalHuman.Services
{
    /// <summary>
    /// 音频处理管道服务接口
    /// </summary>
    public interface IAudioPipelineService
    {
        // 语音识别
        Task<Models.SpeechRecognitionResult> RecognizeSpeechAsync(byte[] audioData, string format = "wav");
        Task<Models.SpeechRecognitionResult> RecognizeSpeechFromFileAsync(string audioPath);
        Task<List<Models.SpeechRecognitionResult>> RecognizeBatchAudioAsync(List<string> audioPaths);

        // 实时语音识别
        Task<string> StartRealtimeSpeechRecognitionAsync();
        Task<Models.SpeechRecognitionResult> ProcessRealtimeAudioChunkAsync(string sessionId, byte[] audioChunk);
        Task<Models.SpeechRecognitionResult> EndRealtimeSpeechRecognitionAsync(string sessionId);

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

    // DTO模型已移至UnifiedModels.cs中统一管理
}