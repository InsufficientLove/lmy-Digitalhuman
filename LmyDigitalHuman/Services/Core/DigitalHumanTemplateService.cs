using LmyDigitalHuman.Models;
using LmyDigitalHuman.Services;
using LmyDigitalHuman.Services.Extensions;
using System.Diagnostics;
using System.Text.Json;
using System.Text.RegularExpressions;
using System.Collections.Concurrent;
using Microsoft.Extensions.Caching.Memory;

namespace LmyDigitalHuman.Services.Core
{
    public class DigitalHumanTemplateService : IDigitalHumanTemplateService
    {
        private readonly ILogger<DigitalHumanTemplateService> _logger;
        private readonly IMemoryCache _cache;
        private readonly IConfiguration _configuration;
        private readonly ILocalLLMService _llmService;
        private readonly IWhisperNetService _whisperService;
        private readonly HttpClient _httpClient;
        private readonly IMuseTalkService _museTalkService;
        
        private readonly ConcurrentDictionary<string, DigitalHumanTemplate> _templates = new();
        private readonly string _templatesPath;
        private readonly string _outputPath;
        private readonly string _tempPath;
        // SadTalker已移除，现在使用MuseTalk

        public DigitalHumanTemplateService(
            ILogger<DigitalHumanTemplateService> logger,
            IMemoryCache cache,
            IConfiguration configuration,
            ILocalLLMService llmService,
            IWhisperNetService whisperService,
            HttpClient httpClient,
            IMuseTalkService museTalkService)
        {
            _logger = logger;
            _cache = cache;
            _configuration = configuration;
            _llmService = llmService;
            _whisperService = whisperService;
            _httpClient = httpClient;
            _museTalkService = museTalkService;
            
            // 优先使用全局 Paths 配置（Docker 环境挂载目录），不存在时回退到 DigitalHumanTemplate 同名配置，再回退到默认值
            _templatesPath = (
                _configuration["Paths:Templates"]
                ?? _configuration["DigitalHumanTemplate:TemplatesPath"]
                ?? Path.Combine("wwwroot", "templates")
            ).Replace('/', Path.DirectorySeparatorChar);
            _outputPath = (
                _configuration["Paths:Videos"]
                ?? _configuration["DigitalHumanTemplate:OutputPath"]
                ?? Path.Combine("wwwroot", "videos")
            ).Replace('/', Path.DirectorySeparatorChar);
            _tempPath = (
                _configuration["Paths:Temp"]
                ?? _configuration["DigitalHumanTemplate:TempPath"]
                ?? "temp"
            ).Replace('/', Path.DirectorySeparatorChar);
            // SadTalker配置已移除，现在使用MuseTalk
            
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
                _logger.LogInformation("开始创建数字人模板: DisplayName={DisplayName}, SystemName={SystemName}, ResourceType={ResourceType}", 
                    request.TemplateName, request.SystemName, request.ResourceType);

                // 生成模板ID
                var templateId = Guid.NewGuid().ToString("N");
                
                // 确保使用完整的绝对路径
                var fullTemplatesPath = Path.IsPathRooted(_templatesPath) 
                    ? _templatesPath 
                    : Path.Combine(Directory.GetCurrentDirectory(), _templatesPath);
                
                // 确保目录存在
                Directory.CreateDirectory(fullTemplatesPath);
                
                string filePath = "";
                string fileUrl = "";
                string resourceType = request.ResourceType ?? "image";
                
                // 处理图片或视频文件
                if (resourceType == "image")
                {
                    // 使用英文SystemName作为文件名，解决中文路径问题
                    var imageFileName = $"{request.SystemName}.jpg";
                    filePath = Path.Combine(fullTemplatesPath, imageFileName);
                    fileUrl = $"/templates/{imageFileName}";
                    
                    // 检查文件是否已存在（防止重名覆盖）
                    if (File.Exists(filePath))
                    {
                        _logger.LogWarning("模板文件已存在，将覆盖: {FileName}", imageFileName);
                    }
                    
                    _logger.LogInformation("保存模板图片到: {ImagePath}", filePath);
                    
                    using (var stream = new FileStream(filePath, FileMode.Create))
                    {
                        await request.ImageFile!.CopyToAsync(stream);
                    }
                }
                else if (resourceType == "video")
                {
                    // 视频模板
                    var videoFileName = $"{request.SystemName}.mp4";
                    filePath = Path.Combine(fullTemplatesPath, videoFileName);
                    fileUrl = $"/templates/{videoFileName}";
                    
                    if (File.Exists(filePath))
                    {
                        _logger.LogWarning("模板视频已存在，将覆盖: {FileName}", videoFileName);
                    }
                    
                    _logger.LogInformation("保存模板视频到: {VideoPath}", filePath);
                    
                    using (var stream = new FileStream(filePath, FileMode.Create))
                    {
                        await request.VideoFile!.CopyToAsync(stream);
                    }
                }

                // 创建模板对象
                var template = new DigitalHumanTemplate
                {
                    TemplateId = templateId,
                    DisplayName = request.TemplateName,  // 中文显示名
                    SystemName = request.SystemName,     // 英文系统名
                    ResourceType = resourceType,          // 资源类型
                    Description = request.Description,
                    TemplateType = request.TemplateType,
                    Gender = request.Gender,
                    AgeRange = request.AgeRange,
                    Style = request.Style,
                    EnableEmotion = request.EnableEmotion,
                    DefaultVoiceSettings = request.DefaultVoiceSettings ?? new VoiceSettings(),
                    CustomParameters = request.CustomParameters ?? new Dictionary<string, object>(),
                    CreatedAt = DateTime.Now,
                    UpdatedAt = DateTime.Now,
                    IsActive = true,
                    Status = "processing"
                };
                
                // 根据资源类型设置不同的路径
                if (resourceType == "image")
                {
                    template.ImagePath = filePath;
                    template.ImageUrl = fileUrl;
                }
                else
                {
                    template.VideoPath = filePath;
                    template.VideoUrl = fileUrl;
                }

                // 保存模板
                _templates[templateId] = template;
                await SaveTemplateToFileAsync(template);

                // 🔄 改为同步执行预处理，确保预处理完成后再返回响应
                try
                {
                    _logger.LogInformation("开始MuseTalk模板预处理: DisplayName={DisplayName}, SystemName={SystemName}, ResourceType={ResourceType}", 
                        template.DisplayName, template.SystemName, resourceType);
                    
                    bool preprocessSuccess = false;
                    
                    if (resourceType == "image")
                    {
                        // 图片模板预处理
                        var preprocessResult = await _museTalkService.PreprocessTemplateAsync(template.SystemName);
                        preprocessSuccess = preprocessResult.Success;
                        
                        if (!preprocessSuccess)
                        {
                            _logger.LogError("MuseTalk图片预处理失败: SystemName={SystemName}", template.SystemName);
                        }
                    }
                    else if (resourceType == "video")
                    {
                        // 视频模板预处理
                        var preprocessResult = await _museTalkService.PreprocessVideoAsync(template.SystemName, filePath);
                        preprocessSuccess = preprocessResult.Success;
                        
                        if (preprocessSuccess && !string.IsNullOrEmpty(preprocessResult.BboxPath))
                        {
                            template.VideoBboxPath = preprocessResult.BboxPath;
                            _logger.LogInformation("视频bbox路径: {BboxPath}", preprocessResult.BboxPath);
                        }
                        else
                        {
                            _logger.LogError("MuseTalk视频预处理失败: SystemName={SystemName}", template.SystemName);
                        }
                    }
                    
                    // 检查预处理结果
                    if (!preprocessSuccess)
                    {
                        template.Status = "error";
                        template.UpdatedAt = DateTime.Now;
                        await SaveTemplateToFileAsync(template);
                        
                        return new CreateDigitalHumanTemplateResponse
                        {
                            Success = false,
                            Message = "模板预处理失败，请检查服务连接",
                            TemplateId = templateId,
                            ProcessingTime = (DateTime.Now - startTime).TotalMilliseconds.ToString()
                        };
                    }
                    
                    _logger.LogInformation("MuseTalk预处理成功: SystemName={SystemName}", template.SystemName);
                    
                    // 预处理完成，模板就绪
                    _logger.LogInformation("模板预处理完成，已就绪: DisplayName={DisplayName}", template.DisplayName);
                    
                    // 更新模板状态为就绪
                    template.Status = "ready";
                    template.UpdatedAt = DateTime.Now;
                    
                    await SaveTemplateToFileAsync(template); // 更新模板信息
                    _logger.LogInformation("模板创建完成: DisplayName={DisplayName}, SystemName={SystemName}, ResourceType={ResourceType}, 预处理已就绪", 
                        template.DisplayName, template.SystemName, resourceType);
                }
                catch (Exception ex)
                {
                    _logger.LogError(ex, "模板预处理异常: DisplayName={DisplayName}, SystemName={SystemName}", 
                        template.DisplayName, template.SystemName);
                    template.Status = "error";
                    template.UpdatedAt = DateTime.Now;
                    await SaveTemplateToFileAsync(template);
                    
                    // 预处理失败时返回错误响应
                    return new CreateDigitalHumanTemplateResponse
                    {
                        Success = false,
                        Message = $"模板预处理异常: {ex.Message}",
                        TemplateId = templateId,
                        ProcessingTime = (DateTime.Now - startTime).TotalMilliseconds.ToString()
                    };
                }

                // 异步进行预览视频生成（可选，不影响模板就绪状态）
                _ = Task.Run(async () =>
                {
                    try
                    {
                        // 这里可以添加预览视频生成逻辑，但不是必需的
                        _logger.LogInformation("可选：生成预览视频...");
                    }
                    catch (Exception ex)
                    {
                        _logger.LogWarning(ex, "预览视频生成失败，但不影响模板使用");
                    }
                });

                // 立即返回创建结果，状态为processing，预处理在后台进行
                var processingTime = DateTime.Now - startTime;

                return new CreateDigitalHumanTemplateResponse
                {
                    Success = true,
                    TemplateId = templateId,
                    Message = "数字人模板创建成功，正在后台预处理...",
                    Template = template,  // 状态仍为"processing"
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
                // 先从内存中移除
                if (!_templates.TryRemove(templateId, out var template))
                {
                    _logger.LogWarning("模板不在内存中: {TemplateId}", templateId);
                    // 即使不在内存中，也尝试删除文件
                }

                // 删除JSON文件
                var templateFile = Path.Combine(_templatesPath, $"{templateId}.json");
                if (File.Exists(templateFile))
                {
                    File.Delete(templateFile);
                    _logger.LogInformation("已删除模板文件: {File}", templateFile);
                }

                // 删除所有可能的图片格式
                var imageExtensions = new[] { ".jpg", ".jpeg", ".png", ".webp", ".gif" };
                foreach (var ext in imageExtensions)
                {
                    var imageFile = Path.Combine(_templatesPath, $"{templateId}{ext}");
                    if (File.Exists(imageFile))
                    {
                        File.Delete(imageFile);
                        _logger.LogInformation("已删除图片文件: {File}", imageFile);
                    }
                    
                    // 也尝试删除以模板名称命名的文件（兼容旧格式）
                    if (template != null)
                    {
                        var nameImageFile = Path.Combine(_templatesPath, $"{template.SystemName}{ext}");
                        if (File.Exists(nameImageFile) && nameImageFile != imageFile)
                        {
                            File.Delete(nameImageFile);
                            _logger.LogInformation("已删除图片文件(按名称): {File}", nameImageFile);
                        }
                    }
                }

                // 删除预处理相关文件 - 使用统一的缓存目录
                // 优先使用环境变量，如果没有则使用配置文件，最后使用默认值
                var templateCacheDir = Environment.GetEnvironmentVariable("MUSE_TEMPLATE_CACHE_DIR") 
                    ?? _configuration["Paths:TemplateCache"] 
                    ?? "/opt/musetalk/template_cache";
                    
                // 使用SystemName作为目录名（如果template存在）
                var preprocessDirName = template?.SystemName ?? templateId;
                var preprocessDir = Path.Combine(templateCacheDir, preprocessDirName);
                
                if (Directory.Exists(preprocessDir))
                {
                    Directory.Delete(preprocessDir, true);
                    _logger.LogInformation("已删除预处理目录: {Dir}", preprocessDir);
                }
                
                // 也尝试用templateId删除（兼容旧数据）
                var preprocessDirById = Path.Combine(templateCacheDir, templateId);
                if (preprocessDirById != preprocessDir && Directory.Exists(preprocessDirById))
                {
                    Directory.Delete(preprocessDirById, true);
                    _logger.LogInformation("已删除预处理目录(按ID): {Dir}", preprocessDirById);
                }

                // 强制重新加载模板列表以确保同步
                LoadExistingTemplates();
                
                _logger.LogInformation("模板删除成功: {TemplateId}", templateId);
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
                var videoUrl = await GenerateVideoWithMuseTalkAsync(
                    template.TemplateName, audioUrl, request.Quality);

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
                    using var audioStream = request.AudioFile.OpenReadStream();
                    var transcriptionResult = await _whisperService.TranscribeAsync(audioStream);
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
                    ModelName = _configuration["LocalLLM:DefaultModel"] ?? _configuration["Ollama:Model"] ?? "qwen2.5:latest",
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

        public async Task<TemplateStatistics> GetStatisticsAsync()
        {
            return await GetTemplateStatisticsAsync();
        }

        public async Task<List<string>> GetPreRenderedVideosAsync(string templateId)
        {
            // 返回模板的预渲染视频列表
            var videos = new List<string>();
            if (_templates.TryGetValue(templateId, out var template) && !string.IsNullOrEmpty(template.PreviewVideoPath))
            {
                videos.Add(template.PreviewVideoPath);
            }
            return videos;
        }

        public async Task<bool> ClearPreRenderedCacheAsync(string templateId)
        {
            // 清理预渲染缓存
            return true;
        }

        public async Task<bool> IncrementUsageCountAsync(string templateId)
        {
            if (_templates.TryGetValue(templateId, out var template))
            {
                template.UsageCount++;
                template.UpdatedAt = DateTime.Now;
                await SaveTemplateToFileAsync(template);
                return true;
            }
            return false;
        }

        public async Task<string> GetOptimalQualitySettingAsync(string templateId, string responseMode)
        {
            // 根据响应模式返回最优质量设置
            return responseMode switch
            {
                "realtime" => "fast",
                "high_quality" => "high",
                _ => "medium"
            };
        }

        public async Task<bool> WarmupTemplateAsync(string templateId)
        {
            // 预热模板
            if (_templates.ContainsKey(templateId))
            {
                _logger.LogInformation("模板预热完成: {TemplateId}", templateId);
                return true;
            }
            return false;
        }

        public async Task<List<GenerateWithTemplateResponse>> ProcessBatchRequestsAsync(List<GenerateWithTemplateRequest> requests)
        {
            var responses = new List<GenerateWithTemplateResponse>();
            foreach (var request in requests)
            {
                try
                {
                    var response = await GenerateWithTemplateAsync(request);
                    responses.Add(response);
                }
                catch (Exception ex)
                {
                    _logger.LogError(ex, "批量处理请求失败");
                    responses.Add(new GenerateWithTemplateResponse
                    {
                        Success = false,
                        Message = ex.Message
                    });
                }
            }
            return responses;
        }

        public async Task<bool> IsTemplateAvailableForProcessingAsync(string templateId)
        {
            return _templates.ContainsKey(templateId) && _templates[templateId].IsActive;
        }

        public async Task<bool> RefreshTemplateCacheAsync(string? templateId = null)
        {
            if (string.IsNullOrEmpty(templateId))
            {
                // 刷新所有模板缓存
                LoadExistingTemplates();
                return true;
            }
            else
            {
                // 刷新特定模板缓存
                return _templates.ContainsKey(templateId);
            }
        }

        public async Task<long> GetCacheSizeAsync()
        {
            // 返回缓存大小估算
            return _templates.Count * 1024; // 简单估算
        }

        public async Task<bool> ClearExpiredCacheAsync()
        {
            // 清理过期缓存
            return true;
        }

        public async Task<bool> ValidateTemplateAsync(string templateId)
        {
            return await Task.FromResult(_templates.ContainsKey(templateId));
        }

        public async Task<string> GetTemplatePreviewAsync(string templateId)
        {
            return await Task.Run(() =>
            {
                if (_templates.TryGetValue(templateId, out var template))
                {
                    return template.PreviewVideoPath ?? string.Empty;
                }
                return string.Empty;
            });
        }

        public async Task<DigitalHumanTemplate> CloneTemplateAsync(string templateId, string newName)
        {
            if (!_templates.TryGetValue(templateId, out var originalTemplate))
            {
                throw new ArgumentException("源模板不存在", nameof(templateId));
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

            return clonedTemplate;
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

        public async Task<Dictionary<string, object>> GetTemplateCacheStatusAsync()
        {
            return new Dictionary<string, object>
            {
                ["total_cached_items"] = _templates.Count,
                ["cache_size_mb"] = 0, // 模拟值
                ["last_cleanup"] = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss"),
                ["templates"] = _templates.Keys.ToList()
            };
        }

        public async Task<bool> ClearTemplateCacheAsync(string? templateId = null)
        {
            // 清理与模板相关的缓存
            return true;
        }

        // 私有辅助方法
        private void InitializeDefaultTemplates()
        {
            // 清理旧的示例模板文件
            CleanupOldSampleTemplates();
            
            // 加载已存在的模板文件
            LoadExistingTemplates();
            
            // 不再自动创建示例模板，由用户手动创建
            _logger.LogInformation("模板服务初始化完成，当前模板数量: {Count}", _templates.Count);
        }

        private void LoadExistingTemplates()
        {
            try
            {
                if (!Directory.Exists(_templatesPath))
                {
                    Directory.CreateDirectory(_templatesPath);
                    _logger.LogInformation("Templates目录不存在，已创建: {Path}", _templatesPath);
                    return;
                }

                var jsonFiles = Directory.GetFiles(_templatesPath, "*.json");
                _logger.LogInformation("正在加载已存在的模板文件，共找到 {Count} 个文件", jsonFiles.Length);

                foreach (var jsonFile in jsonFiles)
                {
                    try
                    {
                        var json = File.ReadAllText(jsonFile, System.Text.Encoding.UTF8);
                        var template = JsonSerializer.Deserialize<DigitalHumanTemplate>(json);
                        
                        if (template != null && !string.IsNullOrEmpty(template.TemplateId))
                        {
                            // 验证图片文件是否存在
                            var imageFileName = Path.GetFileName(template.ImagePath?.TrimStart('/'));
                            var fullImagePath = Path.Combine(_templatesPath, imageFileName ?? "");
                            
                            if (!string.IsNullOrEmpty(imageFileName) && File.Exists(fullImagePath))
                            {
                                // 确保ImagePath和ImageUrl格式正确
                                template.ImagePath = $"/templates/{imageFileName}";
                                template.ImageUrl = $"/templates/{imageFileName}";
                                _templates[template.TemplateId] = template;
                                _logger.LogInformation("成功加载模板: {Name} ({Id})", template.TemplateName, template.TemplateId);
                            }
                            else
                            {
                                _logger.LogWarning("模板 {Name} 的图片文件不存在: {ImagePath}", template.TemplateName, fullImagePath);
                            }
                        }
                        else
                        {
                            _logger.LogWarning("无效的模板文件: {File}", jsonFile);
                        }
                    }
                    catch (Exception ex)
                    {
                        _logger.LogError(ex, "加载模板文件失败: {File}", jsonFile);
                    }
                }

                _logger.LogInformation("模板加载完成，共加载 {Count} 个有效模板", _templates.Count);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "加载现有模板时发生错误");
            }
        }

        // CreateSampleTemplates方法已完全移除 - 业务从用户创建模板开始

        private async Task SaveTemplateToFileAsync(DigitalHumanTemplate template)
        {
            // 直接使用模板名称作为JSON文件名，支持中文
            var filePath = Path.Combine(_templatesPath, $"{template.TemplateName}.json");
            var json = JsonSerializer.Serialize(template, new JsonSerializerOptions { 
                WriteIndented = true,
                Encoder = System.Text.Encodings.Web.JavaScriptEncoder.UnsafeRelaxedJsonEscaping 
            });
            await File.WriteAllTextAsync(filePath, json, System.Text.Encoding.UTF8);
        }

        private async Task GeneratePreviewVideoAsync(DigitalHumanTemplate template)
        {
            try
            {
                var previewText = "你好，我是您的专属数字人助手，很高兴为您服务！";
                var audioUrl = await GenerateAudioAsync(previewText, template.DefaultVoiceSettings);
                                        var videoUrl = await GenerateVideoWithMuseTalkAsync(template.TemplateName, audioUrl, "medium");
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
                // 构建 TTS 命令 - 使用语音设置中的语音或配置中的默认语音
                var voice = voiceSettings?.Voice ?? voiceSettings?.VoiceId ?? _configuration["RealtimeDigitalHuman:EdgeTTS:DefaultVoice"] ?? "zh-CN-XiaoxiaoNeural";
                var rate = voiceSettings?.Speed ?? 1.0f;
                
                // 处理 Pitch - 如果是字符串，转换为数值
                float pitch = 0.0f;
                if (voiceSettings?.Pitch != null)
                {
                    if (float.TryParse(voiceSettings.Pitch, out float parsedPitch))
                    {
                        pitch = parsedPitch;
                    }
                    else
                    {
                        // 处理预设值
                        pitch = voiceSettings.Pitch.ToLower() switch
                        {
                            "low" => -0.2f,
                            "medium" => 0.0f,
                            "high" => 0.2f,
                            _ => 0.0f
                        };
                    }
                }
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

        /// <summary>
        /// 使用MuseTalk生成视频 - 调用OptimizedMuseTalkService
        /// </summary>
        private async Task<string> GenerateVideoWithMuseTalkAsync(string templateName, string audioPath, string quality)
        {
            try
            {
                _logger.LogInformation("使用MuseTalk生成视频: 模板={TemplateName}, 音频={AudioPath}", templateName, audioPath);
                
                // 构建模板图片路径
                var imagePath = Path.Combine(_templatesPath, $"{templateName}.jpg");
                
                // 检查模板图片是否存在
                if (!File.Exists(imagePath))
                {
                    _logger.LogError("模板图片不存在: {ImagePath}", imagePath);
                    throw new Exception($"模板图片不存在: {imagePath}");
                }
                
                // 检查音频文件是否存在
                if (!File.Exists(audioPath))
                {
                    _logger.LogError("音频文件不存在: {AudioPath}", audioPath);
                    throw new Exception($"音频文件不存在: {audioPath}");
                }
                
                // 调用MuseTalk服务生成视频
                var request = new DigitalHumanRequest
                {
                    AvatarImagePath = imagePath, // 使用物理路径
                    AudioPath = audioPath,
                    Quality = quality,
                    EnableEmotion = true
                };
                
                var response = await _museTalkService.GenerateVideoAsync(request);
                
                if (!response.Success)
                {
                    throw new Exception($"MuseTalk视频生成失败: {response.Message}");
                }
                
                _logger.LogInformation("MuseTalk视频生成成功: {VideoPath}", response.VideoPath);
                
                // 返回web访问路径
                var fileName = Path.GetFileName(response.VideoPath);
                return $"/videos/{fileName}";
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "MuseTalk视频生成失败");
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

        /// <summary>
        /// 清理旧的示例模板文件
        /// </summary>
        private void CleanupOldSampleTemplates()
        {
            try
            {
                var sampleTemplateIds = new[] { "sample-female-1", "sample-male-1", "sample-female-2" };
                
                foreach (var templateId in sampleTemplateIds)
                {
                    // 删除JSON配置文件
                    var jsonPath = Path.Combine(_templatesPath, $"{templateId}.json");
                    if (File.Exists(jsonPath))
                    {
                        File.Delete(jsonPath);
                        _logger.LogInformation("已删除旧示例模板配置: {JsonPath}", jsonPath);
                    }
                    
                    // 删除图片文件
                    var imagePath = Path.Combine(_templatesPath, $"{templateId}.jpg");
                    if (File.Exists(imagePath))
                    {
                        File.Delete(imagePath);
                        _logger.LogInformation("已删除旧示例模板图片: {ImagePath}", imagePath);
                    }
                }
            }
            catch (Exception ex)
            {
                _logger.LogWarning(ex, "清理旧示例模板时出现错误");
            }
        }
    }
}