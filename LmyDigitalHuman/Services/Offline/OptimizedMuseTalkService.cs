using System;
using LmyDigitalHuman.Services;
using System.Collections.Generic;
using System.IO;
using System.Threading.Tasks;
using System.Net.Http;
using LmyDigitalHuman.Models;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Configuration;

namespace LmyDigitalHuman.Services.Offline
{
    // 使用HTTP API客户端与Python MuseTalk服务通信
    public class OptimizedMuseTalkService : IMuseTalkService
    {
        private readonly ILogger<OptimizedMuseTalkService> _logger;
        private readonly MuseTalkApiClient _apiClient;
        private readonly IPathManager _pathManager;
        private readonly IConfiguration _configuration;

        public OptimizedMuseTalkService(
            ILogger<OptimizedMuseTalkService> logger,
            IPathManager pathManager,
            IConfiguration configuration,
            IHttpClientFactory httpClientFactory,
            ILoggerFactory loggerFactory)
        {
            _logger = logger;
            _pathManager = pathManager;
            _configuration = configuration;
            _apiClient = new MuseTalkApiClient(
                loggerFactory.CreateLogger<MuseTalkApiClient>(),
                configuration,
                httpClientFactory
            );
        }

        public async Task<DigitalHumanResponse> GenerateVideoAsync(DigitalHumanRequest request)
        {
            try
            {
                var contentRoot = _pathManager.GetContentRootPath();
                var videosDir = Path.Combine(contentRoot, "wwwroot", "videos");
                Directory.CreateDirectory(videosDir);

                var outputPath = Path.Combine(videosDir, $"musetalk_{Guid.NewGuid():N}.mp4");
                // 使用与预处理相同的缓存目录
                // 确保有有效的TemplateId
                if (string.IsNullOrEmpty(request.TemplateId))
                {
                    _logger.LogError("TemplateId不能为空");
                    return new DigitalHumanResponse
                    {
                        Success = false,
                        Message = "TemplateId is required"
                    };
                }
                
                // 使用统一的缓存目录
                var templateCacheDir = Environment.GetEnvironmentVariable("MUSE_TEMPLATE_CACHE_DIR") 
                    ?? _configuration["Paths:TemplateCache"] 
                    ?? "/opt/musetalk/template_cache";
                    
                var cacheDir = Path.Combine(templateCacheDir, request.TemplateId);
                Directory.CreateDirectory(cacheDir);

                // 通过HTTP API进行推理
                var videoPath = await _apiClient.UltraFastInferenceAsync(
                    request.TemplateId,
                    request.AudioPath,
                    outputPath);

                if (!string.IsNullOrEmpty(videoPath) && File.Exists(videoPath))
                {
                    // 如果videoPath和outputPath不同，确保文件在正确位置
                    if (videoPath != outputPath && File.Exists(videoPath))
                    {
                        File.Copy(videoPath, outputPath, true);
                    }
                    
                    return new DigitalHumanResponse
                    {
                        Success = true,
                        VideoPath = outputPath,
                        VideoUrl = $"/videos/{Path.GetFileName(outputPath)}",
                        Message = "Success"
                    };
                }

                return new DigitalHumanResponse
                {
                    Success = false,
                    Message = "MuseTalk API调用失败"
                };
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "GenerateVideoAsync failed");
                return new DigitalHumanResponse { Success = false, Message = ex.Message };
            }
        }

        public Task<List<DigitalHumanResponse>> GenerateBatchVideosAsync(List<DigitalHumanRequest> requests)
        {
            return Task.FromResult(new List<DigitalHumanResponse>());
        }

        public Task<string> QueueVideoGenerationAsync(DigitalHumanRequest request)
        {
            return Task.FromResult(string.Empty);
        }

        public Task<List<QueuedJob>> GetQueueStatusAsync()
        {
            return Task.FromResult(new List<QueuedJob>());
        }

        public Task<bool> CancelQueuedJobAsync(string jobId)
        {
            return Task.FromResult(true);
        }

        public Task<DigitalHumanResponse?> GetQueuedVideoResultAsync(string jobId)
        {
            return Task.FromResult<DigitalHumanResponse?>(null);
        }

        public Task<List<DigitalHumanTemplate>> GetAvailableTemplatesAsync()
        {
            return Task.FromResult(new List<DigitalHumanTemplate>());
        }

        public Task<DigitalHumanTemplate> CreateTemplateAsync(CreateTemplateRequest request)
        {
            throw new NotImplementedException();
        }

        public Task<bool> DeleteTemplateAsync(string templateId)
        {
            return Task.FromResult(true);
        }

        public Task<bool> ValidateTemplateAsync(string templateId)
        {
            return Task.FromResult(true);
        }

        public async Task<PreprocessingResult> PreprocessTemplateAsync(string templateId)
        {
            try
            {
                // 使用共享目录路径，Python容器可以访问
                var imagePath = $"/opt/musetalk/templates/{templateId}.jpg";
                var success = await _apiClient.PreprocessTemplateAsync(templateId, imagePath);
                return new PreprocessingResult
                {
                    Success = success,
                    TemplateId = templateId,
                    PreprocessingTime = 1000 // 默认1秒
                };
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "PreprocessTemplateAsync failed: {TemplateId}", templateId);
                return new PreprocessingResult { Success = false, TemplateId = templateId, PreprocessingTime = 0 };
            }
        }

        public Task<bool> WarmupTemplateAsync(string templateId)
        {
            return Task.FromResult(true);
        }

        public Task<string> GetOptimalSettingsAsync(string templateId, string quality)
        {
            return Task.FromResult(string.Empty);
        }

        public Task<bool> CacheVideoResultAsync(string cacheKey, DigitalHumanResponse response)
        {
            return Task.FromResult(true);
        }

        public Task<DigitalHumanResponse?> GetCachedVideoAsync(string cacheKey)
        {
            return Task.FromResult<DigitalHumanResponse?>(null);
        }

        public Task<bool> ClearVideoCache(string? templateId = null)
        {
            return Task.FromResult(true);
        }

        public Task<CacheStatistics> GetCacheStatisticsAsync()
        {
            return Task.FromResult(new CacheStatistics());
        }

        public Task<bool> IsServiceHealthyAsync()
        {
            return Task.FromResult(true);
        }

        public Task<ServiceMetrics> GetServiceMetricsAsync()
        {
            return Task.FromResult(new ServiceMetrics());
        }

        public Task<List<ProcessingJob>> GetActiveJobsAsync()
        {
            return Task.FromResult(new List<ProcessingJob>());
        }

        public Task<bool> ScaleWorkersAsync(int workerCount)
        {
            return Task.FromResult(true);
        }

        public Task<AudioOptimizationResult> OptimizeAudioForGenerationAsync(string audioPath)
        {
            return Task.FromResult(new AudioOptimizationResult { Success = true, OptimizedAudioPath = audioPath });
        }

        public Task<bool> ValidateAudioAsync(string audioPath)
        {
            return Task.FromResult(true);
        }

        public Task<string> StartStreamingGenerationAsync(StreamingGenerationRequest request)
        {
            return Task.FromResult(string.Empty);
        }

        public Task<StreamingGenerationChunk?> GetGenerationChunkAsync(string sessionId)
        {
            return Task.FromResult<StreamingGenerationChunk?>(null);
        }

        public Task<bool> EndStreamingGenerationAsync(string sessionId)
        {
            return Task.FromResult(true);
        }

        public async Task<DigitalHumanResponse> SimulateRealtimeInference(DigitalHumanRequest request)
        {
            // 使用HTTP API进行实时推理
            return await GenerateVideoAsync(request);
        }
    }
}

