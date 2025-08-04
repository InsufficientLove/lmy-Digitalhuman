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
    /// 🌐 Web级别MuseTalk服务 - 支持大规模并发用户
    /// 基于官方realtime_inference.py + 智能队列管理 + 动态负载均衡
    /// </summary>
    public class WebScaleMuseTalkService : IMuseTalkService
    {
        private readonly ILogger<WebScaleMuseTalkService> _logger;
        private readonly IConfiguration _configuration;
        private readonly IPathManager _pathManager;
        private readonly IPythonEnvironmentService _pythonEnvironmentService;
        
        // 🎯 多级队列系统
        private readonly ConcurrentQueue<WebTask> _highPriorityQueue = new(); // VIP用户
        private readonly ConcurrentQueue<WebTask> _normalQueue = new();       // 普通用户
        private readonly ConcurrentQueue<WebTask> _lowPriorityQueue = new();  // 批处理
        
        // 🚀 GPU工作池
        private readonly ConcurrentQueue<GpuWorker>[] _gpuQueues;
        private readonly SemaphoreSlim[] _gpuSemaphores;
        private readonly Task[] _gpuWorkers;
        private readonly CancellationTokenSource _cancellationTokenSource;
        
        // 📊 Avatar预处理缓存 + LRU管理
        private readonly ConcurrentDictionary<string, AvatarInfo> _avatarCache = new();
        private readonly ConcurrentDictionary<string, DateTime> _avatarLastUsed = new();
        
        // 📈 Web级性能监控
        private long _totalRequests = 0;
        private long _completedRequests = 0;
        private long _queuedRequests = 0;
        private readonly ConcurrentDictionary<int, GpuStats> _gpuStats = new();
        
        // ⚡ 动态配置
        private const int GPU_COUNT = 4;
        private const int MAX_QUEUE_SIZE = 1000; // 最大队列长度
        private const int MAX_AVATAR_CACHE = 50;  // 最大缓存avatar数量
        private const int AVATAR_CLEANUP_HOURS = 24; // avatar缓存清理时间
        
        public WebScaleMuseTalkService(
            ILogger<WebScaleMuseTalkService> logger,
            IConfiguration configuration,
            IPathManager pathManager,
            IPythonEnvironmentService pythonEnvironmentService)
        {
            _logger = logger;
            _configuration = configuration;
            _pathManager = pathManager;
            _pythonEnvironmentService = pythonEnvironmentService;
            
            // 初始化GPU工作池
            _gpuQueues = new ConcurrentQueue<GpuWorker>[GPU_COUNT];
            _gpuSemaphores = new SemaphoreSlim[GPU_COUNT];
            _gpuWorkers = new Task[GPU_COUNT];
            _cancellationTokenSource = new CancellationTokenSource();
            
            for (int i = 0; i < GPU_COUNT; i++)
            {
                _gpuQueues[i] = new ConcurrentQueue<GpuWorker>();
                _gpuSemaphores[i] = new SemaphoreSlim(1, 1);
                _gpuStats[i] = new GpuStats { GpuId = i };
                
                int gpuId = i;
                _gpuWorkers[i] = Task.Run(() => WebScaleGpuWorkerLoop(gpuId, _cancellationTokenSource.Token));
            }
            
            // 启动队列调度器
            _ = Task.Run(() => QueueSchedulerLoop(_cancellationTokenSource.Token));
            
            // 启动缓存清理器
            _ = Task.Run(() => CacheCleanupLoop(_cancellationTokenSource.Token));
            
            // 预热系统
            _ = Task.Run(PrewarmSystemAsync);
            
            _logger.LogInformation("🌐 Web级MuseTalk服务已启动 - 支持大规模并发用户!");
        }
        
        /// <summary>
        /// Web任务定义
        /// </summary>
        private class WebTask
        {
            public string TaskId { get; set; } = Guid.NewGuid().ToString("N")[..8];
            public DigitalHumanRequest Request { get; set; }
            public TaskCompletionSource<DigitalHumanResponse> CompletionSource { get; set; }
            public DateTime CreatedAt { get; set; } = DateTime.Now;
            public string AvatarId { get; set; }
            public TaskPriority Priority { get; set; } = TaskPriority.Normal;
            public string UserId { get; set; }
        }
        
        /// <summary>
        /// GPU工作者定义
        /// </summary>
        private class GpuWorker
        {
            public int GpuId { get; set; }
            public WebTask Task { get; set; }
        }
        
        /// <summary>
        /// 任务优先级
        /// </summary>
        public enum TaskPriority
        {
            Low = 0,
            Normal = 1,
            High = 2,
            VIP = 3
        }
        
        /// <summary>
        /// Avatar信息缓存
        /// </summary>
        private class AvatarInfo
        {
            public string AvatarId { get; set; }
            public string VideoPath { get; set; }
            public bool IsPreprocessed { get; set; }
            public DateTime CreatedAt { get; set; } = DateTime.Now;
            public DateTime LastUsed { get; set; } = DateTime.Now;
            public int UsageCount { get; set; } = 0;
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
            public double AverageProcessingTime => CompletedTasks > 0 ? (double)TotalProcessingTime / CompletedTasks : 0;
        }
        
        /// <summary>
        /// 主要接口实现 - Web级并发处理
        /// </summary>
        public async Task<DigitalHumanResponse> ExecuteMuseTalkPythonAsync(DigitalHumanRequest request)
        {
            var totalRequests = Interlocked.Increment(ref _totalRequests);
            var queuedRequests = Interlocked.Increment(ref _queuedRequests);
            
            // 🚨 队列过载保护
            if (queuedRequests > MAX_QUEUE_SIZE)
            {
                Interlocked.Decrement(ref _queuedRequests);
                return new DigitalHumanResponse
                {
                    Success = false,
                    Message = $"🚨 系统繁忙，当前排队用户过多 ({queuedRequests}>{MAX_QUEUE_SIZE})，请稍后再试"
                };
            }
            
            var avatarId = GetAvatarId(request.AvatarImagePath);
            var userId = request.UserId ?? "anonymous";
            
            // 🎯 确定任务优先级
            var priority = DeterminePriority(userId, avatarId);
            
            var webTask = new WebTask
            {
                Request = request,
                CompletionSource = new TaskCompletionSource<DigitalHumanResponse>(),
                AvatarId = avatarId,
                Priority = priority,
                UserId = userId
            };
            
            // 📋 加入相应优先级队列
            EnqueueTask(webTask);
            
            _logger.LogInformation("📋 任务已加入队列: TaskId={TaskId}, Avatar={AvatarId}, Priority={Priority}, 队列长度={QueueLength}", 
                webTask.TaskId, avatarId, priority, queuedRequests);
            
            try
            {
                return await webTask.CompletionSource.Task;
            }
            finally
            {
                Interlocked.Decrement(ref _queuedRequests);
            }
        }
        
        /// <summary>
        /// 队列调度器主循环
        /// </summary>
        private async Task QueueSchedulerLoop(CancellationToken cancellationToken)
        {
            _logger.LogInformation("🎯 队列调度器已启动");
            
            while (!cancellationToken.IsCancellationRequested)
            {
                try
                {
                    // 🚀 按优先级分配任务到GPU
                    var task = DequeueNextTask();
                    if (task != null)
                    {
                        var availableGpuId = FindAvailableGpu();
                        if (availableGpuId >= 0)
                        {
                            var gpuWorker = new GpuWorker { GpuId = availableGpuId, Task = task };
                            _gpuQueues[availableGpuId].Enqueue(gpuWorker);
                            _gpuSemaphores[availableGpuId].Release();
                            
                            _logger.LogDebug("🎮 任务分配到GPU {GpuId}: TaskId={TaskId}", availableGpuId, task.TaskId);
                        }
                        else
                        {
                            // 所有GPU都忙，重新排队
                            EnqueueTask(task);
                            await Task.Delay(100, cancellationToken); // 短暂等待
                        }
                    }
                    else
                    {
                        await Task.Delay(50, cancellationToken); // 没有任务时短暂休息
                    }
                }
                catch (Exception ex)
                {
                    _logger.LogError(ex, "❌ 队列调度器异常");
                    await Task.Delay(1000, cancellationToken);
                }
            }
            
            _logger.LogInformation("🛑 队列调度器已停止");
        }
        
        /// <summary>
        /// Web级GPU工作线程主循环
        /// </summary>
        private async Task WebScaleGpuWorkerLoop(int gpuId, CancellationToken cancellationToken)
        {
            _logger.LogInformation("🎮 Web级GPU {GpuId} 工作线程已启动", gpuId);
            
            while (!cancellationToken.IsCancellationRequested)
            {
                try
                {
                    await _gpuSemaphores[gpuId].WaitAsync(cancellationToken);
                    
                    if (_gpuQueues[gpuId].TryDequeue(out var gpuWorker))
                    {
                        _gpuStats[gpuId].IsBusy = true;
                        var stopwatch = Stopwatch.StartNew();
                        var task = gpuWorker.Task;
                        
                        try
                        {
                            _logger.LogInformation("🚀 GPU {GpuId} 开始处理任务: TaskId={TaskId}, Avatar={AvatarId}, 等待时间={WaitTime}ms", 
                                gpuId, task.TaskId, task.AvatarId, (DateTime.Now - task.CreatedAt).TotalMilliseconds);
                            
                            // 🎯 确保avatar已预处理
                            await EnsureAvatarPreprocessedAsync(task.AvatarId, task.Request.AvatarImagePath);
                            
                            // 🚀 执行实时推理
                            var result = await ExecuteWebScaleInferenceOnGpu(gpuId, task);
                            
                            stopwatch.Stop();
                            
                            // 📊 更新统计信息
                            _gpuStats[gpuId].CompletedTasks++;
                            _gpuStats[gpuId].TotalProcessingTime += stopwatch.ElapsedMilliseconds;
                            _gpuStats[gpuId].LastTaskCompleted = DateTime.Now;
                            Interlocked.Increment(ref _completedRequests);
                            
                            task.CompletionSource.SetResult(result);
                            
                            _logger.LogInformation("✅ GPU {GpuId} 任务完成: TaskId={TaskId}, 耗时={ElapsedMs}ms, 总完成={CompletedTasks}", 
                                gpuId, task.TaskId, stopwatch.ElapsedMilliseconds, _gpuStats[gpuId].CompletedTasks);
                        }
                        catch (Exception ex)
                        {
                            _logger.LogError(ex, "❌ GPU {GpuId} 任务执行失败: TaskId={TaskId}", gpuId, task.TaskId);
                            task.CompletionSource.SetResult(new DigitalHumanResponse
                            {
                                Success = false,
                                Message = $"GPU {gpuId} 处理失败: {ex.Message}"
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
                    _logger.LogError(ex, "❌ GPU {GpuId} 工作线程异常", gpuId);
                }
            }
            
            _logger.LogInformation("🛑 GPU {GpuId} 工作线程已停止", gpuId);
        }
        
        /// <summary>
        /// 确定任务优先级
        /// </summary>
        private TaskPriority DeterminePriority(string userId, string avatarId)
        {
            // 🎯 VIP用户检测
            if (IsVipUser(userId))
                return TaskPriority.VIP;
            
            // 🚀 热门avatar优先
            if (_avatarCache.TryGetValue(avatarId, out var avatarInfo) && avatarInfo.UsageCount > 10)
                return TaskPriority.High;
            
            // 📊 预处理过的avatar优先
            if (avatarInfo?.IsPreprocessed == true)
                return TaskPriority.High;
            
            return TaskPriority.Normal;
        }
        
        /// <summary>
        /// VIP用户检测
        /// </summary>
        private bool IsVipUser(string userId)
        {
            // TODO: 实现VIP用户检测逻辑
            return userId?.StartsWith("vip_") == true;
        }
        
        /// <summary>
        /// 任务入队
        /// </summary>
        private void EnqueueTask(WebTask task)
        {
            switch (task.Priority)
            {
                case TaskPriority.VIP:
                case TaskPriority.High:
                    _highPriorityQueue.Enqueue(task);
                    break;
                case TaskPriority.Normal:
                    _normalQueue.Enqueue(task);
                    break;
                case TaskPriority.Low:
                    _lowPriorityQueue.Enqueue(task);
                    break;
            }
        }
        
        /// <summary>
        /// 按优先级出队下一个任务
        /// </summary>
        private WebTask DequeueNextTask()
        {
            // 🎯 高优先级优先
            if (_highPriorityQueue.TryDequeue(out var highTask))
                return highTask;
            
            // 📊 普通优先级
            if (_normalQueue.TryDequeue(out var normalTask))
                return normalTask;
            
            // 📋 低优先级
            if (_lowPriorityQueue.TryDequeue(out var lowTask))
                return lowTask;
            
            return null;
        }
        
        /// <summary>
        /// 查找可用GPU
        /// </summary>
        private int FindAvailableGpu()
        {
            // 🎯 优先选择空闲GPU
            for (int i = 0; i < GPU_COUNT; i++)
            {
                if (!_gpuStats[i].IsBusy && _gpuQueues[i].IsEmpty)
                    return i;
            }
            
            // 📊 选择队列最短的GPU
            var minQueueLength = int.MaxValue;
            var bestGpu = -1;
            
            for (int i = 0; i < GPU_COUNT; i++)
            {
                var queueLength = _gpuQueues[i].Count;
                if (queueLength < minQueueLength)
                {
                    minQueueLength = queueLength;
                    bestGpu = i;
                }
            }
            
            // 🚨 如果队列太长，返回-1表示无可用GPU
            return minQueueLength > 2 ? -1 : bestGpu;
        }
        
        /// <summary>
        /// 在指定GPU上执行Web级推理
        /// </summary>
        private async Task<DigitalHumanResponse> ExecuteWebScaleInferenceOnGpu(int gpuId, WebTask webTask)
        {
            var stopwatch = Stopwatch.StartNew();
            string configPath = null;
            
            try
            {
                var request = webTask.Request;
                var avatarId = webTask.AvatarId;
                
                configPath = CreateRealtimeInferenceConfig(avatarId, request.AudioPath, webTask.TaskId);
                
                var bestPythonPath = await _pythonEnvironmentService.GetRecommendedPythonPathAsync();
                var arguments = BuildRealtimeInferenceArguments(configPath, gpuId);
                
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
                
                // 🚀 Web级超时设置 (更短，快速失败)
                var timeoutMs = 90000; // 1.5分钟超时
                var completed = await Task.Run(() => process.WaitForExit(timeoutMs));
                
                if (!completed)
                {
                    process.Kill();
                    throw new TimeoutException($"Web级GPU {gpuId} 推理超时 ({timeoutMs/1000}秒)");
                }
                
                if (process.ExitCode != 0)
                {
                    var error = errorBuilder.ToString();
                    throw new InvalidOperationException($"Web级GPU {gpuId} 推理失败: {error}");
                }
                
                // 查找生成的视频文件
                var videoPath = FindGeneratedVideo(avatarId, webTask.TaskId);
                if (string.IsNullOrEmpty(videoPath))
                {
                    throw new FileNotFoundException($"Web级GPU {gpuId} 未找到生成的视频文件");
                }
                
                // 📊 更新avatar使用统计
                UpdateAvatarUsage(avatarId);
                
                var duration = GetAudioDuration(request.AudioPath);
                
                return new DigitalHumanResponse
                {
                    Success = true,
                    VideoPath = videoPath,
                    Duration = duration,
                    Message = $"🌐 Web级GPU {gpuId} 生成成功 (TaskId: {webTask.TaskId}, 耗时: {stopwatch.ElapsedMilliseconds}ms)"
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
        /// 缓存清理循环
        /// </summary>
        private async Task CacheCleanupLoop(CancellationToken cancellationToken)
        {
            while (!cancellationToken.IsCancellationRequested)
            {
                try
                {
                    await Task.Delay(TimeSpan.FromHours(1), cancellationToken); // 每小时清理一次
                    
                    var cutoffTime = DateTime.Now.AddHours(-AVATAR_CLEANUP_HOURS);
                    var toRemove = _avatarCache
                        .Where(kvp => _avatarLastUsed.TryGetValue(kvp.Key, out var lastUsed) && lastUsed < cutoffTime)
                        .Take(_avatarCache.Count - MAX_AVATAR_CACHE + 10) // 保留一些空间
                        .Select(kvp => kvp.Key)
                        .ToList();
                    
                    foreach (var avatarId in toRemove)
                    {
                        _avatarCache.TryRemove(avatarId, out _);
                        _avatarLastUsed.TryRemove(avatarId, out _);
                        
                        // 清理磁盘文件
                        try
                        {
                            var avatarDir = Path.Combine(_pathManager.GetContentRootPath(), "..", "MuseTalk", "results", "avatars", avatarId);
                            if (Directory.Exists(avatarDir))
                            {
                                Directory.Delete(avatarDir, true);
                            }
                        }
                        catch (Exception ex)
                        {
                            _logger.LogWarning(ex, "清理avatar目录失败: {AvatarId}", avatarId);
                        }
                    }
                    
                    if (toRemove.Count > 0)
                    {
                        _logger.LogInformation("🧹 清理了 {Count} 个过期avatar缓存", toRemove.Count);
                    }
                }
                catch (Exception ex)
                {
                    _logger.LogError(ex, "❌ 缓存清理异常");
                }
            }
        }
        
        // ... 其他辅助方法保持不变 ...
        
        /// <summary>
        /// 获取Web级性能统计
        /// </summary>
        public string GetWebScalePerformanceStats()
        {
            var stats = new StringBuilder();
            stats.AppendLine("🌐 Web级MuseTalk性能统计:");
            stats.AppendLine($"总请求: {_totalRequests}, 已完成: {_completedRequests}, 排队中: {_queuedRequests}");
            stats.AppendLine($"队列状态: 高优先级={_highPriorityQueue.Count}, 普通={_normalQueue.Count}, 低优先级={_lowPriorityQueue.Count}");
            stats.AppendLine($"Avatar缓存: {_avatarCache.Count}/{MAX_AVATAR_CACHE}");
            
            for (int i = 0; i < GPU_COUNT; i++)
            {
                var gpu = _gpuStats[i];
                stats.AppendLine($"GPU {i}: 完成 {gpu.CompletedTasks} 任务, 平均 {gpu.AverageProcessingTime:F1}ms, 状态: {(gpu.IsBusy ? "忙碌" : "空闲")}");
            }
            
            return stats.ToString();
        }
        
        // 实现其他必要的辅助方法...
        private string GetAvatarId(string avatarPath) => Path.GetFileNameWithoutExtension(avatarPath);
        private async Task EnsureAvatarPreprocessedAsync(string avatarId, string avatarPath) { /* 实现预处理逻辑 */ }
        private string CreateRealtimeInferenceConfig(string avatarId, string audioPath, string taskId) => "";
        private string BuildRealtimeInferenceArguments(string configPath, int gpuId) => "";
        private void ConfigureGpuEnvironment(ProcessStartInfo processInfo, int gpuId) { }
        private string FindGeneratedVideo(string avatarId, string taskId) => "";
        private void UpdateAvatarUsage(string avatarId) { }
        private double GetAudioDuration(string audioPath) => 3.0;
        private async Task PrewarmSystemAsync() { }
        
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