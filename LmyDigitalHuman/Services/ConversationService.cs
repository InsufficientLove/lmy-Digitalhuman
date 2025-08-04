using LmyDigitalHuman.Models;
using Microsoft.Extensions.Caching.Memory;
using System.Collections.Concurrent;
using System.Diagnostics;
using System.Text.Json;

namespace LmyDigitalHuman.Services
{
    public class ConversationService : IConversationService
    {
        private readonly IDigitalHumanTemplateService _templateService;
        private readonly IMuseTalkService _museTalkService;
        private readonly IAudioPipelineService _audioPipelineService;
        private readonly ILocalLLMService _llmService;
        private readonly IMemoryCache _cache;
        private readonly IPathManager _pathManager;
        private readonly ILogger<ConversationService> _logger;
        
        // 并发字典用于管理对话上下文
        private readonly ConcurrentDictionary<string, ConversationContext> _conversationContexts = new();
        
        // 信号量控制并发数量
        private readonly SemaphoreSlim _concurrencySemaphore;
        private readonly SemaphoreSlim _realtimeSemaphore;
        
        // 性能统计
        private long _totalConversations = 0;
        private long _totalProcessingTime = 0;
        private readonly ConcurrentDictionary<string, long> _templateUsageCount = new();

        public ConversationService(
            IDigitalHumanTemplateService templateService,
            IMuseTalkService museTalkService,
            IAudioPipelineService audioPipelineService,
            ILocalLLMService llmService,
            IMemoryCache cache,
            IPathManager pathManager,
            ILogger<ConversationService> logger,
            IConfiguration configuration)
        {
            _templateService = templateService;
            _museTalkService = museTalkService;
            _audioPipelineService = audioPipelineService;
            _llmService = llmService;
            _cache = cache;
            _pathManager = pathManager;
            _logger = logger;
            
            // 从配置中获取并发限制
            var maxConcurrency = configuration.GetValue<int>("DigitalHuman:MaxConcurrentConversations", 10);
            var maxRealtimeConcurrency = configuration.GetValue<int>("DigitalHuman:MaxRealtimeConversations", 5);
            
            _concurrencySemaphore = new SemaphoreSlim(maxConcurrency, maxConcurrency);
            _realtimeSemaphore = new SemaphoreSlim(maxRealtimeConcurrency, maxRealtimeConcurrency);
        }

        public async Task<ConversationResponse> GenerateWelcomeVideoAsync(WelcomeVideoRequest request)
        {
            var stopwatch = Stopwatch.StartNew();
            
            try
            {
                _logger.LogInformation("开始生成欢迎视频: TemplateId={TemplateId}", request.TemplateId);

                // 获取模板信息
                var template = await _templateService.GetTemplateByIdAsync(request.TemplateId);
                if (template == null)
                {
                    return new ConversationResponse
                    {
                        Success = false,
                        Message = "模板不存在"
                    };
                }

                // 生成欢迎语
                var welcomeText = $"你好，我是{template.TemplateName}，欢迎咨询！";
                
                // 直接生成TTS，跳过LLM调用
                _logger.LogInformation("生成欢迎语TTS: {WelcomeText}", welcomeText);
                
                var ttsOutputPath = _pathManager.CreateTempAudioPath("wav");
                var ttsRequest = new TTSRequest
                {
                    Text = welcomeText,
                    Voice = template.DefaultVoiceSettings?.Voice ?? "zh-CN-XiaoxiaoNeural",
                    Rate = template.DefaultVoiceSettings?.Rate ?? "medium",
                    Pitch = template.DefaultVoiceSettings?.Pitch ?? "medium",
                    Emotion = "friendly",
                    OutputPath = ttsOutputPath
                };
                
                var ttsResult = await _audioPipelineService.ConvertTextToSpeechAsync(ttsRequest);
                
                if (!ttsResult.Success)
                {
                    return new ConversationResponse
                    {
                        Success = false,
                        Message = "欢迎语TTS生成失败: " + ttsResult.Error
                    };
                }

                // 🎬 直接使用模板的预览视频（已在创建时生成）
                _logger.LogInformation("使用预生成的预览视频: {PreviewVideoPath}", template.PreviewVideoPath);
                
                string videoUrl = template.PreviewVideoPath;
                
                // 如果没有预览视频，才进行实时生成
                if (string.IsNullOrEmpty(videoUrl))
                {
                    _logger.LogInformation("预览视频不存在，开始实时生成...");
                    
                    var videoResponse = await _museTalkService.GenerateVideoAsync(new DigitalHumanRequest
                    {
                        AvatarImagePath = template.ImagePath,
                        AudioPath = ttsResult.AudioPath,
                        Quality = request.Quality,
                        EnableEmotion = true,
                        CacheKey = $"welcome_{request.TemplateId}_{request.Quality}"
                    });
                    
                    if (!videoResponse.Success)
                    {
                        return new ConversationResponse
                        {
                            Success = false,
                            Message = $"欢迎视频生成失败: {videoResponse.Message}"
                        };
                    }
                    
                    videoUrl = videoResponse.VideoUrl;
                }

                stopwatch.Stop();

                return new ConversationResponse
                {
                    Success = true,
                    Message = "欢迎视频已就绪",
                    InputText = "模板选择", 
                    ResponseText = welcomeText,
                    VideoUrl = videoUrl,
                    // AudioUrl 已移除 - 不再显示音频
                    DetectedEmotion = "friendly",
                    ProcessingTime = $"{stopwatch.ElapsedMilliseconds}ms",
                    FromCache = !string.IsNullOrEmpty(template.PreviewVideoPath), // 使用预览视频算作缓存
                    HasVideo = !string.IsNullOrEmpty(videoUrl),
                    Duration = "3.1s" // 预估时长
                };
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "生成欢迎视频失败");
                stopwatch.Stop();
                
                return new ConversationResponse
                {
                    Success = false,
                    Message = ex.Message,
                    ProcessingTime = $"{stopwatch.ElapsedMilliseconds}ms"
                };
            }
        }

        public async Task<ConversationResponse> ProcessTextConversationAsync(TextConversationRequest request)
        {
            var stopwatch = Stopwatch.StartNew();
            
            await _concurrencySemaphore.WaitAsync();
            try
            {
                _logger.LogInformation("开始处理文本对话: TemplateId={TemplateId}, Text={Text}", 
                    request.TemplateId, request.Text[..Math.Min(50, request.Text.Length)]);

                // 获取或创建对话上下文
                var conversationId = request.ConversationId ?? Guid.NewGuid().ToString("N");
                var context = await GetOrCreateConversationContextAsync(conversationId, request.TemplateId);

                // 检查缓存
                var cacheKey = GenerateCacheKey("text", request.TemplateId, request.Text, request.Emotion);
                if (request.UseCache && _cache.TryGetValue(cacheKey, out ConversationResponse? cachedResponse))
                {
                    _logger.LogInformation("从缓存返回对话结果: CacheKey={CacheKey}", cacheKey);
                    cachedResponse!.FromCache = true;
                    cachedResponse.ConversationId = conversationId;
                    return cachedResponse;
                }

                var metrics = new ConversationMetrics();
                var metricsStopwatch = Stopwatch.StartNew();

                // 1. 调用LLM获取响应
                metricsStopwatch.Restart();
                var llmResponse = await _llmService.GenerateResponseAsync(new LocalLLMRequest
                {
                    Message = request.Text,
                    MaxTokens = 500,
                    Temperature = 0.7f
                });
                metrics.LLMResponseTime = metricsStopwatch.ElapsedMilliseconds;

                _logger.LogInformation("LLM响应结果: Success={Success}, ResponseText长度={ResponseLength}, Error={Error}",
                    llmResponse.Success, llmResponse.ResponseText?.Length ?? 0, llmResponse.Error);

                if (!llmResponse.Success)
                {
                    return new ConversationResponse
                    {
                        Success = false,
                        Message = "LLM响应失败: " + llmResponse.Error,
                        ConversationId = conversationId
                    };
                }

                // 检查LLM响应是否为空
                if (string.IsNullOrWhiteSpace(llmResponse.ResponseText))
                {
                    _logger.LogWarning("LLM返回空响应，使用默认回复");
                    llmResponse.ResponseText = "抱歉，我现在无法理解您的问题，请稍后再试。";
                }

                // 2. 获取模板语音设置
                var template = await _templateService.GetTemplateByIdAsync(request.TemplateId);
                if (template == null)
                {
                    return new ConversationResponse
                    {
                        Success = false,
                        Message = "模板不存在",
                        ConversationId = conversationId
                    };
                }

                // 3. 文本转语音
                _logger.LogInformation("开始TTS转换: ResponseText={ResponseText}, Voice={Voice}", 
                    llmResponse.ResponseText?.Length > 50 ? llmResponse.ResponseText.Substring(0, 50) + "..." : llmResponse.ResponseText, 
                    template.DefaultVoiceSettings?.Voice ?? "zh-CN-XiaoxiaoNeural");
                
                metricsStopwatch.Restart();
                var ttsOutputPath = _pathManager.CreateTempAudioPath("wav");
                var ttsRequest = new TTSRequest
                {
                    Text = llmResponse.ResponseText,
                    Voice = template.DefaultVoiceSettings?.Voice ?? "zh-CN-XiaoxiaoNeural",
                    Rate = template.DefaultVoiceSettings?.Rate ?? "medium",
                    Pitch = template.DefaultVoiceSettings?.Pitch ?? "medium",
                    Emotion = request.Emotion,
                    OutputPath = ttsOutputPath
                };
                
                _logger.LogInformation("TTS请求参数: Text长度={TextLength}, Voice={Voice}, Rate={Rate}, Pitch={Pitch}, OutputPath={OutputPath}",
                    ttsRequest.Text?.Length ?? 0, ttsRequest.Voice, ttsRequest.Rate, ttsRequest.Pitch, ttsRequest.OutputPath);
                
                var ttsResult = await _audioPipelineService.ConvertTextToSpeechAsync(ttsRequest);
                metrics.TTSProcessingTime = metricsStopwatch.ElapsedMilliseconds;

                _logger.LogInformation("TTS转换结果: Success={Success}, Error={Error}, AudioPath={AudioPath}",
                    ttsResult.Success, ttsResult.Error, ttsResult.AudioPath);

                if (!ttsResult.Success)
                {
                    _logger.LogError("TTS转换失败: {Error}", ttsResult.Error);
                    return new ConversationResponse
                    {
                        Success = false,
                        Message = "TTS生成失败: " + ttsResult.Error,
                        ConversationId = conversationId
                    };
                }

                // 4. 生成数字人视频
                metricsStopwatch.Restart();
                var videoResponse = await _museTalkService.GenerateVideoAsync(new DigitalHumanRequest
                {
                    AvatarImagePath = template.ImagePath,
                    AudioPath = ttsResult.AudioPath,
                    Quality = request.Quality,
                    EnableEmotion = true,
                    CacheKey = request.UseCache ? cacheKey : null
                });
                metrics.VideoGenerationTime = metricsStopwatch.ElapsedMilliseconds;

                stopwatch.Stop();
                metrics.TotalProcessingTime = stopwatch.ElapsedMilliseconds;

                var response = new ConversationResponse
                {
                    Success = videoResponse.Success,
                    Message = videoResponse.Message,
                    ConversationId = conversationId,
                    InputText = request.Text,
                    ResponseText = llmResponse.ResponseText,
                    VideoUrl = videoResponse.VideoUrl,
                    AudioUrl = $"/temp/{Path.GetFileName(ttsResult.AudioPath)}",
                    DetectedEmotion = request.Emotion,
                    ProcessingTime = $"{stopwatch.ElapsedMilliseconds}ms",
                    FromCache = false,
                    Metrics = new ServiceMetrics
                    {
                        ActiveWorkers = metrics.ActiveWorkers,
                        QueueLength = metrics.QueueLength,
                        AverageProcessingTime = metrics.AverageProcessingTime,
                        ThroughputPerHour = metrics.ThroughputPerHour,
                        ResourceUsage = metrics.ResourceUsage,
                        PerformanceWarnings = metrics.PerformanceWarnings
                    }
                };

                // 更新对话上下文
                await UpdateConversationContextAsync(conversationId, context, request.Text, llmResponse.ResponseText, request.Emotion, stopwatch.ElapsedMilliseconds);

                // 缓存结果
                if (request.UseCache && response.Success)
                {
                    _cache.Set(cacheKey, response, TimeSpan.FromHours(1));
                }

                // 更新统计
                Interlocked.Increment(ref _totalConversations);
                Interlocked.Add(ref _totalProcessingTime, stopwatch.ElapsedMilliseconds);
                _templateUsageCount.AddOrUpdate(request.TemplateId, 1, (key, value) => value + 1);

                return response;
            }
            finally
            {
                _concurrencySemaphore.Release();
            }
        }

        public async Task<ConversationResponse> ProcessAudioConversationAsync(AudioConversationRequest request)
        {
            var stopwatch = Stopwatch.StartNew();
            
            await _concurrencySemaphore.WaitAsync();
            try
            {
                _logger.LogInformation("开始处理音频对话: TemplateId={TemplateId}, AudioPath={AudioPath}", 
                    request.TemplateId, request.AudioPath);

                var conversationId = request.ConversationId ?? Guid.NewGuid().ToString("N");
                var context = await GetOrCreateConversationContextAsync(conversationId, request.TemplateId);
                var metrics = new ConversationMetrics();
                var metricsStopwatch = Stopwatch.StartNew();

                // 1. 语音识别
                metricsStopwatch.Restart();
                var speechResult = await _audioPipelineService.RecognizeSpeechFromFileAsync(request.AudioPath);
                metrics.AudioProcessingTime = metricsStopwatch.ElapsedMilliseconds;

                if (!speechResult.Success)
                {
                    return new ConversationResponse
                    {
                        Success = false,
                        Message = "语音识别失败: " + speechResult.Error,
                        ConversationId = conversationId
                    };
                }

                // 2. 情感检测（如果启用）
                string detectedEmotion = "neutral";
                if (request.EnableEmotionDetection)
                {
                    var emotionResult = await _audioPipelineService.DetectEmotionFromAudioAsync(request.AudioPath);
                    if (emotionResult.Success)
                    {
                        detectedEmotion = emotionResult.PrimaryEmotion;
                    }
                }

                // 检查缓存
                var cacheKey = GenerateCacheKey("audio", request.TemplateId, speechResult.Text, detectedEmotion);
                if (request.UseCache && _cache.TryGetValue(cacheKey, out ConversationResponse? cachedResponse))
                {
                    cachedResponse!.FromCache = true;
                    cachedResponse.ConversationId = conversationId;
                    cachedResponse.InputText = speechResult.Text;
                    cachedResponse.DetectedEmotion = detectedEmotion;
                    return cachedResponse;
                }

                // 3. 调用LLM获取响应
                metricsStopwatch.Restart();
                var llmResponse = await _llmService.GenerateResponseAsync(new LocalLLMRequest
                {
                    Message = speechResult.Text,
                    MaxTokens = 500,
                    Temperature = 0.7f
                });
                metrics.LLMResponseTime = metricsStopwatch.ElapsedMilliseconds;

                if (!llmResponse.Success)
                {
                    return new ConversationResponse
                    {
                        Success = false,
                        Message = "LLM响应失败: " + llmResponse.Error,
                        ConversationId = conversationId,
                        InputText = speechResult.Text
                    };
                }

                // 4. 文本转语音
                metricsStopwatch.Restart();
                var ttsResult = await _audioPipelineService.ConvertTextToSpeechAsync(new TTSRequest
                {
                    Text = llmResponse.ResponseText,
                    Emotion = detectedEmotion,
                    OutputPath = _pathManager.CreateTempAudioPath("wav")
                });
                metrics.TTSProcessingTime = metricsStopwatch.ElapsedMilliseconds;

                if (!ttsResult.Success)
                {
                    return new ConversationResponse
                    {
                        Success = false,
                        Message = "TTS生成失败: " + ttsResult.Error,
                        ConversationId = conversationId,
                        InputText = speechResult.Text
                    };
                }

                // 5. 生成数字人视频
                var template = await _templateService.GetTemplateByIdAsync(request.TemplateId);
                if (template == null)
                {
                    return new ConversationResponse
                    {
                        Success = false,
                        Message = "模板不存在",
                        ConversationId = conversationId,
                        InputText = speechResult.Text
                    };
                }

                metricsStopwatch.Restart();
                var videoResponse = await _museTalkService.GenerateVideoAsync(new DigitalHumanRequest
                {
                    AvatarImagePath = template.ImagePath,
                    AudioPath = ttsResult.AudioPath,
                    Quality = request.Quality,
                    EnableEmotion = true,
                    CacheKey = request.UseCache ? cacheKey : null
                });
                metrics.VideoGenerationTime = metricsStopwatch.ElapsedMilliseconds;

                stopwatch.Stop();
                metrics.TotalProcessingTime = stopwatch.ElapsedMilliseconds;

                var response = new ConversationResponse
                {
                    Success = videoResponse.Success,
                    Message = videoResponse.Message,
                    ConversationId = conversationId,
                    InputText = speechResult.Text,
                    ResponseText = llmResponse.ResponseText,
                    VideoUrl = videoResponse.VideoUrl,
                    AudioUrl = $"/temp/{Path.GetFileName(ttsResult.AudioPath)}",
                    DetectedEmotion = detectedEmotion,
                    ProcessingTime = $"{stopwatch.ElapsedMilliseconds}ms",
                    FromCache = false,
                    Metrics = new ServiceMetrics
                    {
                        ActiveWorkers = metrics.ActiveWorkers,
                        QueueLength = metrics.QueueLength,
                        AverageProcessingTime = metrics.AverageProcessingTime,
                        ThroughputPerHour = metrics.ThroughputPerHour,
                        ResourceUsage = metrics.ResourceUsage,
                        PerformanceWarnings = metrics.PerformanceWarnings
                    }
                };

                // 更新对话上下文
                await UpdateConversationContextAsync(conversationId, context, speechResult.Text, llmResponse.ResponseText, detectedEmotion, stopwatch.ElapsedMilliseconds);

                // 缓存结果
                if (request.UseCache && response.Success)
                {
                    _cache.Set(cacheKey, response, TimeSpan.FromHours(1));
                }

                // 更新统计
                Interlocked.Increment(ref _totalConversations);
                Interlocked.Add(ref _totalProcessingTime, stopwatch.ElapsedMilliseconds);
                _templateUsageCount.AddOrUpdate(request.TemplateId, 1, (key, value) => value + 1);

                return response;
            }
            finally
            {
                _concurrencySemaphore.Release();
            }
        }

        public async Task<RealtimeConversationResponse> StartRealtimeConversationAsync(StartRealtimeConversationRequest request)
        {
            await _realtimeSemaphore.WaitAsync();
            try
            {
                var conversationId = Guid.NewGuid().ToString("N");
                var context = await GetOrCreateConversationContextAsync(conversationId, request.TemplateId);
                
                _logger.LogInformation("开始实时对话: ConversationId={ConversationId}, TemplateId={TemplateId}", 
                    conversationId, request.TemplateId);

                // 预热模板
                await _templateService.WarmupTemplateAsync(request.TemplateId);
                await _museTalkService.WarmupTemplateAsync(request.TemplateId);

                return new RealtimeConversationResponse
                {
                    Success = true,
                    ConversationId = conversationId,
                    Message = "实时对话已启动"
                };
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "启动实时对话失败");
                return new RealtimeConversationResponse
                {
                    Success = false,
                    Message = "启动实时对话失败: " + ex.Message
                };
            }
        }

        public async Task<RealtimeConversationResponse> ProcessRealtimeAudioAsync(ProcessRealtimeAudioRequest request)
        {
            // 实时音频处理的实现，类似于ProcessAudioConversationAsync，但针对实时场景进行优化
            // 这里简化实现，实际需要支持流式处理
            throw new NotImplementedException("实时音频处理功能待实现");
        }

        public async Task<bool> EndRealtimeConversationAsync(string conversationId)
        {
            try
            {
                if (_conversationContexts.TryRemove(conversationId, out var context))
                {
                    context.State = ConversationState.Ended;
                    _logger.LogInformation("结束实时对话: ConversationId={ConversationId}", conversationId);
                    return true;
                }
                return false;
            }
            finally
            {
                _realtimeSemaphore.Release();
            }
        }

        public async Task<ConversationContext> GetConversationContextAsync(string conversationId)
        {
            await Task.CompletedTask;
            return _conversationContexts.GetValueOrDefault(conversationId) ?? new ConversationContext
            {
                ConversationId = conversationId,
                State = ConversationState.Error
            };
        }

        public async Task<bool> UpdateConversationContextAsync(string conversationId, ConversationContext context)
        {
            await Task.CompletedTask;
            _conversationContexts.AddOrUpdate(conversationId, context, (key, existingContext) => context);
            return true;
        }

        public async Task<bool> ClearConversationContextAsync(string conversationId)
        {
            await Task.CompletedTask;
            return _conversationContexts.TryRemove(conversationId, out _);
        }

        public async Task<List<ConversationResponse>> ProcessBatchConversationsAsync(List<TextConversationRequest> requests)
        {
            var tasks = requests.Select(ProcessTextConversationAsync).ToArray();
            var results = await Task.WhenAll(tasks);
            return results.ToList();
        }

        public async Task<List<ConversationHistory>> GetConversationHistoryAsync(string? conversationId = null, int limit = 50)
        {
            await Task.CompletedTask;
            
            var histories = new List<ConversationHistory>();
            var contexts = conversationId != null 
                ? _conversationContexts.Where(kvp => kvp.Key == conversationId)
                : _conversationContexts.AsEnumerable();

            foreach (var (id, context) in contexts.Take(limit))
            {
                histories.Add(new ConversationHistory
                {
                    ConversationId = id,
                    TemplateId = context.TemplateId,
                    StartTime = context.StartTime,
                    EndTime = context.LastUpdateTime,
                    TurnCount = context.History.Count,
                    TotalProcessingTime = context.History.Sum(h => h.ProcessingTime),
                    State = context.State
                });
            }

            return histories;
        }

        public async Task<ConversationStatistics> GetConversationStatisticsAsync()
        {
            await Task.CompletedTask;
            
            var activeConversations = _conversationContexts.Count(kvp => kvp.Value.State == ConversationState.Active);
            var averageProcessingTime = _totalConversations > 0 ? _totalProcessingTime / _totalConversations : 0;
            
            var emotionDistribution = new Dictionary<string, int>();
            var dailyConversationCount = new Dictionary<string, long>();

            foreach (var context in _conversationContexts.Values)
            {
                foreach (var turn in context.History)
                {
                    // 统计情感分布
                    if (!string.IsNullOrEmpty(turn.Emotion))
                    {
                        emotionDistribution[turn.Emotion] = emotionDistribution.GetValueOrDefault(turn.Emotion, 0) + 1;
                    }

                    // 统计每日对话数量
                    var dateKey = turn.Timestamp.ToString("yyyy-MM-dd");
                    dailyConversationCount[dateKey] = dailyConversationCount.GetValueOrDefault(dateKey, 0) + 1;
                }
            }

            return new ConversationStatistics
            {
                TotalConversations = (int)_totalConversations,
                ActiveConversations = activeConversations,
                AverageProcessingTime = averageProcessingTime,
                TemplateUsageCount = _templateUsageCount.ToDictionary(kvp => kvp.Key, kvp => (int)kvp.Value),
                EmotionDistribution = emotionDistribution,
                DailyConversationCount = dailyConversationCount
            };
        }

        public async Task<bool> PreloadTemplateForConversationAsync(string templateId)
        {
            try
            {
                await _templateService.WarmupTemplateAsync(templateId);
                await _museTalkService.WarmupTemplateAsync(templateId);
                return true;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "预加载模板失败: TemplateId={TemplateId}", templateId);
                return false;
            }
        }

        public async Task<string> GetOptimalResponseModeAsync(string templateId, ConversationMetrics metrics)
        {
            await Task.CompletedTask;
            
            // 基于性能指标推荐最优响应模式
            if (metrics.TotalProcessingTime < 2000) // 2秒以内
            {
                return "instant";
            }
            else if (metrics.TotalProcessingTime < 5000) // 5秒以内
            {
                return "fast";
            }
            else
            {
                return "quality";
            }
        }

        private async Task<ConversationContext> GetOrCreateConversationContextAsync(string conversationId, string templateId)
        {
            await Task.CompletedTask;
            
            return _conversationContexts.GetOrAdd(conversationId, id => new ConversationContext
            {
                ConversationId = id,
                TemplateId = templateId,
                StartTime = DateTime.UtcNow,
                LastUpdateTime = DateTime.UtcNow,
                State = ConversationState.Active
            });
        }

        private async Task UpdateConversationContextAsync(string conversationId, ConversationContext context, 
            string userInput, string botResponse, string emotion, long processingTime)
        {
            await Task.CompletedTask;
            
            context.History.Add(new ConversationTurn
            {
                Timestamp = DateTime.UtcNow,
                UserInput = userInput,
                BotResponse = botResponse,
                Emotion = emotion,
                ProcessingTime = processingTime,
                FromCache = false
            });
            
            context.LastUpdateTime = DateTime.UtcNow;
            
            // 限制历史记录数量
            if (context.History.Count > 100)
            {
                context.History.RemoveRange(0, context.History.Count - 100);
            }
        }

        private string GenerateCacheKey(string type, string templateId, string text, string emotion)
        {
            var content = $"{type}:{templateId}:{text}:{emotion}";
            return Convert.ToBase64String(System.Text.Encoding.UTF8.GetBytes(content));
        }


    }
}