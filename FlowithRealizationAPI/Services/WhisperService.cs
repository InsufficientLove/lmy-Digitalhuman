using FlowithRealizationAPI.Models;
using System.ComponentModel;
using System.Diagnostics;
using System.Text;
using System.Text.Json;

namespace FlowithRealizationAPI.Services
{
    /// <summary>
    /// Whisper语音转文本服务实现
    /// </summary>
    public class WhisperService : IWhisperService
    {
        private readonly ILogger<WhisperService> _logger;
        private readonly IConfiguration _configuration;
        private readonly string _whisperPath;
        private readonly string _tempPath;
        private readonly string _modelPath;

        // 支持的音频格式
        private readonly List<string> _supportedFormats = new()
        {
            ".wav", ".mp3", ".mp4", ".mpeg", ".mpga", ".m4a", ".ogg", ".flac", ".webm"
        };

        // 可用的模型
        private readonly List<string> _availableModels = new()
        {
            "tiny", "base", "small", "medium", "large", "large-v2", "large-v3"
        };

        public WhisperService(ILogger<WhisperService> logger, IConfiguration configuration)
        {
            _logger = logger;
            _configuration = configuration;
            
            _whisperPath = _configuration["RealtimeDigitalHuman:Whisper:Path"] ?? "whisper";
            _tempPath = _configuration["RealtimeDigitalHuman:Temp:Path"] ?? "temp";
            _modelPath = _configuration["RealtimeDigitalHuman:Whisper:ModelPath"] ?? "models";
            
            // 确保临时目录存在
            Directory.CreateDirectory(_tempPath);
            Directory.CreateDirectory(_modelPath);
        }

        /// <summary>
        /// 语音转文本
        /// </summary>
        public async Task<WhisperTranscriptionResult> TranscribeAsync(IFormFile audioFile)
        {
            var stopwatch = Stopwatch.StartNew();
            string tempFilePath = "";
            WhisperTranscriptionResult result = null;
            try
            {
                _logger.LogInformation("开始语音转文本，文件: {FileName}, 大小: {Size} bytes", 
                    audioFile.FileName, audioFile.Length);

                // 1. 验证文件格式
                var fileExtension = Path.GetExtension(audioFile.FileName).ToLower();
                if (!_supportedFormats.Contains(fileExtension))
                {
                    throw new ArgumentException($"不支持的音频格式: {fileExtension}");
                }

                // 2. 保存临时文件
                var tempFileName = $"whisper_input_{Guid.NewGuid()}{fileExtension}";
                tempFilePath = Path.Combine(_tempPath, tempFileName);
                
                using (var stream = new FileStream(tempFilePath, FileMode.Create))
                {
                    await audioFile.CopyToAsync(stream);
                }

                // 3. 执行Whisper转录
                result = await TranscribeFileAsync(tempFilePath);
                
                stopwatch.Stop();
                result.ProcessingTime = stopwatch.ElapsedMilliseconds;
                
                _logger.LogInformation("语音转文本完成，耗时: {Time}ms, 文本长度: {Length}", 
                    stopwatch.ElapsedMilliseconds, result.Text.Length);

                return result;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "语音转文本失败");
                stopwatch.Stop();
                
                return new WhisperTranscriptionResult
                {
                    Text = "",
                    Confidence = 0.0f,
                    Language = "unknown",
                    ProcessingTime = stopwatch.ElapsedMilliseconds,
                    WordTimestamps = new List<WordTimestamp>()
                };
            }
            finally
            {
                // 4. 清理临时文件（仅在Whisper命令和输出解析后再清理）
                if (!string.IsNullOrEmpty(tempFilePath) && File.Exists(tempFilePath))
                {
                    try { File.Delete(tempFilePath); } catch { }
                }
                // 清理Whisper输出目录和过期文件
                await CleanupTempFilesAsync(null);
            }
        }

        /// <summary>
        /// 语音转文本（支持多种音频格式）
        /// </summary>
        public async Task<WhisperTranscriptionResult> TranscribeAsync(Stream audioStream, string fileName)
        {
            var stopwatch = Stopwatch.StartNew();
            string tempFilePath = "";
            WhisperTranscriptionResult result = null;
            try
            {
                _logger.LogInformation("开始语音转文本，文件: {FileName}", fileName);

                // 1. 验证文件格式
                var fileExtension = Path.GetExtension(fileName).ToLower();
                if (!_supportedFormats.Contains(fileExtension))
                {
                    throw new ArgumentException($"不支持的音频格式: {fileExtension}");
                }

                // 2. 保存临时文件
                var tempFileName = $"whisper_stream_{Guid.NewGuid()}{fileExtension}";
                tempFilePath = Path.Combine(_tempPath, tempFileName);
                
                using (var fileStream = new FileStream(tempFilePath, FileMode.Create))
                {
                    await audioStream.CopyToAsync(fileStream);
                }

                // 3. 执行Whisper转录
                result = await TranscribeFileAsync(tempFilePath);
                
                stopwatch.Stop();
                result.ProcessingTime = stopwatch.ElapsedMilliseconds;
                
                return result;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "语音转文本失败");
                stopwatch.Stop();
                
                return new WhisperTranscriptionResult
                {
                    Text = "",
                    Confidence = 0.0f,
                    Language = "unknown",
                    ProcessingTime = stopwatch.ElapsedMilliseconds,
                    WordTimestamps = new List<WordTimestamp>()
                };
            }
            finally
            {
                // 4. 清理临时文件（仅在Whisper命令和输出解析后再清理）
                if (!string.IsNullOrEmpty(tempFilePath) && File.Exists(tempFilePath))
                {
                    try { File.Delete(tempFilePath); } catch { }
                }
                // 清理Whisper输出目录和过期文件
                await CleanupTempFilesAsync(null);
            }
        }

        /// <summary>
        /// 批量语音转文本
        /// </summary>
        public async Task<List<WhisperTranscriptionResult>> TranscribeBatchAsync(List<IFormFile> audioFiles)
        {
            var results = new List<WhisperTranscriptionResult>();
            
            _logger.LogInformation("开始批量语音转文本，文件数量: {Count}", audioFiles.Count);

            // 并行处理多个文件
            var tasks = audioFiles.Select(async file =>
            {
                try
                {
                    return await TranscribeAsync(file);
                }
                catch (Exception ex)
                {
                    _logger.LogError(ex, "批量处理文件失败: {FileName}", file.FileName);
                    return new WhisperTranscriptionResult
                    {
                        Text = "",
                        Confidence = 0.0f,
                        Language = "unknown",
                        ProcessingTime = 0,
                        WordTimestamps = new List<WordTimestamp>()
                    };
                }
            });

            results = (await Task.WhenAll(tasks)).ToList();
            
            _logger.LogInformation("批量语音转文本完成，成功: {Success}/{Total}", 
                results.Count(r => !string.IsNullOrEmpty(r.Text)), results.Count);

            return results;
        }

        /// <summary>
        /// 检查Whisper服务状态
        /// </summary>
        public async Task<bool> IsServiceHealthyAsync()
        {
            try
            {
                var result = await RunWhisperCommandAsync("--help");
                return result.Success;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "检查Whisper服务状态失败");
                return false;
            }
        }

        /// <summary>
        /// 获取支持的音频格式
        /// </summary>
        public async Task<List<string>> GetSupportedFormatsAsync()
        {
            return await Task.FromResult(_supportedFormats);
        }

        /// <summary>
        /// 获取可用的语言模型
        /// </summary>
        public async Task<List<string>> GetAvailableModelsAsync()
        {
            return await Task.FromResult(_availableModels);
        }

        /// <summary>
        /// 执行Whisper转录文件
        /// </summary>
        private async Task<WhisperTranscriptionResult> TranscribeFileAsync(string filePath)
        {
            try
            {
                // 首先获取可用的whisper命令
                var whisperCommand = await FindWhisperCommandAsync();
                if (string.IsNullOrEmpty(whisperCommand))
                {
                    throw new Exception("找不到可用的whisper命令");
                }

                // 构建Whisper命令参数
                var model = _configuration["RealtimeDigitalHuman:Whisper:Model"] ?? "base";
                var language = _configuration["RealtimeDigitalHuman:Whisper:Language"] ?? "zh";
                var outputFormat = "json";
                
                var arguments = BuildWhisperArguments(filePath, model, language, outputFormat, whisperCommand);
                
                _logger.LogInformation("执行Whisper命令: {Command} {Arguments}", whisperCommand, arguments);
                
                var result = await RunWhisperCommandAsync(arguments);
                
                if (!result.Success)
                {
                    throw new Exception($"Whisper转录失败: {result.Error}");
                }

                // 解析Whisper输出
                return ParseWhisperOutput(result.Output);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Whisper转录文件失败: {FilePath}", filePath);
                throw;
            }
        }

        /// <summary>
        /// 运行Whisper命令
        /// </summary>
        private async Task<(bool Success, string Output, string Error)> RunWhisperCommandAsync(string arguments)
        {
            try
            {
                // 首先检查whisper命令是否可用
                var whisperCommand = await FindWhisperCommandAsync();
                if (string.IsNullOrEmpty(whisperCommand))
                {
                    return (false, "", "找不到whisper命令。请确保已安装openai-whisper并添加到PATH环境变量中。");
                }

                var processInfo = new ProcessStartInfo
                {
                    FileName = whisperCommand,
                    Arguments = arguments,
                    RedirectStandardOutput = true,
                    RedirectStandardError = true,
                    UseShellExecute = false,
                    CreateNoWindow = true,
                    WorkingDirectory = _tempPath
                };

                // 设置环境变量
                processInfo.Environment["PYTHONIOENCODING"] = "utf-8";
                processInfo.Environment["PYTHONUNBUFFERED"] = "1";
                processInfo.Environment["PYTHONUTF8"] = "1";

                _logger.LogInformation("启动Whisper进程，命令: {Command} {Arguments}", whisperCommand, arguments);

                using var process = Process.Start(processInfo);
                if (process == null)
                {
                    return (false, "", "无法启动Whisper进程");
                }

                var outputBuilder = new StringBuilder();
                var errorBuilder = new StringBuilder();

                // 使用异步读取输出，避免死锁
                process.OutputDataReceived += (sender, e) =>
                {
                    if (e.Data != null)
                    {
                        outputBuilder.AppendLine(e.Data);
                        _logger.LogDebug("Whisper输出: {Data}", e.Data);
                    }
                };

                process.ErrorDataReceived += (sender, e) =>
                {
                    if (e.Data != null)
                    {
                        errorBuilder.AppendLine(e.Data);
                        _logger.LogDebug("Whisper错误: {Data}", e.Data);
                    }
                };

                process.BeginOutputReadLine();
                process.BeginErrorReadLine();

                // 设置超时时间（5分钟）
                var timeoutMs = _configuration.GetValue<int>("RealtimeDigitalHuman:Whisper:TimeoutMs", 300000);
                var completed = await process.WaitForExitAsync(TimeSpan.FromMilliseconds(timeoutMs));
                
                if (!completed)
                {
                    _logger.LogError("Whisper进程超时，正在终止进程");
                    try
                    {
                        process.Kill(true);
                    }
                    catch (Exception killEx)
                    {
                        _logger.LogError(killEx, "终止Whisper进程失败");
                    }
                    return (false, "", "Whisper进程执行超时");
                }

                var output = outputBuilder.ToString();
                var error = errorBuilder.ToString();
                
                _logger.LogInformation("Whisper命令执行完成，退出代码: {ExitCode}", process.ExitCode);
                
                if (process.ExitCode != 0)
                {
                    _logger.LogError("Whisper命令执行失败，错误输出: {Error}", error);
                    return (false, output, error);
                }
                
                return (true, output, error);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "运行Whisper命令失败");
                return (false, "", ex.Message);
            }
        }

        /// <summary>
        /// 查找Whisper命令
        /// </summary>
        private async Task<string> FindWhisperCommandAsync()
        {
            try
            {
                bool result = false;
                // 1. 优先使用配置文件中指定的Python路径
                var configuredPythonPath = _configuration["RealtimeDigitalHuman:Whisper:PythonPath"];
                if (!string.IsNullOrEmpty(configuredPythonPath) && File.Exists(configuredPythonPath))
                {
                    _logger.LogInformation("使用配置的Python路径: {PythonPath}", configuredPythonPath);
                    
                    // 测试配置的Python路径是否可用
                    result = await TestCommandAsync(configuredPythonPath, "-m whisper --help");
                    if (result)
                    {
                        return configuredPythonPath;
                    }
                    else
                    {
                        _logger.LogWarning("配置的Python路径不可用: {PythonPath}", configuredPythonPath);
                    }
                }

                // 2. 尝试直接调用whisper
                result = await TestCommandAsync("whisper", "--help");
                if (result)
                {
                    return "whisper";
                }

                // 3. 尝试python -m whisper
                result = await TestCommandAsync("python", "-m whisper --help");
                if (result)
                {
                    return "python";
                }

                // 4. 尝试python3 -m whisper
                result = await TestCommandAsync("python3", "-m whisper --help");
                if (result)
                {
                    return "python3";
                }

                _logger.LogError("未找到可用的Whisper命令，请确保已安装openai-whisper");
                return "";
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "查找Whisper命令失败");
                return "";
            }
        }

        /// <summary>
        /// 测试命令是否可用
        /// </summary>
        private async Task<bool> TestCommandAsync(string command, string arguments = "--help")
        {
            try
            {
                using var process = new Process();
                process.StartInfo = new ProcessStartInfo
                {
                    FileName = command,
                    Arguments = arguments,
                    RedirectStandardOutput = true,
                    RedirectStandardError = true,
                    UseShellExecute = false,
                    CreateNoWindow = true,
                    Environment =
                    {
                        ["PYTHONUTF8"] = "1",
                        ["PYTHONIOENCODING"] = "utf-8"
                    }
                };

                var outputBuilder = new StringBuilder();
                var errorBuilder = new StringBuilder();

                process.OutputDataReceived += (sender, e) =>
                {
                    if (e.Data != null) outputBuilder.AppendLine(e.Data);
                };

                process.ErrorDataReceived += (sender, e) =>
                {
                    if (e.Data != null) errorBuilder.AppendLine(e.Data);
                };

                process.Start();

                process.BeginOutputReadLine();
                process.BeginErrorReadLine();

                // 设置测试命令的超时时间（30秒）
                var completed = await process.WaitForExitAsync(TimeSpan.FromSeconds(30));
                if (!completed)
                {
                    try
                    {
                        process.Kill(true);
                    }
                    catch { }
                    return false;
                }

                string output = outputBuilder.ToString();
                string error = errorBuilder.ToString();

                // 只在失败时记录详细日志
                if (process.ExitCode != 0)
                {
                    _logger.LogDebug("命令测试失败: {Command} {Arguments}, 退出代码: {ExitCode}", 
                        command, arguments, process.ExitCode);
                }

                return process.ExitCode == 0;
            }
            catch (Exception ex)
            {
                // 测试命令失败是正常的，不记录错误日志
                return false;
            }
        }



        /// <summary>
        /// 构建Whisper命令参数
        /// </summary>
        private string BuildWhisperArguments(string inputFile, string model, string language, string outputFormat, string whisperCommand)
        {
            var outputDir = Path.Combine(_tempPath, "whisper_output");
            Directory.CreateDirectory(outputDir);
            
            var args = new List<string>();
            
            // 检查是否使用python调用whisper模块
            // 如果命令包含python.exe或者就是python/python3，则需要添加-m whisper参数
            if (whisperCommand.Contains("python.exe") || whisperCommand == "python" || whisperCommand == "python3")
            {
                args.Add("-m");
                args.Add("whisper");
            }
            
            args.AddRange(new[]
            {
                $"\"{inputFile}\"",
                $"--model {model}",
                $"--language {language}",
                $"--output_format {outputFormat}",
                $"--output_dir \"{outputDir}\"",
                "--word_timestamps True",
                "--verbose False"
            });

            // 如果有GPU支持，启用GPU加速
            if (_configuration.GetValue<bool>("RealtimeDigitalHuman:Whisper:UseGPU"))
            {
                args.Add("--device cuda");
            }

            return string.Join(" ", args);
        }

        /// <summary>
        /// 解析Whisper输出
        /// </summary>
        private WhisperTranscriptionResult ParseWhisperOutput(string output)
        {
            try
            {
                // 查找JSON输出文件
                var outputDir = Path.Combine(_tempPath, "whisper_output");
                var jsonFiles = Directory.GetFiles(outputDir, "*.json");
                
                if (jsonFiles.Length == 0)
                {
                    throw new Exception("未找到Whisper输出文件");
                }

                var jsonFile = jsonFiles[0];
                var jsonContent = File.ReadAllText(jsonFile);
                
                // 解析JSON
                var whisperResult = JsonSerializer.Deserialize<WhisperJsonResult>(jsonContent);
                
                if (whisperResult == null)
                {
                    throw new Exception("无法解析Whisper输出");
                }

                // 转换为我们的结果格式
                var result = new WhisperTranscriptionResult
                {
                    Text = whisperResult.text ?? "",
                    Language = whisperResult.language ?? "unknown",
                    Confidence = 0.0f,
                    WordTimestamps = new List<WordTimestamp>()
                };

                // 处理词语时间戳
                if (whisperResult.segments != null)
                {
                    foreach (var segment in whisperResult.segments)
                    {
                        if (segment.words != null)
                        {
                            foreach (var word in segment.words)
                            {
                                result.WordTimestamps.Add(new WordTimestamp
                                {
                                    Word = word.word ?? "",
                                    Start = word.start,
                                    End = word.end,
                                    Confidence = word.probability
                                });
                            }
                        }
                    }
                }

                // 计算平均置信度
                if (result.WordTimestamps.Count > 0)
                {
                    result.Confidence = result.WordTimestamps.Average(w => w.Confidence);
                }

                // 清理临时文件
                try
                {
                    File.Delete(jsonFile);
                }
                catch (Exception ex)
                {
                    _logger.LogWarning(ex, "清理Whisper输出文件失败: {FilePath}", jsonFile);
                }

                return result;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "解析Whisper输出失败");
                
                return new WhisperTranscriptionResult
                {
                    Text = "",
                    Confidence = 0.0f,
                    Language = "unknown",
                    ProcessingTime = 0,
                    WordTimestamps = new List<WordTimestamp>()
                };
            }
        }

        /// <summary>
        /// Whisper JSON结果格式
        /// </summary>
        private class WhisperJsonResult
        {
            public string? text { get; set; }
            public string? language { get; set; }
            public float duration { get; set; }
            public List<WhisperSegment>? segments { get; set; }
        }

        private class WhisperSegment
        {
            public int id { get; set; }
            public float start { get; set; }
            public float end { get; set; }
            public string? text { get; set; }
            public List<WhisperWord>? words { get; set; }
        }

        private class WhisperWord
        {
            public string? word { get; set; }
            public float start { get; set; }
            public float end { get; set; }
            public float probability { get; set; }
        }

        /// <summary>
        /// 清理临时文件
        /// </summary>
        private async Task CleanupTempFilesAsync(string tempFilePath)
        {
            try
            {
                // 清理Whisper输出目录
                var outputDir = Path.Combine(_tempPath, "whisper_output");
                if (Directory.Exists(outputDir))
                {
                    var files = Directory.GetFiles(outputDir);
                    foreach (var file in files)
                    {
                        try
                        {
                            File.Delete(file);
                            _logger.LogDebug("已清理Whisper输出文件: {FilePath}", file);
                        }
                        catch (Exception ex)
                        {
                            _logger.LogWarning(ex, "清理Whisper输出文件失败: {FilePath}", file);
                        }
                    }
                }

                // 清理超过1小时的所有临时文件
                await CleanupOldTempFilesAsync();
            }
            catch (Exception ex)
            {
                _logger.LogWarning(ex, "清理临时文件失败");
            }
        }

        /// <summary>
        /// 清理过期的临时文件
        /// </summary>
        private async Task CleanupOldTempFilesAsync()
        {
            try
            {
                var cutoffTime = DateTime.Now.AddHours(-1);
                var tempFiles = Directory.GetFiles(_tempPath, "whisper_*");
                
                foreach (var file in tempFiles)
                {
                    try
                    {
                        var fileInfo = new FileInfo(file);
                        if (fileInfo.CreationTime < cutoffTime)
                        {
                            File.Delete(file);
                            _logger.LogDebug("已清理过期临时文件: {FilePath}", file);
                        }
                    }
                    catch (Exception ex)
                    {
                        _logger.LogWarning(ex, "清理过期临时文件失败: {FilePath}", file);
                    }
                }
            }
            catch (Exception ex)
            {
                _logger.LogWarning(ex, "清理过期临时文件失败");
            }
        }
    }

    // 支持超时的 WaitForExitAsync 扩展方法
    public static class ProcessExtensions
    {
        public static Task WaitForExitAsync(this Process process)
        {
            var tcs = new TaskCompletionSource<bool>();
            process.EnableRaisingEvents = true;
            process.Exited += (sender, args) => tcs.TrySetResult(true);
            if (process.HasExited) tcs.TrySetResult(true);
            return tcs.Task;
        }

        public static async Task<bool> WaitForExitAsync(this Process process, TimeSpan timeout)
        {
            var tcs = new TaskCompletionSource<bool>();
            process.EnableRaisingEvents = true;
            process.Exited += (sender, args) => tcs.TrySetResult(true);
            if (process.HasExited)
            {
                tcs.TrySetResult(true);
                return true;
            }
            
            using var cts = new CancellationTokenSource(timeout);
            cts.Token.Register(() => tcs.TrySetResult(false));
            
            return await tcs.Task;
        }
    }
} 