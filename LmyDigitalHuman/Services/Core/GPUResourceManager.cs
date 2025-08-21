using System.Collections.Concurrent;
using LmyDigitalHuman.Services;
using System.Diagnostics;

namespace LmyDigitalHuman.Services.Core
{
    public class GPUResourceManager : IGPUResourceManager
    {
        private readonly ILogger<GPUResourceManager> _logger;
        private readonly ConcurrentDictionary<int, GPUResource> _gpuResources;
        private readonly Timer _monitoringTimer;
        private readonly SemaphoreSlim _allocationLock;

        public GPUResourceManager(ILogger<GPUResourceManager> logger)
        {
            _logger = logger;
            _gpuResources = new ConcurrentDictionary<int, GPUResource>();
            _allocationLock = new SemaphoreSlim(1, 1);
            
            InitializeGPUResources();
            _monitoringTimer = new Timer(UpdateGPUMetrics, null, TimeSpan.Zero, TimeSpan.FromSeconds(5));
        }

        private void InitializeGPUResources()
        {
            _gpuResources[0] = new GPUResource
            {
                Id = 0,
                Name = "RTX4090-0",
                TotalMemoryMB = 24576,
                PrimaryWorkload = Services.GPUWorkloadType.MuseTalk,
                MaxConcurrentTasks = 4,
                Description = "MuseTalk视频生成专用"
            };

            _gpuResources[1] = new GPUResource
            {
                Id = 1,
                Name = "RTX4090-1", 
                TotalMemoryMB = 24576,
                PrimaryWorkload = Services.GPUWorkloadType.General,
                MaxConcurrentTasks = 8,
                Description = "LLM推理专用"
            };

            _gpuResources[2] = new GPUResource
            {
                Id = 2,
                Name = "RTX4090-2",
                TotalMemoryMB = 24576,
                PrimaryWorkload = Services.GPUWorkloadType.Whisper,
                MaxConcurrentTasks = 12,
                Description = "TTS合成 + 语音识别"
            };

            _gpuResources[3] = new GPUResource
            {
                Id = 3,
                Name = "RTX4090-3",
                TotalMemoryMB = 24576,
                PrimaryWorkload = Services.GPUWorkloadType.General,
                MaxConcurrentTasks = 6,
                Description = "视频后处理 + 缓存预热"
            };

            _logger.LogInformation("初始化4张RTX4090 GPU资源完成");
        }

        // 实现IGPUResourceManager.AllocateGPUAsync接口方法
        public async Task<int> AllocateGPUAsync(int preferredGpu, Services.GPUWorkloadType workloadType)
        {
            if (preferredGpu >= 0 && _gpuResources.TryGetValue(preferredGpu, out var preferredGpuResource))
            {
                if (preferredGpuResource.CurrentTasks < preferredGpuResource.MaxConcurrentTasks)
                {
                    await _allocationLock.WaitAsync();
                    try
                    {
                        preferredGpuResource.CurrentTasks++;
                        preferredGpuResource.LastAllocatedTime = DateTime.UtcNow;
                        _logger.LogDebug($"分配指定GPU {preferredGpu} 用于 {workloadType}");
                        return preferredGpu;
                    }
                    finally
                    {
                        _allocationLock.Release();
                    }
                }
            }
            
            return await AllocateGPUAsync(workloadType);
        }

        private async Task<int> AllocateGPUAsync(Services.GPUWorkloadType workloadType)
        {
            await _allocationLock.WaitAsync();
            try
            {
                var primaryGpu = _gpuResources.Values.FirstOrDefault(g => g.PrimaryWorkload == workloadType);
                if (primaryGpu != null && primaryGpu.CurrentTasks < primaryGpu.MaxConcurrentTasks)
                {
                    primaryGpu.CurrentTasks++;
                    primaryGpu.LastAllocatedTime = DateTime.UtcNow;
                    _logger.LogDebug($"分配主要GPU {primaryGpu.Id} 用于 {workloadType}");
                    return primaryGpu.Id;
                }

                var availableGpu = _gpuResources.Values
                    .Where(g => g.CurrentTasks < g.MaxConcurrentTasks)
                    .OrderBy(g => g.GetLoadPercentage())
                    .FirstOrDefault();

                if (availableGpu != null)
                {
                    availableGpu.CurrentTasks++;
                    availableGpu.LastAllocatedTime = DateTime.UtcNow;
                    _logger.LogDebug($"分配备用GPU {availableGpu.Id} 用于 {workloadType}");
                    return availableGpu.Id;
                }

                _logger.LogWarning($"所有GPU都已满载，无法分配GPU用于 {workloadType}");
                throw new InvalidOperationException("所有GPU都已满载");
            }
            finally
            {
                _allocationLock.Release();
            }
        }

        // 实现IGPUResourceManager.ReleaseGPUAsync接口方法
        public async Task ReleaseGPUAsync(int gpuId, Services.GPUWorkloadType workloadType)
        {
            await _allocationLock.WaitAsync();
            try
            {
                if (_gpuResources.TryGetValue(gpuId, out var gpu))
                {
                    gpu.CurrentTasks = Math.Max(0, gpu.CurrentTasks - 1);
                    gpu.LastReleasedTime = DateTime.UtcNow;
                    _logger.LogDebug($"释放GPU {gpuId}，当前任务数: {gpu.CurrentTasks}");
                }
            }
            finally
            {
                _allocationLock.Release();
            }
        }

        public async Task<GPUInfo> GetGPUInfoAsync()
        {
            var gpuInfo = new GPUInfo
            {
                Count = _gpuResources.Count,
                Devices = _gpuResources.Values.Select(gpu => new GPUDevice
                {
                    Index = gpu.Id,
                    Name = gpu.Name,
                    TotalMemory = gpu.TotalMemoryMB * 1024L * 1024L,
                    UsedMemory = gpu.MemoryUsedMB * 1024L * 1024L,
                    FreeMemory = (gpu.TotalMemoryMB - gpu.MemoryUsedMB) * 1024L * 1024L,
                    Utilization = gpu.GetLoadPercentage()
                }).ToList()
            };
            return await Task.FromResult(gpuInfo);
        }

        public async Task<bool> CheckGPUAvailabilityAsync()
        {
            return await Task.FromResult(_gpuResources.Count > 0);
        }

        public async Task<int> GetAvailableGPUCountAsync()
        {
            return await Task.FromResult(_gpuResources.Count);
        }

        public async Task<long> GetAvailableGPUMemoryAsync(int gpuIndex = 0)
        {
            if (_gpuResources.TryGetValue(gpuIndex, out var gpu))
            {
                return await Task.FromResult((gpu.TotalMemoryMB - gpu.MemoryUsedMB) * 1024L * 1024L);
            }
            return 0;
        }

        public async Task<double> GetGPUUtilizationAsync(int gpuIndex = 0)
        {
            if (_gpuResources.TryGetValue(gpuIndex, out var gpu))
            {
                return await Task.FromResult(gpu.GetLoadPercentage());
            }
            return 0;
        }

        public async Task<GPUStatus[]> GetGPUStatusAsync()
        {
            return await Task.FromResult(_gpuResources.Values.Select(gpu => new GPUStatus
            {
                Id = gpu.Id,
                Name = gpu.Name,
                LoadPercentage = gpu.GetLoadPercentage(),
                MemoryUsedMB = gpu.MemoryUsedMB,
                MemoryTotalMB = gpu.TotalMemoryMB,
                CurrentTasks = gpu.CurrentTasks,
                MaxTasks = gpu.MaxConcurrentTasks,
                PrimaryWorkload = gpu.PrimaryWorkload,
                Temperature = gpu.Temperature,
                PowerUsage = gpu.PowerUsage,
                IsHealthy = gpu.IsHealthy
            }).ToArray());
        }

        public async Task<GPUResourceInfo> GetOptimalGPUAsync(Services.GPUWorkloadType workloadType)
        {
            var statuses = await GetGPUStatusAsync();
            
            var primaryGpu = statuses.FirstOrDefault(s => s.PrimaryWorkload == workloadType && s.LoadPercentage < 80);
            if (primaryGpu != null)
            {
                return new GPUResourceInfo
                {
                    GPUId = primaryGpu.Id,
                    ExpectedLatency = CalculateExpectedLatency(primaryGpu, workloadType),
                    MemoryAvailable = primaryGpu.MemoryTotalMB - primaryGpu.MemoryUsedMB,
                    Recommendation = "使用专用GPU，性能最优"
                };
            }

            var optimalGpu = statuses.Where(s => s.LoadPercentage < 90)
                                   .OrderBy(s => s.LoadPercentage)
                                   .FirstOrDefault();

            if (optimalGpu != null)
            {
                return new GPUResourceInfo
                {
                    GPUId = optimalGpu.Id,
                    ExpectedLatency = CalculateExpectedLatency(optimalGpu, workloadType),
                    MemoryAvailable = optimalGpu.MemoryTotalMB - optimalGpu.MemoryUsedMB,
                    Recommendation = "使用备用GPU，可能有轻微性能影响"
                };
            }

            throw new InvalidOperationException("所有GPU负载过高，建议等待或扩容");
        }

        private async void UpdateGPUMetrics(object? state)
        {
            try
            {
                var gpuMetrics = await GetNvidiaGPUMetricsAsync();
                
                foreach (var metric in gpuMetrics)
                {
                    if (_gpuResources.TryGetValue(metric.Id, out var gpu))
                    {
                        gpu.MemoryUsedMB = metric.MemoryUsedMB;
                        gpu.Temperature = metric.Temperature;
                        gpu.PowerUsage = metric.PowerUsage;
                        gpu.UtilizationPercentage = metric.UtilizationPercentage;
                        gpu.IsHealthy = metric.Temperature < 85 && metric.PowerUsage < 450;
                        gpu.LastUpdateTime = DateTime.UtcNow;
                    }
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "更新GPU指标失败");
            }
        }

        private async Task<List<GPUMetric>> GetNvidiaGPUMetricsAsync()
        {
            try
            {
                var processStartInfo = new ProcessStartInfo
                {
                    FileName = "nvidia-smi",
                    Arguments = "--query-gpu=index,memory.used,memory.total,temperature.gpu,power.draw,utilization.gpu --format=csv,noheader,nounits",
                    RedirectStandardOutput = true,
                    UseShellExecute = false,
                    CreateNoWindow = true
                };

                using var process = Process.Start(processStartInfo);
                var output = await process!.StandardOutput.ReadToEndAsync();
                await process.WaitForExitAsync();

                var metrics = new List<GPUMetric>();
                var lines = output.Split('\n', StringSplitOptions.RemoveEmptyEntries);

                foreach (var line in lines)
                {
                    var parts = line.Split(',').Select(p => p.Trim()).ToArray();
                    if (parts.Length >= 6)
                    {
                        metrics.Add(new GPUMetric
                        {
                            Id = int.Parse(parts[0]),
                            MemoryUsedMB = int.Parse(parts[1]),
                            MemoryTotalMB = int.Parse(parts[2]),
                            Temperature = int.Parse(parts[3]),
                            PowerUsage = float.Parse(parts[4]),
                            UtilizationPercentage = int.Parse(parts[5])
                        });
                    }
                }

                return metrics;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "获取NVIDIA GPU指标失败");
                return new List<GPUMetric>();
            }
        }

        private int CalculateExpectedLatency(GPUStatus gpu, Services.GPUWorkloadType workloadType)
        {
            var baseLatency = workloadType switch
            {
                Services.GPUWorkloadType.MuseTalk => 80,
                Services.GPUWorkloadType.General => 100,
                Services.GPUWorkloadType.Whisper => 60,
                _ => 100
            };

            var loadMultiplier = 1.0f + (gpu.LoadPercentage / 100.0f);
            
            if (gpu.PrimaryWorkload != workloadType)
            {
                loadMultiplier *= 1.2f;
            }

            return (int)(baseLatency * loadMultiplier);
        }

        public void Dispose()
        {
            _monitoringTimer?.Dispose();
            _allocationLock?.Dispose();
        }
    }

    public class GPUResource
    {
        public int Id { get; set; }
        public string Name { get; set; } = string.Empty;
        public int TotalMemoryMB { get; set; }
        public int MemoryUsedMB { get; set; }
        public Services.GPUWorkloadType PrimaryWorkload { get; set; }
        public int MaxConcurrentTasks { get; set; }
        public int CurrentTasks { get; set; }
        public int Temperature { get; set; }
        public float PowerUsage { get; set; }
        public int UtilizationPercentage { get; set; }
        public bool IsHealthy { get; set; } = true;
        public DateTime LastAllocatedTime { get; set; }
        public DateTime LastReleasedTime { get; set; }
        public DateTime LastUpdateTime { get; set; }
        public string Description { get; set; } = string.Empty;

        public float GetLoadPercentage()
        {
            return MaxConcurrentTasks > 0 ? (float)CurrentTasks / MaxConcurrentTasks * 100 : 0;
        }
    }

    public class GPUStatus
    {
        public int Id { get; set; }
        public string Name { get; set; } = string.Empty;
        public float LoadPercentage { get; set; }
        public int MemoryUsedMB { get; set; }
        public int MemoryTotalMB { get; set; }
        public int CurrentTasks { get; set; }
        public int MaxTasks { get; set; }
        public Services.GPUWorkloadType PrimaryWorkload { get; set; }
        public int Temperature { get; set; }
        public float PowerUsage { get; set; }
        public bool IsHealthy { get; set; }
    }

    public class GPUResourceInfo
    {
        public int GPUId { get; set; }
        public int ExpectedLatency { get; set; }
        public int MemoryAvailable { get; set; }
        public string Recommendation { get; set; } = string.Empty;
    }

    public class GPUMetric
    {
        public int Id { get; set; }
        public int MemoryUsedMB { get; set; }
        public int MemoryTotalMB { get; set; }
        public int Temperature { get; set; }
        public float PowerUsage { get; set; }
        public int UtilizationPercentage { get; set; }
    }
}
