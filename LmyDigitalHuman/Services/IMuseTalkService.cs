using LmyDigitalHuman.Models;

namespace LmyDigitalHuman.Services
{
    public interface IMuseTalkService
    {
        Task<DigitalHumanResponse> GenerateVideoAsync(DigitalHumanRequest request);
        Task<bool> IsServiceHealthyAsync();
        Task<List<DigitalHumanTemplate>> GetAvailableTemplatesAsync();
        Task<DigitalHumanTemplate> CreateTemplateAsync(CreateTemplateRequest request);
        Task<bool> DeleteTemplateAsync(string templateId);
    }

    public class DigitalHumanRequest
    {
        public string AvatarImagePath { get; set; } = string.Empty;
        public string AudioPath { get; set; } = string.Empty;
        public string Text { get; set; } = string.Empty;
        public string OutputDirectory { get; set; } = string.Empty;
        public int? BboxShift { get; set; }
        public int? Fps { get; set; } = 25;
        public int? BatchSize { get; set; } = 4;
        public string Quality { get; set; } = "medium";
        public bool EnableEmotion { get; set; } = true;
    }

    public class DigitalHumanResponse
    {
        public bool Success { get; set; }
        public string VideoUrl { get; set; } = string.Empty;
        public string VideoPath { get; set; } = string.Empty;
        public long ProcessingTime { get; set; }
        public string Message { get; set; } = string.Empty;
        public string Error { get; set; } = string.Empty;
        public DigitalHumanMetadata? Metadata { get; set; }
    }

    public class DigitalHumanMetadata
    {
        public string Resolution { get; set; } = string.Empty;
        public int Fps { get; set; }
        public double Duration { get; set; }
        public long FileSize { get; set; }
        public string Quality { get; set; } = string.Empty;
    }

    public class CreateTemplateRequest
    {
        public string Name { get; set; } = string.Empty;
        public string Description { get; set; } = string.Empty;
        public string ImagePath { get; set; } = string.Empty;
        public string Gender { get; set; } = "female";
        public string Style { get; set; } = "professional";
    }
}