using LmyDigitalHuman.Models;
using System.Diagnostics;
using System.Text.Json;

namespace LmyDigitalHuman.Services
{
    public class MuseTalkService : IMuseTalkService
    {
        private readonly HttpClient _httpClient;
        private readonly ILogger<MuseTalkService> _logger;
        private readonly IConfiguration _configuration;
        private readonly string _museTalkUrl;
        private readonly string _templatesPath;
        private readonly string _outputPath;

        public MuseTalkService(
            HttpClient httpClient, 
            ILogger<MuseTalkService> logger, 
            IConfiguration configuration)
        {
            _httpClient = httpClient;
            _logger = logger;
            _configuration = configuration;
            _museTalkUrl = configuration["DigitalHuman:MuseTalk:BaseUrl"] ?? "http://localhost:8000";
            _templatesPath = Path.Combine(Directory.GetCurrentDirectory(), "wwwroot", "templates");
            _outputPath = Path.Combine(Directory.GetCurrentDirectory(), "wwwroot", "videos");
            
            // 确保目录存在
            Directory.CreateDirectory(_templatesPath);
            Directory.CreateDirectory(_outputPath);
            
            // 配置HttpClient
            _httpClient.Timeout = TimeSpan.FromMinutes(5);
        }

        public async Task<DigitalHumanResponse> GenerateVideoAsync(DigitalHumanRequest request)
        {
            var stopwatch = Stopwatch.StartNew();
            
            try
            {
                _logger.LogInformation("开始生成数字人视频: 图片={ImagePath}, 音频={AudioPath}", 
                    request.AvatarImagePath, request.AudioPath);

                // 验证输入文件
                if (!File.Exists(request.AvatarImagePath))
                {
                    return new DigitalHumanResponse
                    {
                        Success = false,
                        Error = $"头像图片不存在: {request.AvatarImagePath}"
                    };
                }

                if (!File.Exists(request.AudioPath))
                {
                    return new DigitalHumanResponse
                    {
                        Success = false,
                        Error = $"音频文件不存在: {request.AudioPath}"
                    };
                }

                // 生成输出文件名
                var outputFileName = $"musetalk_{Guid.NewGuid():N}.mp4";
                var outputPath = Path.Combine(_outputPath, outputFileName);

                // 构建请求负载
                var payload = new
                {
                    avatar_image = Path.GetFullPath(request.AvatarImagePath),
                    audio_path = Path.GetFullPath(request.AudioPath),
                    bbox_shift = request.BboxShift ?? 0,
                    result_dir = _outputPath,
                    output_filename = outputFileName,
                    fps = request.Fps ?? 25,
                    batch_size = request.BatchSize ?? 4,
                    quality = request.Quality,
                    enable_emotion = request.EnableEmotion
                };

                _logger.LogInformation("发送MuseTalk请求: {Payload}", JsonSerializer.Serialize(payload));

                // 发送HTTP请求
                var response = await _httpClient.PostAsJsonAsync($"{_museTalkUrl}/generate", payload);
                
                if (!response.IsSuccessStatusCode)
                {
                    var errorContent = await response.Content.ReadAsStringAsync();
                    _logger.LogError("MuseTalk请求失败: {StatusCode}, {Content}", response.StatusCode, errorContent);
                    
                    return new DigitalHumanResponse
                    {
                        Success = false,
                        Error = $"MuseTalk服务错误: {response.StatusCode} - {errorContent}",
                        ProcessingTime = stopwatch.ElapsedMilliseconds
                    };
                }

                var result = await response.Content.ReadFromJsonAsync<MuseTalkApiResponse>();
                stopwatch.Stop();

                if (result?.Success == true && !string.IsNullOrEmpty(result.VideoPath))
                {
                    // 验证生成的视频文件
                    if (File.Exists(result.VideoPath))
                    {
                        var fileInfo = new FileInfo(result.VideoPath);
                        var videoUrl = $"/videos/{Path.GetFileName(result.VideoPath)}";
                        
                        _logger.LogInformation("数字人视频生成成功: {VideoPath}, 大小: {Size}KB, 耗时: {Time}ms", 
                            result.VideoPath, fileInfo.Length / 1024, stopwatch.ElapsedMilliseconds);

                        return new DigitalHumanResponse
                        {
                            Success = true,
                            VideoUrl = videoUrl,
                            VideoPath = result.VideoPath,
                            ProcessingTime = stopwatch.ElapsedMilliseconds,
                            Message = "数字人视频生成成功",
                            Metadata = new DigitalHumanMetadata
                            {
                                Resolution = GetVideoResolution(request.Quality),
                                Fps = request.Fps ?? 25,
                                Duration = result.Duration,
                                FileSize = fileInfo.Length,
                                Quality = request.Quality
                            }
                        };
                    }
                    else
                    {
                        return new DigitalHumanResponse
                        {
                            Success = false,
                            Error = "视频文件生成失败，输出文件不存在",
                            ProcessingTime = stopwatch.ElapsedMilliseconds
                        };
                    }
                }
                else
                {
                    return new DigitalHumanResponse
                    {
                        Success = false,
                        Error = result?.Message ?? "MuseTalk返回未知错误",
                        ProcessingTime = stopwatch.ElapsedMilliseconds
                    };
                }
            }
            catch (TaskCanceledException ex) when (ex.InnerException is TimeoutException)
            {
                _logger.LogError(ex, "MuseTalk请求超时");
                return new DigitalHumanResponse
                {
                    Success = false,
                    Error = "数字人生成超时，请稍后重试",
                    ProcessingTime = stopwatch.ElapsedMilliseconds
                };
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "生成数字人视频失败");
                stopwatch.Stop();
                
                return new DigitalHumanResponse
                {
                    Success = false,
                    Error = ex.Message,
                    ProcessingTime = stopwatch.ElapsedMilliseconds
                };
            }
        }

        public async Task<bool> IsServiceHealthyAsync()
        {
            try
            {
                _logger.LogDebug("检查MuseTalk服务健康状态");
                
                var response = await _httpClient.GetAsync($"{_museTalkUrl}/health");
                var isHealthy = response.IsSuccessStatusCode;
                
                _logger.LogInformation("MuseTalk服务健康状态: {IsHealthy}", isHealthy);
                return isHealthy;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "检查MuseTalk服务健康状态失败");
                return false;
            }
        }

        public async Task<List<DigitalHumanTemplate>> GetAvailableTemplatesAsync()
        {
            try
            {
                var templates = new List<DigitalHumanTemplate>();
                
                if (!Directory.Exists(_templatesPath))
                {
                    return templates;
                }

                var jsonFiles = Directory.GetFiles(_templatesPath, "*.json");
                
                foreach (var jsonFile in jsonFiles)
                {
                    try
                    {
                        var jsonContent = await File.ReadAllTextAsync(jsonFile);
                        var template = JsonSerializer.Deserialize<DigitalHumanTemplate>(jsonContent);
                        
                        if (template != null)
                        {
                            // 验证关联的图片文件是否存在
                            var imagePath = Path.Combine(_templatesPath, template.ImagePath);
                            if (File.Exists(imagePath))
                            {
                                template.ImageUrl = $"/templates/{template.ImagePath}";
                                template.PreviewImageUrl = template.ImageUrl;
                                templates.Add(template);
                            }
                        }
                    }
                    catch (Exception ex)
                    {
                        _logger.LogWarning(ex, "加载模板文件失败: {JsonFile}", jsonFile);
                    }
                }

                _logger.LogInformation("加载了 {Count} 个数字人模板", templates.Count);
                return templates;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "获取数字人模板列表失败");
                return new List<DigitalHumanTemplate>();
            }
        }

        public async Task<DigitalHumanTemplate> CreateTemplateAsync(CreateTemplateRequest request)
        {
            try
            {
                var templateId = Guid.NewGuid().ToString("N");
                var sanitizedName = SanitizeFileName(request.Name);
                var imageFileName = $"{sanitizedName}_{templateId}.jpg";
                var jsonFileName = $"{sanitizedName}_{templateId}.json";
                
                var imageTargetPath = Path.Combine(_templatesPath, imageFileName);
                var jsonTargetPath = Path.Combine(_templatesPath, jsonFileName);

                // 复制图片文件
                if (File.Exists(request.ImagePath))
                {
                    File.Copy(request.ImagePath, imageTargetPath, true);
                }

                var template = new DigitalHumanTemplate
                {
                    Id = templateId,
                    Name = request.Name,
                    Description = request.Description,
                    ImagePath = imageFileName,
                    ImageUrl = $"/templates/{imageFileName}",
                    PreviewImageUrl = $"/templates/{imageFileName}",
                    Gender = request.Gender,
                    Style = request.Style,
                    Status = "ready",
                    CreatedAt = DateTime.UtcNow
                };

                // 保存JSON文件
                var jsonContent = JsonSerializer.Serialize(template, new JsonSerializerOptions
                {
                    WriteIndented = true,
                    Encoder = System.Text.Encodings.Web.JavaScriptEncoder.UnsafeRelaxedJsonEscaping
                });
                
                await File.WriteAllTextAsync(jsonTargetPath, jsonContent, System.Text.Encoding.UTF8);

                _logger.LogInformation("创建数字人模板成功: {TemplateName} ({TemplateId})", request.Name, templateId);
                return template;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "创建数字人模板失败: {TemplateName}", request.Name);
                throw;
            }
        }

        public async Task<bool> DeleteTemplateAsync(string templateId)
        {
            try
            {
                var jsonFiles = Directory.GetFiles(_templatesPath, "*.json");
                
                foreach (var jsonFile in jsonFiles)
                {
                    var jsonContent = await File.ReadAllTextAsync(jsonFile);
                    var template = JsonSerializer.Deserialize<DigitalHumanTemplate>(jsonContent);
                    
                    if (template?.Id == templateId)
                    {
                        // 删除JSON文件
                        File.Delete(jsonFile);
                        
                        // 删除关联的图片文件
                        var imagePath = Path.Combine(_templatesPath, template.ImagePath);
                        if (File.Exists(imagePath))
                        {
                            File.Delete(imagePath);
                        }
                        
                        _logger.LogInformation("删除数字人模板成功: {TemplateId}", templateId);
                        return true;
                    }
                }
                
                return false;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "删除数字人模板失败: {TemplateId}", templateId);
                return false;
            }
        }

        private string GetVideoResolution(string quality)
        {
            return quality.ToLower() switch
            {
                "low" => "640x480",
                "medium" => "1280x720",
                "high" => "1920x1080",
                "ultra" => "2560x1440",
                _ => "1280x720"
            };
        }

        private string SanitizeFileName(string name)
        {
            var sanitized = name;
            
            // 移除中文字符，避免路径问题
            sanitized = System.Text.RegularExpressions.Regex.Replace(sanitized, @"[\u4e00-\u9fa5]", "");
            
            // 移除所有非字母、数字、下划线的字符
            sanitized = System.Text.RegularExpressions.Regex.Replace(sanitized, @"[^a-zA-Z0-9_]", "");
            
            // 确保文件名不以点或空格开头/结尾
            sanitized = sanitized.Trim('.', ' ');
            
            // 如果清理后为空或太短，使用默认名称加时间戳
            if (string.IsNullOrWhiteSpace(sanitized) || sanitized.Length < 2)
            {
                sanitized = $"Template_{DateTime.Now:yyyyMMdd_HHmmss}";
            }
            
            // 限制长度
            if (sanitized.Length > 20)
            {
                sanitized = sanitized.Substring(0, 20);
            }
            
            return sanitized;
        }
    }

    // MuseTalk API响应模型
    public class MuseTalkApiResponse
    {
        public bool Success { get; set; }
        public string VideoPath { get; set; } = string.Empty;
        public string Message { get; set; } = string.Empty;
        public double Duration { get; set; }
        public long ProcessingTime { get; set; }
    }
}