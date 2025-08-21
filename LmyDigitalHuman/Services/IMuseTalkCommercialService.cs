using System.Threading.Tasks;
using LmyDigitalHuman.Models;

namespace LmyDigitalHuman.Services
{
    public interface IMuseTalkCommercialService
    {
        Task<VideoGenerationResult> GenerateVideoAsync(string templateId, string audioPath);
        Task<PreprocessingResult> PreprocessTemplateAsync(string templateId, string imagePath);
        Task<bool> CheckServiceHealthAsync();
    }
    
    // 临时定义，如果Models命名空间中没有
    public class VideoGenerationResult
    {
        public bool Success { get; set; }
        public string VideoPath { get; set; }
        public string Message { get; set; }
        public long ProcessingTime { get; set; }
    }
}