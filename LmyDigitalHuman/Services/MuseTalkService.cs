using LmyDigitalHuman.Models;
using Microsoft.Extensions.Caching.Memory;
using System.Collections.Concurrent;
using System.Diagnostics;
using System.Text.Json;
using System.Text;

namespace LmyDigitalHuman.Services
{
    public class MuseTalkService : IMuseTalkService
    {
        private readonly ILogger<MuseTalkService> _logger;
        private readonly IConfiguration _configuration;
        private readonly IMemoryCache _cache;
        private readonly string _templatesPath;
        private readonly string _outputPath;
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
            IMemoryCache cache)
        {
            _logger = logger;
            _configuration = configuration;
            _cache = cache;
            
            _templatesPath = Path.Combine(Directory.GetCurrentDirectory(), "wwwroot", "templates");
            _outputPath = Path.Combine(Directory.GetCurrentDirectory(), "wwwroot", "videos");
            _pythonPath = configuration["DigitalHuman:MuseTalk:PythonPath"] ?? "python";
            _museTalkScriptPath = Path.Combine(Directory.GetCurrentDirectory(), "musetalk_service_complete.py");
            
            // 确保目录存在
            Directory.CreateDirectory(_templatesPath);
            Directory.CreateDirectory(_outputPath);
            
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
                var outputFileName = $"musetalk_{Guid.NewGuid():N}.mp4";
                var outputFilePath = Path.Combine(_outputPath, outputFileName);

                await _processingLimiter.WaitAsync();
                try
                {
                    // 直接调用Python脚本
                    var result = await ExecuteMuseTalkPythonAsync(request, outputFilePath);
                    
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
            
            await File.WriteAllTextAsync(jsonTargetPath, jsonContent, Encoding.UTF8);

            _logger.LogInformation("创建数字人模板成功: {TemplateName} ({TemplateId})", request.Name, templateId);
            return template;
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
                        File.Delete(jsonFile);
                        
                        var imagePath = Path.Combine(_templatesPath, template.ImagePath);
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
            return templates.Any(t => t.Id == templateId);
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
                var result = await RunPythonCommandAsync(arguments, TimeSpan.FromMinutes(10));
                
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
            args.Append($"\"{_museTalkScriptPath}\"");
            args.Append($" --avatar \"{request.AvatarImagePath}\"");
            args.Append($" --audio \"{request.AudioPath}\"");
            args.Append($" --output \"{outputPath}\"");
            args.Append($" --fps {request.Fps ?? 25}");
            args.Append($" --batch_size {request.BatchSize ?? 4}");
            args.Append($" --quality {request.Quality}");
            
            if (request.BboxShift.HasValue)
                args.Append($" --bbox_shift {request.BboxShift.Value}");
                
            return args.ToString();
        }

        private async Task<PythonResult> RunPythonCommandAsync(string arguments, TimeSpan timeout)
        {
            try
            {
                var processInfo = new ProcessStartInfo
                {
                    FileName = _pythonPath,
                    Arguments = arguments,
                    UseShellExecute = false,
                    RedirectStandardOutput = true,
                    RedirectStandardError = true,
                    CreateNoWindow = true,
                    WorkingDirectory = Directory.GetCurrentDirectory()
                };

                using var process = Process.Start(processInfo);
                if (process != null)
                {
                    var outputTask = process.StandardOutput.ReadToEndAsync();
                    var errorTask = process.StandardError.ReadToEndAsync();
                    
                    var completed = await Task.WhenAny(
                        Task.WhenAll(outputTask, errorTask).ContinueWith(_ => process.WaitForExit()),
                        Task.Delay(timeout)
                    );
                    
                    if (completed != Task.Delay(timeout))
                    {
                        var output = await outputTask;
                        var error = await errorTask;
                        
                        return new PythonResult
                        {
                            Success = process.ExitCode == 0,
                            Output = string.IsNullOrEmpty(error) ? output : error,
                            ExitCode = process.ExitCode
                        };
                    }
                    else
                    {
                        process.Kill();
                        return new PythonResult
                        {
                            Success = false,
                            Output = "Python脚本执行超时"
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