using System.Diagnostics;
using LmyDigitalHuman.Services;

namespace LmyDigitalHuman.Services.Core
{
    /// <summary>
    /// Docker环境中的Python环境服务
    /// </summary>
    public class DockerPythonEnvironmentService : IPythonEnvironmentService
    {
        private readonly ILogger<DockerPythonEnvironmentService> _logger;
        private readonly string _pythonPath = "python3";

        public DockerPythonEnvironmentService(ILogger<DockerPythonEnvironmentService> logger)
        {
            _logger = logger;
        }

        public async Task<string> GetRecommendedPythonPathAsync()
        {
            // 在Docker环境中，直接使用系统Python3
            return await Task.FromResult(_pythonPath);
        }

        public async Task<bool> CheckPythonEnvironmentAsync()
        {
            try
            {
                var processInfo = new ProcessStartInfo
                {
                    FileName = _pythonPath,
                    Arguments = "--version",
                    RedirectStandardOutput = true,
                    RedirectStandardError = true,
                    UseShellExecute = false,
                    CreateNoWindow = true
                };

                using var process = Process.Start(processInfo);
                if (process != null)
                {
                    await process.WaitForExitAsync();
                    if (process.ExitCode == 0)
                    {
                        var version = await process.StandardOutput.ReadToEndAsync();
                        _logger.LogInformation("Python环境可用: {Version}", version.Trim());
                        return true;
                    }
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "检查Python环境失败");
            }
            return false;
        }

        public async Task<bool> CheckEdgeTTSAsync()
        {
            try
            {
                var processInfo = new ProcessStartInfo
                {
                    FileName = _pythonPath,
                    Arguments = "-m edge_tts --help",
                    RedirectStandardOutput = true,
                    RedirectStandardError = true,
                    UseShellExecute = false,
                    CreateNoWindow = true
                };

                using var process = Process.Start(processInfo);
                if (process != null)
                {
                    await process.WaitForExitAsync();
                    if (process.ExitCode == 0)
                    {
                        _logger.LogInformation("edge-tts已安装");
                        return true;
                    }
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "检查edge-tts失败");
                    }
        return false;
    }

    private async Task<string> GetPythonVersionAsync()
    {
        try
        {
            var processInfo = new ProcessStartInfo
            {
                FileName = _pythonPath,
                Arguments = "--version",
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                UseShellExecute = false,
                CreateNoWindow = true
            };

            using var process = Process.Start(processInfo);
            if (process != null)
            {
                await process.WaitForExitAsync();
                if (process.ExitCode == 0)
                {
                    var version = await process.StandardOutput.ReadToEndAsync();
                    if (string.IsNullOrEmpty(version))
                        version = await process.StandardError.ReadToEndAsync();
                    return version.Trim();
                }
            }
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "获取Python版本失败");
        }
        return "Unknown";
    }

    public async Task<PythonEnvironmentInfo> DetectBestPythonEnvironmentAsync()
    {
        // 在Docker环境中，直接返回python3
        var info = new PythonEnvironmentInfo
        {
            PythonPath = _pythonPath,
            Version = await GetPythonVersionAsync(),
            IsVirtualEnv = false,
            VirtualEnvPath = "",
            InstalledPackages = new List<string> { "edge-tts" },
            IsValid = await CheckPythonEnvironmentAsync(),
            Priority = 1
        };
        return info;
    }

        public async Task<bool> ValidatePythonEnvironmentAsync(string pythonPath, params string[] requiredPackages)
        {
            // 简单验证Python是否可用
            if (pythonPath != _pythonPath)
            {
                return false;
            }
            return await CheckPythonEnvironmentAsync();
        }

            public async Task<List<PythonEnvironmentInfo>> GetAllAvailablePythonEnvironmentsAsync()
    {
        // Docker环境中只有一个Python环境
        var info = new PythonEnvironmentInfo
        {
            PythonPath = _pythonPath,
            Version = await GetPythonVersionAsync(),
            IsVirtualEnv = false,
            VirtualEnvPath = "",
            InstalledPackages = new List<string> { "edge-tts" },
            IsValid = await CheckPythonEnvironmentAsync(),
            Priority = 1
        };
        return new List<PythonEnvironmentInfo> { info };
    }
    }
}