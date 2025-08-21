using LmyDigitalHuman.Services;
using System.Threading.Tasks;

namespace LmyDigitalHuman.Services
{
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