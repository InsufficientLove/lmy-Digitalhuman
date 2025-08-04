using System;
using System.Collections.Concurrent;
using System.Diagnostics;
using System.IO;
using System.Text;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Configuration;
using LmyDigitalHuman.Models;
using LmyDigitalHuman.Services.Interfaces;

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
        
        // 📊 模板缓存管理
        private readonly ConcurrentDictionary<string, TemplateInfo> _templateCache = new();
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
            
            // 后台初始化Python推理器
            _ = Task.Run(InitializePythonInferenceEngineAsync);
        }
        
        /// <summary>
        /// 模板信息
        /// </summary>
        private class TemplateInfo
        {
            public string TemplateId { get; set; }
            public string TemplatePath { get; set; }
            public bool IsPreprocessed { get; set; }
            public DateTime LastUsed { get; set; } = DateTime.Now;
            public long UsageCount { get; set; } = 0;
        }
        
        /// <summary>
        /// 主要接口实现 - 极致优化推理
        /// </summary>
        public async Task<DigitalHumanResponse> ExecuteMuseTalkPythonAsync(DigitalHumanRequest request)
        {
            var stopwatch = Stopwatch.StartNew();
            System.Threading.Interlocked.Increment(ref _totalRequests);
            
            try
            {
                // 🎯 获取模板ID
                var templateId = GetTemplateId(request.AvatarImagePath);
                
                _logger.LogInformation("🚀 开始极致优化推理: TemplateId={TemplateId}, TotalRequests={TotalRequests}", 
                    templateId, _totalRequests);
                
                // 📊 更新模板使用统计
                _templateUsageCount.AddOrUpdate(templateId, 1, (key, oldValue) => oldValue + 1);
                
                // 🎯 确保Python推理器已初始化
                await EnsurePythonInferenceEngineInitializedAsync();
                
                // 🚀 执行优化推理
                var outputPath = await ExecuteOptimizedInferenceAsync(templateId, request.AudioPath);
                
                stopwatch.Stop();
                System.Threading.Interlocked.Increment(ref _completedRequests);
                
                var duration = GetAudioDuration(request.AudioPath);
                
                _logger.LogInformation("✅ 极致优化推理完成: TemplateId={TemplateId}, 耗时={ElapsedMs}ms, 完成率={CompletionRate:P2}", 
                    templateId, stopwatch.ElapsedMilliseconds, (double)_completedRequests / _totalRequests);
                
                return new DigitalHumanResponse
                {
                    Success = true,
                    VideoPath = outputPath,
                    Duration = duration,
                    Message = $"🚀 极致优化完成 (模板: {templateId}, 耗时: {stopwatch.ElapsedMilliseconds}ms)"
                };
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "❌ 极致优化推理失败");
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
                        _logger.LogWarning("⚠️ Python推理器初始化可能未完全成功");
                    }
                }
                catch (Exception ex)
                {
                    _logger.LogError(ex, "❌ Python推理器初始化失败");
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
                _logger.LogInformation("⏳ 等待Python推理器初始化完成...");
                
                // 等待初始化完成，最多等待60秒
                var timeout = TimeSpan.FromSeconds(60);
                var start = DateTime.Now;
                
                while (!_isInitialized && DateTime.Now - start < timeout)
                {
                    await Task.Delay(1000);
                }
                
                if (!_isInitialized)
                {
                    throw new TimeoutException("Python推理器初始化超时");
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
                var pythonPath = await GetCachedPythonPathAsync();
                
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
            var outputFileName = $"optimized_{templateId}_{DateTime.Now:yyyyMMdd_HHmmss}_{Guid.NewGuid():N[..8]}.mp4";
            var outputPath = Path.Combine(_pathManager.GetContentRootPath(), "wwwroot", "videos", outputFileName);
            
            var museTalkDir = Path.Combine(_pathManager.GetContentRootPath(), "..", "MuseTalk");
            var pythonPath = await GetCachedPythonPathAsync();
            var optimizedScriptPath = Path.Combine(museTalkDir, "optimized_musetalk_inference.py");
            
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
        /// 配置优化GPU环境
        /// </summary>
        private void ConfigureOptimizedGpuEnvironment(ProcessStartInfo processInfo)
        {
            // 🚀 4x RTX 4090极致性能配置 - 基于官方基准优化
            processInfo.Environment["CUDA_VISIBLE_DEVICES"] = "0,1,2,3"; // 使用所有GPU
            processInfo.Environment["PYTORCH_CUDA_ALLOC_CONF"] = "max_split_size_mb:12288,expandable_segments:True,roundup_power2_divisions:32"; // RTX 4090 24GB极致配置
            processInfo.Environment["OMP_NUM_THREADS"] = "64"; // 最大化CPU并行，支持batch_size=64
            processInfo.Environment["CUDA_LAUNCH_BLOCKING"] = "0"; // 异步CUDA
            processInfo.Environment["TORCH_CUDNN_V8_API_ENABLED"] = "1";
            processInfo.Environment["TORCH_BACKENDS_CUDNN_BENCHMARK"] = "1"; // cuDNN自动调优
            processInfo.Environment["TORCH_BACKENDS_CUDNN_DETERMINISTIC"] = "0"; // 禁用确定性
            processInfo.Environment["TORCH_BACKENDS_CUDNN_ALLOW_TF32"] = "1"; // TF32加速
            processInfo.Environment["TORCH_ALLOW_TF32_CUBLAS_OVERRIDE"] = "1";
            processInfo.Environment["TOKENIZERS_PARALLELISM"] = "false";
            processInfo.Environment["CUBLAS_WORKSPACE_CONFIG"] = ":16:8";
            processInfo.Environment["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID";
            processInfo.Environment["TORCH_CUDA_ARCH_LIST"] = "8.9"; // RTX 4090架构
            processInfo.Environment["TORCH_COMPILE"] = "1"; // PyTorch 2.0编译
            processInfo.Environment["TORCH_CUDNN_SDPA_ENABLED"] = "1";
            processInfo.Environment["CUDA_MODULE_LOADING"] = "LAZY";
            
            // 🎯 针对4GPU并行优化的特殊配置
            processInfo.Environment["NCCL_DEBUG"] = "WARN"; // 减少NCCL日志
            processInfo.Environment["NCCL_IB_DISABLE"] = "1"; // 禁用InfiniBand
            processInfo.Environment["NCCL_P2P_DISABLE"] = "1"; // 禁用P2P（如果有问题）
            
            _logger.LogInformation("🎮 已配置4x RTX 4090极致性能环境");
        }
        
        /// <summary>
        /// 获取模板ID - 从前端传入的路径中提取模板名称
        /// 支持用户自定义的可读模板名称，而不是GUID
        /// </summary>
        private string GetTemplateId(string avatarPath)
        {
            // 处理前端传入的路径格式，如: /templates/美女主播.jpg 或 /templates/商务男士.jpg
            if (avatarPath.StartsWith("/"))
            {
                return Path.GetFileNameWithoutExtension(avatarPath);
            }
            
            // 处理绝对路径格式
            return Path.GetFileNameWithoutExtension(avatarPath);
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
                _cachedPythonPath = _pythonEnvironmentService.GetRecommendedPythonPathAsync().Result;
                _logger.LogInformation("✅ Python路径已缓存: {PythonPath}", _cachedPythonPath);
                
                return _cachedPythonPath;
            }
        }
        
        public void Dispose()
        {
            _logger.LogInformation("🛑 优化版MuseTalk服务正在关闭");
        }
    }
}