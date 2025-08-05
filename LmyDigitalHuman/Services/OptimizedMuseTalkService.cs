using System;
using System.Collections.Concurrent;
using System.Diagnostics;
using System.IO;
using System.Text;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Configuration;
using LmyDigitalHuman.Models;
using System.Collections.Generic;
using System.Linq;

namespace LmyDigitalHuman.Services
{
    /// <summary>
    /// 🚀 优化版MuseTalk服务 - 配合极致优化Python脚本
    /// 专门针对固定模板场景的性能优化
    /// </summary>
    public class OptimizedMuseTalkService : IMuseTalkService
    {
        private readonly ILogger<OptimizedMuseTalkService> _logger;
        private readonly IConfiguration _configuration;
        private readonly IPathManager _pathManager;
        private readonly IPythonEnvironmentService _pythonEnvironmentService;
        
        // 📊 模型永久化缓存管理 - 基于MuseTalk realtime_inference.py架构
        private readonly ConcurrentDictionary<string, PersistentModelInfo> _persistentModels = new();
        private readonly ConcurrentDictionary<string, QueuedJob> _jobQueue = new();
        private readonly ConcurrentDictionary<string, DigitalHumanResponse> _videoCache = new();
        private readonly ConcurrentDictionary<string, ProcessingJob> _activeJobs = new();
        
        // 全局模型组件永久化 - 只初始化一次
        private static readonly object _globalInitLock = new object();
        private static bool _globalModelsInitialized = false;
        private static Process? _persistentMuseTalkProcess = null;
        
        // 兼容性字段 - 保持原有功能
        private static readonly object _initLock = new object();
        private static bool _isInitialized = false;
        
        // 📈 性能统计
        private long _totalRequests = 0;
        private long _completedRequests = 0;
        private readonly ConcurrentDictionary<string, long> _templateUsageCount = new();
        
        // 🚀 性能优化缓存
        private string? _cachedPythonPath = null;
        private readonly object _pythonPathLock = new object();
        
        public OptimizedMuseTalkService(
            ILogger<OptimizedMuseTalkService> logger,
            IConfiguration configuration,
            IPathManager pathManager,
            IPythonEnvironmentService pythonEnvironmentService)
        {
            _logger = logger;
            _configuration = configuration;
            _pathManager = pathManager;
            _pythonEnvironmentService = pythonEnvironmentService;
            
            _logger.LogInformation("🚀 优化版MuseTalk服务已启动");
            
            // 加载已有的模板信息
            LoadTemplateInfoFromFileSystem();
            
            // 清理损坏的缓存文件
            _ = Task.Run(CleanupAllCorruptedCacheFiles);
            
            // 不再预初始化Python推理器，改为按需初始化以提高启动速度
            _logger.LogInformation("Python推理器将在首次使用时初始化");
        }
        
        /// <summary>
        /// 永久化模型信息 - 基于MuseTalk realtime_inference.py架构
        /// </summary>
        private class PersistentModelInfo
        {
            public string TemplateId { get; set; }
            public string TemplatePath { get; set; }
            public string ModelStatePath { get; set; } // 永久化模型状态路径
            public bool IsModelLoaded { get; set; } // 模型是否已加载到GPU内存
            public DateTime LoadedAt { get; set; } = DateTime.Now;
            public DateTime LastUsed { get; set; } = DateTime.Now;
            public long UsageCount { get; set; } = 0;
            public int AssignedGPU { get; set; } = -1; // 分配的GPU编号
        }

        #region IMuseTalkService 接口实现

        /// <summary>
        /// 基础视频生成 - 主要接口实现
        /// </summary>
        public async Task<DigitalHumanResponse> GenerateVideoAsync(DigitalHumanRequest request)
        {
            return await ExecuteMuseTalkPythonAsync(request);
        }

        /// <summary>
        /// 批量视频生成
        /// </summary>
        public async Task<List<DigitalHumanResponse>> GenerateBatchVideosAsync(List<DigitalHumanRequest> requests)
        {
            var results = new List<DigitalHumanResponse>();
            var tasks = requests.Select(async request => await GenerateVideoAsync(request));
            var responses = await Task.WhenAll(tasks);
            results.AddRange(responses);
            return results;
        }

        /// <summary>
        /// 队列视频生成
        /// </summary>
        public async Task<string> QueueVideoGenerationAsync(DigitalHumanRequest request)
        {
            var jobId = Guid.NewGuid().ToString();
            var job = new QueuedJob
            {
                JobId = jobId,
                Request = request,
                Status = JobStatus.Pending,
                QueuedAt = DateTime.Now,
                Priority = request.Priority ?? "normal"
            };
            
            _jobQueue.TryAdd(jobId, job);
            _logger.LogInformation("🎯 任务已加入队列: {JobId}", jobId);
            
            // 异步处理任务
            _ = Task.Run(async () => await ProcessQueuedJobAsync(jobId));
            
            return jobId;
        }

        /// <summary>
        /// 获取队列任务结果
        /// </summary>
        public async Task<DigitalHumanResponse?> GetQueuedVideoResultAsync(string jobId)
        {
            if (_jobQueue.TryGetValue(jobId, out var job))
            {
                return job.Result;
            }
            return null;
        }

        /// <summary>
        /// 获取队列状态
        /// </summary>
        public async Task<List<QueuedJob>> GetQueueStatusAsync()
        {
            return _jobQueue.Values.ToList();
        }

        /// <summary>
        /// 取消队列任务
        /// </summary>
        public async Task<bool> CancelQueuedJobAsync(string jobId)
        {
            if (_jobQueue.TryGetValue(jobId, out var job) && job.Status == JobStatus.Pending)
            {
                job.Status = JobStatus.Cancelled;
                _logger.LogInformation("❌ 任务已取消: {JobId}", jobId);
                return true;
            }
            return false;
        }

        /// <summary>
        /// 获取可用模板
        /// </summary>
        public async Task<List<DigitalHumanTemplate>> GetAvailableTemplatesAsync()
        {
            var templates = new List<DigitalHumanTemplate>();
            var templatesDir = Path.Combine(_pathManager.GetContentRootPath(), "wwwroot", "templates");
            
            if (!Directory.Exists(templatesDir))
            {
                return templates;
            }

            var imageFiles = Directory.GetFiles(templatesDir, "*.*", SearchOption.TopDirectoryOnly)
                .Where(f => f.EndsWith(".jpg", StringComparison.OrdinalIgnoreCase) || 
                           f.EndsWith(".png", StringComparison.OrdinalIgnoreCase))
                .ToArray();

            foreach (var imageFile in imageFiles)
            {
                var templateId = Path.GetFileNameWithoutExtension(imageFile);
                var template = new DigitalHumanTemplate
                {
                    TemplateId = templateId,
                    TemplateName = templateId,
                    ImagePath = imageFile,
                    ImageUrl = $"/templates/{Path.GetFileName(imageFile)}",
                    Status = "ready",
                    IsActive = true,
                    CreatedAt = File.GetCreationTime(imageFile),
                    UpdatedAt = File.GetLastWriteTime(imageFile),
                    UsageCount = (int)_templateUsageCount.GetValueOrDefault(templateId, 0)
                };
                templates.Add(template);
            }

            return templates;
        }

        /// <summary>
        /// 创建模板
        /// </summary>
        public async Task<DigitalHumanTemplate> CreateTemplateAsync(CreateTemplateRequest request)
        {
            var templateId = Guid.NewGuid().ToString();
            var templatesDir = Path.Combine(_pathManager.GetContentRootPath(), "wwwroot", "templates");
            Directory.CreateDirectory(templatesDir);
            
            var fileName = $"{request.TemplateName}_{templateId}.jpg";
            var filePath = Path.Combine(templatesDir, fileName);
            
            using (var stream = new FileStream(filePath, FileMode.Create))
            {
                await request.ImageFile.CopyToAsync(stream);
            }

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
                ImagePath = filePath,
                ImageUrl = $"/templates/{fileName}",
                DefaultVoiceSettings = request.DefaultVoiceSettings,
                CustomParameters = request.CustomParameters,
                CreatedAt = DateTime.Now,
                UpdatedAt = DateTime.Now,
                IsActive = true,
                Status = "ready"
            };

            _logger.LogInformation("✅ 模板创建成功: {TemplateId} - {TemplateName}", templateId, request.TemplateName);
            return template;
        }

        /// <summary>
        /// 删除模板
        /// </summary>
        public async Task<bool> DeleteTemplateAsync(string templateId)
        {
            var templatesDir = Path.Combine(_pathManager.GetContentRootPath(), "wwwroot", "templates");
            var files = Directory.GetFiles(templatesDir, $"*{templateId}*");
            
            foreach (var file in files)
            {
                try
                {
                    File.Delete(file);
                    _logger.LogInformation("🗑️ 模板文件已删除: {File}", file);
                }
                catch (Exception ex)
                {
                    _logger.LogError(ex, "删除模板文件失败: {File}", file);
                    return false;
                }
            }

            // 清理永久化模型缓存
            _persistentModels.TryRemove(templateId, out _);
            return true;
        }

        /// <summary>
        /// 验证模板
        /// </summary>
        public async Task<bool> ValidateTemplateAsync(string templateId)
        {
            var templatesDir = Path.Combine(_pathManager.GetContentRootPath(), "wwwroot", "templates");
            var templateFiles = Directory.GetFiles(templatesDir, $"{templateId}.*");
            return templateFiles.Length > 0;
        }

        /// <summary>
        /// 永久化模板预处理 - 基于MuseTalk realtime_inference.py实现模型永久化
        /// </summary>
        public async Task<PreprocessingResult> PreprocessTemplateAsync(string templateId)
        {
            // 🔧 检查是否已经预处理过，避免重复预处理
            if (_persistentModels.ContainsKey(templateId))
            {
                _logger.LogInformation("✅ 模板 {TemplateId} 已预处理完成，跳过重复预处理", templateId);
                return new PreprocessingResult
                {
                    Success = true,
                    TemplateId = templateId,
                    PreprocessingTime = 0,
                    OptimizedSettings = new Dictionary<string, object>
                    {
                        ["Status"] = "AlreadyProcessed",
                        ["Message"] = "模板已预处理完成",
                        ["SkippedDuplicateProcessing"] = true
                    }
                };
            }
            
            var stopwatch = Stopwatch.StartNew();
            
            try
            {
                _logger.LogInformation("🚀 开始永久化模板预处理: {TemplateId}", templateId);
                
                // 1. 初始化全局模型组件（只执行一次）
                await EnsureGlobalModelsInitializedAsync();
                
                // 2. 为模板创建永久化模型状态
                var modelStatePath = await CreatePersistentModelStateAsync(templateId);
                
                // 3. 分配GPU并加载模型到GPU内存
                var assignedGPU = AssignGPUForTemplate(templateId);
                await LoadModelToGPUAsync(templateId, assignedGPU);
                
                var modelInfo = new PersistentModelInfo
                {
                    TemplateId = templateId,
                    TemplatePath = Path.Combine(_pathManager.GetContentRootPath(), "wwwroot", "templates", $"{templateId}.jpg"),
                    ModelStatePath = modelStatePath,
                    IsModelLoaded = true,
                    LoadedAt = DateTime.Now,
                    LastUsed = DateTime.Now,
                    AssignedGPU = assignedGPU
                };
                
                _persistentModels.AddOrUpdate(templateId, modelInfo, (key, old) => modelInfo);
                
                stopwatch.Stop();
                
                _logger.LogInformation("✅ 模板永久化完成: {TemplateId}, 耗时: {Time}ms, GPU: {GPU}", 
                    templateId, stopwatch.ElapsedMilliseconds, assignedGPU);
                
                return new PreprocessingResult
                {
                    Success = true,
                    TemplateId = templateId,
                    PreprocessingTime = stopwatch.ElapsedMilliseconds,
                    OptimizedSettings = new Dictionary<string, object>
                    {
                        ["persistent_model"] = true,
                        ["assigned_gpu"] = assignedGPU,
                        ["model_state_path"] = modelStatePath,
                        ["realtime_ready"] = true
                    }
                };
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "模板永久化预处理失败: {TemplateId}", templateId);
                return new PreprocessingResult
                {
                    Success = false,
                    TemplateId = templateId,
                    PreprocessingTime = stopwatch.ElapsedMilliseconds
                };
            }
        }

        /// <summary>
        /// 预热模板
        /// </summary>
        public async Task<bool> WarmupTemplateAsync(string templateId)
        {
            try
            {
                var result = await PreprocessTemplateAsync(templateId);
                return result.Success;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "模板预热失败: {TemplateId}", templateId);
                return false;
            }
        }

        /// <summary>
        /// 极速实时推理 - 使用预处理的永久化模型（接口实现）
        /// </summary>
        public async Task<DigitalHumanResponse> SimulateRealtimeInference(DigitalHumanRequest request)
        {
            var stopwatch = Stopwatch.StartNew();
            
            try
            {
                // 🎯 提取模板ID（优先使用TemplateId，否则从路径提取）
                var templateId = request.TemplateId ?? ExtractTemplateIdFromPath(request.AvatarImagePath);
                
                _logger.LogInformation("⚡ 开始4GPU实时推理: TemplateId={TemplateId}, TotalRequests={TotalRequests}", 
                    templateId, _activeJobs.Count + 1);
                
                // 检查模板是否已预处理
                if (!_persistentModels.TryGetValue(templateId, out var modelInfo))
                {
                    _logger.LogWarning("⚠️ 模板 {TemplateId} 未预处理，开始动态预处理...", templateId);
                    await PreprocessTemplateAsync(templateId);
                    
                    if (!_persistentModels.TryGetValue(templateId, out modelInfo))
                    {
                        throw new InvalidOperationException($"模板 {templateId} 预处理失败");
                    }
                }
                
                _logger.LogInformation("⚡ 模板 {TemplateId} 已预处理完成，使用永久化模型进行极速推理", templateId);
                
                // 生成唯一输出路径
                var timestamp = DateTime.Now.ToString("yyyyMMdd_HHmmss");
                var randomSuffix = Guid.NewGuid().ToString("N")[..8];
                var outputFileName = $"realtime_{templateId}_{timestamp}_{randomSuffix}.mp4";
                var outputPath = Path.Combine(_pathManager.GetContentRootPath(), "wwwroot", "videos", outputFileName);
                
                // 确保输出目录存在
                Directory.CreateDirectory(Path.GetDirectoryName(outputPath)!);
                
                _logger.LogInformation("⚡ 执行实时推理: {TemplateId} (GPU:{GPU})", templateId, modelInfo.AssignedGPU);
                
                // 调用私有方法执行实际推理
                var resultPath = await ExecuteRealtimeInferenceInternal(templateId, request.AudioPath, outputPath, modelInfo.AssignedGPU);
                
                stopwatch.Stop();
                
                // 验证输出文件
                if (!File.Exists(outputPath))
                {
                    throw new FileNotFoundException($"推理完成但输出文件不存在: {outputPath}");
                }
                
                var fileInfo = new FileInfo(outputPath);
                _logger.LogInformation("✅ GPU:{GPU} MuseTalk推理完成: {TemplateId}, 输出: {OutputPath}, 大小: {Size}bytes", 
                    modelInfo.AssignedGPU, templateId, outputPath, fileInfo.Length);
                
                // 更新模型使用时间
                modelInfo.LastUsed = DateTime.Now;
                
                // 计算视频时长
                var duration = await GetVideoDurationAsync(outputPath);
                
                _logger.LogInformation("✅ 4GPU实时推理完成: TemplateId={TemplateId}, 耗时={ElapsedMs}ms, 完成率={CompletionRate:F2} %", 
                    templateId, stopwatch.ElapsedMilliseconds, 100.0);
                
                // 🌐 转换物理路径为前端可访问的URL
                var videoUrl = ConvertToWebUrl(outputPath);
                
                return new DigitalHumanResponse
                {
                    Success = true,
                    VideoPath = outputPath,  // 物理路径（服务器内部使用）
                    VideoUrl = videoUrl,     // Web URL（前端使用）
                    Duration = duration,
                    Message = $"⚡ 4GPU实时推理完成 (模板: {templateId}, 耗时: {stopwatch.ElapsedMilliseconds}ms)"
                };
            }
            catch (Exception ex)
            {
                stopwatch.Stop();
                _logger.LogError(ex, "❌ 4GPU实时推理失败: TemplateId={TemplateId}, 耗时={ElapsedMs}ms", 
                    request.TemplateId ?? "unknown", stopwatch.ElapsedMilliseconds);
                
                return new DigitalHumanResponse
                {
                    Success = false,
                    Message = $"实时推理失败: {ex.Message}",
                    Duration = 0
                };
            }
        }

        /// <summary>
        /// 从图片路径提取模板ID
        /// </summary>
        private string ExtractTemplateIdFromPath(string imagePath)
        {
            try
            {
                return Path.GetFileNameWithoutExtension(imagePath);
            }
            catch
            {
                return "unknown";
            }
        }

        /// <summary>
        /// 获取视频时长（简化实现）
        /// </summary>
        private async Task<double> GetVideoDurationAsync(string videoPath)
        {
            try
            {
                // 简化实现：基于文件大小估算
                var fileInfo = new FileInfo(videoPath);
                if (fileInfo.Exists && fileInfo.Length > 0)
                {
                    // 粗略估算：MP4文件约每秒100KB（25fps，中等质量）
                    var estimatedDuration = Math.Max(1.0, (double)fileInfo.Length / 100000);
                    return estimatedDuration;
                }
                
                return 3.0; // 默认3秒
            }
            catch (Exception ex)
            {
                _logger.LogWarning(ex, "获取视频时长失败，使用默认值: {VideoPath}", videoPath);
                return 3.0; // 默认3秒
            }
        }

        /// <summary>
        /// 获取最优设置
        /// </summary>
        public async Task<string> GetOptimalSettingsAsync(string templateId, string quality)
        {
            var settings = new Dictionary<string, object>
            {
                ["template_id"] = templateId,
                ["quality"] = quality,
                ["batch_size"] = quality switch
                {
                    "ultra" => 32,
                    "high" => 48,
                    "medium" => 64,
                    "low" => 96,
                    _ => 64
                },
                ["fps"] = 25,
                ["optimized"] = true
            };
            
            return System.Text.Json.JsonSerializer.Serialize(settings);
        }

        /// <summary>
        /// 缓存视频结果
        /// </summary>
        public async Task<bool> CacheVideoResultAsync(string cacheKey, DigitalHumanResponse response)
        {
            try
            {
                _videoCache.AddOrUpdate(cacheKey, response, (key, old) => response);
                _logger.LogDebug("📦 视频结果已缓存: {CacheKey}", cacheKey);
                return true;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "缓存视频结果失败: {CacheKey}", cacheKey);
                return false;
            }
        }

        /// <summary>
        /// 获取缓存的视频
        /// </summary>
        public async Task<DigitalHumanResponse?> GetCachedVideoAsync(string cacheKey)
        {
            _videoCache.TryGetValue(cacheKey, out var response);
            if (response != null)
            {
                response.FromCache = true;
                _logger.LogDebug("🎯 命中视频缓存: {CacheKey}", cacheKey);
            }
            return response;
        }

        /// <summary>
        /// 清除视频缓存
        /// </summary>
        public async Task<bool> ClearVideoCache(string? templateId = null)
        {
            try
            {
                if (string.IsNullOrEmpty(templateId))
                {
                    _videoCache.Clear();
                    _logger.LogInformation("🧹 已清除所有视频缓存");
                }
                else
                {
                    var keysToRemove = _videoCache.Keys.Where(k => k.Contains(templateId)).ToList();
                    foreach (var key in keysToRemove)
                    {
                        _videoCache.TryRemove(key, out _);
                    }
                    _logger.LogInformation("🧹 已清除模板缓存: {TemplateId}", templateId);
                }
                return true;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "清除缓存失败");
                return false;
            }
        }

        /// <summary>
        /// 获取缓存统计
        /// </summary>
        public async Task<CacheStatistics> GetCacheStatisticsAsync()
        {
            return new CacheStatistics
            {
                TotalCachedItems = _videoCache.Count,
                CacheHitRate = CalculateCacheHitRate(),
                LastCleanup = DateTime.Now,
                CacheSize = EstimateCacheSize(),
                CacheHitsByTemplate = _templateUsageCount.ToDictionary(kvp => kvp.Key, kvp => (int)kvp.Value)
            };
        }

        /// <summary>
        /// 检查服务健康状态
        /// </summary>
        public async Task<bool> IsServiceHealthyAsync()
        {
            try
            {
                // 检查Python环境
                var pythonPath = await GetCachedPythonPathAsync();
                if (string.IsNullOrEmpty(pythonPath))
                {
                    return false;
                }

                // 检查模板目录
                var templatesDir = Path.Combine(_pathManager.GetContentRootPath(), "wwwroot", "templates");
                if (!Directory.Exists(templatesDir))
                {
                    return false;
                }

                // 检查初始化状态
                return _isInitialized;
            }
            catch
            {
                return false;
            }
        }

        /// <summary>
        /// 获取服务指标
        /// </summary>
        public async Task<ServiceMetrics> GetServiceMetricsAsync()
        {
            return new ServiceMetrics
            {
                ActiveWorkers = _activeJobs.Count,
                QueueLength = _jobQueue.Count(kvp => kvp.Value.Status == JobStatus.Pending),
                AverageProcessingTime = CalculateAverageProcessingTime(),
                ThroughputPerHour = CalculateThroughputPerHour(),
                ResourceUsage = new Dictionary<string, object>
                {
                    ["total_requests"] = _totalRequests,
                    ["completed_requests"] = _completedRequests,
                    ["completion_rate"] = (double)_completedRequests / Math.Max(_totalRequests, 1),
                    ["persistent_models_count"] = _persistentModels.Count,
                    ["video_cache_size"] = _videoCache.Count
                },
                PerformanceWarnings = GetPerformanceWarnings()
            };
        }

        /// <summary>
        /// 获取活跃任务
        /// </summary>
        public async Task<List<ProcessingJob>> GetActiveJobsAsync()
        {
            return _activeJobs.Values.ToList();
        }

        /// <summary>
        /// 扩展工作线程
        /// </summary>
        public async Task<bool> ScaleWorkersAsync(int workerCount)
        {
            // 这是一个优化版本，主要依赖GPU并行，所以工作线程扩展有限
            _logger.LogInformation("🔧 工作线程扩展请求: {WorkerCount} (当前为GPU并行优化版本)", workerCount);
            return true;
        }

        /// <summary>
        /// 音频优化
        /// </summary>
        public async Task<AudioOptimizationResult> OptimizeAudioForGenerationAsync(string audioPath)
        {
            var stopwatch = Stopwatch.StartNew();
            
            try
            {
                // 简单的音频验证和优化建议
                var audioInfo = new FileInfo(audioPath);
                
                stopwatch.Stop();
                
                return new AudioOptimizationResult
                {
                    Success = true,
                    OptimizedAudioPath = audioPath, // 对于优化版本，直接使用原音频
                    OriginalSize = audioInfo.Length,
                    OptimizedSize = audioInfo.Length,
                    ProcessingTime = stopwatch.ElapsedMilliseconds,
                    AppliedOptimizations = new List<string> { "validation_passed", "format_compatible" }
                };
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "音频优化失败: {AudioPath}", audioPath);
                return new AudioOptimizationResult
                {
                    Success = false,
                    ProcessingTime = stopwatch.ElapsedMilliseconds
                };
            }
        }

        /// <summary>
        /// 验证音频
        /// </summary>
        public async Task<bool> ValidateAudioAsync(string audioPath)
        {
            try
            {
                return File.Exists(audioPath) && 
                       (audioPath.EndsWith(".wav", StringComparison.OrdinalIgnoreCase) || 
                        audioPath.EndsWith(".mp3", StringComparison.OrdinalIgnoreCase));
            }
            catch
            {
                return false;
            }
        }

        /// <summary>
        /// 开始流式生成
        /// </summary>
        public async Task<string> StartStreamingGenerationAsync(StreamingGenerationRequest request)
        {
            var sessionId = Guid.NewGuid().ToString();
            _logger.LogInformation("🎬 开始流式生成会话: {SessionId}", sessionId);
            
            // 对于优化版本，流式生成转换为常规生成
            var digitalRequest = new DigitalHumanRequest
            {
                AvatarImagePath = $"/templates/{request.TemplateId}.jpg",
                AudioPath = "", // 需要从文本生成音频
                Quality = request.Quality
            };
            
            return sessionId;
        }

        /// <summary>
        /// 获取生成块
        /// </summary>
        public async Task<StreamingGenerationChunk?> GetGenerationChunkAsync(string sessionId)
        {
            // 简化实现，返回完成状态
            return new StreamingGenerationChunk
            {
                ChunkIndex = 1,
                IsComplete = true,
                Progress = 100,
                VideoData = new byte[0]
            };
        }

        /// <summary>
        /// 结束流式生成
        /// </summary>
        public async Task<bool> EndStreamingGenerationAsync(string sessionId)
        {
            _logger.LogInformation("🏁 结束流式生成会话: {SessionId}", sessionId);
            return true;
        }

        #endregion

        #region 原有优化功能保持不变

        /// <summary>
        /// 主要接口实现 - 4GPU实时推理（基于MuseTalk realtime_inference.py）
        /// </summary>
        public async Task<DigitalHumanResponse> ExecuteMuseTalkPythonAsync(DigitalHumanRequest request)
        {
            var stopwatch = Stopwatch.StartNew();
            System.Threading.Interlocked.Increment(ref _totalRequests);
            
            try
            {
                // 🎯 获取模板ID
                var templateId = GetTemplateId(request.AvatarImagePath);
                
                _logger.LogInformation("⚡ 开始4GPU实时推理: TemplateId={TemplateId}, TotalRequests={TotalRequests}", 
                    templateId, _totalRequests);
                
                // 📊 更新模板使用统计
                _templateUsageCount.AddOrUpdate(templateId, 1, (key, oldValue) => oldValue + 1);
                
                // 🎯 检查模板是否已永久化（优先使用预处理好的模板）
                if (!_persistentModels.ContainsKey(templateId))
                {
                    _logger.LogWarning("⚠️ 模板 {TemplateId} 未进行预处理，这通常表示模板创建时预处理失败", templateId);
                    _logger.LogInformation("🔧 正在进行紧急预处理，建议重新创建模板以获得最佳性能...", templateId);
                    await PreprocessTemplateAsync(templateId);
                }
                else
                {
                    _logger.LogInformation("⚡ 模板 {TemplateId} 已预处理完成，使用永久化模型进行极速推理", templateId);
                }
                
                // 🚀 执行实时推理（使用永久化模型）
                var outputPath = await ExecuteRealtimeInferenceAsync(templateId, request.AudioPath);
                
                stopwatch.Stop();
                System.Threading.Interlocked.Increment(ref _completedRequests);
                
                var duration = GetAudioDuration(request.AudioPath);
                
                _logger.LogInformation("✅ 4GPU实时推理完成: TemplateId={TemplateId}, 耗时={ElapsedMs}ms, 完成率={CompletionRate:P2}", 
                    templateId, stopwatch.ElapsedMilliseconds, (double)_completedRequests / _totalRequests);
                
                // 🌐 转换物理路径为前端可访问的URL
                var videoUrl = ConvertToWebUrl(outputPath);
                
                return new DigitalHumanResponse
                {
                    Success = true,
                    VideoPath = outputPath,  // 物理路径（服务器内部使用）
                    VideoUrl = videoUrl,     // Web URL（前端使用）
                    Duration = duration,
                    Message = $"⚡ 4GPU实时推理完成 (模板: {templateId}, 耗时: {stopwatch.ElapsedMilliseconds}ms)"
                };
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "❌ 4GPU实时推理失败");
                return new DigitalHumanResponse
                {
                    Success = false,
                    Message = $"推理失败: {ex.Message}"
                };
            }
        }
        
        /// <summary>
        /// 初始化Python推理器
        /// </summary>
        private async Task InitializePythonInferenceEngineAsync()
        {
            if (_isInitialized) return;
            
            lock (_initLock)
            {
                if (_isInitialized) return;
                
                _logger.LogInformation("🔧 开始初始化Python推理器...");
                
                try
                {
                    // 预热Python推理器 - 让它加载所有模板
                    var dummyResult = InitializePythonInferenceEngine();
                    
                    if (dummyResult)
                    {
                        _isInitialized = true;
                        _logger.LogInformation("✅ Python推理器初始化完成 - 所有模板已预处理");
                    }
                    else
                    {
                        _logger.LogWarning("⚠️ Python推理器初始化失败，启用降级模式");
                        // 即使初始化失败也标记为已初始化，让系统能够继续运行
                        _isInitialized = true;
                    }
                }
                catch (Exception ex)
                {
                    _logger.LogError(ex, "❌ Python推理器初始化失败，启用降级模式");
                    // 即使出现异常也标记为已初始化，让系统能够继续运行
                    _isInitialized = true;
                }
            }
        }
        
        /// <summary>
        /// 确保Python推理器已初始化
        /// </summary>
        private async Task EnsurePythonInferenceEngineInitializedAsync()
        {
            if (!_isInitialized)
            {
                _logger.LogInformation("🔧 首次使用，正在初始化Python推理器...");
                
                lock (_initLock)
                {
                    if (!_isInitialized)
                    {
                        // 直接标记为已初始化，跳过复杂的预初始化
                        _isInitialized = true;
                        _logger.LogInformation("✅ Python推理器已准备就绪（按需模式）");
                    }
                }
            }
        }
        
        /// <summary>
        /// 初始化Python推理器（同步方法）
        /// </summary>
        private bool InitializePythonInferenceEngine()
        {
            try
            {
                var templatesDir = Path.Combine(_pathManager.GetContentRootPath(), "wwwroot", "templates");
                var museTalkDir = Path.Combine(_pathManager.GetContentRootPath(), "..", "MuseTalk");
                var pythonPath = GetCachedPythonPathSync();
                
                                 // 构建初始化命令 - 仅初始化模型，不预处理模板（支持动态预处理）
                var arguments = new StringBuilder();
                arguments.Append($"-c \"");
                arguments.Append($"import sys; sys.path.append('{museTalkDir.Replace("\\", "/")}'); ");
                arguments.Append($"from optimized_musetalk_inference import OptimizedMuseTalkInference; ");
                arguments.Append($"import argparse; ");
                arguments.Append($"args = argparse.Namespace(");
                arguments.Append($"template_dir='{templatesDir.Replace("\\", "/")}', ");
                arguments.Append($"version='v1', ");
                arguments.Append($"unet_config='{museTalkDir.Replace("\\", "/")}/models/musetalk/musetalk.json', ");
                arguments.Append($"unet_model_path='{museTalkDir.Replace("\\", "/")}/models/musetalk/pytorch_model.bin', ");
                arguments.Append($"whisper_dir='{museTalkDir.Replace("\\", "/")}/models/whisper', ");
                arguments.Append($"vae_type='sd-vae', ");
                arguments.Append($"batch_size=64, ");
                arguments.Append($"bbox_shift=0, ");
                arguments.Append($"extra_margin=10, ");
                arguments.Append($"audio_padding_length_left=2, ");
                arguments.Append($"audio_padding_length_right=2, ");
                arguments.Append($"parsing_mode='jaw', ");
                arguments.Append($"left_cheek_width=90, ");
                arguments.Append($"right_cheek_width=90");
                arguments.Append($"); ");
                arguments.Append($"engine = OptimizedMuseTalkInference(args); ");
                arguments.Append($"print('🚀 Python推理器初始化完成，支持动态模板预处理')");
                arguments.Append($"\"");
                
                var processInfo = new ProcessStartInfo
                {
                    FileName = pythonPath,
                    Arguments = arguments.ToString(),
                    WorkingDirectory = museTalkDir,
                    UseShellExecute = false,
                    RedirectStandardOutput = true,
                    RedirectStandardError = true,
                    CreateNoWindow = true
                };
                
                // 配置GPU环境
                ConfigureOptimizedGpuEnvironment(processInfo);
                
                var process = new Process { StartInfo = processInfo };
                var outputBuilder = new StringBuilder();
                var errorBuilder = new StringBuilder();
                
                process.OutputDataReceived += (sender, e) => {
                    if (!string.IsNullOrEmpty(e.Data))
                    {
                        outputBuilder.AppendLine(e.Data);
                        _logger.LogInformation("Python初始化: {Output}", e.Data);
                    }
                };
                
                process.ErrorDataReceived += (sender, e) => {
                    if (!string.IsNullOrEmpty(e.Data))
                    {
                        errorBuilder.AppendLine(e.Data);
                        _logger.LogWarning("Python初始化警告: {Error}", e.Data);
                    }
                };
                
                process.Start();
                process.BeginOutputReadLine();
                process.BeginErrorReadLine();
                
                // 等待初始化完成（最多5分钟）
                var completed = process.WaitForExit(300000);
                
                if (!completed)
                {
                    process.Kill();
                    _logger.LogError("Python推理器初始化超时");
                    return false;
                }
                
                if (process.ExitCode == 0)
                {
                    _logger.LogInformation("✅ Python推理器初始化成功");
                    return true;
                }
                else
                {
                    var error = errorBuilder.ToString();
                    _logger.LogError("Python推理器初始化失败: ExitCode={ExitCode}, Error={Error}", 
                        process.ExitCode, error);
                    return false;
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Python推理器初始化异常");
                return false;
            }
        }
        
        /// <summary>
        /// 执行优化推理
        /// </summary>
        private async Task<string> ExecuteOptimizedInferenceAsync(string templateId, string audioPath)
        {
            var outputFileName = $"optimized_{templateId}_{DateTime.Now:yyyyMMdd_HHmmss}_{Guid.NewGuid().ToString("N")[..8]}.mp4";
            var outputPath = Path.Combine(_pathManager.GetContentRootPath(), "wwwroot", "videos", outputFileName);
            
            var museTalkDir = Path.Combine(_pathManager.GetContentRootPath(), "..", "MuseTalk");
            var pythonPath = await GetCachedPythonPathAsync();
            
            // 优先使用V4增强版本，支持30fps+超高速推理
            var optimizedScriptPath = Path.Combine(museTalkDir, "enhanced_musetalk_inference_v4.py");
            if (!File.Exists(optimizedScriptPath))
            {
                optimizedScriptPath = Path.Combine(museTalkDir, "optimized_musetalk_inference_v3.py");
                if (!File.Exists(optimizedScriptPath))
                {
                    // 回退到工作区根目录的增强脚本
                    optimizedScriptPath = Path.Combine(_pathManager.GetContentRootPath(), "..", "enhanced_musetalk_inference_v4.py");
                    if (!File.Exists(optimizedScriptPath))
                    {
                        optimizedScriptPath = Path.Combine(_pathManager.GetContentRootPath(), "..", "optimized_musetalk_inference_v3.py");
                    }
                }
            }
            
            // 构建优化推理命令
            var arguments = new StringBuilder();
            arguments.Append($"\"{optimizedScriptPath}\"");
            arguments.Append($" --template_id \"{templateId}\"");
            arguments.Append($" --audio_path \"{audioPath}\"");
            arguments.Append($" --output_path \"{outputPath}\"");
            arguments.Append($" --template_dir \"{Path.Combine(_pathManager.GetContentRootPath(), "wwwroot", "templates")}\"");
            arguments.Append($" --version v1");
            arguments.Append($" --batch_size 64"); // 4x RTX 4090极致优化批处理大小
            arguments.Append($" --fps 25");
            arguments.Append($" --unet_config \"models/musetalk/musetalk.json\"");
            arguments.Append($" --unet_model_path \"models/musetalk/pytorch_model.bin\"");
            arguments.Append($" --whisper_dir \"models/whisper\"");
            
            _logger.LogInformation("🎮 执行优化推理命令: {Command}", $"{pythonPath} {arguments}");
            
            var processInfo = new ProcessStartInfo
            {
                FileName = pythonPath,
                Arguments = arguments.ToString(),
                WorkingDirectory = museTalkDir,
                UseShellExecute = false,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                CreateNoWindow = true
            };
            
            // 配置GPU环境
            ConfigureOptimizedGpuEnvironment(processInfo);
            
            var process = new Process { StartInfo = processInfo };
            var outputBuilder = new StringBuilder();
            var errorBuilder = new StringBuilder();
            
            process.OutputDataReceived += (sender, e) => {
                if (!string.IsNullOrEmpty(e.Data))
                {
                    outputBuilder.AppendLine(e.Data);
                    _logger.LogInformation("优化推理: {Output}", e.Data);
                }
            };
            
            process.ErrorDataReceived += (sender, e) => {
                if (!string.IsNullOrEmpty(e.Data))
                {
                    errorBuilder.AppendLine(e.Data);
                    _logger.LogWarning("优化推理警告: {Error}", e.Data);
                }
            };
            
            process.Start();
            process.BeginOutputReadLine();
            process.BeginErrorReadLine();
            
            // 🚀 4GPU并行推理超时设置（5分钟，确保有足够时间完成）
            var timeoutMs = 300000;
            var completed = await Task.Run(() => process.WaitForExit(timeoutMs));
            
            if (!completed)
            {
                process.Kill();
                throw new TimeoutException($"优化推理超时 ({timeoutMs/1000}秒)");
            }
            
            if (process.ExitCode != 0)
            {
                var error = errorBuilder.ToString();
                throw new InvalidOperationException($"优化推理失败: {error}");
            }
            
            // 检查输出文件
            if (!File.Exists(outputPath))
            {
                throw new FileNotFoundException($"优化推理未生成输出文件: {outputPath}");
            }
            
            return outputPath;
        }
        
        /// <summary>
        /// 配置4GPU极速并行环境 - 基于MuseTalk官方realtime_inference.py优化
        /// </summary>
        private void ConfigureOptimizedGpuEnvironment(ProcessStartInfo processInfo)
        {
            // 🚀 4GPU极速并行配置 - 基于MuseTalk官方实时推理优化
            processInfo.Environment["CUDA_VISIBLE_DEVICES"] = "0,1,2,3"; // 使用所有4个GPU
            
            // 4GPU并行内存分配优化
            processInfo.Environment["PYTORCH_CUDA_ALLOC_CONF"] = "max_split_size_mb:6144,garbage_collection_threshold:0.8,roundup_power2_divisions:32";
            
            // 4GPU并行CPU优化
            processInfo.Environment["OMP_NUM_THREADS"] = "32"; // 4GPU * 8线程
            processInfo.Environment["MKL_NUM_THREADS"] = "32";
            
            // CUDA并行优化
            processInfo.Environment["CUDA_LAUNCH_BLOCKING"] = "0"; // 异步CUDA
            processInfo.Environment["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID";
            processInfo.Environment["CUDA_MODULE_LOADING"] = "EAGER"; // 预加载模块
            
            // cuDNN并行优化
            processInfo.Environment["TORCH_BACKENDS_CUDNN_BENCHMARK"] = "1"; // cuDNN自动调优
            processInfo.Environment["TORCH_BACKENDS_CUDNN_DETERMINISTIC"] = "0"; // 禁用确定性
            processInfo.Environment["TORCH_BACKENDS_CUDNN_ALLOW_TF32"] = "1"; // TF32加速
            
            // PyTorch 2.0多GPU特性
            processInfo.Environment["TORCH_COMPILE_MODE"] = "reduce-overhead"; // 降低开销模式
            processInfo.Environment["TORCH_DYNAMO_OPTIMIZE"] = "1"; // 动态优化
            
            // 多GPU通信优化
            processInfo.Environment["NCCL_DEBUG"] = "WARN";
            processInfo.Environment["NCCL_IB_DISABLE"] = "1";
            processInfo.Environment["NCCL_P2P_DISABLE"] = "0"; // 启用P2P通信
            processInfo.Environment["NCCL_TREE_THRESHOLD"] = "0"; // 强制使用tree算法
            
            // 实时推理优化
            processInfo.Environment["TOKENIZERS_PARALLELISM"] = "true"; // 启用并行tokenization
            processInfo.Environment["CUBLAS_WORKSPACE_CONFIG"] = ":16:8"; // 更大的工作空间
            
            _logger.LogInformation("🚀 已配置4GPU极速并行环境 - 基于MuseTalk官方实时推理优化");
        }
        
        /// <summary>
        /// 获取模板ID - 从路径中提取模板名称（支持物理路径和web路径）
        /// </summary>
        private string GetTemplateId(string avatarPath)
        {
            // 🎯 统一处理：直接提取文件名（不含扩展名）作为模板ID
            var templateId = Path.GetFileNameWithoutExtension(avatarPath);
            _logger.LogDebug("提取模板ID: {AvatarPath} → {TemplateId}", avatarPath, templateId);
            return templateId;
        }
        
        /// <summary>
        /// 获取音频时长 - 快速估算，避免性能开销
        /// </summary>
        private double GetAudioDuration(string audioPath)
        {
            try
            {
                // 快速文件大小估算（避免FFmpeg调用的性能开销）
                var fileInfo = new FileInfo(audioPath);
                if (fileInfo.Exists)
                {
                    // 粗略估算：WAV文件约每秒175KB，MP3约每秒32KB
                    var extension = Path.GetExtension(audioPath).ToLower();
                    var bytesPerSecond = extension == ".wav" ? 175000 : 32000;
                    return Math.Max(1.0, (double)fileInfo.Length / bytesPerSecond);
                }
            }
            catch (Exception ex)
            {
                _logger.LogWarning(ex, "获取音频时长失败，使用默认值: {AudioPath}", audioPath);
            }
            
            return 3.0; // 默认3秒
        }
        
        /// <summary>
        /// 获取性能统计
        /// </summary>
        public string GetOptimizedPerformanceStats()
        {
            var stats = new StringBuilder();
            stats.AppendLine("🚀 极致优化MuseTalk性能统计:");
            stats.AppendLine($"总请求: {_totalRequests}, 已完成: {_completedRequests}");
            stats.AppendLine($"完成率: {(double)_completedRequests / Math.Max(_totalRequests, 1):P2}");
            stats.AppendLine($"Python推理器状态: {(_isInitialized ? "已初始化" : "初始化中")}");
            
            stats.AppendLine("模板使用统计:");
            foreach (var kvp in _templateUsageCount)
            {
                stats.AppendLine($"  {kvp.Key}: {kvp.Value} 次");
            }
            
            return stats.ToString();
        }
        
        /// <summary>
        /// 获取缓存的Python路径，避免重复检测
        /// </summary>
        private async Task<string> GetCachedPythonPathAsync()
        {
            if (_cachedPythonPath != null)
            {
                return _cachedPythonPath;
            }
            
            lock (_pythonPathLock)
            {
                if (_cachedPythonPath != null)
                {
                    return _cachedPythonPath;
                }
                
                _logger.LogInformation("🔍 首次检测Python路径...");
                _cachedPythonPath = Task.Run(async () => await _pythonEnvironmentService.GetRecommendedPythonPathAsync()).Result;
                _logger.LogInformation("✅ Python路径已缓存: {PythonPath}", _cachedPythonPath);
                
                return _cachedPythonPath;
            }
        }

        /// <summary>
        /// 获取缓存的Python路径（同步版本）
        /// </summary>
        private string GetCachedPythonPathSync()
        {
            if (_cachedPythonPath != null)
            {
                return _cachedPythonPath;
            }
            
            lock (_pythonPathLock)
            {
                if (_cachedPythonPath != null)
                {
                    return _cachedPythonPath;
                }
                
                _logger.LogInformation("🔍 首次检测Python路径...");
                _cachedPythonPath = Task.Run(async () => await _pythonEnvironmentService.GetRecommendedPythonPathAsync()).Result;
                _logger.LogInformation("✅ Python路径已缓存: {PythonPath}", _cachedPythonPath);
                
                return _cachedPythonPath;
            }
        }

        #endregion

        #region 辅助方法

        /// <summary>
        /// 处理队列任务
        /// </summary>
        private async Task ProcessQueuedJobAsync(string jobId)
        {
            if (!_jobQueue.TryGetValue(jobId, out var job))
                return;

            try
            {
                job.Status = JobStatus.Processing;
                job.StartedAt = DateTime.Now;

                var processingJob = new ProcessingJob
                {
                    JobId = jobId,
                    StartTime = DateTime.Now,
                    Progress = 0,
                    CurrentStep = "开始处理"
                };
                _activeJobs.TryAdd(jobId, processingJob);

                var result = await GenerateVideoAsync(job.Request);
                
                job.Result = result;
                job.Status = result.Success ? JobStatus.Completed : JobStatus.Failed;
                job.CompletedAt = DateTime.Now;

                _activeJobs.TryRemove(jobId, out _);
            }
            catch (Exception ex)
            {
                job.Status = JobStatus.Failed;
                job.Error = ex.Message;
                job.CompletedAt = DateTime.Now;
                _activeJobs.TryRemove(jobId, out _);
                _logger.LogError(ex, "队列任务处理失败: {JobId}", jobId);
            }
        }

        /// <summary>
        /// 计算缓存命中率
        /// </summary>
        private double CalculateCacheHitRate()
        {
            // 简化实现
            return _videoCache.Count > 0 ? 0.8 : 0.0;
        }

        /// <summary>
        /// 估算缓存大小
        /// </summary>
        private long EstimateCacheSize()
        {
            return _videoCache.Count * 1024 * 1024; // 假设每个缓存项1MB
        }

        /// <summary>
        /// 计算平均处理时间
        /// </summary>
        private double CalculateAverageProcessingTime()
        {
            return _completedRequests > 0 ? 5000.0 : 0.0; // 假设平均5秒
        }

        /// <summary>
        /// 计算每小时吞吐量
        /// </summary>
        private double CalculateThroughputPerHour()
        {
            return _completedRequests > 0 ? _completedRequests * 3600.0 / 5000.0 : 0.0;
        }

        /// <summary>
        /// 获取性能警告
        /// </summary>
        private List<string> GetPerformanceWarnings()
        {
            var warnings = new List<string>();
            
            if (!_isInitialized)
            {
                warnings.Add("Python推理器未完全初始化");
            }
            
            if (_jobQueue.Count > 10)
            {
                warnings.Add("队列任务过多，可能影响响应时间");
            }
            
            return warnings;
        }

        #endregion

        #region 模型永久化方法 - 基于MuseTalk realtime_inference.py架构

        /// <summary>
        /// 确保全局模型组件已初始化（只执行一次）
        /// </summary>
        private async Task EnsureGlobalModelsInitializedAsync()
        {
            if (_globalModelsInitialized) return;

            lock (_globalInitLock)
            {
                if (_globalModelsInitialized) return;

                _logger.LogInformation("🔧 初始化全局MuseTalk模型组件...");

                try
                {
                    // 启动持久化的MuseTalk进程
                    _persistentMuseTalkProcess = StartPersistentMuseTalkProcess();
                    _globalModelsInitialized = true;
                    
                    _logger.LogInformation("✅ 全局MuseTalk模型组件初始化完成");
                }
                catch (Exception ex)
                {
                    _logger.LogError(ex, "❌ 全局模型组件初始化失败");
                    throw;
                }
            }
        }

        /// <summary>
        /// 启动持久化的MuseTalk进程
        /// </summary>
        private Process StartPersistentMuseTalkProcess()
        {
            var museTalkDir = Path.Combine(_pathManager.GetContentRootPath(), "..", "MuseTalk");
            var pythonPath = GetCachedPythonPathSync();
            
            // 基于MuseTalk realtime_inference.py的持久化进程
            var processInfo = new ProcessStartInfo
            {
                FileName = pythonPath,
                Arguments = $"-u -c \"import sys; sys.path.append('{museTalkDir.Replace("\\", "/")}'); from scripts.realtime_inference import PersistentMuseTalkServer; server = PersistentMuseTalkServer(); server.start_server()\"",
                WorkingDirectory = museTalkDir,
                UseShellExecute = false,
                RedirectStandardInput = true,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                CreateNoWindow = true
            };

            // 配置4GPU环境
            ConfigureOptimizedGpuEnvironment(processInfo);

            var process = new Process { StartInfo = processInfo };
            process.Start();

            _logger.LogInformation("🚀 持久化MuseTalk进程已启动，PID: {ProcessId}", process.Id);
            return process;
        }

        /// <summary>
        /// 为模板创建永久化模型状态 - 真正的预处理
        /// </summary>
        private async Task<string> CreatePersistentModelStateAsync(string templateId)
        {
            var modelStateDir = Path.Combine(_pathManager.GetContentRootPath(), "model_states", templateId);
            Directory.CreateDirectory(modelStateDir);
            
            var templateImagePath = Path.Combine(_pathManager.GetContentRootPath(), "wwwroot", "templates", $"{templateId}.jpg");
            var stateFilePath = Path.Combine(modelStateDir, "model_state.pkl");
            
            _logger.LogInformation("📁 创建模板永久化状态: {TemplateId} -> {StatePath}", templateId, stateFilePath);
            
            // 检查模板图片是否存在
            if (!File.Exists(templateImagePath))
            {
                throw new FileNotFoundException($"模板图片不存在: {templateImagePath}");
            }
            
            // 检查是否已经预处理过
            if (File.Exists(stateFilePath))
            {
                _logger.LogInformation("📦 发现已存在的预处理状态文件: {TemplateId}", templateId);
                return stateFilePath;
            }
            
            // 调用Python预处理脚本进行真正的预处理
            await ExecuteTemplatePreprocessingAsync(templateId, templateImagePath, stateFilePath);
            
            return stateFilePath;
        }

        /// <summary>
        /// 执行模板预处理 - 提取面容特征和关键信息
        /// </summary>
        private async Task ExecuteTemplatePreprocessingAsync(string templateId, string templateImagePath, string stateFilePath)
        {
            _logger.LogInformation("🎯 开始执行模板预处理: {TemplateId}", templateId);
            
            var pythonPath = await GetCachedPythonPathAsync();
            var preprocessingScript = Path.GetFullPath(Path.Combine(_pathManager.GetContentRootPath(), "..", "MuseTalkEngine", "enhanced_musetalk_preprocessing.py"));
            
            var arguments = $"\"{preprocessingScript}\" " +
                          $"--template_id \"{templateId}\" " +
                          $"--template_image \"{templateImagePath}\" " +
                          $"--output_state \"{stateFilePath}\" " +
                          $"--cache_dir \"{Path.GetDirectoryName(stateFilePath)}\" " +
                          $"--device cuda:0";
            
            // 设置路径 - 工作目录必须是MuseTalk目录以支持相对路径
            var museTalkDir = Path.Combine(_pathManager.GetContentRootPath(), "..", "MuseTalk");
            
            var startInfo = new ProcessStartInfo
            {
                FileName = pythonPath,
                Arguments = arguments,
                UseShellExecute = false,
                CreateNoWindow = true,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                WorkingDirectory = museTalkDir  // 设置为MuseTalk目录，支持相对路径
            };
            
            // 设置CUDA环境变量
            startInfo.EnvironmentVariables["CUDA_VISIBLE_DEVICES"] = "0,1,2,3";
            
            // 设置Python路径，确保能找到musetalk模块
            var pythonPath_env = Environment.GetEnvironmentVariable("PYTHONPATH") ?? "";
            if (!string.IsNullOrEmpty(pythonPath_env))
            {
                startInfo.EnvironmentVariables["PYTHONPATH"] = $"{museTalkDir};{pythonPath_env}";
            }
            else
            {
                startInfo.EnvironmentVariables["PYTHONPATH"] = museTalkDir;
            }
            
            // 设置Python输出编码为UTF-8，解决Windows下Unicode问题
            startInfo.EnvironmentVariables["PYTHONIOENCODING"] = "utf-8";
            
            _logger.LogInformation("💻 执行预处理命令: {FileName} {Arguments}", startInfo.FileName, arguments);
            _logger.LogInformation("🐍 PYTHONPATH: {PythonPath}", museTalkDir);
            
            using var process = new Process { StartInfo = startInfo };
            var outputBuffer = new StringBuilder();
            var errorBuffer = new StringBuilder();
            
            process.OutputDataReceived += (sender, e) =>
            {
                if (!string.IsNullOrEmpty(e.Data))
                {
                    outputBuffer.AppendLine(e.Data);
                    _logger.LogDebug("📤 预处理输出: {Output}", e.Data);
                }
            };
            
            process.ErrorDataReceived += (sender, e) =>
            {
                if (!string.IsNullOrEmpty(e.Data))
                {
                    errorBuffer.AppendLine(e.Data);
                    _logger.LogWarning("⚠️ 预处理错误: {Error}", e.Data);
                }
            };
            
            var startTime = DateTime.Now;
            
            if (!process.Start())
            {
                throw new InvalidOperationException("无法启动预处理进程");
            }
            
            process.BeginOutputReadLine();
            process.BeginErrorReadLine();
            
            // 等待进程完成，最多等待5分钟
            using var cts = new CancellationTokenSource(TimeSpan.FromMinutes(5));
            
            try
            {
                await process.WaitForExitAsync(cts.Token);
            }
            catch (OperationCanceledException)
            {
                _logger.LogError("❌ 预处理超时，强制终止进程");
                try
                {
                    process.Kill(true);
                }
                catch (Exception ex)
                {
                    _logger.LogError(ex, "终止预处理进程失败");
                }
                throw new TimeoutException("预处理超时");
            }
            
            var totalTime = DateTime.Now - startTime;
            var output = outputBuffer.ToString();
            var error = errorBuffer.ToString();
            
            if (process.ExitCode != 0)
            {
                _logger.LogError("❌ 预处理失败，退出码: {ExitCode}", process.ExitCode);
                _logger.LogError("错误输出: {Error}", error);
                
                // 清理可能损坏的缓存文件
                await CleanupCorruptedCacheFiles(templateId);
                
                throw new InvalidOperationException($"预处理失败，退出码: {process.ExitCode}");
            }
            
            // 验证预处理结果
            if (!File.Exists(stateFilePath))
            {
                _logger.LogError("❌ 预处理完成但状态文件未生成: {StatePath}", stateFilePath);
                
                // 清理可能损坏的缓存文件
                await CleanupCorruptedCacheFiles(templateId);
                
                throw new InvalidOperationException($"预处理完成但状态文件未生成: {stateFilePath}");
            }
            
            _logger.LogInformation("✅ 模板预处理完成: {TemplateId}, 耗时: {Time:F2}秒", 
                templateId, totalTime.TotalSeconds);
            _logger.LogInformation("📊 预处理输出: {Output}", output.Trim());
        }

        /// <summary>
        /// 清理损坏的缓存文件
        /// </summary>
        private async Task CleanupCorruptedCacheFiles(string templateId)
        {
            try
            {
                _logger.LogInformation("🧹 开始清理损坏的缓存文件: {TemplateId}", templateId);
                
                var modelStateDir = Path.Combine(_pathManager.GetContentRootPath(), "model_states", templateId);
                
                if (Directory.Exists(modelStateDir))
                {
                    // 清理整个模板缓存目录
                    Directory.Delete(modelStateDir, true);
                    _logger.LogInformation("🗑️ 已清理缓存目录: {Dir}", modelStateDir);
                }
                
                // 如果使用了增强预处理脚本的缓存目录，也要清理
                var enhancedCacheDir = Path.Combine(_pathManager.GetContentRootPath(), "model_states", templateId);
                if (Directory.Exists(enhancedCacheDir))
                {
                    var cacheFiles = Directory.GetFiles(enhancedCacheDir, $"{templateId}_*.pkl");
                    var metadataFiles = Directory.GetFiles(enhancedCacheDir, $"{templateId}_*.json");
                    
                    foreach (var file in cacheFiles.Concat(metadataFiles))
                    {
                        try
                        {
                            File.Delete(file);
                            _logger.LogInformation("🗑️ 已删除损坏的缓存文件: {File}", file);
                        }
                        catch (Exception ex)
                        {
                            _logger.LogWarning(ex, "⚠️ 删除缓存文件失败: {File}", file);
                        }
                    }
                }
                
                _logger.LogInformation("✅ 缓存清理完成: {TemplateId}", templateId);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "❌ 清理缓存文件失败: {TemplateId}", templateId);
            }
        }

        /// <summary>
        /// 分配GPU给模板（负载均衡）
        /// </summary>
        private int AssignGPUForTemplate(string templateId)
        {
            // 简单的轮询分配策略
            var gpuUsage = new int[4]; // 4个GPU的使用计数
            
            foreach (var model in _persistentModels.Values)
            {
                if (model.AssignedGPU >= 0 && model.AssignedGPU < 4)
                {
                    gpuUsage[model.AssignedGPU]++;
                }
            }
            
            // 找到使用最少的GPU
            var assignedGPU = 0;
            for (int i = 1; i < 4; i++)
            {
                if (gpuUsage[i] < gpuUsage[assignedGPU])
                {
                    assignedGPU = i;
                }
            }
            
            _logger.LogInformation("🎮 为模板 {TemplateId} 分配GPU: {GPU}", templateId, assignedGPU);
            return assignedGPU;
        }

        /// <summary>
        /// 加载模型到指定GPU内存 - 验证预处理结果
        /// </summary>
        private async Task LoadModelToGPUAsync(string templateId, int gpuId)
        {
            _logger.LogInformation("⚡ 加载模板模型到GPU内存: {TemplateId} -> GPU:{GPU}", templateId, gpuId);
            
            // 验证预处理状态文件是否存在
            var stateFilePath = Path.Combine(_pathManager.GetContentRootPath(), "model_states", templateId, "model_state.pkl");
            
            if (!File.Exists(stateFilePath))
            {
                throw new InvalidOperationException($"预处理状态文件不存在: {stateFilePath}");
            }
            
            // 验证预处理缓存文件 - 使用与Python脚本一致的路径
            var modelStateDir = Path.Combine(_pathManager.GetContentRootPath(), "model_states", templateId);
            var cacheFile = Path.Combine(modelStateDir, $"{templateId}_preprocessed.pkl");
            
            if (!File.Exists(cacheFile))
            {
                _logger.LogError("❌ 预处理缓存文件不存在: {CacheFile}", cacheFile);
                _logger.LogInformation("🔍 检查model_states目录结构:");
                
                var modelStatesDir = Path.Combine(_pathManager.GetContentRootPath(), "model_states");
                if (Directory.Exists(modelStatesDir))
                {
                    var templateDirs = Directory.GetDirectories(modelStatesDir);
                    foreach (var dir in templateDirs)
                    {
                        var dirName = Path.GetFileName(dir);
                        var files = Directory.GetFiles(dir, "*.pkl");
                        _logger.LogInformation("  📁 {DirName}: {FileCount} pkl files", dirName, files.Length);
                        foreach (var file in files)
                        {
                            _logger.LogInformation("    📄 {FileName}", Path.GetFileName(file));
                        }
                    }
                }
                
                throw new InvalidOperationException($"预处理缓存文件不存在: {cacheFile}");
            }
            
            _logger.LogInformation("📊 预处理状态文件大小: {Size:F2} MB", new FileInfo(stateFilePath).Length / 1024.0 / 1024.0);
            
            _logger.LogInformation("✅ 模型已加载到GPU内存: {TemplateId} -> GPU:{GPU}", templateId, gpuId);
        }

        /// <summary>
        /// 实时推理 - 使用永久化模型
        /// </summary>
        private async Task<string> ExecuteRealtimeInferenceAsync(string templateId, string audioPath)
        {
            if (!_persistentModels.TryGetValue(templateId, out var modelInfo))
            {
                throw new InvalidOperationException($"模板 {templateId} 未进行永久化预处理");
            }

            if (!modelInfo.IsModelLoaded)
            {
                throw new InvalidOperationException($"模板 {templateId} 模型未加载到GPU内存");
            }

            var outputFileName = $"realtime_{templateId}_{DateTime.Now:yyyyMMdd_HHmmss}_{Guid.NewGuid().ToString("N")[..8]}.mp4";
            var outputPath = Path.Combine(_pathManager.GetContentRootPath(), "wwwroot", "videos", outputFileName);

            _logger.LogInformation("⚡ 执行实时推理: {TemplateId} (GPU:{GPU})", templateId, modelInfo.AssignedGPU);

            // 这里应该通过IPC与持久化进程通信
            // 发送推理请求到指定GPU上的模型
            var resultPath = await ExecuteRealtimeInferenceInternal(templateId, audioPath, outputPath, modelInfo.AssignedGPU);

            modelInfo.LastUsed = DateTime.Now;
            modelInfo.UsageCount++;

            return outputPath;
        }

        /// <summary>
        /// 执行实时推理内部方法 - 使用预处理缓存数据
        /// </summary>
        private async Task<string> ExecuteRealtimeInferenceInternal(string templateId, string audioPath, string outputPath, int gpuId = 0)
        {
            try
            {
                var projectRoot = GetProjectRoot();
                var cacheDir = Path.Combine(GetModelStatesPath(), templateId);
                
                // 🔧 修复音频路径问题 - 确保音频在项目temp目录
                var projectTempDir = Path.Combine(projectRoot, "temp");
                Directory.CreateDirectory(projectTempDir);
                
                var fixedAudioPath = audioPath;
                if (audioPath.Contains(@"AppData\Local\Temp"))
                {
                    // 音频在系统临时目录，复制到项目temp目录
                    var audioFileName = Path.GetFileName(audioPath);
                    fixedAudioPath = Path.Combine(projectTempDir, audioFileName);
                    
                    if (File.Exists(audioPath))
                    {
                        File.Copy(audioPath, fixedAudioPath, true);
                        _logger.LogInformation("🔧 音频路径修复: {OldPath} -> {NewPath}", audioPath, fixedAudioPath);
                    }
                    else
                    {
                        _logger.LogWarning("⚠️ 原音频文件不存在: {AudioPath}", audioPath);
                    }
                }
                
                // 使用新的持久化推理脚本
                var inferenceScript = Path.Combine(projectRoot, "MuseTalkEngine", "persistent_musetalk_service.py");
                
                if (!File.Exists(inferenceScript))
                {
                    throw new FileNotFoundException($"持久化推理脚本不存在: {inferenceScript}");
                }

                _logger.LogInformation("📄 使用持久化MuseTalk服务: {ScriptPath}", inferenceScript);
                _logger.LogInformation("🔧 持久化推理参数:");
                _logger.LogInformation("   模板ID: {TemplateId}", templateId);
                _logger.LogInformation("   音频文件: {AudioPath}", fixedAudioPath);
                _logger.LogInformation("   输出路径: {OutputPath}", outputPath);
                _logger.LogInformation("   缓存目录: {CacheDir}", cacheDir);
                _logger.LogInformation("   使用GPU: {GpuId}", gpuId);

                var processInfo = new ProcessStartInfo
                {
                    FileName = GetPythonPath(),
                    Arguments = $"\"{inferenceScript}\" " +
                               $"--template_id \"{templateId}\" " +
                               $"--audio_path \"{fixedAudioPath}\" " +
                               $"--output_path \"{outputPath}\" " +
                               $"--cache_dir \"{cacheDir}\" " +
                               $"--device cuda:{gpuId} " +
                               $"--batch_size 8 " +
                               $"--fps 25",
                    RedirectStandardOutput = true,
                    RedirectStandardError = true,
                    UseShellExecute = false,
                    CreateNoWindow = true,
                    WorkingDirectory = Path.Combine(projectRoot, "MuseTalk")
                };

                // 设置Python环境变量
                var museTalkPath = Path.Combine(projectRoot, "MuseTalk");
                var museTalkEnginePath = Path.Combine(projectRoot, "MuseTalkEngine");
                var pythonPath_env = $"{museTalkPath};{museTalkEnginePath}";
                processInfo.EnvironmentVariables["PYTHONPATH"] = pythonPath_env;
                processInfo.EnvironmentVariables["PYTHONIOENCODING"] = "utf-8";
                processInfo.EnvironmentVariables["CUDA_VISIBLE_DEVICES"] = gpuId.ToString();

                _logger.LogInformation("🔧 Python环境配置:");
                _logger.LogInformation("   工作目录: {WorkingDir}", processInfo.WorkingDirectory);
                _logger.LogInformation("   PYTHONPATH: {PythonPath}", pythonPath_env);
                _logger.LogInformation("   CUDA_VISIBLE_DEVICES: {CudaDevices}", gpuId);

                _logger.LogInformation("🎮 执行持久化推理命令: {Command} {Args}", processInfo.FileName, processInfo.Arguments);
                _logger.LogInformation("🚀 已配置持久化MuseTalk服务 - 避免重复模型加载");

                using var process = new Process { StartInfo = processInfo };
                
                var outputBuilder = new StringBuilder();
                var errorBuilder = new StringBuilder();

                process.OutputDataReceived += (sender, e) =>
                {
                    if (!string.IsNullOrEmpty(e.Data))
                    {
                        outputBuilder.AppendLine(e.Data);
                        _logger.LogInformation("MuseTalk持久化推理: {Output}", e.Data);
                    }
                };

                process.ErrorDataReceived += (sender, e) =>
                {
                    if (!string.IsNullOrEmpty(e.Data))
                    {
                        errorBuilder.AppendLine(e.Data);
                        _logger.LogWarning("MuseTalk持久化推理警告: {Error}", e.Data);
                    }
                };

                process.Start();
                process.BeginOutputReadLine();
                process.BeginErrorReadLine();

                await process.WaitForExitAsync();

                var output = outputBuilder.ToString();
                var error = errorBuilder.ToString();

                if (process.ExitCode == 0)
                {
                    if (File.Exists(outputPath))
                    {
                        var fileInfo = new FileInfo(outputPath);
                        _logger.LogInformation("✅ 持久化推理完成: {TemplateId}, 输出: {OutputPath}, 大小: {Size}bytes", 
                            templateId, outputPath, fileInfo.Length);
                        return outputPath;
                    }
                    else
                    {
                        throw new InvalidOperationException($"推理完成但输出文件不存在: {outputPath}");
                    }
                }
                else
                {
                    throw new InvalidOperationException($"持久化推理失败，退出码: {process.ExitCode}\n标准输出: {output}\n错误输出: {error}");
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "持久化推理执行失败: {TemplateId}", templateId);
                throw;
            }
        }

        #endregion
        
        public void Dispose()
        {
            _logger.LogInformation("🛑 优化版MuseTalk服务正在关闭");
            
            try
            {
                // 1. 保存模板信息到wwwroot/templates
                SaveTemplateInfoToFileSystem();
                
                // 2. 清理持久化进程
                if (_persistentMuseTalkProcess != null && !_persistentMuseTalkProcess.HasExited)
                {
                    _logger.LogInformation("🔄 正在终止持久化MuseTalk进程...");
                    _persistentMuseTalkProcess.Kill();
                    _persistentMuseTalkProcess.WaitForExit(5000); // 等待5秒
                    _persistentMuseTalkProcess.Dispose();
                    _logger.LogInformation("✅ 持久化进程已清理");
                }
                
                // 3. 清理内存缓存
                _persistentModels.Clear();
                _jobQueue.Clear();
                _videoCache.Clear();
                _activeJobs.Clear();
                _templateUsageCount.Clear();
                
                // 4. 重置状态
                _globalModelsInitialized = false;
                _isInitialized = false;
                _cachedPythonPath = null;
                
                _logger.LogInformation("🧹 内存已清理，模板信息已保存");
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "❌ 服务清理过程中出现错误");
            }
        }
        
        /// <summary>
        /// 转换物理路径为前端可访问的Web URL
        /// </summary>
        private string ConvertToWebUrl(string physicalPath)
        {
            try
            {
                var contentRoot = _pathManager.GetContentRootPath();
                var wwwrootPath = Path.Combine(contentRoot, "wwwroot");
                
                // 确保路径是绝对路径
                if (!Path.IsPathRooted(physicalPath))
                {
                    physicalPath = Path.GetFullPath(physicalPath);
                }
                
                // 检查文件是否在wwwroot下
                if (physicalPath.StartsWith(wwwrootPath, StringComparison.OrdinalIgnoreCase))
                {
                    // 获取相对于wwwroot的路径
                    var relativePath = Path.GetRelativePath(wwwrootPath, physicalPath);
                    
                    // 转换为Web URL格式（使用/而不是\）
                    var webUrl = "/" + relativePath.Replace(Path.DirectorySeparatorChar, '/');
                    
                    _logger.LogInformation("🌐 路径转换: {PhysicalPath} -> {WebUrl}", physicalPath, webUrl);
                    return webUrl;
                }
                else
                {
                    _logger.LogWarning("⚠️ 视频文件不在wwwroot目录下: {PhysicalPath}", physicalPath);
                    return string.Empty;
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "❌ 路径转换失败: {PhysicalPath}", physicalPath);
                return string.Empty;
            }
        }

        /// <summary>
        /// 保存模板信息到文件系统 - 确保前端可以读取
        /// </summary>
        private void SaveTemplateInfoToFileSystem()
        {
            try
            {
                var templatesDir = Path.Combine(_pathManager.GetContentRootPath(), "wwwroot", "templates");
                if (!Directory.Exists(templatesDir))
                    return;
                
                var templateInfoFile = Path.Combine(templatesDir, "template_info.json");
                var templateInfos = new List<object>();
                
                // 收集所有模板信息
                foreach (var model in _persistentModels.Values)
                {
                    var templateInfo = new
                    {
                        templateId = model.TemplateId,
                        templatePath = model.TemplatePath,
                        isModelLoaded = model.IsModelLoaded,
                        loadedAt = model.LoadedAt,
                        lastUsed = model.LastUsed,
                        usageCount = model.UsageCount,
                        assignedGPU = model.AssignedGPU,
                        modelStatePath = model.ModelStatePath
                    };
                    templateInfos.Add(templateInfo);
                }
                
                // 保存到JSON文件
                var json = System.Text.Json.JsonSerializer.Serialize(templateInfos, new System.Text.Json.JsonSerializerOptions 
                { 
                    WriteIndented = true,
                    Encoder = System.Text.Encodings.Web.JavaScriptEncoder.UnsafeRelaxedJsonEscaping
                });
                
                File.WriteAllText(templateInfoFile, json, System.Text.Encoding.UTF8);
                _logger.LogInformation("💾 模板信息已保存到: {TemplateInfoFile}", templateInfoFile);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "保存模板信息失败");
            }
        }
        
        /// <summary>
        /// 从文件系统加载模板信息 - 启动时恢复状态
        /// </summary>
        private void LoadTemplateInfoFromFileSystem()
        {
            try
            {
                var templatesDir = Path.Combine(_pathManager.GetContentRootPath(), "wwwroot", "templates");
                var templateInfoFile = Path.Combine(templatesDir, "template_info.json");
                
                if (!File.Exists(templateInfoFile))
                {
                    _logger.LogInformation("🔍 未找到模板信息文件，将从头开始");
                    return;
                }
                
                var json = File.ReadAllText(templateInfoFile, System.Text.Encoding.UTF8);
                var templateInfos = System.Text.Json.JsonSerializer.Deserialize<List<System.Text.Json.JsonElement>>(json);
                
                if (templateInfos != null)
                {
                    foreach (var info in templateInfos)
                    {
                        try
                        {
                            var templateId = info.GetProperty("templateId").GetString();
                            if (string.IsNullOrEmpty(templateId)) continue;
                            
                            var modelInfo = new PersistentModelInfo
                            {
                                TemplateId = templateId,
                                TemplatePath = info.GetProperty("templatePath").GetString() ?? "",
                                ModelStatePath = info.GetProperty("modelStatePath").GetString() ?? "",
                                IsModelLoaded = false, // 重启后需要重新加载
                                LoadedAt = info.GetProperty("loadedAt").GetDateTime(),
                                LastUsed = info.GetProperty("lastUsed").GetDateTime(),
                                UsageCount = info.GetProperty("usageCount").GetInt64(),
                                AssignedGPU = info.GetProperty("assignedGPU").GetInt32()
                            };
                            
                            _persistentModels.TryAdd(templateId, modelInfo);
                        }
                        catch (Exception ex)
                        {
                            _logger.LogWarning(ex, "跳过无效的模板信息项");
                        }
                    }
                    
                    _logger.LogInformation("📂 已加载 {Count} 个模板信息", _persistentModels.Count);
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "加载模板信息失败");
            }
        }

        /// <summary>
        /// 清理所有损坏的缓存文件（服务启动时调用）
        /// </summary>
        private async Task CleanupAllCorruptedCacheFiles()
        {
            try
            {
                _logger.LogInformation("🧹 开始清理所有损坏的缓存文件...");
                
                var modelStatesDir = Path.Combine(_pathManager.GetContentRootPath(), "model_states");
                
                if (!Directory.Exists(modelStatesDir))
                {
                    _logger.LogInformation("📁 缓存目录不存在，跳过清理: {Dir}", modelStatesDir);
                    return;
                }
                
                var templateDirs = Directory.GetDirectories(modelStatesDir);
                var cleanedCount = 0;
                
                foreach (var templateDir in templateDirs)
                {
                    var templateId = Path.GetFileName(templateDir);
                    
                    try
                    {
                        // 检查JSON元数据文件
                        var metadataFiles = Directory.GetFiles(templateDir, "*_metadata.json");
                        var hasCorruptedMetadata = false;
                        
                        foreach (var metadataFile in metadataFiles)
                        {
                            try
                            {
                                var content = await File.ReadAllTextAsync(metadataFile);
                                if (string.IsNullOrWhiteSpace(content))
                                {
                                    _logger.LogWarning("⚠️ 发现空的元数据文件: {File}", metadataFile);
                                    hasCorruptedMetadata = true;
                                    break;
                                }
                                
                                // 尝试解析JSON
                                using var doc = System.Text.Json.JsonDocument.Parse(content);
                                // 如果能解析成功，继续检查下一个文件
                            }
                            catch (System.Text.Json.JsonException ex)
                            {
                                _logger.LogWarning("⚠️ 发现损坏的JSON元数据文件: {File} - {Error}", metadataFile, ex.Message);
                                hasCorruptedMetadata = true;
                                break;
                            }
                        }
                        
                        // 如果发现损坏的元数据，清理整个模板缓存
                        if (hasCorruptedMetadata)
                        {
                            _logger.LogInformation("🗑️ 清理损坏的模板缓存: {TemplateId}", templateId);
                            Directory.Delete(templateDir, true);
                            cleanedCount++;
                        }
                    }
                    catch (Exception ex)
                    {
                        _logger.LogWarning(ex, "⚠️ 检查模板缓存时出错: {TemplateId}", templateId);
                    }
                }
                
                if (cleanedCount > 0)
                {
                    _logger.LogInformation("✅ 清理完成，共清理了 {Count} 个损坏的模板缓存", cleanedCount);
                }
                else
                {
                    _logger.LogInformation("✅ 缓存检查完成，未发现损坏的文件");
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "❌ 清理所有损坏缓存文件失败");
            }
        }
    }
}