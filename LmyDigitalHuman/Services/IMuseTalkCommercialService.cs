using LmyDigitalHuman.Services;
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
}