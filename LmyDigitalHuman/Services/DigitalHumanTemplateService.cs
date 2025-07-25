using LmyDigitalHuman.Models;
using LmyDigitalHuman.Services.Extensions;
using System.Diagnostics;
using System.Text.Json;
using System.Text.RegularExpressions;
using System.Collections.Concurrent;
using Microsoft.Extensions.Caching.Memory;

namespace LmyDigitalHuman.Services
{
    public class DigitalHumanTemplateService : IDigitalHumanTemplateService
    {
        private readonly ILogger<DigitalHumanTemplateService> _logger;
        private readonly IMemoryCache _cache;
        private readonly IConfiguration _configuration;
        private readonly ILocalLLMService _llmService;
        private readonly IWhisperService _whisperService;
        private readonly HttpClient _httpClient;
        
        private readonly ConcurrentDictionary<string, DigitalHumanTemplate> _templates = new();
        private readonly string _templatesPath;
        private readonly string _outputPath;
        private readonly string _tempPath;
        private readonly string _sadTalkerPath;

        public DigitalHumanTemplateService(
            ILogger<DigitalHumanTemplateService> logger,
            IMemoryCache cache,
            IConfiguration configuration,
            ILocalLLMService llmService,
            IWhisperService whisperService,
            HttpClient httpClient)
        {
            _logger = logger;
            _cache = cache;
            _configuration = configuration;
            _llmService = llmService;
            _whisperService = whisperService;
            _httpClient = httpClient;
            
            _templatesPath = (_configuration["DigitalHumanTemplate:TemplatesPath"] ?? Path.Combine("wwwroot", "templates")).Replace('/', Path.DirectorySeparatorChar);
            _outputPath = (_configuration["DigitalHumanTemplate:OutputPath"] ?? Path.Combine("wwwroot", "videos")).Replace('/', Path.DirectorySeparatorChar);
            _tempPath = (_configuration["DigitalHumanTemplate:TempPath"] ?? "temp").Replace('/', Path.DirectorySeparatorChar);
            _sadTalkerPath = (_configuration["RealtimeDigitalHuman:SadTalker:Path"] ?? Path.Combine("C:", "AI", "SadTalker")).Replace('/', Path.DirectorySeparatorChar);
            
            Directory.CreateDirectory(_templatesPath);
            Directory.CreateDirectory(_outputPath);
            Directory.CreateDirectory(_tempPath);
            
            // 初始化默认模板
            InitializeDefaultTemplates();
        }

        public async Task<CreateDigitalHumanTemplateResponse> CreateTemplateAsync(CreateDigitalHumanTemplateRequest request)
        {
            var startTime = DateTime.Now;
            
            try
            {
                _logger.LogInformation("开始创建数字人模板: {TemplateName}", request.TemplateName);

                // 生成模板ID
                var templateId = Guid.NewGuid().ToString("N");
                
                // 保存头像图片
                var imageFileName = $"{templateId}.jpg";
                var imagePath = Path.Combine(_templatesPath, imageFileName);
                
                using (var stream = new FileStream(imagePath, FileMode.Create))
                {
                    await request.ImageFile.CopyToAsync(stream);
                }

                // 创建模板对象
                var template = new DigitalHumanTemplate
                {
                    TemplateId = templateId,
                    TemplateName = request.TemplateName,
                    Description = request.Description,
                    TemplateType = request.TemplateType,
                    Gender = request.Gender,
                    AgeRange = request.AgeRange,
                    Style = request.Style,
                    EnableEmotion = request.EnableEmotion,
                    ImagePath = $"/templates/{imageFileName}",
                    DefaultVoiceSettings = request.DefaultVoiceSettings ?? new VoiceSettings(),
                    CustomParameters = request.CustomParameters ?? new Dictionary<string, object>(),
                    CreatedAt = DateTime.Now,
                    UpdatedAt = DateTime.Now,
                    IsActive = true,
                    Status = "processing"
                };

                // 保存模板
                _templates[templateId] = template;
                await SaveTemplateToFileAsync(template);

                // 异步生成预览视频，不阻塞模板创建
                _ = Task.Run(async () =>
                {
                    try
                    {
                        var previewText = "你好，我是明懿，欢迎咨询";
                        var audioUrl = await GenerateAudioAsync(previewText, template.DefaultVoiceSettings);
                        var videoUrl = await GenerateVideoWithSadTalkerAsync(template.ImagePath, audioUrl, "medium", "neutral");
                        template.PreviewVideoPath = videoUrl;
                        await SaveTemplateToFileAsync(template); // 更新模板信息
                        _logger.LogInformation("预览视频生成成功: {VideoUrl}", videoUrl);
                    }
                    catch (Exception ex)
                    {
                        _logger.LogError(ex, "生成预览视频失败");
                    }
                });

                template.Status = "ready";
                template.UpdatedAt = DateTime.Now;

                // 重新保存包含预览视频信息的模板
                await SaveTemplateToFileAsync(template);

                var processingTime = DateTime.Now - startTime;

                return new CreateDigitalHumanTemplateResponse
                {
                    Success = true,
                    TemplateId = templateId,
                    Message = "数字人模板创建成功",
                    Template = template,
                    ProcessingTime = $"{processingTime.TotalMilliseconds:F0}ms"
                };
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "创建数字人模板失败: {TemplateName}", request.TemplateName);
                return new CreateDigitalHumanTemplateResponse
                {
                    Success = false,
                    Message = $"创建失败: {ex.Message}",
                    ProcessingTime = $"{(DateTime.Now - startTime).TotalMilliseconds:F0}ms"
                };
            }
        }

        public async Task<GetTemplatesResponse> GetTemplatesAsync(GetTemplatesRequest request)
        {
            try
            {
                var templates = _templates.Values.AsEnumerable();

                // 过滤条件
                if (!string.IsNullOrEmpty(request.TemplateType))
                {
                    templates = templates.Where(t => t.TemplateType == request.TemplateType);
                }

                if (!string.IsNullOrEmpty(request.Gender))
                {
                    templates = templates.Where(t => t.Gender == request.Gender);
                }

                if (!string.IsNullOrEmpty(request.Style))
                {
                    templates = templates.Where(t => t.Style == request.Style);
                }

                if (!string.IsNullOrEmpty(request.SearchKeyword))
                {
                    templates = templates.Where(t => 
                        t.TemplateName.Contains(request.SearchKeyword, StringComparison.OrdinalIgnoreCase) ||
                        t.Description.Contains(request.SearchKeyword, StringComparison.OrdinalIgnoreCase));
                }

                // 排序
                templates = request.SortBy switch
                {
                    "usage_desc" => templates.OrderByDescending(t => t.UsageCount),
                    "name_asc" => templates.OrderBy(t => t.TemplateName),
                    _ => templates.OrderByDescending(t => t.CreatedAt)
                };

                var totalCount = templates.Count();
                var totalPages = (int)Math.Ceiling((double)totalCount / request.PageSize);

                // 分页
                var pagedTemplates = templates
                    .Skip((request.Page - 1) * request.PageSize)
                    .Take(request.PageSize)
                    .ToList();

                return new GetTemplatesResponse
                {
                    Success = true,
                    Templates = pagedTemplates,
                    TotalCount = totalCount,
                    Page = request.Page,
                    PageSize = request.PageSize,
                    TotalPages = totalPages
                };
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "获取模板列表失败");
                return new GetTemplatesResponse
                {
                    Success = false,
                    Templates = new List<DigitalHumanTemplate>()
                };
            }
        }

        public async Task<DigitalHumanTemplate?> GetTemplateByIdAsync(string templateId)
        {
            return _templates.TryGetValue(templateId, out var template) ? template : null;
        }

        public async Task<bool> UpdateTemplateAsync(string templateId, CreateDigitalHumanTemplateRequest request)
        {
            try
            {
                if (!_templates.TryGetValue(templateId, out var template))
                {
                    return false;
                }

                template.TemplateName = request.TemplateName;
                template.Description = request.Description;
                template.TemplateType = request.TemplateType;
                template.Gender = request.Gender;
                template.AgeRange = request.AgeRange;
                template.Style = request.Style;
                template.EnableEmotion = request.EnableEmotion;
                template.DefaultVoiceSettings = request.DefaultVoiceSettings ?? template.DefaultVoiceSettings;
                template.CustomParameters = request.CustomParameters ?? template.CustomParameters;
                template.UpdatedAt = DateTime.Now;

                await SaveTemplateToFileAsync(template);
                return true;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "更新模板失败: {TemplateId}", templateId);
                return false;
            }
        }

        public async Task<bool> DeleteTemplateAsync(string templateId)
        {
            try
            {
                if (!_templates.TryRemove(templateId, out var template))
                {
                    return false;
                }

                // 删除相关文件
                var templateFile = Path.Combine(_templatesPath, $"{templateId}.json");
                if (File.Exists(templateFile))
                {
                    File.Delete(templateFile);
                }

                var imageFile = Path.Combine(_templatesPath, $"{templateId}.jpg");
                if (File.Exists(imageFile))
                {
                    File.Delete(imageFile);
                }

                return true;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "删除模板失败: {TemplateId}", templateId);
                return false;
            }
        }

        public async Task<GenerateWithTemplateResponse> GenerateWithTemplateAsync(GenerateWithTemplateRequest request)
        {
            var startTime = DateTime.Now;
            
            try
            {
                _logger.LogInformation("使用模板生成视频: {TemplateId}, 文本: {Text}", 
                    request.TemplateId, request.Text);

                if (!_templates.TryGetValue(request.TemplateId, out var template))
                {
                    return new GenerateWithTemplateResponse
                    {
                        Success = false,
                        Message = "模板不存在"
                    };
                }

                // 检查缓存
                var cacheKey = $"video_{request.TemplateId}_{request.Text.GetHashCode()}_{request.Quality}_{request.Emotion}";
                if (request.UseCache && _cache.TryGetValue(cacheKey, out string cachedVideoUrl))
                {
                    return new GenerateWithTemplateResponse
                    {
                        Success = true,
                        VideoUrl = cachedVideoUrl,
                        ProcessingTime = "0ms",
                        ResponseMode = request.ResponseMode,
                        FromCache = true,
                        Template = template
                    };
                }

                // 生成语音
                var audioUrl = await GenerateAudioAsync(request.Text, 
                    request.VoiceSettings ?? template.DefaultVoiceSettings);

                // 生成视频
                var videoUrl = await GenerateVideoWithSadTalkerAsync(
                    template.ImagePath, audioUrl, request.Quality, request.Emotion);

                // 更新使用次数
                template.UsageCount++;
                template.UpdatedAt = DateTime.Now;

                // 缓存结果
                if (request.UseCache)
                {
                    _cache.Set(cacheKey, videoUrl, TimeSpan.FromHours(24));
                }

                var processingTime = DateTime.Now - startTime;

                return new GenerateWithTemplateResponse
                {
                    Success = true,
                    VideoUrl = videoUrl,
                    AudioUrl = audioUrl,
                    ProcessingTime = $"{processingTime.TotalMilliseconds:F0}ms",
                    ResponseMode = request.ResponseMode,
                    FromCache = false,
                    Template = template
                };
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "使用模板生成视频失败");
                return new GenerateWithTemplateResponse
                {
                    Success = false,
                    Message = $"生成失败: {ex.Message}",
                    ProcessingTime = $"{(DateTime.Now - startTime).TotalMilliseconds:F0}ms"
                };
            }
        }

        public async Task<RealtimeConversationResponse> RealtimeConversationAsync(RealtimeConversationRequest request)
        {
            var startTime = DateTime.Now;
            
            try
            {
                _logger.LogInformation("实时对话: {TemplateId}, 输入类型: {InputType}", 
                    request.TemplateId, request.InputType);

                if (!_templates.TryGetValue(request.TemplateId, out var template))
                {
                    return new RealtimeConversationResponse
                    {
                        Success = false,
                        Message = "模板不存在"
                    };
                }

                string userInput = request.Text ?? "";
                string detectedEmotion = "neutral";

                // 处理音频输入
                if (request.InputType == "audio" && request.AudioFile != null)
                {
                    var transcriptionResult = await _whisperService.TranscribeAsync(request.AudioFile);
                    userInput = transcriptionResult.Text;
                    
                    // 简单的情感检测
                    if (request.EnableEmotionDetection)
                    {
                        detectedEmotion = DetectEmotionFromText(userInput);
                    }
                }

                // 调用本地大模型获取回复
                var llmResponse = await _llmService.ChatAsync(new LocalLLMRequest
                {
                    ModelName = _configuration["LocalLLM:DefaultModel"] ?? "qwen2.5:14b-instruct-q4_0",
                    Message = userInput,
                    ConversationId = request.ConversationId,
                    Temperature = 0.7f,
                    MaxTokens = 500,
                    SystemPrompt = "你是一个友好、专业的AI助手。请用简洁、自然的语言回答问题。"
                });

                if (!llmResponse.Success)
                {
                    return new RealtimeConversationResponse
                    {
                        Success = false,
                        Message = "大模型服务异常"
                    };
                }

                // 生成数字人视频
                var videoResponse = await GenerateWithTemplateAsync(new GenerateWithTemplateRequest
                {
                    TemplateId = request.TemplateId,
                    Text = llmResponse.Response,
                    ResponseMode = request.ResponseMode,
                    Quality = request.Quality,
                    Emotion = detectedEmotion,
                    UseCache = true
                });

                var processingTime = DateTime.Now - startTime;

                return new RealtimeConversationResponse
                {
                    Success = true,
                    ConversationId = request.ConversationId ?? Guid.NewGuid().ToString("N"),
                    RecognizedText = userInput,
                    ResponseText = llmResponse.Response,
                    VideoUrl = videoResponse.VideoUrl ?? "",
                    AudioUrl = videoResponse.AudioUrl ?? "",
                    DetectedEmotion = detectedEmotion,
                    ProcessingTime = $"{processingTime.TotalMilliseconds:F0}ms",
                    FromCache = videoResponse.FromCache,
                    Template = template
                };
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "实时对话失败");
                return new RealtimeConversationResponse
                {
                    Success = false,
                    Message = $"对话失败: {ex.Message}",
                    ProcessingTime = $"{(DateTime.Now - startTime).TotalMilliseconds:F0}ms"
                };
            }
        }

        // 其他方法的实现...
        public async Task<BatchPreRenderResponse> BatchPreRenderAsync(BatchPreRenderRequest request)
        {
            var startTime = DateTime.Now;
            int successCount = 0;
            var failedTexts = new List<string>();

            try
            {
                if (!_templates.TryGetValue(request.TemplateId, out var template))
                {
                    return new BatchPreRenderResponse
                    {
                        Success = false,
                        Message = "模板不存在"
                    };
                }

                for (int i = 0; i < request.TextList.Count; i++)
                {
                    try
                    {
                        var text = request.TextList[i];
                        var emotion = request.EmotionList?.ElementAtOrDefault(i) ?? "neutral";

                        await GenerateWithTemplateAsync(new GenerateWithTemplateRequest
                        {
                            TemplateId = request.TemplateId,
                            Text = text,
                            Quality = request.Quality,
                            Emotion = emotion,
                            UseCache = true
                        });

                        successCount++;
                    }
                    catch
                    {
                        failedTexts.Add(request.TextList[i]);
                    }
                }

                return new BatchPreRenderResponse
                {
                    Success = true,
                    TotalCount = request.TextList.Count,
                    SuccessCount = successCount,
                    FailedCount = failedTexts.Count,
                    FailedTexts = failedTexts,
                    ProcessingTime = $"{(DateTime.Now - startTime).TotalMilliseconds:F0}ms"
                };
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "批量预渲染失败");
                return new BatchPreRenderResponse
                {
                    Success = false,
                    Message = $"批量预渲染失败: {ex.Message}"
                };
            }
        }

        public async Task<TemplateStatistics> GetTemplateStatisticsAsync()
        {
            var templates = _templates.Values.ToList();
            
            return new TemplateStatistics
            {
                TotalTemplates = templates.Count,
                ActiveTemplates = templates.Count(t => t.IsActive),
                TotalUsage = templates.Sum(t => t.UsageCount),
                TemplateTypeCount = templates.GroupBy(t => t.TemplateType)
                    .ToDictionary(g => g.Key, g => g.Count()),
                GenderCount = templates.GroupBy(t => t.Gender)
                    .ToDictionary(g => g.Key, g => g.Count()),
                StyleCount = templates.GroupBy(t => t.Style)
                    .ToDictionary(g => g.Key, g => g.Count()),
                MostUsedTemplates = templates.OrderByDescending(t => t.UsageCount).Take(5).ToList(),
                RecentTemplates = templates.OrderByDescending(t => t.CreatedAt).Take(5).ToList()
            };
        }

        public async Task<bool> ValidateTemplateAsync(string templateId)
        {
            return await Task.FromResult(_templates.ContainsKey(templateId));
        }

        public async Task<string?> GetTemplatePreviewAsync(string templateId)
        {
            return await Task.Run(() =>
            {
                if (_templates.TryGetValue(templateId, out var template))
                {
                    return template.PreviewVideoPath;
                }
                return null;
            });
        }

        public async Task<CreateDigitalHumanTemplateResponse> CloneTemplateAsync(string templateId, string newName)
        {
            if (!_templates.TryGetValue(templateId, out var originalTemplate))
            {
                return new CreateDigitalHumanTemplateResponse
                {
                    Success = false,
                    Message = "源模板不存在"
                };
            }

            var newTemplateId = Guid.NewGuid().ToString("N");
            var clonedTemplate = new DigitalHumanTemplate
            {
                TemplateId = newTemplateId,
                TemplateName = newName,
                Description = originalTemplate.Description,
                TemplateType = originalTemplate.TemplateType,
                Gender = originalTemplate.Gender,
                AgeRange = originalTemplate.AgeRange,
                Style = originalTemplate.Style,
                EnableEmotion = originalTemplate.EnableEmotion,
                ImagePath = originalTemplate.ImagePath, // 共享图片
                DefaultVoiceSettings = originalTemplate.DefaultVoiceSettings,
                CustomParameters = originalTemplate.CustomParameters,
                CreatedAt = DateTime.Now,
                UpdatedAt = DateTime.Now,
                IsActive = true,
                Status = "ready"
            };

            _templates[newTemplateId] = clonedTemplate;
            await SaveTemplateToFileAsync(clonedTemplate);

            return new CreateDigitalHumanTemplateResponse
            {
                Success = true,
                TemplateId = newTemplateId,
                Template = clonedTemplate,
                Message = "模板复制成功"
            };
        }

        public async Task<byte[]> ExportTemplateAsync(string templateId)
        {
            if (!_templates.TryGetValue(templateId, out var template))
            {
                return Array.Empty<byte>();
            }

            var json = JsonSerializer.Serialize(template, new JsonSerializerOptions { WriteIndented = true });
            return System.Text.Encoding.UTF8.GetBytes(json);
        }

        public async Task<CreateDigitalHumanTemplateResponse> ImportTemplateAsync(IFormFile configFile)
        {
            try
            {
                using var stream = configFile.OpenReadStream();
                var template = await JsonSerializer.DeserializeAsync<DigitalHumanTemplate>(stream);
                
                if (template == null)
                {
                    return new CreateDigitalHumanTemplateResponse
                    {
                        Success = false,
                        Message = "配置文件格式错误"
                    };
                }

                template.TemplateId = Guid.NewGuid().ToString("N");
                template.CreatedAt = DateTime.Now;
                template.UpdatedAt = DateTime.Now;

                _templates[template.TemplateId] = template;
                await SaveTemplateToFileAsync(template);

                return new CreateDigitalHumanTemplateResponse
                {
                    Success = true,
                    TemplateId = template.TemplateId,
                    Template = template,
                    Message = "模板导入成功"
                };
            }
            catch (Exception ex)
            {
                return new CreateDigitalHumanTemplateResponse
                {
                    Success = false,
                    Message = $"导入失败: {ex.Message}"
                };
            }
        }

        public async Task<Dictionary<string, object>> GetTemplateCacheStatusAsync(string templateId)
        {
            return new Dictionary<string, object>
            {
                ["template_id"] = templateId,
                ["cache_size"] = 0,
                ["cache_hits"] = 0,
                ["cache_misses"] = 0
            };
        }

        public async Task<bool> ClearTemplateCacheAsync(string templateId)
        {
            // 清理与模板相关的缓存
            return true;
        }

        // 私有辅助方法
        private void InitializeDefaultTemplates()
        {
            // 移除默认模板，只支持自定义数字人
            // 不再初始化任何默认模板
        }

        private async Task SaveTemplateToFileAsync(DigitalHumanTemplate template)
        {
            var filePath = Path.Combine(_templatesPath, $"{template.TemplateId}.json");
            var json = JsonSerializer.Serialize(template, new JsonSerializerOptions { WriteIndented = true });
            await File.WriteAllTextAsync(filePath, json);
        }

        private async Task GeneratePreviewVideoAsync(DigitalHumanTemplate template)
        {
            try
            {
                var previewText = "你好，我是您的专属数字人助手，很高兴为您服务！";
                var audioUrl = await GenerateAudioAsync(previewText, template.DefaultVoiceSettings);
                var videoUrl = await GenerateVideoWithSadTalkerAsync(template.ImagePath, audioUrl, "medium", "neutral");
                template.PreviewVideoPath = videoUrl;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "生成预览视频失败");
            }
        }

        private async Task<string> GenerateAudioAsync(string text, VoiceSettings voiceSettings)
        {
            try
            {
                // 构建 TTS 命令 - 使用配置中的默认语音
                var voice = _configuration["RealtimeDigitalHuman:EdgeTTS:DefaultVoice"] ?? "zh-CN-XiaoxiaoNeural";
                var rate = voiceSettings?.Speed ?? 1.0f;
                var pitch = voiceSettings?.Pitch ?? 0.0f;
                var fileName = $"tts_{Guid.NewGuid()}.wav";
                var outputPath = Path.Combine(_tempPath, fileName);

                // 确保temp目录存在
                Directory.CreateDirectory(_tempPath);

                // 构造 edge-tts 命令
                string ratePercent = rate == 1.0f ? "+0%" : (rate > 1.0f ? $"+{(int)((rate - 1.0f) * 100)}%" : $"-{(int)((1.0f - rate) * 100)}%");
                // 尝试执行 edge-tts
                var success = await TryExecuteEdgeTTSAsync(text, voice, ratePercent, pitch, outputPath);
                
                if (!success)
                {
                    _logger.LogError("所有TTS执行方式都失败了");
                    throw new Exception("语音合成失败: edge-tts 命令不可用。请确保已安装 edge-tts (pip install edge-tts)");
                }

                // 检查文件是否生成
                if (!File.Exists(outputPath))
                {
                    _logger.LogError("TTS输出文件不存在: {Path}", outputPath);
                    throw new Exception($"语音合成失败，输出文件不存在: {outputPath}");
                }

                // 检查文件大小
                var fileInfo = new FileInfo(outputPath);
                if (fileInfo.Length == 0)
                {
                    _logger.LogError("TTS输出文件为空: {Path}", outputPath);
                    throw new Exception("语音合成失败，输出文件为空");
                }

                _logger.LogInformation("TTS成功生成音频文件: {Path}, 大小: {Size} bytes", outputPath, fileInfo.Length);

                return outputPath;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "GenerateAudioAsync 语音合成失败，text: {Text}", text);
                throw new Exception("语音合成失败: " + ex.Message);
            }
        }

        private async Task<string> GenerateVideoWithSadTalkerAsync(string imagePath, string audioPath, string quality, string emotion)
        {
            try
            {
                var videoFileName = $"video_{Guid.NewGuid():N}.mp4";
                var videoPath = Path.Combine(_outputPath, videoFileName);

                // 确保输出目录存在
                Directory.CreateDirectory(_outputPath);

                // 构建完整路径
                var fullImagePath = Path.Combine(Directory.GetCurrentDirectory(), "wwwroot", imagePath.TrimStart('/'));
                // 如果音频路径是相对路径，转换为绝对路径
                var fullAudioPath = Path.IsPathRooted(audioPath) ? audioPath : Path.GetFullPath(audioPath);

                // 检查文件是否存在
                if (!File.Exists(fullImagePath))
                {
                    _logger.LogError("图片文件不存在: {Path}", fullImagePath);
                    throw new Exception($"图片文件不存在: {fullImagePath}");
                }

                if (!File.Exists(fullAudioPath))
                {
                    _logger.LogError("音频文件不存在: {Path}", fullAudioPath);
                    throw new Exception($"音频文件不存在: {fullAudioPath}");
                }

                _logger.LogInformation("开始生成视频，图片: {ImagePath}, 音频: {AudioPath}", fullImagePath, fullAudioPath);

                // 检查SadTalker目录是否存在
                if (!Directory.Exists(_sadTalkerPath))
                {
                    _logger.LogError("SadTalker目录不存在: {Path}", _sadTalkerPath);
                    throw new Exception($"SadTalker目录不存在: {_sadTalkerPath}");
                }

                // 检查inference.py是否存在
                var inferencePath = Path.Combine(_sadTalkerPath, "inference.py");
                if (!File.Exists(inferencePath))
                {
                    _logger.LogError("SadTalker inference.py不存在: {Path}", inferencePath);
                    throw new Exception($"SadTalker inference.py不存在: {inferencePath}");
                }

                // 使用配置的Python路径（SadTalker虚拟环境）
                var pythonPath = _configuration["RealtimeDigitalHuman:SadTalker:PythonPath"] ?? 
                    _configuration["RealtimeDigitalHuman:Whisper:PythonPath"] ?? 
                    "python";

                // 将输出路径转换为绝对路径
                var fullOutputPath = Path.IsPathRooted(_outputPath) ? _outputPath : Path.GetFullPath(_outputPath);

                var process = new Process
                {
                    StartInfo = new ProcessStartInfo
                    {
                        FileName = pythonPath,
                        Arguments = BuildSadTalkerArguments(fullAudioPath, fullImagePath, fullOutputPath, quality),
                        WorkingDirectory = _sadTalkerPath,
                        UseShellExecute = false,
                        RedirectStandardOutput = true,
                        RedirectStandardError = true,
                        CreateNoWindow = true,
                        StandardOutputEncoding = System.Text.Encoding.UTF8,
                        StandardErrorEncoding = System.Text.Encoding.UTF8
                    }
                };

                // 设置Python环境变量
                process.StartInfo.EnvironmentVariables["PYTHONIOENCODING"] = "utf-8";
                process.StartInfo.EnvironmentVariables["PYTHONUNBUFFERED"] = "1";
                process.StartInfo.EnvironmentVariables["PYTHONUTF8"] = "1";
                // 禁用代理以避免edge-tts的警告
                process.StartInfo.EnvironmentVariables["NO_PROXY"] = "*";
                process.StartInfo.EnvironmentVariables["no_proxy"] = "*";

                _logger.LogInformation("执行SadTalker命令: {Python} {Arguments}", pythonPath, process.StartInfo.Arguments);
                _logger.LogInformation("工作目录: {WorkingDirectory}", _sadTalkerPath);
                _logger.LogInformation("输出目录: {OutputPath}", fullOutputPath);

                process.Start();
                
                // 添加超时机制
                var timeoutSeconds = _configuration.GetValue<int>("RealtimeDigitalHuman:SadTalker:TimeoutSeconds", 120);
                using var cts = new CancellationTokenSource(TimeSpan.FromSeconds(timeoutSeconds));
                
                var outputTask = process.StandardOutput.ReadToEndAsync();
                var errorTask = process.StandardError.ReadToEndAsync();
                
                try
                {
                    await process.WaitForExitAsync(cts.Token);
                    var output = await outputTask;
                    var error = await errorTask;

                // 清理进度条输出，只保留有意义的信息
                var cleanOutput = CleanProgressBarOutput(output);
                if (!string.IsNullOrWhiteSpace(cleanOutput))
                {
                    _logger.LogInformation("SadTalker输出: {Output}", cleanOutput);
                }
                
                // 尝试从输出中解析生成的视频路径
                var generatedVideoPath = ParseGeneratedVideoPath(output);
                
                if (!string.IsNullOrWhiteSpace(error))
                {
                    // 只记录真正的错误，忽略进度条
                    var cleanError = CleanProgressBarOutput(error);
                    if (!string.IsNullOrWhiteSpace(cleanError) && !cleanError.Contains("it/s]"))
                    {
                        _logger.LogError("SadTalker错误: {Error}", cleanError);
                    }
                }

                    if (process.ExitCode == 0)
                    {
                        // 优先使用从输出中解析的路径
                        string foundVideoPath = null;
                        
                        if (!string.IsNullOrEmpty(generatedVideoPath))
                        {
                            // 处理相对路径
                            var candidatePath = Path.IsPathRooted(generatedVideoPath) 
                                ? generatedVideoPath 
                                : Path.Combine(_sadTalkerPath, generatedVideoPath);
                            
                            if (File.Exists(candidatePath))
                            {
                                foundVideoPath = candidatePath;
                                _logger.LogInformation("使用从输出解析的视频路径: {Path}", foundVideoPath);
                            }
                        }
                        
                        // 如果解析失败，使用查找方法
                        if (string.IsNullOrEmpty(foundVideoPath))
                        {
                            foundVideoPath = FindGeneratedVideo(fullOutputPath, imagePath, audioPath);
                        }
                        
                        if (!string.IsNullOrEmpty(foundVideoPath))
                        {
                            var fileInfo = new FileInfo(foundVideoPath);
                            _logger.LogInformation("视频生成成功: {Path}, 大小: {Size} bytes", foundVideoPath, fileInfo.Length);
                            
                            // 如果生成在子目录，移动到主目录
                            var targetPath = Path.Combine(_outputPath, videoFileName);
                            if (foundVideoPath != targetPath)
                            {
                                Directory.CreateDirectory(Path.GetDirectoryName(targetPath));
                                File.Move(foundVideoPath, targetPath, true);
                                
                                // 清理空的子目录
                                TryCleanupEmptyDirectories(Path.GetDirectoryName(foundVideoPath));
                            }
                            
                            return $"/videos/{videoFileName}";
                        }
                        else
                        {
                            _logger.LogError("视频文件未找到，尝试路径: {Path}", Path.Combine(_outputPath, videoFileName));
                            throw new Exception("视频文件未生成");
                        }
                    }
                    else
                    {
                        var errorMessage = $"SadTalker视频生成失败，退出码: {process.ExitCode}";
                        if (!string.IsNullOrWhiteSpace(error))
                        {
                            errorMessage += $", 错误: {error}";
                        }
                        throw new Exception(errorMessage);
                    }
                }
                catch (OperationCanceledException)
                {
                    _logger.LogError("SadTalker执行超时 ({Timeout}秒)", timeoutSeconds);
                    
                    // 尝试终止进程
                    try
                    {
                        process.Kill(true);
                    }
                    catch { }
                    
                    throw new Exception($"视频生成超时（超过{timeoutSeconds}秒）");
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "生成视频失败");
                throw;
            }
        }

        private string DetectEmotionFromText(string text)
        {
            // 简单的情感检测逻辑
            if (text.Contains("高兴") || text.Contains("开心") || text.Contains("哈哈"))
                return "happy";
            if (text.Contains("生气") || text.Contains("愤怒") || text.Contains("讨厌"))
                return "angry";
            if (text.Contains("伤心") || text.Contains("难过") || text.Contains("哭"))
                return "sad";
            if (text.Contains("惊讶") || text.Contains("震惊") || text.Contains("哇"))
                return "surprised";
            
            return "neutral";
        }

        /// <summary>
        /// 尝试多种方式执行edge-tts命令
        /// </summary>
        private async Task<bool> TryExecuteEdgeTTSAsync(string text, string voice, string ratePercent, float pitch, string outputPath)
        {
            // 优先使用配置的Python路径（SadTalker虚拟环境）
            var pythonPath = _configuration["RealtimeDigitalHuman:SadTalker:PythonPath"] ?? 
                _configuration["RealtimeDigitalHuman:Whisper:PythonPath"] ?? 
                "python";
            
            try
            {
                _logger.LogInformation("使用Python路径执行edge-tts: {PythonPath}", pythonPath);
                
                if (await ExecuteCommandAsync(pythonPath, $"-m edge_tts --voice {voice} --rate {ratePercent} --pitch {pitch:+0}Hz --text \"{text}\" --write-media \"{outputPath}\""))
                {
                    if (File.Exists(outputPath) && new FileInfo(outputPath).Length > 0)
                    {
                        _logger.LogInformation("TTS成功生成音频文件: {Path}, 大小: {Size} bytes", outputPath, new FileInfo(outputPath).Length);
                        return true;
                    }
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "执行edge-tts失败: {PythonPath}", pythonPath);
            }

            // 备用方式: 直接执行edge-tts命令（如果已添加到PATH）
            try
            {
                _logger.LogInformation("尝试直接执行edge-tts命令");
                
                if (await ExecuteCommandAsync("edge-tts", $"--voice {voice} --rate {ratePercent} --pitch {pitch:+0}Hz --text \"{text}\" --write-media \"{outputPath}\""))
                {
                    if (File.Exists(outputPath) && new FileInfo(outputPath).Length > 0)
                    {
                        _logger.LogInformation("TTS成功生成音频文件（直接命令）: {Path}", outputPath);
                        return true;
                    }
                }
            }
            catch (Exception ex)
            {
                _logger.LogWarning("直接执行edge-tts失败: {Message}", ex.Message);
            }

            _logger.LogError("所有edge-tts执行方式都失败了");
            return false;
        }

        /// <summary>
        /// 执行命令的辅助方法
        /// </summary>
        private async Task<bool> ExecuteCommandAsync(string fileName, string arguments)
        {
            try
            {
                var processInfo = new ProcessStartInfo
                {
                    FileName = fileName,
                    Arguments = arguments,
                    RedirectStandardOutput = true,
                    RedirectStandardError = true,
                    UseShellExecute = false,
                    CreateNoWindow = true,
                    WorkingDirectory = Directory.GetCurrentDirectory(),
                    StandardOutputEncoding = System.Text.Encoding.UTF8,
                    StandardErrorEncoding = System.Text.Encoding.UTF8
                };

                // 设置环境变量
                processInfo.Environment["PYTHONIOENCODING"] = "utf-8";
                processInfo.Environment["PYTHONUNBUFFERED"] = "1";
                processInfo.Environment["PYTHONUTF8"] = "1";
                // 禁用代理以避免edge-tts的警告
                processInfo.Environment["NO_PROXY"] = "*";
                processInfo.Environment["no_proxy"] = "*";

                using var process = Process.Start(processInfo);
                if (process == null)
                {
                    return false;
                }

                var output = await process.StandardOutput.ReadToEndAsync();
                var error = await process.StandardError.ReadToEndAsync();
                await process.WaitForExitAsync();

                if (!string.IsNullOrWhiteSpace(output))
                {
                    _logger.LogDebug("命令输出: {Output}", output);
                }
                if (!string.IsNullOrWhiteSpace(error))
                {
                    _logger.LogDebug("命令错误: {Error}", error);
                }

                return process.ExitCode == 0;
            }
            catch (Exception ex)
            {
                _logger.LogDebug("执行命令失败 {FileName}: {Message}", fileName, ex.Message);
                return false;
            }
        }

        private string BuildSadTalkerArguments(string audioPath, string imagePath, string outputPath, string quality)
        {
            // 规范化路径分隔符（在Windows上SadTalker可能期望反斜杠）
            var normalizedAudioPath = audioPath.Replace('/', Path.DirectorySeparatorChar);
            var normalizedImagePath = imagePath.Replace('/', Path.DirectorySeparatorChar);
            var normalizedOutputPath = outputPath.Replace('/', Path.DirectorySeparatorChar);
            
            var args = new List<string>
            {
                "inference.py",
                $"--driven_audio \"{normalizedAudioPath}\"",
                $"--source_image \"{normalizedImagePath}\"",
                $"--result_dir \"{normalizedOutputPath}\"",
                "--still"
            };

            // 根据质量设置决定是否使用增强器
            var enableEnhancer = _configuration.GetValue<bool>("RealtimeDigitalHuman:SadTalker:EnableEnhancer", false);
            if (enableEnhancer && quality != "fast")
            {
                args.Add("--preprocess full");
                args.Add("--enhancer gfpgan");
            }
            else
            {
                args.Add("--preprocess crop");
            }

            // 其他可配置参数
            var batchSize = _configuration.GetValue<int>("RealtimeDigitalHuman:SadTalker:BatchSize", 2);
            args.Add($"--batch_size {batchSize}");
            
            // 添加size参数，确保输出文件名可预测
            args.Add("--size 256");

            return string.Join(" ", args);
        }

        private string FindGeneratedVideo(string outputPath, string imagePath, string audioPath)
        {
            try
            {
                // 获取图片和音频的文件名（不含扩展名）
                var imageNameWithoutExt = Path.GetFileNameWithoutExtension(imagePath);
                var audioNameWithoutExt = Path.GetFileNameWithoutExtension(audioPath);
                
                // 确保输出路径存在
                if (!Directory.Exists(outputPath))
                {
                    _logger.LogWarning("输出目录不存在: {Path}", outputPath);
                    
                    // 尝试在SadTalker工作目录下查找相对路径
                    var sadTalkerOutputPath = Path.Combine(_sadTalkerPath, _outputPath);
                    if (Directory.Exists(sadTalkerOutputPath))
                    {
                        _logger.LogInformation("在SadTalker目录下查找: {Path}", sadTalkerOutputPath);
                        outputPath = sadTalkerOutputPath;
                    }
                    else
                    {
                        return null;
                    }
                }
                
                // 查找所有mp4文件
                var mp4Files = Directory.GetFiles(outputPath, "*.mp4", SearchOption.AllDirectories);
                _logger.LogInformation("在目录 {Path} 中找到 {Count} 个MP4文件", outputPath, mp4Files.Length);
                
                foreach (var mp4File in mp4Files)
                {
                    var fileName = Path.GetFileName(mp4File);
                    
                    // SadTalker生成的文件名可能包含图片名和音频名
                    if (fileName.Contains(imageNameWithoutExt) || 
                        fileName.Contains(audioNameWithoutExt) ||
                        fileName.Contains("##"))
                    {
                        _logger.LogInformation("找到生成的视频文件: {Path}", mp4File);
                        return mp4File;
                    }
                }
                
                // 如果没找到，尝试获取最新的mp4文件
                var latestFile = mp4Files
                    .Select(f => new FileInfo(f))
                    .OrderByDescending(f => f.CreationTime)
                    .FirstOrDefault();
                    
                if (latestFile != null && (DateTime.Now - latestFile.CreationTime).TotalSeconds < 120)
                {
                    _logger.LogInformation("找到最新生成的视频文件: {Path}", latestFile.FullName);
                    return latestFile.FullName;
                }
                
                _logger.LogWarning("未找到符合条件的视频文件");
                return null;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "查找生成的视频文件时出错");
                return null;
            }
        }

        private void TryCleanupEmptyDirectories(string directory)
        {
            try
            {
                if (string.IsNullOrEmpty(directory) || !Directory.Exists(directory))
                    return;
                    
                // 如果目录为空，删除它
                if (!Directory.GetFiles(directory).Any() && !Directory.GetDirectories(directory).Any())
                {
                    Directory.Delete(directory);
                    _logger.LogInformation("清理空目录: {Path}", directory);
                }
            }
            catch (Exception ex)
            {
                _logger.LogWarning(ex, "清理目录失败: {Path}", directory);
            }
        }

        private string ParseGeneratedVideoPath(string output)
        {
            if (string.IsNullOrWhiteSpace(output))
                return null;
                
            try
            {
                // 查找 "The generated video is named" 的行
                var lines = output.Split(new[] { '\r', '\n' }, StringSplitOptions.RemoveEmptyEntries);
                foreach (var line in lines)
                {
                    if (line.Contains("The generated video is named") && line.Contains(".mp4"))
                    {
                        // 提取路径部分
                        var startIndex = line.IndexOf("named") + 5;
                        var path = line.Substring(startIndex).Trim();
                        
                        // 移除可能的冒号
                        if (path.EndsWith(":"))
                            path = path.TrimEnd(':');
                            
                        // 规范化路径分隔符
                        path = path.Replace('/', Path.DirectorySeparatorChar)
                                  .Replace('\\', Path.DirectorySeparatorChar);
                        
                        _logger.LogInformation("从输出中解析到视频路径: {Path}", path);
                        return path;
                    }
                }
            }
            catch (Exception ex)
            {
                _logger.LogWarning(ex, "解析视频路径时出错");
            }
            
            return null;
        }

        private string CleanProgressBarOutput(string output)
        {
            if (string.IsNullOrWhiteSpace(output))
                return output;

            // 移除进度条和重复的行
            var lines = output.Split(new[] { '\r', '\n' }, StringSplitOptions.RemoveEmptyEntries);
            var cleanedLines = new List<string>();
            var lastProgressLine = "";

            foreach (var line in lines)
            {
                // 跳过重复的进度条行
                if (line.Contains("%|") && line.Contains("it/s]"))
                {
                    // 只保留最后一个进度条行
                    lastProgressLine = line;
                    continue;
                }
                
                // 保留非进度条行
                if (!string.IsNullOrWhiteSpace(line))
                {
                    cleanedLines.Add(line);
                }
            }

            // 如果有进度条，添加最后一个
            if (!string.IsNullOrWhiteSpace(lastProgressLine))
            {
                cleanedLines.Add(lastProgressLine);
            }

            return string.Join("\n", cleanedLines);
        }
    }
}