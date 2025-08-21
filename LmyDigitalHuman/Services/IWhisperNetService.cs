using System.Threading.Tasks;

namespace LmyDigitalHuman.Services
{
    /// <summary>
    /// Whisper语音识别服务接口
    /// </summary>
    public interface IWhisperNetService
    {
        Task<string> TranscribeAsync(string audioPath);
        Task<TranscriptionResult> TranscribeWithTimestampsAsync(string audioPath);
        Task<bool> InitializeAsync();
    }

    public class TranscriptionResult
    {
        public string Text { get; set; }
        public double[] Timestamps { get; set; }
        public string Language { get; set; }
        public double Confidence { get; set; }
    }
}