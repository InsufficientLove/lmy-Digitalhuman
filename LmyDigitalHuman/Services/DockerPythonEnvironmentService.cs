using System.Diagnostics;

namespace LmyDigitalHuman.Services
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
    }
}