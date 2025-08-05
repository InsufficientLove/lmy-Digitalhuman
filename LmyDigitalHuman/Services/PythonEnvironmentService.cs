using System.Diagnostics;
using System.Text.Json;

namespace LmyDigitalHuman.Services
{
    /// <summary>
    /// Python环境检测和管理服务
    /// </summary>
    public interface IPythonEnvironmentService
    {
        Task<PythonEnvironmentInfo> DetectBestPythonEnvironmentAsync();
        Task<bool> ValidatePythonEnvironmentAsync(string pythonPath, params string[] requiredPackages);
        Task<string> GetRecommendedPythonPathAsync();
        Task<List<PythonEnvironmentInfo>> GetAllAvailablePythonEnvironmentsAsync();

    }

    public class PythonEnvironmentInfo
    {
        public string PythonPath { get; set; } = "";
        public string Version { get; set; } = "";
        public bool IsVirtualEnv { get; set; }
        public string VirtualEnvPath { get; set; } = "";
        public List<string> InstalledPackages { get; set; } = new();
        public bool IsValid { get; set; }
        public string ErrorMessage { get; set; } = "";
        public int Priority { get; set; } // 优先级，数字越小优先级越高
    }

    public class PythonEnvironmentService : IPythonEnvironmentService
    {
        private readonly ILogger<PythonEnvironmentService> _logger;
        private readonly IConfiguration _configuration;
        private readonly IPathManager _pathManager;
        
        // 常见的Python可执行文件路径
        private readonly string[] _commonPythonPaths = new[]
        {
            "python.exe", "python3.exe", "python", "python3",
            "py.exe", "py", // Windows Python Launcher
        };

        // 常见的虚拟环境路径模式（优先级顺序）
        private readonly string[] _commonVenvPatterns = new[]
        {
            // 优先使用项目专用虚拟环境 venv_musetalk
            "../venv_musetalk/Scripts/python.exe", // 项目根目录的虚拟环境（最高优先级）
            "../../venv_musetalk/Scripts/python.exe", // 上上级目录
            "venv_musetalk/Scripts/python.exe",    // 当前目录的虚拟环境
            "../venv_musetalk/bin/python",         // Linux版本
            "../../venv_musetalk/bin/python",
            "venv_musetalk/bin/python"
        };

        public PythonEnvironmentService(
            ILogger<PythonEnvironmentService> logger,
            IConfiguration configuration,
            IPathManager pathManager)
        {
            _logger = logger;
            _configuration = configuration;
            _pathManager = pathManager;
        }

        public async Task<PythonEnvironmentInfo> DetectBestPythonEnvironmentAsync()
        {
            var allEnvs = await GetAllAvailablePythonEnvironmentsAsync();
            
            // 按优先级排序：虚拟环境 > 有edge-tts的环境 > 系统Python
            var bestEnv = allEnvs
                .Where(env => env.IsValid)
                .OrderBy(env => env.Priority)
                .ThenByDescending(env => env.IsVirtualEnv)
                .ThenByDescending(env => env.InstalledPackages.Contains("edge-tts"))
                .FirstOrDefault();

            if (bestEnv == null)
            {
                _logger.LogWarning("未找到可用的Python环境");
                return new PythonEnvironmentInfo
                {
                    PythonPath = "python",
                    IsValid = false,
                    ErrorMessage = "未找到可用的Python环境"
                };
            }

            _logger.LogInformation("检测到最佳Python环境: {PythonPath} (版本: {Version}, 虚拟环境: {IsVirtualEnv})", 
                bestEnv.PythonPath, bestEnv.Version, bestEnv.IsVirtualEnv);

            return bestEnv;
        }

        public async Task<string> GetRecommendedPythonPathAsync()
        {
            // 基于实际部署路径进行检测
            var contentRoot = _pathManager.GetContentRootPath();
            _logger.LogInformation("当前内容根路径: {ContentRoot}", contentRoot);
            
            var knownPaths = new[]
            {
                // 基于日志中的实际路径结构
                Path.Combine(contentRoot, "..", "venv_musetalk", "Scripts", "python.exe"),
                Path.Combine(contentRoot, "venv_musetalk", "Scripts", "python.exe"),
                Path.Combine(contentRoot, "..", "..", "venv_musetalk", "Scripts", "python.exe"),
                // Linux/macOS 路径
                Path.Combine(contentRoot, "..", "venv_musetalk", "bin", "python"),
                Path.Combine(contentRoot, "venv_musetalk", "bin", "python"),
                // 系统Python作为备用
                "python.exe",
                "python3.exe",
                "python",
                "python3"
            };

            foreach (var knownPath in knownPaths)
            {
                var resolvedPath = Path.GetFullPath(knownPath);
                _logger.LogDebug("检查Python路径: {Path}", resolvedPath);
                
                if (File.Exists(resolvedPath))
                {
                    _logger.LogInformation("找到可用的Python路径: {PythonPath}", resolvedPath);
                    return resolvedPath;
                }
            }

            // 如果所有路径都不存在，尝试使用环境变量中的python
            try
            {
                var process = new Process
                {
                    StartInfo = new ProcessStartInfo
                    {
                        FileName = "python",
                        Arguments = "--version",
                        UseShellExecute = false,
                        RedirectStandardOutput = true,
                        CreateNoWindow = true
                    }
                };
                
                process.Start();
                await process.WaitForExitAsync();
                
                if (process.ExitCode == 0)
                {
                    _logger.LogInformation("使用系统Python: python");
                    return "python";
                }
            }
            catch (Exception ex)
            {
                _logger.LogDebug("系统Python检测失败: {Error}", ex.Message);
            }

            // 最后的错误处理
            var expectedPath = Path.Combine(contentRoot, "..", "venv_musetalk", "Scripts", "python.exe");
            _logger.LogError("Python环境未找到，请确保虚拟环境存在。检查了以下路径:");
            foreach (var path in knownPaths.Take(6)) // 只显示主要路径
            {
                _logger.LogError("  - {Path}", Path.GetFullPath(path));
            }
            _logger.LogError("建议创建虚拟环境: python -m venv ../venv_musetalk");
            
            throw new FileNotFoundException($"Python环境未找到，请确保虚拟环境存在于: {expectedPath}");
        }



        public async Task<List<PythonEnvironmentInfo>> GetAllAvailablePythonEnvironmentsAsync()
        {
            var environments = new List<PythonEnvironmentInfo>();
            var checkedPaths = new HashSet<string>();

            // 1. 检查项目虚拟环境
            await CheckVirtualEnvironments(environments, checkedPaths);

            // 2. 检查系统Python
            await CheckSystemPython(environments, checkedPaths);

            // 3. 检查常见安装路径（Windows）
            if (OperatingSystem.IsWindows())
            {
                await CheckWindowsCommonPaths(environments, checkedPaths);
            }

            return environments;
        }

        private async Task CheckVirtualEnvironments(List<PythonEnvironmentInfo> environments, HashSet<string> checkedPaths)
        {
            var contentRoot = _pathManager.GetContentRootPath();
            
            foreach (var pattern in _commonVenvPatterns)
            {
                var pythonPath = Path.Combine(contentRoot, pattern);
                if (checkedPaths.Contains(pythonPath) || !File.Exists(pythonPath))
                    continue;

                checkedPaths.Add(pythonPath);
                var env = await CreatePythonEnvironmentInfoAsync(pythonPath, priority: 1);
                if (env != null)
                {
                    env.IsVirtualEnv = true;
                    env.VirtualEnvPath = Path.GetDirectoryName(Path.GetDirectoryName(pythonPath)) ?? "";
                    environments.Add(env);
                }
            }
        }

        private async Task CheckSystemPython(List<PythonEnvironmentInfo> environments, HashSet<string> checkedPaths)
        {
            foreach (var pythonCmd in _commonPythonPaths)
            {
                if (checkedPaths.Contains(pythonCmd))
                    continue;

                checkedPaths.Add(pythonCmd);
                var env = await CreatePythonEnvironmentInfoAsync(pythonCmd, priority: 5);
                if (env != null)
                {
                    environments.Add(env);
                }
            }
        }

        private async Task CheckWindowsCommonPaths(List<PythonEnvironmentInfo> environments, HashSet<string> checkedPaths)
        {
            // 获取配置的回退路径
            var configuredFallbackPaths = _configuration.GetSection("Paths:PythonFallbackPaths").Get<string[]>() ?? Array.Empty<string>();
            
            var commonPaths = new[]
            {
                @"C:\Python39\python.exe",
                @"C:\Python310\python.exe", 
                @"C:\Python311\python.exe",
                @"C:\Python312\python.exe",
                @"C:\Python313\python.exe",
                @"C:\Program Files\Python39\python.exe",
                @"C:\Program Files\Python310\python.exe",
                @"C:\Program Files\Python311\python.exe", 
                @"C:\Program Files\Python312\python.exe",
                @"C:\Program Files\Python313\python.exe"
            }.Concat(configuredFallbackPaths).ToArray();

            foreach (var path in commonPaths)
            {
                // 解析相对路径
                var resolvedPath = Path.IsPathRooted(path) ? path : _pathManager.ResolvePath(path);
                
                if (checkedPaths.Contains(resolvedPath) || !File.Exists(resolvedPath))
                    continue;

                checkedPaths.Add(resolvedPath);
                var env = await CreatePythonEnvironmentInfoAsync(resolvedPath, priority: 3);
                if (env != null)
                {
                    environments.Add(env);
                }
            }
        }

        private async Task<PythonEnvironmentInfo?> CreatePythonEnvironmentInfoAsync(string pythonPath, int priority)
        {
            var env = new PythonEnvironmentInfo
            {
                PythonPath = pythonPath,
                Priority = priority
            };

            try
            {
                // 获取Python版本
                var versionResult = await RunPythonCommandAsync(pythonPath, "--version");
                if (!versionResult.Success)
                {
                    env.ErrorMessage = $"无法获取Python版本: {versionResult.Error}";
                    return env;
                }

                env.Version = versionResult.Output.Trim().Replace("Python ", "");

                // 检查是否为虚拟环境
                var venvResult = await RunPythonCommandAsync(pythonPath, "-c \"import sys; print(hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix))\"");
                if (venvResult.Success && venvResult.Output.Trim().ToLower() == "true")
                {
                    env.IsVirtualEnv = true;
                    env.Priority = Math.Max(1, env.Priority - 1); // 虚拟环境优先级更高
                }

                // 获取已安装的包列表
                var packagesResult = await RunPythonCommandAsync(pythonPath, "-m pip list --format=json");
                if (packagesResult.Success)
                {
                    try
                    {
                        var packages = JsonSerializer.Deserialize<JsonElement[]>(packagesResult.Output);
                        env.InstalledPackages = packages?.Select(p => p.GetProperty("name").GetString()?.ToLower() ?? "").ToList() ?? new List<string>();
                    }
                    catch (Exception ex)
                    {
                        _logger.LogDebug(ex, "解析包列表失败: {PythonPath}", pythonPath);
                    }
                }

                env.IsValid = true;
                return env;
            }
            catch (Exception ex)
            {
                env.ErrorMessage = ex.Message;
                return env;
            }
        }

        public async Task<bool> ValidatePythonEnvironmentAsync(string pythonPath, params string[] requiredPackages)
        {
            try
            {
                // 检查Python可执行文件是否存在
                if (pythonPath != "python" && pythonPath != "python3" && !File.Exists(pythonPath))
                {
                    return false;
                }

                // 检查Python是否可以运行
                var versionResult = await RunPythonCommandAsync(pythonPath, "--version");
                if (!versionResult.Success)
                {
                    return false;
                }

                // 检查必需的包
                foreach (var package in requiredPackages)
                {
                    var packageResult = await RunPythonCommandAsync(pythonPath, $"-c \"import {package}\"");
                    if (!packageResult.Success)
                    {
                        _logger.LogDebug("Python环境 {PythonPath} 缺少包: {Package}", pythonPath, package);
                        return false;
                    }
                }

                return true;
            }
            catch (Exception ex)
            {
                _logger.LogDebug(ex, "验证Python环境失败: {PythonPath}", pythonPath);
                return false;
            }
        }

        private async Task<(bool Success, string Output, string Error)> RunPythonCommandAsync(string pythonPath, string arguments)
        {
            try
            {
                var processInfo = new ProcessStartInfo
                {
                    FileName = pythonPath,
                    Arguments = arguments,
                    RedirectStandardOutput = true,
                    RedirectStandardError = true,
                    UseShellExecute = false,
                    CreateNoWindow = true,
                    WorkingDirectory = _pathManager.GetContentRootPath()
                };

                using var process = Process.Start(processInfo);
                if (process == null)
                {
                    return (false, "", "无法启动Python进程");
                }

                using var cts = new CancellationTokenSource(TimeSpan.FromSeconds(5));
                try
                {
                    await process.WaitForExitAsync(cts.Token);
                }
                catch (OperationCanceledException)
                {
                    try { process.Kill(true); } catch { }
                    return (false, "", "Python命令执行超时");
                }

                var output = await process.StandardOutput.ReadToEndAsync();
                var error = await process.StandardError.ReadToEndAsync();

                return (process.ExitCode == 0, output, error);
            }
            catch (Exception ex)
            {
                return (false, "", ex.Message);
            }
        }
    }
}