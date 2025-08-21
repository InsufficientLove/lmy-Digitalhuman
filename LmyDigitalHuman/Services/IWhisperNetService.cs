using System;
using System.IO;
using System.Threading.Tasks;
using LmyDigitalHuman.Models;

namespace LmyDigitalHuman.Services
{
    /// <summary>
    /// Whisper语音识别服务接口
    /// </summary>
    public interface IWhisperNetService
    {
        Task<SpeechToTextResponse> TranscribeAsync(Stream audioStream, string language = "zh");
        Task<SpeechToTextResponse> TranscribeAsync(byte[] audioData, string language = "zh");
        Task<SpeechToTextResponse> TranscribeAsync(string audioFilePath, string language = "zh");
        Task<bool> InitializeAsync();
        void Dispose();
    }
    
    public class TranscriptionResult
    {
        public string Text { get; set; }
        public double[] Timestamps { get; set; }
        public string Language { get; set; }
        public double Confidence { get; set; }
    }
}