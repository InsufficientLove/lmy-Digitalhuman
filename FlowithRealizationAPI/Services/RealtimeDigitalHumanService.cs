using FlowithRealizationAPI.Models;
using System.Diagnostics;
using System.Text.Json;
using System.Text.RegularExpressions;
using System.Collections.Concurrent;
using Microsoft.Extensions.Caching.Memory;

namespace FlowithRealizationAPI.Services
{
    public class RealtimeDigitalHumanService : IRealtimeDigitalHumanService
    {
        private readonly ILogger<RealtimeDigitalHumanService> _logger;
        private readonly IMemoryCache _cache;
        private readonly IConfiguration _configuration;
        private readonly HttpClient _httpClient;
        private readonly IServiceProvider _serviceProvider;
        
        private readonly ConcurrentDictionary<string, PrerenderedVideo> _prerenderedCache = new();
        
        private readonly Dictionary<string, string> _commonResponses = new()
        {
            { "你好|您好|hello|hi", "您好！我是您的专属数字人助手，很高兴为您服务！" },
            { "谢谢|感谢|thanks|thank you", "不客气！很高兴能够帮助到您！" },
            { "再见|拜拜|goodbye|bye", "再见！期待下次为您服务！" },
            { "帮助|帮忙|help", "我可以为您提供各种服务，请告诉我您需要什么帮助。" },
            { "价格|费用|多少钱|cost|price", "关于价格信息，我来为您详细介绍一下我们的服务套餐。" }
        };

        private readonly string _sadTalkerPath;
        private readonly string _outputPath;
        private readonly string _tempPath;

        public RealtimeDigitalHumanService(
            ILogger<RealtimeDigitalHumanService> logger,
            IMemoryCache cache,
            IConfiguration configuration,
            HttpClient httpClient,
            IServiceProvider serviceProvider)
        {
            _logger = logger;
            _cache = cache;
            _configuration = configuration;
            _httpClient = httpClient;
            _serviceProvider = serviceProvider;
            
            _sadTalkerPath = _configuration["RealtimeDigitalHuman:SadTalker:Path"] ?? "C:\\AI\\SadTalker";
            _outputPath = _configuration["RealtimeDigitalHuman:Output:Path"] ?? "wwwroot\\videos";
            _tempPath = _configuration["RealtimeDigitalHuman:Temp:Path"] ?? "temp";
            
            Directory.CreateDirectory(_outputPath);
            Directory.CreateDirectory(_tempPath);
        }

        public async Task<InstantChatResponse> ProcessInstantChatAsync(InstantChatRequest request)
        {
            var stopwatch = Stopwatch.StartNew();
            
            try
            {
                _logger.LogInformation("开始处理立即响应对话: {Text}", request.Text);

                // 验证输入参数
                if (string.IsNullOrWhiteSpace(request.Text))
                {
                    throw new ArgumentException("输入文本不能为空");
                }

                // 检查头像是否存在
                var avatarImagePath = await GetAvatarImageAsync(request.AvatarId);
                if (string.IsNullOrEmpty(avatarImagePath) || !File.Exists(avatarImagePath))
                {
                    _logger.LogWarning("头像不存在: {AvatarId}", request.AvatarId);
                    // 使用默认头像
                    avatarImagePath = await GetAvatarImageAsync("default");
                }

                // 检查预渲染视频
                var prerenderedResult = await CheckPrerenderedVideoAsync(request.Text, request.AvatarId);
                if (prerenderedResult != null)
                {
                    stopwatch.Stop();
                    return new InstantChatResponse
                    {
                        Success = true,
                        ResponseText = prerenderedResult.Text,
                        VideoUrl = prerenderedResult.VideoUrl,
                        AudioUrl = prerenderedResult.VideoUrl.Replace(".mp4", ".wav"),
                        Metadata = new ResponseMetadata
                        {
                            ResponseType = "prerendered",
                            ProcessingTime = stopwatch.ElapsedMilliseconds,
                            VideoDuration = prerenderedResult.Duration,
                            AvatarId = request.AvatarId,
                            Quality = new VideoQualityInfo
                            {
                                Resolution = GetResolutionByQuality(request.Quality),
                                Fps = 30,
                                Bitrate = 1500,
                                Codec = "h264",
                                FileSize = 0
                            }
                        }
                    };
                }

                // 处理立即模式
                return await ProcessInstantModeAsync(request, stopwatch);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "处理立即响应对话失败: {Text}", request.Text);
                stopwatch.Stop();
                
                return new InstantChatResponse
                {
                    Success = false,
                    ResponseText = "抱歉，处理您的请求时出现了问题，请稍后再试。",
                    VideoUrl = "",
                    AudioUrl = "",
                    Metadata = new ResponseMetadata
                    {
                        ResponseType = "error",
                        ProcessingTime = stopwatch.ElapsedMilliseconds,
                        VideoDuration = 0,
                        AvatarId = request.AvatarId,
                        Quality = new VideoQualityInfo
                        {
                            Resolution = "",
                            Fps = 0,
                            Bitrate = 0,
                            Codec = "",
                            FileSize = 0
                        },
                        Emotion = null
                    }
                };
            }
        }

        private async Task<InstantChatResponse> ProcessInstantModeAsync(InstantChatRequest request, Stopwatch stopwatch)
        {
            try
            {
                _logger.LogInformation("开始立即模式处理: {Text}", request.Text);

                // 1. 生成TTS音频
                var audioResult = await GenerateTTSAsync(request.Text, request.VoiceSettings);
                if (string.IsNullOrEmpty(audioResult.AudioPath) || !File.Exists(audioResult.AudioPath))
                {
                    throw new Exception("TTS音频生成失败");
                }

                // 2. 获取头像图片
                var avatarImagePath = await GetAvatarImageAsync(request.AvatarId);
                if (string.IsNullOrEmpty(avatarImagePath) || !File.Exists(avatarImagePath))
                {
                    throw new Exception($"头像图片不存在: {request.AvatarId}");
                }

                // 3. 创建视频
                var videoPath = await CreateAudioVisualizationVideoAsync(audioResult.AudioPath, avatarImagePath, request.Quality);
                if (string.IsNullOrEmpty(videoPath) || !File.Exists(videoPath))
                {
                    throw new Exception("视频生成失败");
                }

                // 4. 获取文件信息
                var videoFileInfo = new FileInfo(videoPath);
                var resolution = GetResolutionByQuality(request.Quality);
                
                stopwatch.Stop();
                
                _logger.LogInformation("立即模式处理完成，耗时: {Time}ms", stopwatch.ElapsedMilliseconds);
                
                return new InstantChatResponse
                {
                    Success = true,
                    ResponseText = request.Text,
                    VideoUrl = $"/videos/{Path.GetFileName(videoPath)}",
                    AudioUrl = $"/temp/{Path.GetFileName(audioResult.AudioPath)}",
                    Metadata = new ResponseMetadata
                    {
                        ResponseType = "instant",
                        ProcessingTime = stopwatch.ElapsedMilliseconds,
                        VideoDuration = audioResult.Duration,
                        AvatarId = request.AvatarId,
                        Quality = new VideoQualityInfo
                        {
                            Resolution = resolution,
                            Fps = 30,
                            Bitrate = GetBitrateByQuality(request.Quality),
                            Codec = "h264",
                            FileSize = videoFileInfo.Length
                        },
                        Emotion = null
                    }
                };
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "立即模式处理失败: {Text}", request.Text);
                throw;
            }
        }

        private async Task<(string AudioPath, double Duration)> GenerateTTSAsync(string text, VoiceSettings? voiceSettings = null)
        {
            try
            {
                var fileName = $"tts_{Guid.NewGuid()}.wav";
                var audioPath = Path.Combine(_tempPath, fileName);
                
                var edgeTtsCommand = BuildEdgeTTSCommand(text, audioPath, voiceSettings);
                var result = await RunCommandAsync(edgeTtsCommand);
                
                if (!result.Success)
                {
                    throw new Exception($"TTS生成失败: {result.Error}");
                }
                
                var duration = await GetAudioDurationAsync(audioPath);
                return (audioPath, duration);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "TTS音频生成失败");
                throw;
            }
        }

        private async Task<PrerenderedVideo?> CheckPrerenderedVideoAsync(string text, string avatarId)
        {
            try
            {
                var exactKey = $"{avatarId}_{text}";
                if (_prerenderedCache.TryGetValue(exactKey, out var exactMatch))
                {
                    exactMatch.UseCount++;
                    return exactMatch;
                }
                
                foreach (var (pattern, response) in _commonResponses)
                {
                    if (Regex.IsMatch(text, pattern, RegexOptions.IgnoreCase))
                    {
                        var keywordKey = $"{avatarId}_{pattern}";
                        if (_prerenderedCache.TryGetValue(keywordKey, out var keywordMatch))
                        {
                            keywordMatch.UseCount++;
                            return keywordMatch;
                        }
                    }
                }
                
                return null;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "检查预渲染视频库失败");
                return null;
            }
        }

        private string BuildEdgeTTSCommand(string text, string outputPath, VoiceSettings? settings = null)
        {
            var voice = _configuration["RealtimeDigitalHuman:EdgeTTS:DefaultVoice"] ?? "zh-CN-XiaoxiaoNeural";
            var rate = settings?.Speed ?? 1.0f;
            var pitch = settings?.Pitch ?? 0.0f;
            
            // 将浮点数rate转换为edge-tts要求的百分比格式
            string ratePercent;
            if (Math.Abs(rate - 1.0f) < 0.1)
            {
                ratePercent = "+0%";
            }
            else if (rate > 1.0)
            {
                ratePercent = $"+{(int)((rate - 1.0) * 100)}%";
            }
            else
            {
                ratePercent = $"-{(int)((1.0 - rate) * 100)}%";
            }
            
            return $"edge-tts --voice {voice} --rate {ratePercent} --pitch {pitch:+0}Hz --text \"{text}\" --write-media \"{outputPath}\"";
        }

        private async Task<(bool Success, string Error)> RunCommandAsync(string command)
        {
            try
            {
                var processInfo = new ProcessStartInfo
                {
                    FileName = "cmd.exe",
                    Arguments = $"/c {command}",
                    RedirectStandardOutput = true,
                    RedirectStandardError = true,
                    UseShellExecute = false,
                    CreateNoWindow = true
                };

                using var process = Process.Start(processInfo);
                if (process == null)
                {
                    return (false, "无法启动进程");
                }

                var output = await process.StandardOutput.ReadToEndAsync();
                var error = await process.StandardError.ReadToEndAsync();
                
                await process.WaitForExitAsync();
                
                return (process.ExitCode == 0, process.ExitCode == 0 ? output : error);
            }
            catch (Exception ex)
            {
                return (false, ex.Message);
            }
        }

        private async Task<double> GetAudioDurationAsync(string audioPath)
        {
            var command = $"ffprobe -v quiet -show_entries format=duration -of csv=p=0 \"{audioPath}\"";
            var result = await RunCommandAsync(command);
            
            if (result.Success && double.TryParse(result.Error.Trim(), out var duration))
            {
                return duration;
            }
            
            return 1.0;
        }

        private async Task<string> GetAvatarImageAsync(string avatarId)
        {
            var avatarPath = Path.Combine("wwwroot", "images", "avatars", $"{avatarId}.jpg");
            if (File.Exists(avatarPath))
            {
                return avatarPath;
            }
            
            return Path.Combine("wwwroot", "images", "avatars", "default.jpg");
        }

        private async Task<string> CreateAudioVisualizationVideoAsync(string audioPath, string imagePath, string quality)
        {
            var outputFileName = $"audio_viz_{Guid.NewGuid()}.mp4";
            var outputPath = Path.Combine(_outputPath, outputFileName);
            
            var resolution = GetResolutionByQuality(quality);
            var command = $"ffmpeg -loop 1 -i \"{imagePath}\" -i \"{audioPath}\" -c:v libx264 -tune stillimage -c:a aac -b:a 192k -pix_fmt yuv420p -shortest -s {resolution} \"{outputPath}\"";
            
            var result = await RunCommandAsync(command);
            if (!result.Success)
            {
                throw new Exception($"音频可视化视频创建失败: {result.Error}");
            }
            
            return outputPath;
        }

        private string GetResolutionByQuality(string quality)
        {
            return quality switch
            {
                "low" => "640x480",
                "medium" => "1280x720",
                "high" => "1920x1080",
                "ultra" => "2560x1440",
                _ => "1280x720"
            };
        }

        private int GetBitrateByQuality(string quality)
        {
            return quality switch
            {
                "low" => 500,
                "medium" => 1500,
                "high" => 3000,
                "ultra" => 5000,
                _ => 1500
            };
        }

        public async Task<List<DigitalHumanAvatar>> GetAvailableAvatarsAsync()
        {
            try
            {
                var avatars = new List<DigitalHumanAvatar>();
                
                // 加载自定义模板头像
                var templateService = _serviceProvider.GetService<IDigitalHumanTemplateService>();
                if (templateService != null)
                {
                    var templatesResult = await templateService.GetTemplatesAsync(new GetTemplatesRequest());
                    if (templatesResult.Success && templatesResult.Templates != null)
                    {
                        foreach (var template in templatesResult.Templates)
                        {
                            if (template.IsActive && template.Status == "ready")
                            {
                                avatars.Add(new DigitalHumanAvatar
                                {
                                    Id = template.TemplateId,
                                    Name = template.TemplateName,
                                    Description = template.Description,
                                    PreviewImageUrl = template.ImagePath,
                                    PreviewVideoUrl = template.PreviewVideoPath,
                                    Style = template.Style,
                                    IsCustom = true,
                                    CreatedAt = template.CreatedAt,
                                    Capabilities = new AvatarCapabilities
                                    {
                                        SupportsEmotion = template.EnableEmotion,
                                        SupportsLipSync = true,
                                        SupportsHeadMovement = true,
                                        SupportedLanguages = new List<string> { "zh-CN", "en-US" },
                                        SupportedEmotions = template.EnableEmotion ?
                                            new List<string> { "neutral", "happy", "sad", "angry", "surprised" } :
                                            new List<string> { "neutral" }
                                    }
                                });
                            }
                        }
                    }
                }
                
                // 按创建时间排序，最新的在前面
                avatars = avatars.OrderByDescending(a => a.CreatedAt).ToList();
                _logger.LogInformation("加载了 {Count} 个自定义数字人头像", avatars.Count);
                return avatars;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "获取可用头像失败");
                return new List<DigitalHumanAvatar>(); // 返回空列表
            }
        }

        public async Task<CreateAvatarResponse> CreateAvatarAsync(CreateAvatarRequest request)
        {
            var startTime = DateTime.Now;
            
            try
            {
                _logger.LogInformation("开始创建自定义数字人头像: {Name}", request.Name);

                // 验证输入
                if (request.ImageFile == null || request.ImageFile.Length == 0)
                {
                    throw new ArgumentException("头像图片不能为空");
                }

                if (string.IsNullOrWhiteSpace(request.Name))
                {
                    throw new ArgumentException("头像名称不能为空");
                }

                // 验证文件格式
                var allowedExtensions = new[] { ".jpg", ".jpeg", ".png", ".webp" };
                var fileExtension = Path.GetExtension(request.ImageFile.FileName).ToLower();
                if (!allowedExtensions.Contains(fileExtension))
                {
                    throw new ArgumentException($"不支持的图片格式: {fileExtension}");
                }

                // 验证文件大小 (最大10MB)
                if (request.ImageFile.Length > 10 * 1024 * 1024)
                {
                    throw new ArgumentException("图片文件过大，最大支持10MB");
                }

                // 使用模板服务创建头像
                var templateService = _serviceProvider.GetService<IDigitalHumanTemplateService>();
                if (templateService == null)
                {
                    throw new Exception("模板服务不可用");
                }

                var templateRequest = new CreateDigitalHumanTemplateRequest
                {
                    ImageFile = request.ImageFile,
                    TemplateName = request.Name,
                    Description = request.Description,
                    TemplateType = "headshot",
                    Gender = "neutral",
                    AgeRange = "adult",
                    Style = request.Style,
                    EnableEmotion = true,
                    DefaultVoiceSettings = new VoiceSettings
                    {
                        Speed = 1.0f,
                        Pitch = 0.0f,
                        Volume = 1.0f,
                        Style = "friendly"
                    }
                };

                var templateResult = await templateService.CreateTemplateAsync(templateRequest);
                
                if (!templateResult.Success)
                {
                    throw new Exception($"创建模板失败: {templateResult.Message}");
                }

                var processingTime = DateTime.Now - startTime;

                // 创建头像对象
                var avatar = new DigitalHumanAvatar
                {
                    Id = templateResult.TemplateId,
                    Name = request.Name,
                    Description = request.Description,
                    PreviewImageUrl = templateResult.Template?.ImagePath ?? "",
                    PreviewVideoUrl = templateResult.Template?.PreviewVideoPath ?? "",
                    Style = request.Style,
                    IsCustom = true,
                    CreatedAt = DateTime.Now,
                    Capabilities = new AvatarCapabilities
                    {
                        SupportsEmotion = true,
                        SupportsLipSync = true,
                        SupportsHeadMovement = true,
                        SupportedLanguages = new List<string> { "zh-CN", "en-US" },
                        SupportedEmotions = new List<string> { "neutral", "happy", "sad", "angry", "surprised" }
                    }
                };

                _logger.LogInformation("自定义数字人头像创建成功: {Name}, 耗时: {Time}ms", 
                    request.Name, processingTime.TotalMilliseconds);

                return new CreateAvatarResponse
                {
                    Success = true,
                    AvatarId = templateResult.TemplateId,
                    Message = "头像创建成功",
                    Avatar = avatar,
                    ProcessingTime = (long)processingTime.TotalMilliseconds
                };
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "创建自定义数字人头像失败: {Name}", request.Name);
                var processingTime = DateTime.Now - startTime;
                
                return new CreateAvatarResponse
                {
                    Success = false,
                    AvatarId = "",
                    Message = $"创建失败: {ex.Message}",
                    Avatar = null,
                    ProcessingTime = (long)processingTime.TotalMilliseconds
                };
            }
        }

        private string GetAvatarDisplayName(string fileName)
        {
            // 只处理自定义头像，移除默认头像
            return fileName.Replace("_", " ").Replace("-", " ");
        }

        private string GetAvatarDescription(string fileName)
        {
            // 只处理自定义头像，移除默认头像
            return $"自定义数字人头像 - {fileName}";
        }

        public async Task<PrerenderedStatus> GetPrerenderedStatusAsync()
        {
            return new PrerenderedStatus
            {
                TotalVideos = _prerenderedCache.Count,
                AvailableVideos = _prerenderedCache.Count,
                ProcessingVideos = 0,
                LastUpdate = DateTime.UtcNow
            };
        }

        public async Task<SystemHealth> GetSystemHealthAsync()
        {
            return new SystemHealth
            {
                IsHealthy = true,
                Status = "健康",
                CheckTime = DateTime.UtcNow,
                Services = new Dictionary<string, ServiceHealth>
                {
                    ["EdgeTTS"] = new ServiceHealth { IsHealthy = true, Status = "正常", LastCheck = DateTime.UtcNow }
                }
            };
        }

        public async Task<bool> PreRenderCommonPhrasesAsync(string avatarId, List<string> phrases)
        {
            return true;
        }

        public async Task<bool> CleanupExpiredVideosAsync()
        {
            return true;
        }

        public async Task<Dictionary<string, object>> GetCacheStatisticsAsync()
        {
            return new Dictionary<string, object>
            {
                ["total_videos"] = _prerenderedCache.Count,
                ["total_size"] = _prerenderedCache.Sum(v => v.Value.FileSize)
            };
        }
    }
} 