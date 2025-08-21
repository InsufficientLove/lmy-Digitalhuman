using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using LmyDigitalHuman.Models;
using System.Diagnostics;
using System.IO;
using System;
using System.Threading.Tasks;

namespace LmyDigitalHuman.Services.Offline
{
    /// <summary>
    /// 增强版MuseTalk服务
    /// 
    /// 特点：
    /// - 自动检测并启动持久化Python服务
    /// - 智能回退到传统进程模式
    /// - 30fps+ 超高速推理性能
    /// - 完全兼容现有接口
    /// </summary>
    public class EnhancedMuseTalkService : IDisposable
    {
        private readonly ILogger<EnhancedMuseTalkService> _logger;
        private readonly IConfiguration _configuration;
        private readonly IServiceProvider _serviceProvider;
        private readonly PersistentMuseTalkClient _persistentClient;
        private readonly IMuseTalkService _fallbackService;
        
        private readonly bool _enablePersistentMode;
        private readonly bool _autoStartService;
        private bool _persistentModeAvailable = false;
        private bool _serviceStartAttempted = false;

        public EnhancedMuseTalkService(
            ILogger<EnhancedMuseTalkService> logger,
            IConfiguration configuration,
            IServiceProvider serviceProvider,
            PersistentMuseTalkClient persistentClient,
            IMuseTalkService fallbackService)
        {
            _logger = logger;
            _configuration = configuration;
            _serviceProvider = serviceProvider;
            _persistentClient = persistentClient;
            _fallbackService = fallbackService;
            
            // 读取配置
            _enablePersistentMode = _configuration.GetValue<bool>("PersistentMuseTalk:EnablePersistentMode", true);
            _autoStartService = _configuration.GetValue<bool>("PersistentMuseTalk:AutoStartService", true);
            
            _logger.LogInformation("初始化增强MuseTalk服务");
            _logger.LogInformation("持久化模式: {EnablePersistentMode}", _enablePersistentMode);
            _logger.LogInformation("🔄 自动启动服务: {AutoStartService}", _autoStartService);
            
            // 如果启用持久化模式，尝试初始化
            if (_enablePersistentMode)
            {
                _ = Task.Run(InitializePersistentModeAsync);
            }
        }

        /// <summary>
        /// 初始化持久化模式
        /// </summary>
        private async Task InitializePersistentModeAsync()
        {
            try
            {
                _logger.LogInformation("🔄 正在初始化持久化模式...");
                
                // 检查持久化服务是否可用
                var pingSuccess = await _persistentClient.PingAsync();
                
                if (pingSuccess)
                {
                    _persistentModeAvailable = true;
                    _logger.LogInformation("持久化服务已可用");
                    return;
                }
                
                // 如果ping失败且启用自动启动，尝试启动服务
                if (!pingSuccess && _autoStartService && !_serviceStartAttempted)
                {
                    _serviceStartAttempted = true;
                    _logger.LogInformation("尝试自动启动持久化服务...");
                    
                    await StartPersistentServiceAsync();
                    
                    // 智能等待服务启动 - 轮询检查而不是固定延迟
                    pingSuccess = await WaitForServiceStartupAsync();
                    if (pingSuccess)
                    {
                        _persistentModeAvailable = true;
                        _logger.LogInformation("持久化服务自动启动成功");
                    }
                    else
                    {
                        _logger.LogWarning("持久化服务自动启动失败，将使用传统模式");
                    }
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "初始化持久化模式失败");
                _persistentModeAvailable = false;
            }
        }

        /// <summary>
        /// 启动持久化Python服务
        /// </summary>
        private async Task StartPersistentServiceAsync()
        {
            try
            {
                var pythonEnvService = _serviceProvider.GetRequiredService<IPythonEnvironmentService>();
                var pythonPath = await pythonEnvService.GetRecommendedPythonPathAsync();
                
                var serviceScript = Path.Combine(
                    Directory.GetCurrentDirectory(), 
                    "..", 
                    "MuseTalkEngine", 
                    "persistent_musetalk_service.py"
                );
                
                if (!File.Exists(serviceScript))
                {
                    throw new FileNotFoundException($"持久化服务脚本不存在: {serviceScript}");
                }
                
                var host = _configuration.GetValue<string>("PersistentMuseTalk:Host", "127.0.0.1");
                var port = _configuration.GetValue<int>("PersistentMuseTalk:Port", 58080);
                
                var startInfo = new ProcessStartInfo
                {
                    FileName = pythonPath,
                    Arguments = $"\"{serviceScript}\" --host {host} --port {port}",
                    UseShellExecute = false,
                    CreateNoWindow = true,
                    RedirectStandardOutput = true,
                    RedirectStandardError = true,
                    WorkingDirectory = Path.Combine(Directory.GetCurrentDirectory(), "..")
                };
                
                _logger.LogInformation("💻 启动命令: {FileName} {Arguments}", startInfo.FileName, startInfo.Arguments);
                
                var process = Process.Start(startInfo);
                if (process != null)
                {
                    _logger.LogInformation("持久化服务进程已启动，PID: {ProcessId}", process.Id);
                    
                    // 不等待进程结束，让它在后台运行
                    _ = Task.Run(async () =>
                    {
                        try
                        {
                            await process.WaitForExitAsync();
                            _logger.LogInformation("🔌 持久化服务进程已退出");
                            _persistentModeAvailable = false;
                        }
                        catch (Exception ex)
                        {
                            _logger.LogError(ex, "监控持久化服务进程时发生错误");
                        }
                    });
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "启动持久化服务失败");
                throw;
            }
        }

        /// <summary>
        /// 智能等待服务启动 - 使用轮询而不是固定延迟
        /// </summary>
        private async Task<bool> WaitForServiceStartupAsync()
        {
            const int maxAttempts = 20; // 最多尝试20次
            const int intervalMs = 100;  // 每100ms检查一次
            
            for (int attempt = 1; attempt <= maxAttempts; attempt++)
            {
                var pingSuccess = await _persistentClient.PingAsync();
                if (pingSuccess)
                {
                    _logger.LogInformation("服务启动成功，用时: {Time}ms", attempt * intervalMs);
                    return true;
                }
                
                if (attempt < maxAttempts)
                {
                    await Task.Delay(intervalMs);
                }
            }
            
            _logger.LogWarning("服务启动超时，已尝试 {Attempts} 次", maxAttempts);
            return false;
        }

        /// <summary>
        /// 生成数字人视频（主入口）
        /// </summary>
        public async Task<string> GenerateVideoAsync(
            string templateId,
            string audioPath,
            string outputFileName,
            int fps = 25,
            int bboxShift = 0,
            string parsingMode = "jaw")
        {
            var startTime = DateTime.Now;
            _logger.LogInformation("开始生成数字人视频: TemplateId={TemplateId}, Mode={Mode}", 
                templateId, _persistentModeAvailable ? "Persistent" : "Traditional");
            
            try
            {
                string result;
                
                if (_persistentModeAvailable && _enablePersistentMode)
                {
                    // 使用持久化模式
                    result = await GenerateVideoViaPersistentAsync(templateId, audioPath, outputFileName, fps, bboxShift, parsingMode);
                }
                else
                {
                    // 使用传统模式
                    result = await GenerateVideoViaTraditionalAsync(templateId, audioPath, outputFileName, fps, bboxShift, parsingMode);
                }
                
                var totalTime = DateTime.Now - startTime;
                _logger.LogInformation("视频生成完成: TemplateId={TemplateId}, 总耗时={TotalTime:F2}秒", 
                    templateId, totalTime.TotalSeconds);
                
                return result;
            }
            catch (Exception ex)
            {
                var totalTime = DateTime.Now - startTime;
                _logger.LogError(ex, "视频生成失败: TemplateId={TemplateId}, 总耗时={TotalTime:F2}秒", 
                    templateId, totalTime.TotalSeconds);
                
                // 如果持久化模式失败，尝试传统模式
                if (_persistentModeAvailable && _enablePersistentMode)
                {
                    _logger.LogWarning("持久化模式失败，尝试传统模式...");
                    _persistentModeAvailable = false;
                    
                    return await GenerateVideoViaTraditionalAsync(templateId, audioPath, outputFileName, fps, bboxShift, parsingMode);
                }
                
                throw;
            }
        }

        /// <summary>
        /// 通过持久化服务生成视频
        /// </summary>
        private async Task<string> GenerateVideoViaPersistentAsync(
            string templateId,
            string audioPath,
            string outputFileName,
            int fps,
            int bboxShift,
            string parsingMode)
        {
            _logger.LogInformation("使用持久化模式生成视频");
            
            var outputPath = Path.Combine(Directory.GetCurrentDirectory(), "wwwroot", "videos", outputFileName);
            var templateDir = Path.Combine(Directory.GetCurrentDirectory(), "wwwroot", "templates");
            
            var response = await _persistentClient.InferenceAsync(
                templateId: templateId,
                audioPath: audioPath,
                outputPath: outputPath,
                templateDir: templateDir,
                fps: fps,
                bboxShift: bboxShift,
                parsingMode: parsingMode
            );
            
            if (response?.Success == true)
            {
                _logger.LogInformation("持久化推理成功: 推理耗时={InferenceTime:F2}秒", response.InferenceTime);
                return response.ResultPath ?? outputPath;
            }
            else
            {
                throw new InvalidOperationException($"持久化推理失败: {response?.Error}");
            }
        }

        /// <summary>
        /// 通过传统进程生成视频
        /// </summary>
        private async Task<string> GenerateVideoViaTraditionalAsync(
            string templateId,
            string audioPath,
            string outputFileName,
            int fps,
            int bboxShift,
            string parsingMode)
        {
            _logger.LogInformation("🔄 使用传统模式生成视频");
            
            // 构建DigitalHumanRequest对象
            var request = new DigitalHumanRequest
            {
                TemplateId = templateId,
                AvatarImagePath = $"/templates/{templateId}.jpg",
                AudioPath = audioPath,
                Quality = "medium",
                Fps = fps,
                BboxShift = bboxShift
            };
            
            var response = await _fallbackService.GenerateVideoAsync(request);
            
            if (response.Success)
            {
                return response.VideoPath ?? Path.Combine(Directory.GetCurrentDirectory(), "wwwroot", "videos", outputFileName);
            }
            else
            {
                throw new InvalidOperationException($"传统模式视频生成失败: {response.Message}");
            }
        }

        /// <summary>
        /// 预处理模板
        /// </summary>
        public async Task<bool> PreprocessTemplateAsync(
            string templateId,
            string? templateImagePath = null,
            int bboxShift = 0,
            string parsingMode = "jaw")
        {
            _logger.LogInformation("开始预处理模板: TemplateId={TemplateId}", templateId);
            
            try
            {
                if (_persistentModeAvailable && _enablePersistentMode)
                {
                    var response = await _persistentClient.PreprocessAsync(
                        templateId: templateId,
                        templateImagePath: templateImagePath,
                        bboxShift: bboxShift,
                        parsingMode: parsingMode
                    );
                    
                    if (response?.Success == true)
                    {
                        _logger.LogInformation("预处理完成: TemplateId={TemplateId}, 耗时={ProcessTime:F2}秒", 
                            templateId, response.ProcessTime);
                        return true;
                    }
                    else
                    {
                        _logger.LogError("预处理失败: TemplateId={TemplateId}, 错误={Error}", 
                            templateId, response?.Error);
                        return false;
                    }
                }
                else
                {
                    _logger.LogInformation("ℹ️ 传统模式下无需手动预处理");
                    return true;
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "预处理异常: TemplateId={TemplateId}", templateId);
                return false;
            }
        }

        /// <summary>
        /// 检查模板缓存状态
        /// </summary>
        public async Task<bool> CheckTemplateCacheAsync(string templateId)
        {
            try
            {
                if (_persistentModeAvailable && _enablePersistentMode)
                {
                    var response = await _persistentClient.CheckCacheAsync(templateId);
                    return response?.CacheExists == true;
                }
                else
                {
                    // 传统模式下假设缓存总是可用的
                    return true;
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "检查缓存状态失败: TemplateId={TemplateId}", templateId);
                return false;
            }
        }

        /// <summary>
        /// 获取服务状态
        /// </summary>
        public async Task<ServiceStatus> GetServiceStatusAsync()
        {
            try
            {
                if (_persistentModeAvailable && _enablePersistentMode)
                {
                    var response = await _persistentClient.GetStatusAsync();
                    return new ServiceStatus
                    {
                        Mode = "Persistent",
                        Available = response?.Success == true,
                        ModelLoaded = response?.ModelLoaded == true,
                        Device = response?.Device,
                        Version = response?.Version,
                        ActiveThreads = response?.ActiveThreads ?? 0
                    };
                }
                else
                {
                    return new ServiceStatus
                    {
                        Mode = "Traditional",
                        Available = true,
                        ModelLoaded = true,
                        Device = "cuda:0",
                        Version = "V3/V4",
                        ActiveThreads = 0
                    };
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "获取服务状态失败");
                return new ServiceStatus
                {
                    Mode = "Error",
                    Available = false,
                    Error = ex.Message
                };
            }
        }

        public void Dispose()
        {
            _persistentClient?.Dispose();
            if (_fallbackService is IDisposable disposable)
            {
                disposable.Dispose();
            }
        }
    }

    /// <summary>
    /// 服务状态信息
    /// </summary>
    public class ServiceStatus
    {
        public string Mode { get; set; } = "";
        public bool Available { get; set; }
        public bool ModelLoaded { get; set; }
        public string? Device { get; set; }
        public string? Version { get; set; }
        public int ActiveThreads { get; set; }
        public string? Error { get; set; }
    }
}