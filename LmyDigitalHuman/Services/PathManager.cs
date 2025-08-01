using Microsoft.AspNetCore.Hosting;

namespace LmyDigitalHuman.Services
{
    /// <summary>
    /// 统一路径管理服务，解决开发环境和生产环境路径不一致问题
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
    }

    public class PathManager : IPathManager
    {
        private readonly IWebHostEnvironment _environment;
        private readonly IConfiguration _configuration;
        private readonly ILogger<PathManager> _logger;
        
        private readonly string _contentRootPath;
        private readonly string _webRootPath;
        private readonly string _templatesPath;
        private readonly string _videosPath;
        private readonly string _tempPath;
        private readonly string _modelsPath;
        private readonly string _scriptsPath;

        public PathManager(
            IWebHostEnvironment environment,
            IConfiguration configuration,
            ILogger<PathManager> logger)
        {
            _environment = environment;
            _configuration = configuration;
            _logger = logger;
            
            // 获取基础路径
            _contentRootPath = _environment.ContentRootPath;
            _webRootPath = _environment.WebRootPath ?? Path.Combine(_contentRootPath, "wwwroot");
            
            // 配置各种路径，支持配置文件覆盖
            _templatesPath = GetConfiguredPath("Paths:Templates", Path.Combine(_webRootPath, "templates"));
            _videosPath = GetConfiguredPath("Paths:Videos", Path.Combine(_webRootPath, "videos"));
            _tempPath = GetConfiguredPath("Paths:Temp", Path.Combine(_contentRootPath, "temp"));
            _modelsPath = GetConfiguredPath("Paths:Models", Path.Combine(_contentRootPath, "models"));
            _scriptsPath = GetConfiguredPath("Paths:Scripts", _contentRootPath);
            
            // 确保关键目录存在
            EnsureDirectoryExists(_templatesPath);
            EnsureDirectoryExists(_videosPath);
            EnsureDirectoryExists(_tempPath);
            EnsureDirectoryExists(_modelsPath);
            
            _logger.LogInformation("路径管理器初始化完成:");
            _logger.LogInformation("  ContentRoot: {ContentRoot}", _contentRootPath);
            _logger.LogInformation("  WebRoot: {WebRoot}", _webRootPath);
            _logger.LogInformation("  Templates: {Templates}", _templatesPath);
            _logger.LogInformation("  Videos: {Videos}", _videosPath);
            _logger.LogInformation("  Temp: {Temp}", _tempPath);
            _logger.LogInformation("  Models: {Models}", _modelsPath);
            _logger.LogInformation("  Scripts: {Scripts}", _scriptsPath);
        }

        public string GetContentRootPath() => _contentRootPath;
        public string GetWebRootPath() => _webRootPath;
        public string GetTemplatesPath() => _templatesPath;
        public string GetVideosPath() => _videosPath;
        public string GetTempPath() => _tempPath;
        public string GetModelsPath() => _modelsPath;
        public string GetScriptsPath() => _scriptsPath;

        public string ResolvePath(string relativePath)
        {
            if (string.IsNullOrEmpty(relativePath))
                return _contentRootPath;
                
            if (Path.IsPathRooted(relativePath))
                return Path.GetFullPath(relativePath);
                
            return Path.GetFullPath(Path.Combine(_contentRootPath, relativePath));
        }

        public string ResolveWebPath(string webPath)
        {
            if (string.IsNullOrEmpty(webPath))
                return _webRootPath;
                
            // 移除开头的斜杠
            var relativePath = webPath.TrimStart('/', '\\');
            
            // 如果已经是绝对路径，直接返回
            if (Path.IsPathRooted(relativePath))
                return Path.GetFullPath(relativePath);
                
            return Path.GetFullPath(Path.Combine(_webRootPath, relativePath));
        }

        public string ResolveImagePath(string imagePath)
        {
            if (string.IsNullOrEmpty(imagePath))
                return _templatesPath;
                
            if (Path.IsPathRooted(imagePath))
                return Path.GetFullPath(imagePath);

            // 移除开头的斜杠
            var relativePath = imagePath.TrimStart('/', '\\');
            
            // 检查是否是web路径格式
            if (relativePath.StartsWith("templates/") || relativePath.StartsWith("templates\\"))
            {
                // 移除templates前缀，直接使用wwwroot/templates
                var fileName = relativePath.Substring("templates/".Length);
                return Path.GetFullPath(Path.Combine(_webRootPath, "templates", fileName));
            }
            else if (relativePath.StartsWith("images/") || relativePath.StartsWith("images\\"))
            {
                // 处理images路径
                return Path.GetFullPath(Path.Combine(_webRootPath, relativePath));
            }
            else
            {
                // 默认所有模板文件都在wwwroot/templates目录中
                return Path.GetFullPath(Path.Combine(_webRootPath, "templates", relativePath));
            }
        }

        public string ResolveAudioPath(string audioPath)
        {
            if (string.IsNullOrEmpty(audioPath))
                return _tempPath;
                
            if (Path.IsPathRooted(audioPath))
                return Path.GetFullPath(audioPath);

            // 移除开头的斜杠
            var relativePath = audioPath.TrimStart('/', '\\');
            
            // 检查是否是temp路径
            if (relativePath.StartsWith("temp/") || relativePath.StartsWith("temp\\"))
            {
                return Path.GetFullPath(Path.Combine(_tempPath, relativePath.Substring("temp/".Length)));
            }
            else
            {
                // 默认放在temp目录
                return Path.GetFullPath(Path.Combine(_tempPath, relativePath));
            }
        }

        public string ResolveVideoPath(string videoPath)
        {
            if (string.IsNullOrEmpty(videoPath))
                return _videosPath;
                
            if (Path.IsPathRooted(videoPath))
                return Path.GetFullPath(videoPath);

            // 移除开头的斜杠
            var relativePath = videoPath.TrimStart('/', '\\');
            
            // 检查是否是videos路径
            if (relativePath.StartsWith("videos/") || relativePath.StartsWith("videos\\"))
            {
                return Path.GetFullPath(Path.Combine(_videosPath, relativePath.Substring("videos/".Length)));
            }
            else
            {
                // 默认放在videos目录
                return Path.GetFullPath(Path.Combine(_videosPath, relativePath));
            }
        }

        public string CreateTempAudioPath(string extension = "wav")
        {
            var fileName = $"audio_{Guid.NewGuid():N}.{extension.TrimStart('.')}";
            var fullPath = Path.GetFullPath(Path.Combine(_tempPath, fileName));
            
            // 确保目录存在
            EnsureDirectoryExists(Path.GetDirectoryName(fullPath)!);
            
            return fullPath;
        }

        public string CreateTempVideoPath(string extension = "mp4")
        {
            var fileName = $"video_{Guid.NewGuid():N}.{extension.TrimStart('.')}";
            var fullPath = Path.GetFullPath(Path.Combine(_videosPath, fileName));
            
            // 确保目录存在
            EnsureDirectoryExists(Path.GetDirectoryName(fullPath)!);
            
            return fullPath;
        }

        public bool EnsureDirectoryExists(string path)
        {
            try
            {
                if (!Directory.Exists(path))
                {
                    Directory.CreateDirectory(path);
                    _logger.LogInformation("创建目录: {Path}", path);
                }
                return true;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "创建目录失败: {Path}", path);
                return false;
            }
        }

        private string GetConfiguredPath(string configKey, string defaultPath)
        {
            var configuredPath = _configuration[configKey];
            if (!string.IsNullOrEmpty(configuredPath))
            {
                return Path.IsPathRooted(configuredPath) 
                    ? Path.GetFullPath(configuredPath)
                    : Path.GetFullPath(Path.Combine(_contentRootPath, configuredPath));
            }
            
            return Path.GetFullPath(defaultPath);
        }
    }
}