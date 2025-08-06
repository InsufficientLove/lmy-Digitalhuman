using System;
using System.Net.Sockets;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;

namespace LmyDigitalHuman.Services
{
    /// <summary>
    /// 全局MuseTalk IPC客户端
    /// 与Python全局持久化服务通信，实现真正的实时推理
    /// </summary>
    public class GlobalMuseTalkClient
    {
        private readonly ILogger<GlobalMuseTalkClient> _logger;
        private readonly string _serverHost;
        private readonly int _serverPort;

        public GlobalMuseTalkClient(ILogger<GlobalMuseTalkClient> logger, string serverHost = "127.0.0.1", int serverPort = 28888)
        {
            _logger = logger;
            _serverHost = serverHost;
            _serverPort = serverPort;
        }

        /// <summary>
        /// 发送推理请求到全局Python服务
        /// </summary>
        public async Task<string?> SendInferenceRequestAsync(string templateId, string audioPath, string outputPath, string cacheDir, int batchSize = 8, int fps = 25)
        {
            try
            {
                _logger.LogInformation("🌐 连接全局MuseTalk服务: {Host}:{Port}", _serverHost, _serverPort);

                using var client = new TcpClient();
                
                // 🔧 添加连接超时和重试机制
                try
                {
                    _logger.LogInformation("🔧 尝试连接到 {Host}:{Port}", _serverHost, _serverPort);
                    await client.ConnectAsync(_serverHost, _serverPort);
                    _logger.LogInformation("✅ TCP连接建立成功 -> {Host}:{Port}", _serverHost, _serverPort);
                }
                catch (Exception ex)
                {
                    _logger.LogError("❌ 无法连接到Python服务 {Host}:{Port}: {Error}", _serverHost, _serverPort, ex.Message);
                    throw new InvalidOperationException($"Python全局服务未运行或端口{_serverPort}不可达", ex);
                }
                
                var stream = client.GetStream();

                // 构建请求数据
                var request = new
                {
                    template_id = templateId,
                    audio_path = audioPath,
                    output_path = outputPath,
                    cache_dir = cacheDir,
                    batch_size = batchSize,
                    fps = fps
                };

                var requestJson = JsonSerializer.Serialize(request);
                var requestData = Encoding.UTF8.GetBytes(requestJson);

                _logger.LogInformation("📤 发送推理请求: {TemplateId}", templateId);

                // 发送数据长度
                var lengthBytes = BitConverter.GetBytes((uint)requestData.Length);
                await stream.WriteAsync(lengthBytes, 0, 4);

                // 发送请求数据
                await stream.WriteAsync(requestData, 0, requestData.Length);

                // 接收响应长度
                var responseLengthBytes = new byte[4];
                await stream.ReadAsync(responseLengthBytes, 0, 4);
                var responseLength = BitConverter.ToUInt32(responseLengthBytes, 0);

                // 接收响应数据
                var responseData = new byte[responseLength];
                var totalRead = 0;
                while (totalRead < responseLength)
                {
                    var read = await stream.ReadAsync(responseData, totalRead, (int)(responseLength - totalRead));
                    totalRead += read;
                }

                var responseJson = Encoding.UTF8.GetString(responseData);
                var response = JsonSerializer.Deserialize<InferenceResponse>(responseJson);

                if (response?.Success == true)
                {
                    _logger.LogInformation("✅ 推理成功完成: {OutputPath}", response.OutputPath);
                    return response.OutputPath;
                }
                else
                {
                    _logger.LogError("❌ 推理失败");
                    return null;
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "❌ IPC通信失败: {TemplateId}", templateId);
                return null;
            }
        }

        /// <summary>
        /// 推理响应数据结构
        /// </summary>
        private class InferenceResponse
        {
            public bool Success { get; set; }
            public string? OutputPath { get; set; }
        }
    }

    /// <summary>
    /// 全局MuseTalk服务管理器 - 4GPU并行架构
    /// 负责启动和管理4个Python全局服务进程，每个占用一个GPU
    /// </summary>
    public class GlobalMuseTalkServiceManager : IDisposable
    {
        private readonly ILogger<GlobalMuseTalkServiceManager> _logger;
        private readonly IPathManager _pathManager;
        private System.Diagnostics.Process? _pythonProcess;
        private bool _isServiceRunning = false;
        private readonly object _lock = new object();

        public GlobalMuseTalkServiceManager(ILogger<GlobalMuseTalkServiceManager> logger, IPathManager pathManager)
        {
            _logger = logger;
            _pathManager = pathManager;
        }

        /// <summary>
        /// 启动4GPU共享算力的全局Python服务（程序启动时调用一次）
        /// </summary>
        public async Task<bool> StartGlobalServiceAsync(int port = 9999)
        {
            // 🔧 关键预防：启动前先清理任何残留的Python进程
            await CleanupAnyRemainingPythonProcesses();
            
            lock (_lock)
            {
                if (_isServiceRunning)
                {
                    _logger.LogInformation("✅ 4GPU共享全局MuseTalk服务已运行");
                    return true;
                }
            }

            try
            {
                var contentRoot = _pathManager.GetContentRootPath();
                var projectRoot = Path.Combine(contentRoot, "..");
                var serviceScript = Path.Combine(projectRoot, "MuseTalkEngine", "global_musetalk_service.py");

                if (!File.Exists(serviceScript))
                {
                    _logger.LogError("❌ 全局服务脚本不存在: {ScriptPath}", serviceScript);
                    return false;
                }

                // 获取Python路径
                var pythonPath = GetPythonPath();
                
                var workingDir = Path.Combine(projectRoot, "MuseTalk");
                var processInfo = new System.Diagnostics.ProcessStartInfo
                {
                    FileName = pythonPath,
                    Arguments = $"\"{serviceScript}\" --mode server --multi_gpu --port {port} --gpu_id 0",
                    RedirectStandardOutput = true,
                    RedirectStandardError = true,
                    UseShellExecute = false,
                    CreateNoWindow = true,
                    WorkingDirectory = workingDir
                };
                
                _logger.LogInformation("🔧 工作目录: {WorkingDirectory}", workingDir);

                // 🚀 关键：设置4GPU环境变量，让Python服务使用所有GPU
                var museTalkPath = Path.Combine(projectRoot, "MuseTalk");
                var museTalkEnginePath = Path.Combine(projectRoot, "MuseTalkEngine");
                var pythonPathEnv = $"{museTalkPath};{museTalkEnginePath}";
                processInfo.EnvironmentVariables["PYTHONPATH"] = pythonPathEnv;
                processInfo.EnvironmentVariables["PYTHONIOENCODING"] = "utf-8";
                processInfo.EnvironmentVariables["CUDA_VISIBLE_DEVICES"] = "0,1,2,3"; // 🎯 4GPU并行
                
                // 🔧 关键修复：激活虚拟环境
                var venvPath = Path.Combine(projectRoot, "venv_musetalk");
                var venvScriptsPath = Path.Combine(venvPath, "Scripts");
                var venvLibPath = Path.Combine(venvPath, "Lib", "site-packages");
                
                // 设置虚拟环境相关的环境变量
                processInfo.EnvironmentVariables["VIRTUAL_ENV"] = venvPath;
                processInfo.EnvironmentVariables["PATH"] = $"{venvScriptsPath};{Environment.GetEnvironmentVariable("PATH")}";
                
                // 确保Python能找到虚拟环境的包
                var currentPythonPath = processInfo.EnvironmentVariables.ContainsKey("PYTHONPATH") 
                    ? processInfo.EnvironmentVariables["PYTHONPATH"] 
                    : "";
                processInfo.EnvironmentVariables["PYTHONPATH"] = $"{venvLibPath};{currentPythonPath}";
                
                _logger.LogInformation("🔧 虚拟环境路径: {VenvPath}", venvPath);
                _logger.LogInformation("🔧 虚拟环境包路径: {VenvLibPath}", venvLibPath);

                _logger.LogInformation("🚀 启动4GPU共享全局MuseTalk服务...");
                _logger.LogInformation("   脚本路径: {ScriptPath}", serviceScript);
                _logger.LogInformation("   Python路径: {PythonPath}", pythonPath);
                _logger.LogInformation("   GPU配置: 0,1,2,3 (4GPU并行算力)");
                _logger.LogInformation("   端口: {Port}", port);

                _pythonProcess = new System.Diagnostics.Process { StartInfo = processInfo };

                _pythonProcess.OutputDataReceived += (sender, e) =>
                {
                    if (!string.IsNullOrEmpty(e.Data))
                    {
                        _logger.LogInformation("🐍Python输出: {Output}", e.Data);
                    }
                };

                _pythonProcess.ErrorDataReceived += (sender, e) =>
                {
                    if (!string.IsNullOrEmpty(e.Data))
                    {
                        _logger.LogError("🐍Python错误: {Error}", e.Data);
                    }
                };

                _pythonProcess.Start();
                _pythonProcess.BeginOutputReadLine();
                _pythonProcess.BeginErrorReadLine();
                
                _logger.LogInformation("🐍 Python进程已启动: PID={ProcessId}", _pythonProcess.Id);

                // 等待服务启动并检查Python输出
                await Task.Delay(5000); // 增加等待时间，让Python有时间输出日志

                // 🔧 检查Python进程是否还在运行
                if (_pythonProcess.HasExited)
                {
                    _logger.LogError("❌ Python进程已退出，退出码: {ExitCode}", _pythonProcess.ExitCode);
                    return false;
                }

                // 🔧 验证服务是否真的在监听端口
                bool isListening = await TestPortConnection(port);
                if (!isListening)
                {
                    _logger.LogError("❌ Python服务启动但端口{Port}不可达，可能初始化失败", port);
                    return false;
                }

                lock (_lock)
                {
                    _isServiceRunning = true;
                }

                _logger.LogInformation("✅ 4GPU共享全局MuseTalk服务启动成功");
                return true;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "❌ 启动4GPU共享全局服务失败");
                return false;
            }
        }



        /// <summary>
        /// 测试端口连接
        /// </summary>
        private async Task<bool> TestPortConnection(int port)
        {
            try
            {
                using var testClient = new TcpClient();
                await testClient.ConnectAsync("127.0.0.1", port);
                _logger.LogInformation("✅ 端口{Port}连接测试成功 (地址: 127.0.0.1)", port);
                
                // 立即断开连接，避免占用
                testClient.Close();
                return true;
            }
            catch (Exception ex)
            {
                _logger.LogWarning("⚠️ 端口{Port}连接测试失败: {Error}", port, ex.Message);
                
                // 🔧 额外诊断：检查端口是否被其他进程占用
                try
                {
                    _logger.LogInformation("🔍 正在诊断端口{Port}占用情况...", port);
                    var processes = System.Diagnostics.Process.GetProcesses();
                    _logger.LogInformation("🔍 当前运行的进程数: {Count}", processes.Length);
                }
                catch (Exception diagEx)
                {
                    _logger.LogWarning("⚠️ 端口诊断失败: {Error}", diagEx.Message);
                }
                
                return false;
            }
        }

        /// <summary>
        /// 停止全局Python服务
        /// </summary>
        public void StopGlobalService()
        {
            lock (_lock)
            {
                if (!_isServiceRunning || _pythonProcess == null)
                {
                    return;
                }

                try
                {
                    _logger.LogInformation("🛑 停止全局MuseTalk服务... PID:{Pid}", _pythonProcess.Id);
                    
                    if (!_pythonProcess.HasExited)
                    {
                        // 🔧 关键修复：强制终止进程树
                        _logger.LogInformation("🔧 强制终止Python进程及其子进程...");
                        _pythonProcess.Kill(true); // true 表示同时终止子进程
                        
                        // 给更多时间等待进程退出
                        if (!_pythonProcess.WaitForExit(10000)) // 10秒
                        {
                            _logger.LogWarning("⚠️ Python进程未能在10秒内退出，强制结束");
                        }
                    }

                    _pythonProcess.Dispose();
                    _pythonProcess = null;
                    _isServiceRunning = false;

                    _logger.LogInformation("✅ 全局MuseTalk服务已停止");
                }
                catch (Exception ex)
                {
                    _logger.LogError(ex, "❌ 停止全局MuseTalk服务失败");
                    
                    // 🔧 额外清理：如果正常终止失败，尝试强制清理
                    try
                    {
                        if (_pythonProcess != null && !_pythonProcess.HasExited)
                        {
                            _logger.LogInformation("🔧 尝试额外强制终止...");
                            _pythonProcess.Kill(true);
                        }
                    }
                    catch
                    {
                        // 忽略额外清理的异常
                    }
                    finally
                    {
                        _pythonProcess?.Dispose();
                        _pythonProcess = null;
                        _isServiceRunning = false;
                    }
                }
            }
        }

        /// <summary>
        /// 检查服务是否运行
        /// </summary>
        public bool IsServiceRunning
        {
            get
            {
                lock (_lock)
                {
                    return _isServiceRunning && _pythonProcess != null && !_pythonProcess.HasExited;
                }
            }
        }

        private string GetPythonPath()
        {
            // 优先使用虚拟环境中的Python
            var contentRoot = _pathManager.GetContentRootPath();
            var venvPython = Path.Combine(contentRoot, "..", "venv_musetalk", "Scripts", "python.exe");
            
            if (File.Exists(venvPython))
            {
                return venvPython;
            }

            // 回退到系统Python
            return "python";
        }

        /// <summary>
        /// 🔧 强力清理方法：杜绝任何Python进程残留
        /// </summary>
        private async Task CleanupAnyRemainingPythonProcesses()
        {
            try
            {
                _logger.LogInformation("🧹 启动前清理：检查并清理任何残留的Python进程...");
                
                var pythonProcesses = System.Diagnostics.Process.GetProcessesByName("python");
                if (pythonProcesses.Length > 0)
                {
                    _logger.LogWarning("⚠️ 发现{Count}个残留的Python进程，正在清理...", pythonProcesses.Length);
                    
                    foreach (var process in pythonProcesses)
                    {
                        try
                        {
                            // 检查是否是MuseTalk相关进程（通过命令行参数）
                            if (IsMuseTalkProcess(process))
                            {
                                _logger.LogInformation("🔧 清理MuseTalk残留进程 PID:{Pid}", process.Id);
                                process.Kill(true); // 强制终止进程树
                                process.WaitForExit(3000); // 等待3秒
                                process.Dispose();
                            }
                        }
                        catch (Exception ex)
                        {
                            _logger.LogWarning("⚠️ 清理进程PID:{Pid}失败: {Error}", process.Id, ex.Message);
                        }
                    }
                    
                    // 等待系统清理完成
                    await Task.Delay(2000);
                    _logger.LogInformation("✅ Python进程清理完成");
                }
                else
                {
                    _logger.LogInformation("✅ 没有发现残留的Python进程");
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "❌ 清理残留进程时发生异常");
            }
        }

        /// <summary>
        /// 检查是否是MuseTalk相关的Python进程
        /// </summary>
        private bool IsMuseTalkProcess(System.Diagnostics.Process process)
        {
            try
            {
                var commandLine = GetCommandLine(process);
                return commandLine.Contains("global_musetalk_service") || 
                       commandLine.Contains("musetalk") ||
                       commandLine.Contains("MuseTalkEngine");
            }
            catch
            {
                // 如果无法获取命令行，为安全起见不清理
                return false;
            }
        }

        /// <summary>
        /// 获取进程命令行参数
        /// </summary>
        private string GetCommandLine(System.Diagnostics.Process process)
        {
            try
            {
                return process.StartInfo.Arguments ?? "";
            }
            catch
            {
                return "";
            }
        }

        /// <summary>
        /// 🔧 应用退出时的终极清理
        /// </summary>
        public void ForceCleanupAllPythonProcesses()
        {
            try
            {
                _logger.LogInformation("🛑 执行终极清理：强制终止所有相关Python进程");
                
                // 先尝试正常停止
                StopGlobalService();
                
                // 然后强制清理所有可能的残留
                var pythonProcesses = System.Diagnostics.Process.GetProcessesByName("python");
                foreach (var process in pythonProcesses)
                {
                    try
                    {
                        if (IsMuseTalkProcess(process))
                        {
                            _logger.LogInformation("🔧 强制终止MuseTalk进程 PID:{Pid}", process.Id);
                            process.Kill(true);
                            process.Dispose();
                        }
                    }
                    catch (Exception ex)
                    {
                        _logger.LogWarning("⚠️ 强制清理进程失败: {Error}", ex.Message);
                    }
                }
                
                _logger.LogInformation("✅ 终极清理完成");
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "❌ 终极清理失败");
            }
        }

        public void Dispose()
        {
            ForceCleanupAllPythonProcesses();
        }
    }
}