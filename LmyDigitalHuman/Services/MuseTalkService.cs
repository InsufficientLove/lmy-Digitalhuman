using LmyDigitalHuman.Models;
using Microsoft.Extensions.Caching.Memory;
using System.Collections.Concurrent;
using System.Diagnostics;
using System.Text.Json;
using System.Text;
using System.Threading.Channels;

namespace LmyDigitalHuman.Services
{
    public class MuseTalkService : IMuseTalkService
    {
        private readonly ILogger<MuseTalkService> _logger;
        private readonly IConfiguration _configuration;
        private readonly IMemoryCache _cache;
        private readonly IPathManager _pathManager;
        private readonly IPythonEnvironmentService _pythonEnvironmentService;
        private readonly string _pythonPath;
        private readonly string _museTalkScriptPath;
        
        // 任务队列和并发控制
        private readonly ConcurrentDictionary<string, QueuedJob> _jobQueue = new();
        private readonly ConcurrentDictionary<string, ProcessingJob> _activeJobs = new();
        private readonly SemaphoreSlim _processingLimiter;
        private readonly Channel<QueuedJob> _processingChannel;
        private readonly ChannelWriter<QueuedJob> _channelWriter;
        private readonly CancellationTokenSource _cancellationTokenSource = new();
        
        // 性能统计
        private long _totalProcessedJobs = 0;
        private long _totalProcessingTime = 0;
        private readonly ConcurrentDictionary<string, CacheStatistics> _cacheStats = new();

        public MuseTalkService(
            ILogger<MuseTalkService> logger,
            IConfiguration configuration,
            IMemoryCache cache,
            IPathManager pathManager,
            IPythonEnvironmentService pythonEnvironmentService)
        {
            _logger = logger;
            _configuration = configuration;
            _cache = cache;
            _pathManager = pathManager;
            _pythonEnvironmentService = pythonEnvironmentService;
            
            // 使用Python环境服务获取最佳路径
            _pythonPath = configuration["DigitalHuman:MuseTalk:PythonPath"];
            if (string.IsNullOrEmpty(_pythonPath))
            {
                _pythonPath = "python"; // 临时默认值，运行时会通过PythonEnvironmentService获取
            }
            _museTalkScriptPath = _pathManager.ResolvePath("musetalk_service_complete.py");
            
            _logger.LogInformation("MuseTalk Python路径: {PythonPath}", _pythonPath);
            _logger.LogInformation("MuseTalk脚本路径: {ScriptPath}", _museTalkScriptPath);
            
            // 高并发支持：200个同时处理
            var maxConcurrentJobs = configuration.GetValue<int>("DigitalHuman:MaxVideoGeneration", 8);
            _processingLimiter = new SemaphoreSlim(maxConcurrentJobs, maxConcurrentJobs);
            
            // 创建处理队列
            var options = new BoundedChannelOptions(1000)
            {
                FullMode = BoundedChannelFullMode.Wait,
                SingleReader = false,
                SingleWriter = false
            };
            var channel = Channel.CreateBounded<QueuedJob>(options);
            _processingChannel = channel;
            _channelWriter = channel.Writer;
            
            // 启动后台处理任务
            StartBackgroundProcessors();
            
            _logger.LogInformation("MuseTalk服务初始化完成，最大并发数: {MaxConcurrency}", maxConcurrentJobs);
        }

        public async Task<DigitalHumanResponse> GenerateVideoAsync(DigitalHumanRequest request)
        {
            var stopwatch = Stopwatch.StartNew();
            
            try
            {
                _logger.LogInformation("开始生成数字人视频: Avatar={Avatar}, Audio={Audio}", 
                    request.AvatarImagePath, request.AudioPath);

                // 转换和验证输入文件路径
                var fullImagePath = _pathManager.ResolveImagePath(request.AvatarImagePath);
                var fullAudioPath = _pathManager.ResolveAudioPath(request.AudioPath);
                
                _logger.LogInformation("路径解析结果:");
                _logger.LogInformation("  原始图片路径: {OriginalImagePath}", request.AvatarImagePath);
                _logger.LogInformation("  解析图片路径: {ResolvedImagePath}", fullImagePath);
                _logger.LogInformation("  图片文件存在: {ImageExists}", File.Exists(fullImagePath));
                _logger.LogInformation("  原始音频路径: {OriginalAudioPath}", request.AudioPath);
                _logger.LogInformation("  解析音频路径: {ResolvedAudioPath}", fullAudioPath);
                _logger.LogInformation("  音频文件存在: {AudioExists}", File.Exists(fullAudioPath));
                
                // 图片路径验证
                if (!File.Exists(fullImagePath))
                {
                    _logger.LogError("图片文件不存在: {ImagePath}", fullImagePath);
                }
                
                // 音频路径验证
                if (!File.Exists(fullAudioPath))
                {
                    _logger.LogError("音频文件不存在: {AudioPath}", fullAudioPath);
                }
                
                // 最终验证
                if (!File.Exists(fullImagePath))
                {
                    _logger.LogError("最终图片路径验证失败: {FinalImagePath}", fullImagePath);
                    return new DigitalHumanResponse
                    {
                        Success = false,
                        Error = $"头像图片不存在: {request.AvatarImagePath} (最终解析为: {fullImagePath})"
                    };
                }

                if (!File.Exists(fullAudioPath))
                {
                    _logger.LogError("最终音频路径验证失败: {FinalAudioPath}", fullAudioPath);
                    return new DigitalHumanResponse
                    {
                        Success = false,
                        Error = $"音频文件不存在: {request.AudioPath} (最终解析为: {fullAudioPath})"
                    };
                }

                // 检查缓存
                if (!string.IsNullOrEmpty(request.CacheKey))
                {
                    var cachedResult = await GetCachedVideoAsync(request.CacheKey);
                    if (cachedResult != null)
                    {
                        _logger.LogInformation("从缓存返回视频结果: CacheKey={CacheKey}", request.CacheKey);
                        return cachedResult;
                    }
                }

                // 生成输出文件名
                var outputFilePath = _pathManager.CreateTempVideoPath("mp4");

                await _processingLimiter.WaitAsync();
                try
                {
                    // 使用解析后的完整路径调用Python脚本
                    var updatedRequest = new DigitalHumanRequest
                    {
                        AvatarImagePath = fullImagePath,
                        AudioPath = fullAudioPath,
                        Quality = request.Quality,
                        Fps = request.Fps,
                        BatchSize = request.BatchSize,
                        BboxShift = request.BboxShift,
                        EnableEmotion = request.EnableEmotion,
                        Priority = request.Priority,
                        CacheKey = request.CacheKey
                    };
                    
                    var result = await ExecuteMuseTalkPythonAsync(updatedRequest, outputFilePath);
                    
                    stopwatch.Stop();

                    if (result.Success)
                    {
                        // 缓存结果
                        if (!string.IsNullOrEmpty(request.CacheKey))
                        {
                            await CacheVideoResultAsync(request.CacheKey, result);
                        }

                        // 更新统计
                        Interlocked.Increment(ref _totalProcessedJobs);
                        Interlocked.Add(ref _totalProcessingTime, stopwatch.ElapsedMilliseconds);
                    }

                    return result;
                }
                finally
                {
                    _processingLimiter.Release();
                }
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

        public async Task<List<DigitalHumanResponse>> GenerateBatchVideosAsync(List<DigitalHumanRequest> requests)
        {
            _logger.LogInformation("开始批量生成数字人视频: Count={Count}", requests.Count);

            var tasks = requests.Select(GenerateVideoAsync).ToArray();
            var results = await Task.WhenAll(tasks);
            
            return results.ToList();
        }

        public async Task<string> QueueVideoGenerationAsync(DigitalHumanRequest request)
        {
            var jobId = Guid.NewGuid().ToString("N");
            var job = new QueuedJob
            {
                JobId = jobId,
                Request = request,
                Status = JobStatus.Pending,
                QueuedAt = DateTime.UtcNow,
                Priority = request.Priority,
                EstimatedProcessingTime = EstimateProcessingTime(request)
            };

            _jobQueue.TryAdd(jobId, job);
            
            // 将任务加入处理队列
            await _channelWriter.WriteAsync(job);
            
            _logger.LogInformation("任务已加入队列: JobId={JobId}, Priority={Priority}", jobId, request.Priority);
            
            return jobId;
        }

        public async Task<DigitalHumanResponse?> GetQueuedVideoResultAsync(string jobId)
        {
            await Task.CompletedTask;
            
            if (_jobQueue.TryGetValue(jobId, out var job))
            {
                return job.Status == JobStatus.Completed ? job.Result : null;
            }
            
            return null;
        }

        public async Task<List<QueuedJob>> GetQueueStatusAsync()
        {
            await Task.CompletedTask;
            return _jobQueue.Values.ToList();
        }

        public async Task<bool> CancelQueuedJobAsync(string jobId)
        {
            await Task.CompletedTask;
            
            if (_jobQueue.TryGetValue(jobId, out var job) && job.Status == JobStatus.Pending)
            {
                job.Status = JobStatus.Cancelled;
                return true;
            }
            
            return false;
        }

        public async Task<List<DigitalHumanTemplate>> GetAvailableTemplatesAsync()
        {
            try
            {
                var templates = new List<DigitalHumanTemplate>();
                
                var templatesPath = _pathManager.GetTemplatesPath();
                if (!Directory.Exists(templatesPath))
                {
                    return templates;
                }

                var jsonFiles = Directory.GetFiles(templatesPath, "*.json");
                
                foreach (var jsonFile in jsonFiles)
                {
                    try
                    {
                        var jsonContent = await File.ReadAllTextAsync(jsonFile);
                        var template = JsonSerializer.Deserialize<DigitalHumanTemplate>(jsonContent);
                        
                        if (template != null)
                        {
                            // 确保兼容性属性正确设置
                            if (string.IsNullOrEmpty(template.Id) && !string.IsNullOrEmpty(template.TemplateId))
                                template.Id = template.TemplateId;
                            if (string.IsNullOrEmpty(template.Name) && !string.IsNullOrEmpty(template.TemplateName))
                                template.Name = template.TemplateName;
                                
                            var imagePath = _pathManager.ResolveImagePath(template.ImagePath);
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
            var templateId = Guid.NewGuid().ToString("N");
            var sanitizedName = SanitizeFileName(request.TemplateName);
            var imageFileName = $"{sanitizedName}_{templateId}.jpg";
            var jsonFileName = $"{sanitizedName}_{templateId}.json";
            
            var templatesPath = _pathManager.GetTemplatesPath();
            var imageTargetPath = Path.Combine(templatesPath, imageFileName);
            var jsonTargetPath = Path.Combine(templatesPath, jsonFileName);

            // 保存上传的图片文件
            if (request.ImageFile != null)
            {
                using var stream = new FileStream(imageTargetPath, FileMode.Create);
                await request.ImageFile.CopyToAsync(stream);
            }

            var template = new DigitalHumanTemplate
            {
                TemplateId = templateId,
                TemplateName = request.TemplateName,
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
            
            await File.WriteAllTextAsync(jsonTargetPath, jsonContent, Encoding.UTF8);

            _logger.LogInformation("创建数字人模板成功: {TemplateName} ({TemplateId})", request.TemplateName, templateId);
            return template;
        }

        public async Task<bool> DeleteTemplateAsync(string templateId)
        {
            try
            {
                var templatesPath = _pathManager.GetTemplatesPath();
                var jsonFiles = Directory.GetFiles(templatesPath, "*.json");
                
                foreach (var jsonFile in jsonFiles)
                {
                    var jsonContent = await File.ReadAllTextAsync(jsonFile);
                    var template = JsonSerializer.Deserialize<DigitalHumanTemplate>(jsonContent);
                    
                    if (template?.TemplateId == templateId || template?.Id == templateId)
                    {
                        File.Delete(jsonFile);
                        
                        var imagePath = _pathManager.ResolveImagePath(template.ImagePath);
                        if (File.Exists(imagePath))
                        {
                            File.Delete(imagePath);
                        }
                        
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

        public async Task<bool> ValidateTemplateAsync(string templateId)
        {
            var templates = await GetAvailableTemplatesAsync();
            return templates.Any(t => t.TemplateId == templateId || t.Id == templateId);
        }

        public async Task<PreprocessingResult> PreprocessTemplateAsync(string templateId)
        {
            // 模板预处理逻辑（占位符实现）
            await Task.Delay(100);
            
            return new PreprocessingResult
            {
                Success = true,
                TemplateId = templateId,
                PreprocessingTime = 100,
                OptimizedSettings = new Dictionary<string, object>
                {
                    ["optimized"] = true,
                    ["timestamp"] = DateTime.UtcNow
                }
            };
        }

        public async Task<bool> WarmupTemplateAsync(string templateId)
        {
            try
            {
                await PreprocessTemplateAsync(templateId);
                return true;
            }
            catch
            {
                return false;
            }
        }

        public async Task<string> GetOptimalSettingsAsync(string templateId, string quality)
        {
            await Task.CompletedTask;
            
            return quality switch
            {
                "low" => "fast",
                "medium" => "balanced",
                "high" => "quality",
                "ultra" => "ultra_quality",
                _ => "balanced"
            };
        }

        public async Task<bool> CacheVideoResultAsync(string cacheKey, DigitalHumanResponse response)
        {
            try
            {
                _cache.Set(cacheKey, response, TimeSpan.FromHours(
                    _configuration.GetValue<int>("DigitalHuman:CacheExpirationHours", 2)));
                return true;
            }
            catch
            {
                return false;
            }
        }

        public async Task<DigitalHumanResponse?> GetCachedVideoAsync(string cacheKey)
        {
            await Task.CompletedTask;
            
            if (_cache.TryGetValue(cacheKey, out DigitalHumanResponse? cachedResult))
            {
                if (cachedResult != null)
                {
                    cachedResult.FromCache = true;
                }
                return cachedResult;
            }
            
            return null;
        }

        public async Task<bool> ClearVideoCache(string? templateId = null)
        {
            // IMemoryCache 没有直接清除特定模式的方法
            // 这里只是标记，实际实现可能需要自定义缓存管理
            await Task.CompletedTask;
            return true;
        }

        public async Task<CacheStatistics> GetCacheStatisticsAsync()
        {
            await Task.CompletedTask;
            
            return new CacheStatistics
            {
                TotalCachedItems = _cacheStats.Count,
                CacheHitRate = CalculateCacheHitRate(),
                LastCleanup = DateTime.UtcNow
            };
        }

        public async Task<bool> IsServiceHealthyAsync()
        {
            try
            {
                // 检查Python和脚本文件是否存在
                var result = await RunPythonCommandAsync("--version", TimeSpan.FromSeconds(5));
                return result.Success;
            }
            catch
            {
                return false;
            }
        }

        public async Task<ServiceMetrics> GetServiceMetricsAsync()
        {
            await Task.CompletedTask;
            
            var averageProcessingTime = _totalProcessedJobs > 0 ? _totalProcessingTime / _totalProcessedJobs : 0;
            var throughputPerHour = _totalProcessedJobs > 0 ? (3600000.0 / averageProcessingTime) : 0;
            
            return new ServiceMetrics
            {
                ActiveWorkers = _activeJobs.Count,
                QueueLength = _jobQueue.Count(j => j.Value.Status == JobStatus.Pending),
                AverageProcessingTime = averageProcessingTime,
                ThroughputPerHour = throughputPerHour,
                ResourceUsage = new Dictionary<string, object>
                {
                    ["total_processed"] = _totalProcessedJobs,
                    ["total_time"] = _totalProcessingTime,
                    ["active_jobs"] = _activeJobs.Count
                }
            };
        }

        public async Task<List<ProcessingJob>> GetActiveJobsAsync()
        {
            await Task.CompletedTask;
            return _activeJobs.Values.ToList();
        }

        public async Task<bool> ScaleWorkersAsync(int workerCount)
        {
            // 动态调整工作线程数（简化实现）
            await Task.CompletedTask;
            return true;
        }

        public async Task<AudioOptimizationResult> OptimizeAudioForGenerationAsync(string audioPath)
        {
            // 使用FFmpeg优化音频用于MuseTalk
            var stopwatch = Stopwatch.StartNew();
            
            try
            {
                var outputPath = Path.Combine(Path.GetDirectoryName(audioPath)!, 
                    $"optimized_{Path.GetFileNameWithoutExtension(audioPath)}.wav");
                
                var processInfo = new ProcessStartInfo
                {
                    FileName = "ffmpeg",
                    Arguments = $"-i \"{audioPath}\" -ar 16000 -ac 1 -c:a pcm_s16le \"{outputPath}\" -y",
                    UseShellExecute = false,
                    RedirectStandardOutput = true,
                    RedirectStandardError = true,
                    CreateNoWindow = true
                };

                using var process = Process.Start(processInfo);
                if (process != null)
                {
                    await process.WaitForExitAsync();
                    
                    if (process.ExitCode == 0)
                    {
                        var inputInfo = new FileInfo(audioPath);
                        var outputInfo = new FileInfo(outputPath);
                        
                        return new AudioOptimizationResult
                        {
                            Success = true,
                            OptimizedAudioPath = outputPath,
                            OriginalSize = inputInfo.Length,
                            OptimizedSize = outputInfo.Length,
                            ProcessingTime = stopwatch.ElapsedMilliseconds,
                            AppliedOptimizations = new List<string> { "16kHz", "mono", "16-bit" }
                        };
                    }
                }
                
                return new AudioOptimizationResult { Success = false };
            }
            catch (Exception ex)
            {
                return new AudioOptimizationResult 
                { 
                    Success = false, 
                    ProcessingTime = stopwatch.ElapsedMilliseconds 
                };
            }
        }

        public async Task<bool> ValidateAudioAsync(string audioPath)
        {
            try
            {
                var processInfo = new ProcessStartInfo
                {
                    FileName = "ffprobe",
                    Arguments = $"-v quiet -print_format json -show_format -show_streams \"{audioPath}\"",
                    UseShellExecute = false,
                    RedirectStandardOutput = true,
                    CreateNoWindow = true
                };

                using var process = Process.Start(processInfo);
                if (process != null)
                {
                    var output = await process.StandardOutput.ReadToEndAsync();
                    await process.WaitForExitAsync();
                    
                    return process.ExitCode == 0 && !string.IsNullOrEmpty(output);
                }
                
                return false;
            }
            catch
            {
                return false;
            }
        }

        public async Task<string> StartStreamingGenerationAsync(StreamingGenerationRequest request)
        {
            // 流式生成（占位符实现）
            await Task.CompletedTask;
            return Guid.NewGuid().ToString("N");
        }

        public async Task<StreamingGenerationChunk?> GetGenerationChunkAsync(string sessionId)
        {
            // 获取生成块（占位符实现）
            await Task.CompletedTask;
            return null;
        }

        public async Task<bool> EndStreamingGenerationAsync(string sessionId)
        {
            // 结束流式生成（占位符实现）
            await Task.CompletedTask;
            return true;
        }

        // 私有方法
        private async Task<DigitalHumanResponse> ExecuteMuseTalkPythonAsync(DigitalHumanRequest request, string outputPath)
        {
            var stopwatch = Stopwatch.StartNew();
            
            try
            {
                var arguments = BuildPythonArguments(request, outputPath);
                // 根据视频类型设置合适的超时时间
                var timeout = request.CacheKey?.StartsWith("welcome_") == true 
                    ? TimeSpan.FromMinutes(3)  // 欢迎视频3分钟超时
                    : TimeSpan.FromMinutes(10); // 普通视频10分钟超时
                var result = await RunPythonCommandAsync(arguments, timeout);
                
                stopwatch.Stop();

                if (result.Success && File.Exists(outputPath))
                {
                    var fileInfo = new FileInfo(outputPath);
                    var videoUrl = $"/videos/{Path.GetFileName(outputPath)}";
                    
                    return new DigitalHumanResponse
                    {
                        Success = true,
                        VideoUrl = videoUrl,
                        VideoPath = outputPath,
                        ProcessingTime = stopwatch.ElapsedMilliseconds,
                        Message = "数字人视频生成成功",
                        CompletedAt = DateTime.UtcNow,
                        Metadata = new DigitalHumanMetadata
                        {
                            Resolution = GetVideoResolution(request.Quality),
                            Fps = request.Fps ?? 25,
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
                        Error = result.Output,
                        ProcessingTime = stopwatch.ElapsedMilliseconds
                    };
                }
            }
            catch (Exception ex)
            {
                return new DigitalHumanResponse
                {
                    Success = false,
                    Error = ex.Message,
                    ProcessingTime = stopwatch.ElapsedMilliseconds
                };
            }
        }

        private string BuildPythonArguments(DigitalHumanRequest request, string outputPath)
        {
            var args = new StringBuilder();
            
            // 直接使用官方MuseTalk的inference脚本
            args.Append($"-m scripts.inference");
            
            // 使用相对于MuseTalk工作目录的路径（因为WorkingDirectory已经是MuseTalk目录）
            args.Append($" --inference_config \"configs/inference/test.yaml\"");
            args.Append($" --result_dir \"{Path.GetDirectoryName(outputPath)}\"");
            
            // 模型路径 - 相对于MuseTalk目录
            args.Append($" --unet_model_path \"models/musetalk/pytorch_model.bin\"");
            args.Append($" --unet_config \"models/musetalk/musetalk.json\"");
            
            // 版本和其他参数
            args.Append($" --version v1");
            
            if (request.BboxShift.HasValue)
                args.Append($" --bbox_shift {request.BboxShift.Value}");
            
            // 添加调试参数，让inference脚本输出更多信息
            args.Append($" --use_float16"); // 使用float16可能更快更稳定
            args.Append($" --batch_size 1"); // 强制使用最小batch size
                
            return args.ToString();
        }

        private async Task<PythonResult> RunPythonCommandAsync(string arguments, TimeSpan timeout)
        {
            try
            {
                // 使用Python环境服务获取最佳Python路径
                var bestPythonPath = await _pythonEnvironmentService.GetRecommendedPythonPathAsync();
                
                // MuseTalk工作目录应该是MuseTalk目录本身，因为scripts.inference使用相对路径"./musetalk/..."
                var parentDir = Directory.GetParent(_pathManager.GetContentRootPath())?.FullName ?? _pathManager.GetContentRootPath();
                var workingDir = Path.Combine(parentDir, "MuseTalk");
                
                _logger.LogInformation("执行Python命令: {PythonPath} {Arguments}", bestPythonPath, arguments);
                _logger.LogInformation("ContentRoot: {ContentRoot}", _pathManager.GetContentRootPath());
                _logger.LogInformation("工作目录: {WorkingDirectory}", workingDir);
                _logger.LogInformation("工作目录存在: {Exists}", Directory.Exists(workingDir));
                
                // 额外的环境信息
                _logger.LogInformation("CUDA版本检查: {CudaDevices}", Environment.GetEnvironmentVariable("CUDA_VISIBLE_DEVICES"));
                _logger.LogInformation("输入图片路径: {ImagePath}", request.AvatarImagePath);
                _logger.LogInformation("输入音频路径: {AudioPath}", request.AudioPath);
                
                var processInfo = new ProcessStartInfo
                {
                    FileName = bestPythonPath,
                    Arguments = arguments,
                    UseShellExecute = false,
                    RedirectStandardOutput = true,
                    RedirectStandardError = true,
                    CreateNoWindow = true,
                    WorkingDirectory = workingDir
                };
                
                // 设置环境变量解决中文乱码问题
                processInfo.Environment["PYTHONIOENCODING"] = "utf-8";
                processInfo.Environment["PYTHONUNBUFFERED"] = "1";
                processInfo.Environment["PYTHONUTF8"] = "1";
                
                // 检查MuseTalk目录是否存在
                if (!Directory.Exists(workingDir))
                {
                    _logger.LogError("MuseTalk目录不存在: {MuseTalkDir}", workingDir);
                    _logger.LogError("请确保MuseTalk目录位于: {ExpectedPath}", workingDir);
                    return new PythonResult
                    {
                        Success = false,
                        Output = $"MuseTalk目录不存在: {workingDir}"
                    };
                }
                
                // 检查关键的脚本目录是否存在
                var scriptsDir = Path.Combine(workingDir, "scripts");
                var musetalkDir = Path.Combine(workingDir, "musetalk");
                if (!Directory.Exists(scriptsDir) || !Directory.Exists(musetalkDir))
                {
                    _logger.LogError("MuseTalk关键目录缺失: scripts={ScriptsExists}, musetalk={MusetalkExists}", 
                        Directory.Exists(scriptsDir), Directory.Exists(musetalkDir));
                    return new PythonResult
                    {
                        Success = false,
                        Output = $"MuseTalk目录结构不完整，缺少scripts或musetalk目录"
                    };
                }
                
                // 配置虚拟环境
                ConfigureVirtualEnvironment(processInfo, bestPythonPath);
                
                // 检查Python路径和脚本文件是否存在
                if (!File.Exists(bestPythonPath) && !bestPythonPath.Equals("python", StringComparison.OrdinalIgnoreCase))
                {
                    _logger.LogError("Python可执行文件不存在: {PythonPath}", bestPythonPath);
                    return new PythonResult
                    {
                        Success = false,
                        Output = $"Python可执行文件不存在: {_pythonPath}"
                    };
                }
                
                if (!File.Exists(_museTalkScriptPath))
                {
                    _logger.LogError("MuseTalk脚本文件不存在: {ScriptPath}", _museTalkScriptPath);
                    return new PythonResult
                    {
                        Success = false,
                        Output = $"MuseTalk脚本文件不存在: {_museTalkScriptPath}"
                    };
                }

                using var process = Process.Start(processInfo);
                if (process != null)
                {
                    _logger.LogInformation("MuseTalk进程已启动: PID={ProcessId}", process.Id);
                    
                    var processStartTime = DateTime.UtcNow;
                    var outputTask = process.StandardOutput.ReadToEndAsync();
                    var errorTask = process.StandardError.ReadToEndAsync();
                    
                    // 启动进程监控任务
                    var monitoringTask = Task.Run(async () =>
                    {
                        var lastCheck = DateTime.UtcNow;
                        while (!process.HasExited)
                        {
                            await Task.Delay(15000); // 每15秒检查一次
                            
                            if (!process.HasExited && DateTime.UtcNow - lastCheck > TimeSpan.FromSeconds(15))
                            {
                                try
                                {
                                    var elapsed = DateTime.UtcNow - processStartTime;
                                    var workingSet = process.WorkingSet64 / (1024 * 1024); // MB
                                    var cpuTime = process.TotalProcessorTime.TotalSeconds;
                                    
                                    _logger.LogInformation("MuseTalk运行状态: PID={ProcessId}, 已运行={Elapsed:mm\\:ss}, 内存={Memory}MB, CPU时间={CpuTime:F1}s",
                                        process.Id, elapsed, workingSet, cpuTime);
                                        
                                    lastCheck = DateTime.UtcNow;
                                }
                                catch
                                {
                                    // 进程可能已退出，忽略异常
                                    break;
                                }
                            }
                        }
                    });
                    
                    var processTask = Task.Run(async () =>
                    {
                        await Task.WhenAll(outputTask, errorTask);
                        await process.WaitForExitAsync();
                    });
                    
                    var completed = await Task.WhenAny(processTask, Task.Delay(timeout));
                    
                    if (completed == processTask)
                    {
                        var output = await outputTask;
                        var error = await errorTask;
                        
                        _logger.LogInformation("Python进程退出码: {ExitCode}", process.ExitCode);
                        _logger.LogInformation("Python标准输出: {Output}", 
                            string.IsNullOrEmpty(output) ? "[空]" : (output.Length > 500 ? output.Substring(0, 500) + "..." : output));
                        _logger.LogInformation("Python错误输出: {Error}", 
                            string.IsNullOrEmpty(error) ? "[空]" : (error.Length > 500 ? error.Substring(0, 500) + "..." : error));
                        
                        var isSuccess = process.ExitCode == 0;
                        var resultOutput = string.IsNullOrEmpty(error) ? output : error;
                        
                        // 尝试解析JSON输出
                        if (isSuccess && !string.IsNullOrEmpty(output))
                        {
                            try
                            {
                                // 查找JSON输出（通常在最后几行）
                                var lines = output.Split('\n', StringSplitOptions.RemoveEmptyEntries);
                                for (int i = lines.Length - 1; i >= 0; i--)
                                {
                                    var line = lines[i].Trim();
                                    if (line.StartsWith("{") && line.EndsWith("}"))
                                    {
                                        var jsonResult = JsonSerializer.Deserialize<JsonElement>(line);
                                        if (jsonResult.TryGetProperty("success", out var successProp))
                                        {
                                            isSuccess = successProp.GetBoolean();
                                            if (jsonResult.TryGetProperty("error", out var errorProp))
                                            {
                                                var errorMsg = errorProp.GetString();
                                                if (!string.IsNullOrEmpty(errorMsg))
                                                {
                                                    resultOutput = errorMsg;
                                                    isSuccess = false;
                                                }
                                            }
                                            break;
                                        }
                                    }
                                }
                            }
                            catch (Exception jsonEx)
                            {
                                _logger.LogWarning(jsonEx, "解析Python JSON输出失败");
                            }
                        }
                        
                        return new PythonResult
                        {
                            Success = isSuccess,
                            Output = resultOutput ?? "",
                            ExitCode = process.ExitCode
                        };
                    }
                    else
                    {
                        _logger.LogWarning("MuseTalk进程超时，正在终止进程: PID={ProcessId}, Timeout={Timeout}s", 
                            process.Id, timeout.TotalSeconds);
                            
                        // 收集超时前的输出，帮助诊断问题
                        string partialOutput = "";
                        string partialError = "";
                        try
                        {
                            if (outputTask.IsCompletedSuccessfully)
                                partialOutput = await outputTask;
                            if (errorTask.IsCompletedSuccessfully) 
                                partialError = await errorTask;
                                
                            _logger.LogInformation("超时前的Python标准输出: {Output}", 
                                string.IsNullOrEmpty(partialOutput) ? "[空]" : (partialOutput.Length > 1000 ? partialOutput.Substring(0, 1000) + "..." : partialOutput));
                            _logger.LogInformation("超时前的Python错误输出: {Error}", 
                                string.IsNullOrEmpty(partialError) ? "[空]" : (partialError.Length > 1000 ? partialError.Substring(0, 1000) + "..." : partialError));
                        }
                        catch (Exception ex)
                        {
                            _logger.LogWarning(ex, "收集超时输出失败");
                        }
                        
                        try
                        {
                            if (!process.HasExited)
                            {
                                process.Kill();
                                _logger.LogInformation("MuseTalk进程已被终止");
                            }
                        }
                        catch (Exception ex)
                        {
                            _logger.LogError(ex, "终止MuseTalk进程失败");
                        }
                        
                        return new PythonResult
                        {
                            Success = false,
                            Output = $"MuseTalk脚本执行超时({timeout.TotalSeconds}秒)。" +
                                    (string.IsNullOrEmpty(partialError) ? "" : $" 错误信息: {partialError}")
                        };
                    }
                }
                
                return new PythonResult
                {
                    Success = false,
                    Output = "无法启动Python进程"
                };
            }
            catch (Exception ex)
            {
                return new PythonResult
                {
                    Success = false,
                    Output = ex.Message
                };
            }
        }

        private void StartBackgroundProcessors()
        {
            // 启动多个后台处理器以支持高并发
            var processorCount = Environment.ProcessorCount;
            for (int i = 0; i < processorCount; i++)
            {
                _ = Task.Run(ProcessJobQueueAsync);
            }
        }

        private async Task ProcessJobQueueAsync()
        {
            await foreach (var job in _processingChannel.Reader.ReadAllAsync(_cancellationTokenSource.Token))
            {
                if (job.Status != JobStatus.Pending) continue;
                
                job.Status = JobStatus.Processing;
                job.StartedAt = DateTime.UtcNow;
                
                var processingJob = new ProcessingJob
                {
                    JobId = job.JobId,
                    StartTime = DateTime.UtcNow,
                    Progress = 0,
                    CurrentStep = "开始处理"
                };
                
                _activeJobs.TryAdd(job.JobId, processingJob);
                
                try
                {
                    var result = await GenerateVideoAsync(job.Request);
                    job.Result = result;
                    job.Status = result.Success ? JobStatus.Completed : JobStatus.Failed;
                    job.CompletedAt = DateTime.UtcNow;
                    
                    if (!result.Success)
                    {
                        job.Error = result.Error;
                    }
                }
                catch (Exception ex)
                {
                    job.Status = JobStatus.Failed;
                    job.Error = ex.Message;
                    job.CompletedAt = DateTime.UtcNow;
                }
                finally
                {
                    _activeJobs.TryRemove(job.JobId, out _);
                }
            }
        }

        private long EstimateProcessingTime(DigitalHumanRequest request)
        {
            // 基于质量和其他参数估算处理时间
            var baseTime = request.Quality switch
            {
                "low" => 30000,      // 30秒
                "medium" => 60000,   // 1分钟
                "high" => 120000,    // 2分钟
                "ultra" => 240000,   // 4分钟
                _ => 60000
            };
            
            return baseTime;
        }

        private double CalculateCacheHitRate()
        {
            // 简化的缓存命中率计算
            return _totalProcessedJobs > 0 ? 0.3 : 0; // 假设30%的命中率
        }

        private void ConfigureVirtualEnvironment(ProcessStartInfo processInfo, string pythonPath)
        {
            try
            {
                // 检查是否使用虚拟环境
                if (pythonPath.Contains("venv_musetalk"))
                {
                    _logger.LogInformation("配置虚拟环境: {PythonPath}", pythonPath);
                    
                    // 获取虚拟环境目录
                    var venvDir = Path.GetDirectoryName(Path.GetDirectoryName(pythonPath)); // Scripts的上级目录
                    if (!string.IsNullOrEmpty(venvDir) && Directory.Exists(venvDir))
                    {
                        // 设置虚拟环境相关的环境变量
                        processInfo.Environment["VIRTUAL_ENV"] = venvDir;
                        processInfo.Environment["VIRTUAL_ENV_PROMPT"] = "(venv_musetalk)";
                        
                        // 设置Python路径，确保使用虚拟环境的包
                        var sitePackages = Path.Combine(venvDir, "Lib", "site-packages");
                        if (Directory.Exists(sitePackages))
                        {
                            // 工作目录就是MuseTalk目录，直接将其添加到PYTHONPATH
                            var museTalkDir = processInfo.WorkingDirectory;
                            // 将MuseTalk目录和site-packages都添加到PYTHONPATH
                            processInfo.Environment["PYTHONPATH"] = museTalkDir + ";" + sitePackages;
                            _logger.LogInformation("设置PYTHONPATH: {MuseTalkDir};{SitePackages}", museTalkDir, sitePackages);
                        }
                        
                        // 修改PATH环境变量，优先使用虚拟环境的Scripts目录，同时保持系统FFmpeg可用
                        var scriptsDir = Path.Combine(venvDir, "Scripts");
                        if (Directory.Exists(scriptsDir))
                        {
                            var currentPath = Environment.GetEnvironmentVariable("PATH") ?? "";
                            // 确保系统PATH中的FFmpeg仍然可用
                            processInfo.Environment["PATH"] = scriptsDir + ";" + currentPath;
                            _logger.LogInformation("更新PATH，优先使用虚拟环境Scripts: {ScriptsDir}", scriptsDir);
                        }
                        
                        // 设置4x GPU环境变量
                        processInfo.Environment["CUDA_VISIBLE_DEVICES"] = "0,1,2,3";
                        processInfo.Environment["PYTORCH_CUDA_ALLOC_CONF"] = "max_split_size_mb:512";
                        processInfo.Environment["OMP_NUM_THREADS"] = "8";
                        
                        _logger.LogInformation("虚拟环境配置完成: {VenvDir}", venvDir);
                        _logger.LogInformation("GPU配置: CUDA_VISIBLE_DEVICES=0,1,2,3");
                    }
                    else
                    {
                        _logger.LogWarning("虚拟环境目录不存在: {VenvDir}", venvDir);
                    }
                }
                else
                {
                    _logger.LogInformation("使用系统Python: {PythonPath}", pythonPath);
                    
                    // 为系统Python也设置MuseTalk目录到PYTHONPATH
                    var museTalkDir = processInfo.WorkingDirectory; // 工作目录就是MuseTalk目录
                    var currentPythonPath = Environment.GetEnvironmentVariable("PYTHONPATH") ?? "";
                    if (!string.IsNullOrEmpty(currentPythonPath))
                    {
                        processInfo.Environment["PYTHONPATH"] = museTalkDir + ";" + currentPythonPath;
                    }
                    else
                    {
                        processInfo.Environment["PYTHONPATH"] = museTalkDir;
                    }
                    _logger.LogInformation("为系统Python设置PYTHONPATH: {MuseTalkDir}", museTalkDir);
                }
            }
            catch (Exception ex)
            {
                _logger.LogWarning("配置虚拟环境时发生错误: {Error}", ex.Message);
            }
        }

        private string GetVideoResolution(string quality)
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

        private string SanitizeFileName(string name)
        {
            var sanitized = System.Text.RegularExpressions.Regex.Replace(name, @"[^\w\-_\.]", "_");
            return sanitized.Length > 50 ? sanitized.Substring(0, 50) : sanitized;
        }

        private string DetectPythonPath(string configuredPath)
        {
            // 1. 首先尝试配置的路径
            if (!string.IsNullOrEmpty(configuredPath) && configuredPath != "python")
            {
                // 如果是相对路径，转换为绝对路径
                var resolvedPath = configuredPath;
                if (!Path.IsPathRooted(configuredPath))
                {
                    resolvedPath = _pathManager.ResolvePath(configuredPath);
                }
                
                _logger.LogInformation("检查配置的Python路径: {OriginalPath} → {ResolvedPath}", configuredPath, resolvedPath);
                
                if (File.Exists(resolvedPath))
                {
                    _logger.LogInformation("使用配置的Python路径: {Path}", resolvedPath);
                    return resolvedPath;
                }
                else
                {
                    _logger.LogWarning("配置的Python路径不存在: {Path}", resolvedPath);
                }
            }

            // 2. 尝试常见的Python路径
            var commonPaths = new[]
            {
                "python",
                "py",
                @"C:\Python310\python.exe",
                @"C:\Python311\python.exe",
                @"C:\Python312\python.exe",
                @"C:\Program Files\Python310\python.exe",
                @"C:\Program Files\Python311\python.exe",
                @"C:\Program Files\Python312\python.exe",
                @"C:\Users\Administrator\AppData\Local\Programs\Python\Python310\python.exe",
                @"C:\Users\Administrator\AppData\Local\Programs\Python\Python311\python.exe",
                @"C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe"
            };

            foreach (var path in commonPaths)
            {
                try
                {
                    if (path == "python" || path == "py")
                    {
                        // 测试命令行Python
                        var testProcess = new ProcessStartInfo
                        {
                            FileName = path,
                            Arguments = "--version",
                            UseShellExecute = false,
                            RedirectStandardOutput = true,
                            RedirectStandardError = true,
                            CreateNoWindow = true
                        };

                        using var process = Process.Start(testProcess);
                        if (process != null)
                        {
                            process.WaitForExit(5000); // 5秒超时
                            if (process.ExitCode == 0)
                            {
                                var output = process.StandardOutput.ReadToEnd();
                                _logger.LogInformation("检测到Python: {Path}, 版本: {Version}", path, output.Trim());
                                return path;
                            }
                        }
                    }
                    else if (File.Exists(path))
                    {
                        _logger.LogInformation("检测到Python文件: {Path}", path);
                        return path;
                    }
                }
                catch (Exception ex)
                {
                    _logger.LogDebug(ex, "测试Python路径失败: {Path}", path);
                }
            }

            // 3. 如果都找不到，返回原始配置
            _logger.LogWarning("未找到有效的Python路径，使用默认值: {Path}", configuredPath);
            return configuredPath;
        }



        public void Dispose()
        {
            _cancellationTokenSource?.Cancel();
            _channelWriter?.Complete();
            _processingLimiter?.Dispose();
            _cancellationTokenSource?.Dispose();
        }
    }

    // 辅助类
    internal class PythonResult
    {
        public bool Success { get; set; }
        public string Output { get; set; } = string.Empty;
        public int ExitCode { get; set; }
    }
}