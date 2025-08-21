using LmyDigitalHuman.Services;
using System.Threading.Tasks;

namespace LmyDigitalHuman.Services
{
    public interface IPathManager
    {
        string GetTemplatesPath();
        string GetVideosPath();
        string GetAudioPath();
        string GetTempPath();
        string GetTemplateCachePath();
        string GetTemplatePath(string templateId);
        string GetVideoPath(string fileName);
        string GetAudioFilePath(string fileName);
        Task<string> SaveTemplateImageAsync(string templateId, byte[] imageData);
        void EnsureDirectoriesExist();
    }
}