using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Configuration;
using LmyDigitalHuman.Models;
using LmyDigitalHuman.Services.Interfaces;

namespace LmyDigitalHuman.Services
{
    /// <summary>
    /// 🚀 基于官方realtime_inference.py的真正实时多GPU MuseTalk服务
    /// 预处理avatar材料 + 4x RTX 4090并行推理 = 真正实时响应
    /// </summary>
    public class RealtimeMultiGpuMuseTalkService : IMuseTalkService
    {
        private readonly ILogger<RealtimeMultiGpuMuseTalkService> _logger;
        private readonly IConfiguration _configuration;
        private readonly IPathManager _pathManager;
        private readonly IPythonEnvironmentService _pythonEnvironmentService;
        
        // 🎯 GPU任务队列管理
        private readonly ConcurrentQueue<GpuTask>[] _gpuQueues;
        private readonly SemaphoreSlim[] _gpuSemaphores;
        private readonly Task[] _gpuWorkers;
        private readonly CancellationTokenSource _cancellationTokenSource;
        
        // 📊 Avatar预处理缓存
        private readonly ConcurrentDictionary<string, AvatarInfo> _avatarCache = new();
        
        // 📈 性能监控
        private long _totalRequests = 0;
        private long _completedRequests = 0;
        private readonly ConcurrentDictionary<int, GpuStats> _gpuStats = new();
        
        private const int GPU_COUNT = 4; // RTX 4090 x4
        
        public RealtimeMultiGpuMuseTalkService(
            ILogger<RealtimeMultiGpuMuseTalkService> logger,
            IConfiguration configuration,
            IPathManager pathManager,
            IPythonEnvironmentService pythonEnvironmentService)
        {
            _logger = logger;
            _configuration = configuration;
            _pathManager = pathManager;
            _pythonEnvironmentService = pythonEnvironmentService;
            
            // 初始化GPU队列和信号量
            _gpuQueues = new ConcurrentQueue<GpuTask>[GPU_COUNT];
            _gpuSemaphores = new SemaphoreSlim[GPU_COUNT];
            _gpuWorkers = new Task[GPU_COUNT];
            _cancellationTokenSource = new CancellationTokenSource();
            
            for (int i = 0; i < GPU_COUNT; i++)
            {
                _gpuQueues[i] = new ConcurrentQueue<GpuTask>();
                _gpuSemaphores[i] = new SemaphoreSlim(1, 1);
                _gpuStats[i] = new GpuStats { GpuId = i };
                
                // 启动GPU工作线程
                int gpuId = i;
                _gpuWorkers[i] = Task.Run(() => GpuWorkerLoop(gpuId, _cancellationTokenSource.Token));
            }
            
            _logger.LogInformation("🚀 实时多GPU MuseTalk服务已启动 - 4x RTX 4090 ready!");
            
            // 预热常用avatar
            _ = Task.Run(PrewarmAvatarsAsync);
        }
        
        /// <summary>
        /// Avatar信息缓存
        /// </summary>
        private class AvatarInfo
        {
            public string AvatarId { get; set; }
            public string VideoPath { get; set; }
            public bool IsPreprocessed { get; set; }
            public DateTime LastUsed { get; set; } = DateTime.Now;
        }
        
        /// <summary>
        /// GPU任务定义
        /// </summary>
        private class GpuTask
        {
            public DigitalHumanRequest Request { get; set; }
            public TaskCompletionSource<DigitalHumanResponse> CompletionSource { get; set; }
            public DateTime CreatedAt { get; set; } = DateTime.Now;
            public string AvatarId { get; set; }
        }
        
        /// <summary>
        /// GPU统计信息
        /// </summary>
        private class GpuStats
        {
            public int GpuId { get; set; }
            public long CompletedTasks { get; set; }
            public long TotalProcessingTime { get; set; }
            public DateTime LastTaskCompleted { get; set; }
            public bool IsBusy { get; set; }
        }
        
        /// <summary>
        /// 主要接口实现 - 实时响应
        /// </summary>
        public async Task<DigitalHumanResponse> ExecuteMuseTalkPythonAsync(DigitalHumanRequest request)
        {
            Interlocked.Increment(ref _totalRequests);
            
            // 🎯 获取avatar ID
            var avatarId = GetAvatarId(request.AvatarImagePath);
            
            // 🚀 确保avatar已预处理
            await EnsureAvatarPreprocessedAsync(avatarId, request.AvatarImagePath);
            
            // 📋 选择最空闲的GPU
            var selectedGpuId = SelectBestGpu();
            
            var task = new GpuTask
            {
                Request = request,
                CompletionSource = new TaskCompletionSource<DigitalHumanResponse>(),
                AvatarId = avatarId
            };
            
            _gpuQueues[selectedGpuId].Enqueue(task);
            _gpuSemaphores[selectedGpuId].Release();
            
            _logger.LogInformation("📋 实时任务已分配到GPU {GpuId}, Avatar: {AvatarId}", 
                selectedGpuId, avatarId);
            
            return await task.CompletionSource.Task;
        }
        
        /// <summary>
        /// 从avatar路径提取ID
        /// </summary>
        private string GetAvatarId(string avatarPath)
        {
            return Path.GetFileNameWithoutExtension(avatarPath);
        }
        
        /// <summary>
        /// 确保avatar已预处理
        /// </summary>
        private async Task EnsureAvatarPreprocessedAsync(string avatarId, string avatarPath)
        {
            if (_avatarCache.TryGetValue(avatarId, out var cachedInfo))
            {
                cachedInfo.LastUsed = DateTime.Now;
                if (cachedInfo.IsPreprocessed)
                {
                    return; // 已预处理，直接返回
                }
            }
            
            // 需要预处理
            _logger.LogInformation("🔄 预处理Avatar: {AvatarId}", avatarId);
            await PreprocessAvatarAsync(avatarId, avatarPath);
            
            _avatarCache.AddOrUpdate(avatarId, 
                new AvatarInfo 
                { 
                    AvatarId = avatarId, 
                    VideoPath = avatarPath, 
                    IsPreprocessed = true 
                },
                (key, existing) => 
                {
                    existing.IsPreprocessed = true;
                    existing.LastUsed = DateTime.Now;
                    return existing;
                });
        }
        
        /// <summary>
        /// 预处理Avatar材料
        /// </summary>
        private async Task PreprocessAvatarAsync(string avatarId, string avatarPath)
        {
            var stopwatch = Stopwatch.StartNew();
            
            try
            {
                var bestPythonPath = await _pythonEnvironmentService.GetRecommendedPythonPathAsync();
                
                // 创建预处理配置
                var configPath = CreatePreprocessConfig(avatarId, avatarPath);
                
                var arguments = BuildPreprocessArguments(configPath);
                
                var processInfo = new ProcessStartInfo
                {
                    FileName = bestPythonPath,
                    Arguments = arguments,
                    WorkingDirectory = Path.Combine(_pathManager.GetContentRootPath(), "..", "MuseTalk"),
                    UseShellExecute = false,
                    RedirectStandardOutput = true,
                    RedirectStandardError = true,
                    CreateNoWindow = true
                };
                
                // 使用GPU 0进行预处理
                ConfigureGpuEnvironment(processInfo, 0);
                
                var process = new Process { StartInfo = processInfo };
                var outputBuilder = new StringBuilder();
                var errorBuilder = new StringBuilder();
                
                process.OutputDataReceived += (sender, e) => {
                    if (!string.IsNullOrEmpty(e.Data))
                        outputBuilder.AppendLine(e.Data);
                };
                
                process.ErrorDataReceived += (sender, e) => {
                    if (!string.IsNullOrEmpty(e.Data))
                        errorBuilder.AppendLine(e.Data);
                };
                
                process.Start();
                process.BeginOutputReadLine();
                process.BeginErrorReadLine();
                
                var completed = await Task.Run(() => process.WaitForExit(300000)); // 5分钟超时
                
                if (!completed)
                {
                    process.Kill();
                    throw new TimeoutException($"Avatar {avatarId} 预处理超时");
                }
                
                if (process.ExitCode != 0)
                {
                    var error = errorBuilder.ToString();
                    throw new InvalidOperationException($"Avatar {avatarId} 预处理失败: {error}");
                }
                
                _logger.LogInformation("✅ Avatar {AvatarId} 预处理完成 - 耗时: {ElapsedMs}ms", 
                    avatarId, stopwatch.ElapsedMilliseconds);
                
                // 清理配置文件
                if (File.Exists(configPath))
                {
                    File.Delete(configPath);
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "❌ Avatar {AvatarId} 预处理失败", avatarId);
                throw;
            }
        }
        
        /// <summary>
        /// 创建预处理配置文件
        /// </summary>
        private string CreatePreprocessConfig(string avatarId, string avatarPath)
        {
            var configDir = Path.Combine(Path.GetTempPath(), "musetalk_preprocess");
            Directory.CreateDirectory(configDir);
            
            var configPath = Path.Combine(configDir, $"preprocess_{avatarId}_{DateTime.Now:yyyyMMdd_HHmmss}.yaml");
            
            var videoPath = avatarPath.Replace("\\", "/");
            
            var configContent = $@"{avatarId}:
 preparation: True
 video_path: ""{videoPath}""
 bbox_shift: 0
 audio_clips:
   dummy: ""dummy.wav""
";
            
            File.WriteAllText(configPath, configContent, Encoding.UTF8);
            return configPath;
        }
        
        /// <summary>
        /// 构建预处理参数
        /// </summary>
        private string BuildPreprocessArguments(string configPath)
        {
            var args = new StringBuilder();
            args.Append($"-m scripts.realtime_inference");
            args.Append($" --inference_config \"{configPath}\"");
            args.Append($" --version v1");
            args.Append($" --batch_size 20");
            args.Append($" --gpu_id 0");
            args.Append($" --skip_save_images"); // 预处理时跳过图像保存
            
            return args.ToString();
        }
        
        /// <summary>
        /// 智能GPU选择算法
        /// </summary>
        private int SelectBestGpu()
        {
            var minQueueLength = int.MaxValue;
            var bestGpu = 0;
            
            for (int i = 0; i < GPU_COUNT; i++)
            {
                var queueLength = _gpuQueues[i].Count;
                if (queueLength < minQueueLength)
                {
                    minQueueLength = queueLength;
                    bestGpu = i;
                }
            }
            
            return bestGpu;
        }
        
        /// <summary>
        /// GPU工作线程主循环
        /// </summary>
        private async Task GpuWorkerLoop(int gpuId, CancellationToken cancellationToken)
        {
            _logger.LogInformation("🎮 实时GPU {GpuId} 工作线程已启动", gpuId);
            
            while (!cancellationToken.IsCancellationRequested)
            {
                try
                {
                    await _gpuSemaphores[gpuId].WaitAsync(cancellationToken);
                    
                    if (_gpuQueues[gpuId].TryDequeue(out var task))
                    {
                        _gpuStats[gpuId].IsBusy = true;
                        var stopwatch = Stopwatch.StartNew();
                        
                        try
                        {
                            _logger.LogInformation("🚀 实时GPU {GpuId} 开始处理任务 - Avatar: {AvatarId}", 
                                gpuId, task.AvatarId);
                            
                            var result = await ExecuteRealtimeInferenceOnGpu(gpuId, task.Request, task.AvatarId);
                            
                            stopwatch.Stop();
                            
                            _gpuStats[gpuId].CompletedTasks++;
                            _gpuStats[gpuId].TotalProcessingTime += stopwatch.ElapsedMilliseconds;
                            _gpuStats[gpuId].LastTaskCompleted = DateTime.Now;
                            Interlocked.Increment(ref _completedRequests);
                            
                            task.CompletionSource.SetResult(result);
                            
                            _logger.LogInformation("⚡ 实时GPU {GpuId} 任务完成 - 耗时: {ElapsedMs}ms", 
                                gpuId, stopwatch.ElapsedMilliseconds);
                        }
                        catch (Exception ex)
                        {
                            _logger.LogError(ex, "❌ 实时GPU {GpuId} 任务执行失败", gpuId);
                            task.CompletionSource.SetResult(new DigitalHumanResponse
                            {
                                Success = false,
                                Message = $"实时GPU {gpuId} 执行失败: {ex.Message}"
                            });
                        }
                        finally
                        {
                            _gpuStats[gpuId].IsBusy = false;
                        }
                    }
                }
                catch (OperationCanceledException)
                {
                    break;
                }
                catch (Exception ex)
                {
                    _logger.LogError(ex, "❌ 实时GPU {GpuId} 工作线程异常", gpuId);
                }
            }
            
            _logger.LogInformation("🛑 实时GPU {GpuId} 工作线程已停止", gpuId);
        }
        
        /// <summary>
        /// 在指定GPU上执行实时推理
        /// </summary>
        private async Task<DigitalHumanResponse> ExecuteRealtimeInferenceOnGpu(int gpuId, DigitalHumanRequest request, string avatarId)
        {
            var stopwatch = Stopwatch.StartNew();
            string configPath = null;
            
            try
            {
                var outputPath = Path.Combine(_pathManager.GetContentRootPath(), "wwwroot", "videos", 
                    $"realtime_{DateTime.Now:yyyyMMdd_HHmmss}_{gpuId}_{avatarId}.mp4");
                
                configPath = CreateRealtimeInferenceConfig(avatarId, request.AudioPath);
                
                var bestPythonPath = await _pythonEnvironmentService.GetRecommendedPythonPathAsync();
                var arguments = BuildRealtimeInferenceArguments(configPath, gpuId);
                
                _logger.LogInformation("🎮 实时GPU {GpuId} 执行命令: {Arguments}", gpuId, arguments);
                
                var processInfo = new ProcessStartInfo
                {
                    FileName = bestPythonPath,
                    Arguments = arguments,
                    WorkingDirectory = Path.Combine(_pathManager.GetContentRootPath(), "..", "MuseTalk"),
                    UseShellExecute = false,
                    RedirectStandardOutput = true,
                    RedirectStandardError = true,
                    CreateNoWindow = true
                };
                
                ConfigureGpuEnvironment(processInfo, gpuId);
                
                var process = new Process { StartInfo = processInfo };
                var outputBuilder = new StringBuilder();
                var errorBuilder = new StringBuilder();
                
                process.OutputDataReceived += (sender, e) => {
                    if (!string.IsNullOrEmpty(e.Data))
                        outputBuilder.AppendLine(e.Data);
                };
                
                process.ErrorDataReceived += (sender, e) => {
                    if (!string.IsNullOrEmpty(e.Data))
                        errorBuilder.AppendLine(e.Data);
                };
                
                process.Start();
                process.BeginOutputReadLine();
                process.BeginErrorReadLine();
                
                // 🚀 实时推理超时设置 (更短)
                var timeoutMs = 60000; // 1分钟超时
                var completed = await Task.Run(() => process.WaitForExit(timeoutMs));
                
                if (!completed)
                {
                    process.Kill();
                    throw new TimeoutException($"实时GPU {gpuId} 推理超时 ({timeoutMs/1000}秒)");
                }
                
                var output = outputBuilder.ToString();
                var error = errorBuilder.ToString();
                
                if (process.ExitCode != 0)
                {
                    throw new InvalidOperationException($"实时GPU {gpuId} 推理失败: {error}");
                }
                
                // 查找生成的视频文件
                var videoPath = FindGeneratedVideo(avatarId);
                if (string.IsNullOrEmpty(videoPath))
                {
                    throw new FileNotFoundException($"实时GPU {gpuId} 未找到生成的视频文件");
                }
                
                var duration = GetAudioDuration(request.AudioPath);
                
                return new DigitalHumanResponse
                {
                    Success = true,
                    VideoPath = videoPath,
                    Duration = duration,
                    Message = $"⚡ 实时GPU {gpuId} 生成成功 (耗时: {stopwatch.ElapsedMilliseconds}ms)"
                };
            }
            finally
            {
                if (!string.IsNullOrEmpty(configPath) && File.Exists(configPath))
                {
                    try { File.Delete(configPath); } catch { }
                }
            }
        }
        
        /// <summary>
        /// 创建实时推理配置文件
        /// </summary>
        private string CreateRealtimeInferenceConfig(string avatarId, string audioPath)
        {
            var configDir = Path.Combine(Path.GetTempPath(), "musetalk_realtime");
            Directory.CreateDirectory(configDir);
            
            var configPath = Path.Combine(configDir, $"realtime_{avatarId}_{DateTime.Now:yyyyMMdd_HHmmss}_{Guid.NewGuid():N[..8]}.yaml");
            
            var audioPathFixed = audioPath.Replace("\\", "/");
            
            var configContent = $@"{avatarId}:
 preparation: False
 video_path: ""dummy""
 bbox_shift: 0
 audio_clips:
   output: ""{audioPathFixed}""
";
            
            File.WriteAllText(configPath, configContent, Encoding.UTF8);
            return configPath;
        }
        
        /// <summary>
        /// 构建实时推理参数
        /// </summary>
        private string BuildRealtimeInferenceArguments(string configPath, int gpuId)
        {
            var args = new StringBuilder();
            args.Append($"-m scripts.realtime_inference");
            args.Append($" --inference_config \"{configPath}\"");
            args.Append($" --version v1");
            args.Append($" --batch_size 20"); // 实时推理大批处理
            args.Append($" --gpu_id 0"); // 在CUDA_VISIBLE_DEVICES环境下总是0
            args.Append($" --fps 25");
            
            return args.ToString();
        }
        
        /// <summary>
        /// 配置GPU专用环境变量
        /// </summary>
        private void ConfigureGpuEnvironment(ProcessStartInfo processInfo, int gpuId)
        {
            processInfo.Environment["CUDA_VISIBLE_DEVICES"] = gpuId.ToString();
            processInfo.Environment["PYTORCH_CUDA_ALLOC_CONF"] = "max_split_size_mb:6144,expandable_segments:True";
            processInfo.Environment["OMP_NUM_THREADS"] = "8";
            processInfo.Environment["CUDA_LAUNCH_BLOCKING"] = "0";
            processInfo.Environment["TORCH_CUDNN_V8_API_ENABLED"] = "1";
            processInfo.Environment["TORCH_BACKENDS_CUDNN_BENCHMARK"] = "1";
            processInfo.Environment["TORCH_BACKENDS_CUDNN_DETERMINISTIC"] = "0";
            processInfo.Environment["TORCH_BACKENDS_CUDNN_ALLOW_TF32"] = "1";
            processInfo.Environment["TORCH_ALLOW_TF32_CUBLAS_OVERRIDE"] = "1";
            processInfo.Environment["TOKENIZERS_PARALLELISM"] = "false";
            processInfo.Environment["CUBLAS_WORKSPACE_CONFIG"] = ":16:8";
            processInfo.Environment["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID";
            processInfo.Environment["TORCH_CUDA_ARCH_LIST"] = "8.9";
            processInfo.Environment["TORCH_COMPILE"] = "1";
            processInfo.Environment["TORCH_CUDNN_SDPA_ENABLED"] = "1";
            processInfo.Environment["CUDA_MODULE_LOADING"] = "LAZY";
            
            _logger.LogInformation("🎮 实时GPU {GpuId} 环境配置完成", gpuId);
        }
        
        /// <summary>
        /// 查找生成的视频文件
        /// </summary>
        private string FindGeneratedVideo(string avatarId)
        {
            var resultsDir = Path.Combine(_pathManager.GetContentRootPath(), "..", "MuseTalk", "results", "avatars", avatarId, "vid_output");
            
            if (!Directory.Exists(resultsDir))
                return null;
            
            var files = Directory.GetFiles(resultsDir, "*.mp4")
                .Where(f => File.GetLastWriteTime(f) > DateTime.Now.AddMinutes(-5))
                .OrderByDescending(f => File.GetLastWriteTime(f))
                .ToList();
            
            if (files.Count > 0)
            {
                // 复制到Web可访问目录
                var webVideoPath = Path.Combine(_pathManager.GetContentRootPath(), "wwwroot", "videos", Path.GetFileName(files[0]));
                File.Copy(files[0], webVideoPath, true);
                return webVideoPath;
            }
            
            return null;
        }
        
        /// <summary>
        /// 预热常用avatars
        /// </summary>
        private async Task PrewarmAvatarsAsync()
        {
            try
            {
                var templatesDir = Path.Combine(_pathManager.GetContentRootPath(), "wwwroot", "templates");
                if (!Directory.Exists(templatesDir))
                    return;
                
                var avatarFiles = Directory.GetFiles(templatesDir, "*.jpg")
                    .Concat(Directory.GetFiles(templatesDir, "*.png"))
                    .Take(3) // 预热前3个avatar
                    .ToList();
                
                foreach (var avatarFile in avatarFiles)
                {
                    var avatarId = Path.GetFileNameWithoutExtension(avatarFile);
                    _logger.LogInformation("🔥 预热Avatar: {AvatarId}", avatarId);
                    
                    try
                    {
                        await PreprocessAvatarAsync(avatarId, avatarFile);
                        _avatarCache.TryAdd(avatarId, new AvatarInfo
                        {
                            AvatarId = avatarId,
                            VideoPath = avatarFile,
                            IsPreprocessed = true
                        });
                    }
                    catch (Exception ex)
                    {
                        _logger.LogWarning(ex, "预热Avatar失败: {AvatarId}", avatarId);
                    }
                }
                
                _logger.LogInformation("🔥 Avatar预热完成，已预热 {Count} 个avatar", avatarFiles.Count);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Avatar预热过程出错");
            }
        }
        
        /// <summary>
        /// 获取音频时长
        /// </summary>
        private double GetAudioDuration(string audioPath)
        {
            return 3.0; // 默认3秒，实际应该使用FFmpeg
        }
        
        /// <summary>
        /// 获取性能统计
        /// </summary>
        public string GetPerformanceStats()
        {
            var stats = new StringBuilder();
            stats.AppendLine("⚡ 实时多GPU MuseTalk 性能统计:");
            stats.AppendLine($"总请求: {_totalRequests}, 已完成: {_completedRequests}");
            stats.AppendLine($"预处理Avatar数量: {_avatarCache.Count}");
            
            for (int i = 0; i < GPU_COUNT; i++)
            {
                var gpu = _gpuStats[i];
                var avgTime = gpu.CompletedTasks > 0 ? gpu.TotalProcessingTime / gpu.CompletedTasks : 0;
                stats.AppendLine($"实时GPU {i}: 完成 {gpu.CompletedTasks} 任务, 平均耗时 {avgTime}ms, 状态: {(gpu.IsBusy ? "忙碌" : "空闲")}");
            }
            
            return stats.ToString();
        }
        
        public void Dispose()
        {
            _cancellationTokenSource.Cancel();
            Task.WaitAll(_gpuWorkers, TimeSpan.FromSeconds(10));
            
            for (int i = 0; i < GPU_COUNT; i++)
            {
                _gpuSemaphores[i]?.Dispose();
            }
            
            _cancellationTokenSource.Dispose();
        }
    }
}