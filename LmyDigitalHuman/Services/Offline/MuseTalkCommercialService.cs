using LmyDigitalHuman.Models;
using System.Diagnostics;
using System.Text.Json;

namespace LmyDigitalHuman.Services.Offline
{
    public interface IMuseTalkCommercialService
    {
        Task<string> GenerateHighQualityVideoAsync(string templateImagePath, string audioPath, MuseTalkConfig config);
        Task<string> GenerateRealtimeVideoAsync(string templateImagePath, string audioPath, MuseTalkConfig config);
        Task<bool> IsMuseTalkAvailableAsync();
        Task<MuseTalkStatus> GetStatusAsync();
    }

    public class MuseTalkCommercialService : IMuseTalkCommercialService
    {
        private readonly ILogger<MuseTalkCommercialService> _logger;
        private readonly IConfiguration _configuration;
        private readonly string _museTalkPath;
        private readonly string _venvPath;

        public MuseTalkCommercialService(
            ILogger<MuseTalkCommercialService> logger,
            IConfiguration configuration)
        {
            _logger = logger;
            _configuration = configuration;
            _museTalkPath = _configuration["MuseTalk:Path"] ?? Path.Combine(Directory.GetCurrentDirectory(), "MuseTalk");
            _venvPath = _configuration["MuseTalk:VenvPath"] ?? Path.Combine(Directory.GetCurrentDirectory(), "venv_musetalk");
        }

        public async Task<string> GenerateHighQualityVideoAsync(string templateImagePath, string audioPath, MuseTalkConfig config)
        {
            _logger.LogInformation("开始生成高质量数字人视频...");
            
            try
            {
                var outputPath = Path.Combine("wwwroot", "videos", $"musetalk_hq_{Guid.NewGuid()}.mp4");
                
                var arguments = BuildMuseTalkArguments(templateImagePath, audioPath, outputPath, config, isHighQuality: true);
                
                var result = await ExecuteMuseTalkAsync(arguments);
                
                if (result.Success && File.Exists(outputPath))
                {
                    _logger.LogInformation("高质量视频生成成功: {OutputPath}", outputPath);
                    return outputPath;
                }
                else
                {
                    throw new Exception($"MuseTalk生成失败: {result.Error}");
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "生成高质量视频失败");
                throw;
            }
        }

        public async Task<string> GenerateRealtimeVideoAsync(string templateImagePath, string audioPath, MuseTalkConfig config)
        {
            _logger.LogInformation("开始生成实时数字人视频...");
            
            try
            {
                var outputPath = Path.Combine("wwwroot", "videos", $"musetalk_rt_{Guid.NewGuid()}.mp4");
                
                var arguments = BuildMuseTalkArguments(templateImagePath, audioPath, outputPath, config, isHighQuality: false);
                
                var result = await ExecuteMuseTalkAsync(arguments);
                
                if (result.Success && File.Exists(outputPath))
                {
                    _logger.LogInformation("实时视频生成成功: {OutputPath}", outputPath);
                    return outputPath;
                }
                else
                {
                    throw new Exception($"MuseTalk生成失败: {result.Error}");
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "生成实时视频失败");
                throw;
            }
        }

        public async Task<bool> IsMuseTalkAvailableAsync()
        {
            try
            {
                var pythonPath = Path.Combine(_venvPath, "Scripts", "python.exe");
                var museTalkScript = Path.Combine(_museTalkPath, "app.py");
                
                return File.Exists(pythonPath) && File.Exists(museTalkScript);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "检查MuseTalk可用性失败");
                return false;
            }
        }

        public async Task<MuseTalkStatus> GetStatusAsync()
        {
            try
            {
                var status = new MuseTalkStatus
                {
                    IsAvailable = await IsMuseTalkAvailableAsync(),
                    MuseTalkPath = _museTalkPath,
                    VenvPath = _venvPath,
                    GPUCount = await GetGPUCountAsync(),
                    MemoryUsage = await GetMemoryUsageAsync()
                };

                return status;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "获取MuseTalk状态失败");
                return new MuseTalkStatus { IsAvailable = false, Error = ex.Message };
            }
        }

        private string BuildMuseTalkArguments(string imagePath, string audioPath, string outputPath, MuseTalkConfig config, bool isHighQuality)
        {
            var args = new List<string>
            {
                "-m", "scripts.inference",
                "--avatar_id", Path.GetFileNameWithoutExtension(imagePath),
                "--bbox_shift", config.BboxShift.ToString(),
                "--audio_path", $"\"{audioPath}\"",
                "--result_dir", $"\"{Path.GetDirectoryName(outputPath)}\"",
                "--fps", config.Fps.ToString(),
                "--batch_size", config.BatchSize.ToString()
            };

            if (isHighQuality)
            {
                // 商用高质量设置
                args.AddRange(new[]
                {
                    "--use_float16", "false",
                    "--num_inference_steps", "25",
                    "--resolution", "512"
                });
            }
            else
            {
                // 实时模式设置
                args.AddRange(new[]
                {
                    "--use_float16", "true",
                    "--num_inference_steps", "15",
                    "--resolution", "256"
                });
            }

            return string.Join(" ", args);
        }

        private async Task<(bool Success, string Error)> ExecuteMuseTalkAsync(string arguments)
        {
            try
            {
                var pythonPath = Path.Combine(_venvPath, "Scripts", "python.exe");
                
                var processStartInfo = new ProcessStartInfo
                {
                    FileName = pythonPath,
                    Arguments = arguments,
                    WorkingDirectory = _museTalkPath,
                    RedirectStandardOutput = true,
                    RedirectStandardError = true,
                    UseShellExecute = false,
                    CreateNoWindow = true
                };

                // 设置CUDA环境变量
                processStartInfo.EnvironmentVariables["CUDA_VISIBLE_DEVICES"] = "0,1,2,3";
                processStartInfo.EnvironmentVariables["PYTORCH_CUDA_ALLOC_CONF"] = "max_split_size_mb:512";

                using var process = new Process { StartInfo = processStartInfo };
                
                var outputBuilder = new System.Text.StringBuilder();
                var errorBuilder = new System.Text.StringBuilder();

                process.OutputDataReceived += (sender, e) =>
                {
                    if (!string.IsNullOrEmpty(e.Data))
                    {
                        outputBuilder.AppendLine(e.Data);
                        _logger.LogInformation("MuseTalk输出: {Output}", e.Data);
                    }
                };

                process.ErrorDataReceived += (sender, e) =>
                {
                    if (!string.IsNullOrEmpty(e.Data))
                    {
                        errorBuilder.AppendLine(e.Data);
                        _logger.LogWarning("MuseTalk错误: {Error}", e.Data);
                    }
                };

                process.Start();
                process.BeginOutputReadLine();
                process.BeginErrorReadLine();

                // 设置超时时间（商用模式10分钟，实时模式2分钟）
                var timeout = arguments.Contains("use_float16 false") ? TimeSpan.FromMinutes(10) : TimeSpan.FromMinutes(2);
                
                if (!process.WaitForExit((int)timeout.TotalMilliseconds))
                {
                    process.Kill();
                    return (false, "MuseTalk执行超时");
                }

                if (process.ExitCode == 0)
                {
                    return (true, string.Empty);
                }
                else
                {
                    return (false, $"MuseTalk执行失败，退出码: {process.ExitCode}, 错误信息: {errorBuilder}");
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "执行MuseTalk失败");
                return (false, ex.Message);
            }
        }

        private async Task<int> GetGPUCountAsync()
        {
            try
            {
                // 使用nvidia-smi检查GPU数量
                var processStartInfo = new ProcessStartInfo
                {
                    FileName = "nvidia-smi",
                    Arguments = "--list-gpus",
                    RedirectStandardOutput = true,
                    UseShellExecute = false,
                    CreateNoWindow = true
                };

                using var process = Process.Start(processStartInfo);
                var output = await process.StandardOutput.ReadToEndAsync();
                await process.WaitForExitAsync();

                if (process.ExitCode == 0)
                {
                    return output.Split('\n', StringSplitOptions.RemoveEmptyEntries).Length;
                }
            }
            catch (Exception ex)
            {
                _logger.LogWarning(ex, "无法获取GPU数量");
            }

            return 0;
        }

        private async Task<string> GetMemoryUsageAsync()
        {
            try
            {
                var processStartInfo = new ProcessStartInfo
                {
                    FileName = "nvidia-smi",
                    Arguments = "--query-gpu=memory.used,memory.total --format=csv,noheader,nounits",
                    RedirectStandardOutput = true,
                    UseShellExecute = false,
                    CreateNoWindow = true
                };

                using var process = Process.Start(processStartInfo);
                var output = await process.StandardOutput.ReadToEndAsync();
                await process.WaitForExitAsync();

                if (process.ExitCode == 0)
                {
                    return output.Trim();
                }
            }
            catch (Exception ex)
            {
                _logger.LogWarning(ex, "无法获取显存使用情况");
            }

            return "未知";
        }
    }

    public class MuseTalkConfig
    {
        public int BboxShift { get; set; } = 0;
        public int Fps { get; set; } = 25;
        public int BatchSize { get; set; } = 4;
        public bool UseFloat16 { get; set; } = false;
        public int NumInferenceSteps { get; set; } = 25;
        public int Resolution { get; set; } = 512;
    }

    public class MuseTalkStatus
    {
        public bool IsAvailable { get; set; }
        public string MuseTalkPath { get; set; } = string.Empty;
        public string VenvPath { get; set; } = string.Empty;
        public int GPUCount { get; set; }
        public string MemoryUsage { get; set; } = string.Empty;
        public string? Error { get; set; }
    }
}