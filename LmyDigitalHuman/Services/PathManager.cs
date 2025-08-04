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
            
            // 验证templates目录是否存在
            _logger.LogInformation("Templates目录存在: {Exists}", Directory.Exists(_templatesPath));
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

            // 🎯 快速路径解析 - 直接基于wwwroot/templates构建，避免重复检查
            string fileName;
            
            // 处理web路径格式（如 /templates/小哈.jpg）
            if (imagePath.StartsWith("/templates/"))
            {
                fileName = imagePath.Substring("/templates/".Length);
            }
            // 处理错误的绝对路径 C:\templates\xxx
            else if (imagePath.StartsWith("C:\\templates\\") || imagePath.StartsWith("C:/templates/"))
            {
                fileName = Path.GetFileName(imagePath);
                _logger.LogDebug("修正错误路径: {ErrorPath} → 文件名: {FileName}", imagePath, fileName);
            }
            // 处理其他绝对路径
            else if (Path.IsPathRooted(imagePath))
            {
                fileName = Path.GetFileName(imagePath);
            }
            // 处理相对路径
            else
            {
                fileName = imagePath;
            }
            
            var fullPath = Path.GetFullPath(Path.Combine(_templatesPath, fileName));
            _logger.LogDebug("解析图片路径: {InputPath} → {FullPath}", imagePath, fullPath);
            return fullPath;
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
            // 首先尝试完整的配置键 (如 "Paths:Templates")
            var configuredPath = _configuration[configKey];
            
            // 如果没有找到，尝试简化的键 (如 "Templates")，主要用于Docker环境
            if (string.IsNullOrEmpty(configuredPath) && configKey.Contains(":"))
            {
                var simpleKey = configKey.Split(':').Last();
                configuredPath = _configuration[$"Paths:{simpleKey}"];
                
                // 如果还是没找到，直接尝试简化键
                if (string.IsNullOrEmpty(configuredPath))
                {
                    configuredPath = _configuration[simpleKey];
                }
            }
            
            if (!string.IsNullOrEmpty(configuredPath))
            {
                _logger.LogInformation("使用配置路径: {ConfigKey} = {ConfiguredPath} (环境: {Environment})", 
                    configKey, configuredPath, _environment.EnvironmentName);
                return Path.IsPathRooted(configuredPath) 
                    ? Path.GetFullPath(configuredPath)
                    : Path.GetFullPath(Path.Combine(_contentRootPath, configuredPath));
            }
            
            _logger.LogInformation("使用默认路径: {ConfigKey} = {DefaultPath} (环境: {Environment})", 
                configKey, defaultPath, _environment.EnvironmentName);
            return Path.GetFullPath(defaultPath);
        }
    }
}