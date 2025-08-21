namespace LmyDigitalHuman.Services
{
    /// <summary>
    /// 统一路径管理服务接口
    /// </summary>
    public interface IPathManager
    {
        string GetContentRootPath();
        string GetWebRootPath();
        string GetTemplatesPath();
        string GetVideosPath();
        string GetTempPath();
        string GetModelsPath();
        string GetScriptsPath();
        string ResolvePath(string relativePath);
        string ResolveWebPath(string webPath);
        string ResolveImagePath(string imagePath);
        string ResolveAudioPath(string audioPath);
        string ResolveVideoPath(string videoPath);
        string CreateTempAudioPath(string extension = "wav");
        string CreateTempVideoPath(string extension = "mp4");
        bool EnsureDirectoryExists(string path);
        
        // 额外的方法（从实现中发现的）
        string GetAudioPath();
        string GetTemplateCachePath();
        string GetTemplatePath(string templateId);
        string GetVideoPath(string fileName);
        string GetAudioFilePath(string fileName);
        Task<string> SaveTemplateImageAsync(string templateId, byte[] imageData);
        void EnsureDirectoriesExist();
    }
}