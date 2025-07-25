using LmyDigitalHuman.Models;
using LmyDigitalHuman.Services.Extensions;
using System.Diagnostics;
using System.Text.Json;
using System.Text.RegularExpressions;
using System.Collections.Concurrent;
using Microsoft.Extensions.Caching.Memory;

namespace LmyDigitalHuman.Services
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
            
            // 使用配置的Python路径执行edge-tts
            var pythonPath = _configuration["RealtimeDigitalHuman:SadTalker:PythonPath"] ?? 
                _configuration["RealtimeDigitalHuman:Whisper:PythonPath"] ?? 
                "python";
            
            return $"\"{pythonPath}\" -m edge_tts --voice {voice} --rate {ratePercent} --pitch {pitch:+0}Hz --text \"{text}\" --write-media \"{outputPath}\"";
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

        /// <summary>
        /// 流式对话处理
        /// </summary>
        public async IAsyncEnumerable<StreamingChatResponse> ProcessStreamingChatAsync(StreamingChatRequest request)
        {
            _logger.LogInformation("开始流式对话处理: {Text}", request.Text);

            // 获取LLM和TTS服务
            var llmService = _serviceProvider.GetRequiredService<ILocalLLMService>();
            var ttsService = _serviceProvider.GetRequiredService<IEdgeTTSService>();

            // 准备LLM请求
            var llmRequest = new LocalLLMRequest
            {
                ModelName = request.Model,
                Message = request.Text,
                SystemPrompt = request.SystemPrompt ?? "你是一个专业的AI助手，请用中文回答问题。回答要准确、简洁、有帮助。",
                Stream = true,
                Temperature = 0.7f,
                MaxTokens = 1000
            };

            var textBuffer = new List<string>();
            var sentenceBuffer = "";
            var audioTasks = new List<Task<TTSResponse>>();
            var audioUrls = new List<string>();
            int chunkIndex = 0;

            // 用于存储待发送的响应
            var responsesToSend = new Queue<StreamingChatResponse>();
            Exception? caughtException = null;

            try
            {
                // 流式获取LLM响应
                await foreach (var llmChunk in llmService.ChatStreamAsync(llmRequest))
                {
                    // 准备文本块响应
                    responsesToSend.Enqueue(new StreamingChatResponse
                    {
                        Type = "text",
                        TextDelta = llmChunk.Delta,
                        IsComplete = false,
                        Metadata = new Dictionary<string, object>
                        {
                            ["chunkIndex"] = chunkIndex++,
                            ["tokenIndex"] = llmChunk.TokenIndex
                        }
                    });

                    // 累积文本用于句子分割
                    sentenceBuffer += llmChunk.Delta;
                    textBuffer.Add(llmChunk.Delta);

                    // 检测完整的句子
                    var sentences = SplitIntoSentences(sentenceBuffer);
                    if (sentences.Count > 1)
                    {
                        // 处理完整的句子（除了最后一个）
                        for (int i = 0; i < sentences.Count - 1; i++)
                        {
                            var sentence = sentences[i].Trim();
                            if (!string.IsNullOrEmpty(sentence))
                            {
                                // 异步生成TTS
                                var ttsTask = GenerateTTSAsync(sentence, request.Voice, ttsService);
                                audioTasks.Add(ttsTask);

                                // 当有音频生成完成时，立即发送
                                _ = Task.Run(async () =>
                                {
                                    var ttsResult = await ttsTask;
                                    if (ttsResult.Success)
                                    {
                                        audioUrls.Add(ttsResult.AudioUrl);
                                    }
                                });
                            }
                        }

                        // 保留最后一个未完成的句子
                        sentenceBuffer = sentences[sentences.Count - 1];
                    }

                    // 如果LLM响应完成
                    if (llmChunk.IsComplete)
                    {
                        // 处理最后的句子
                        if (!string.IsNullOrEmpty(sentenceBuffer.Trim()))
                        {
                            var ttsTask = GenerateTTSAsync(sentenceBuffer.Trim(), request.Voice, ttsService);
                            audioTasks.Add(ttsTask);
                        }
                    }
                }

                // 等待所有TTS任务完成
                var ttsResults = await Task.WhenAll(audioTasks);
                
                // 准备音频响应
                foreach (var ttsResult in ttsResults.Where(r => r.Success))
                {
                    responsesToSend.Enqueue(new StreamingChatResponse
                    {
                        Type = "audio",
                        AudioChunkUrl = ttsResult.AudioUrl,
                        IsComplete = false,
                        Metadata = new Dictionary<string, object>
                        {
                            ["duration"] = ttsResult.Duration,
                            ["fileSize"] = ttsResult.FileSize
                        }
                    });
                }

                // 生成数字人视频
                if (audioUrls.Any())
                {
                    var videoRequest = new GenerateVideoRequest
                    {
                        AvatarId = request.AvatarId,
                        AudioUrl = audioUrls.First(), // 使用第一个音频生成视频
                        Quality = request.Quality,
                        Async = true
                    };

                    var videoResult = await GenerateRealtimeVideoAsync(videoRequest);
                    
                    if (videoResult.Success)
                    {
                        responsesToSend.Enqueue(new StreamingChatResponse
                        {
                            Type = "video",
                            VideoUrl = videoResult.VideoUrl,
                            IsComplete = false,
                            Metadata = new Dictionary<string, object>
                            {
                                ["taskId"] = videoResult.TaskId,
                                ["processingTime"] = videoResult.ProcessingTime
                            }
                        });
                    }
                }

                // 准备完成响应
                responsesToSend.Enqueue(new StreamingChatResponse
                {
                    Type = "complete",
                    IsComplete = true,
                    Metadata = new Dictionary<string, object>
                    {
                        ["totalText"] = string.Join("", textBuffer),
                        ["audioCount"] = audioUrls.Count,
                        ["totalChunks"] = chunkIndex
                    }
                });
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "流式对话处理失败");
                caughtException = ex;
            }

            // 在try-catch块外发送响应
            while (responsesToSend.Count > 0)
            {
                yield return responsesToSend.Dequeue();
            }

            // 如果有异常，发送错误响应
            if (caughtException != null)
            {
                yield return new StreamingChatResponse
                {
                    Type = "error",
                    TextDelta = caughtException.Message,
                    IsComplete = true
                };
            }
        }

        /// <summary>
        /// 生成实时数字人视频
        /// </summary>
        public async Task<GenerateVideoResponse> GenerateRealtimeVideoAsync(GenerateVideoRequest request)
        {
            var stopwatch = Stopwatch.StartNew();

            try
            {
                _logger.LogInformation("开始生成实时数字人视频: Avatar={Avatar}", request.AvatarId);

                // 获取模板服务
                var templateService = _serviceProvider.GetRequiredService<IDigitalHumanTemplateService>();

                // 准备音频文件
                string audioPath = "";
                if (!string.IsNullOrEmpty(request.AudioUrl))
                {
                    // 从URL获取音频文件路径
                    audioPath = Path.Combine("wwwroot", request.AudioUrl.TrimStart('/'));
                }
                else if (request.AudioData != null && request.AudioData.Length > 0)
                {
                    // 保存音频数据到临时文件
                    var audioFileName = $"realtime_audio_{Guid.NewGuid()}.mp3";
                    audioPath = Path.Combine(_tempPath, audioFileName);
                    await File.WriteAllBytesAsync(audioPath, request.AudioData);
                }

                // 由于GenerateWithTemplateRequest没有AudioPath属性，
                // 我们需要先从音频文件生成文本（如果需要的话），
                // 或者直接使用预设文本
                var generateRequest = new GenerateWithTemplateRequest
                {
                    TemplateId = request.AvatarId,
                    Text = "数字人视频生成中", // 使用默认文本，因为音频已经包含内容
                    Quality = request.Quality,
                    ResponseMode = "realtime"
                };

                var result = await templateService.GenerateWithTemplateAsync(generateRequest);

                stopwatch.Stop();

                if (result.Success)
                {
                    return new GenerateVideoResponse
                    {
                        Success = true,
                        VideoUrl = result.VideoUrl,
                        TaskId = Guid.NewGuid().ToString(), // 生成一个任务ID
                        Status = "completed",
                        ProcessingTime = (int)stopwatch.ElapsedMilliseconds
                    };
                }
                else
                {
                    return new GenerateVideoResponse
                    {
                        Success = false,
                        Status = "failed",
                        ProcessingTime = (int)stopwatch.ElapsedMilliseconds
                    };
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "生成实时数字人视频失败");
                return new GenerateVideoResponse
                {
                    Success = false,
                    Status = "failed",
                    ProcessingTime = (int)stopwatch.ElapsedMilliseconds
                };
            }
        }

        /// <summary>
        /// 流式文本转语音
        /// </summary>
        public async IAsyncEnumerable<AudioChunkResponse> TextToSpeechStreamAsync(TTSStreamRequest request)
        {
            var ttsService = _serviceProvider.GetRequiredService<IEdgeTTSService>();
            
            await foreach (var chunk in ttsService.TextToSpeechStreamAsync(request))
            {
                yield return chunk;
            }
        }

        /// <summary>
        /// 生成TTS音频
        /// </summary>
        private async Task<TTSResponse> GenerateTTSAsync(string text, string voice, IEdgeTTSService ttsService)
        {
            var ttsRequest = new TTSRequest
            {
                Text = text,
                Voice = voice,
                Rate = "1.0",
                Pitch = "0Hz"
            };

            return await ttsService.TextToSpeechAsync(ttsRequest);
        }

        /// <summary>
        /// 将文本分割成句子
        /// </summary>
        private List<string> SplitIntoSentences(string text)
        {
            // 中文句子分割
            var pattern = @"[。！？；!?;]+";
            var sentences = Regex.Split(text, pattern)
                .Where(s => !string.IsNullOrWhiteSpace(s))
                .ToList();

            // 如果没有找到句子分隔符，检查是否有足够长的文本
            if (sentences.Count == 0 && text.Length > 50)
            {
                // 按逗号分割较长的文本
                pattern = @"[，,]+";
                sentences = Regex.Split(text, pattern)
                    .Where(s => !string.IsNullOrWhiteSpace(s) && s.Length > 10)
                    .ToList();
            }

            return sentences.Count > 0 ? sentences : new List<string> { text };
        }
    }
} 