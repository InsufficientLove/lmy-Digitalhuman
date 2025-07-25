using System.Diagnostics;
using System.Text;
using LmyDigitalHuman.Models;
using LmyDigitalHuman.Services.Extensions;

namespace LmyDigitalHuman.Services
{
    /// <summary>
    /// Edge TTS 语音合成服务实现
    /// </summary>
    public class EdgeTTSService : IEdgeTTSService
    {
        private readonly ILogger<EdgeTTSService> _logger;
        private readonly IConfiguration _configuration;
        private readonly string _outputPath;
        private readonly string _defaultVoice;

        // 中文语音列表
        private readonly List<VoiceInfo> _chineseVoices = new()
        {
            new VoiceInfo { Name = "zh-CN-XiaoxiaoNeural", DisplayName = "晓晓", Language = "zh-CN", Gender = "Female", Style = "友好" },
            new VoiceInfo { Name = "zh-CN-XiaoyiNeural", DisplayName = "晓伊", Language = "zh-CN", Gender = "Female", Style = "专业" },
            new VoiceInfo { Name = "zh-CN-XiaochenNeural", DisplayName = "晓辰", Language = "zh-CN", Gender = "Female", Style = "活泼" },
            new VoiceInfo { Name = "zh-CN-XiaohanNeural", DisplayName = "晓涵", Language = "zh-CN", Gender = "Female", Style = "温柔" },
            new VoiceInfo { Name = "zh-CN-XiaomoNeural", DisplayName = "晓墨", Language = "zh-CN", Gender = "Female", Style = "成熟" },
            new VoiceInfo { Name = "zh-CN-XiaoruiNeural", DisplayName = "晓睿", Language = "zh-CN", Gender = "Female", Style = "知性" },
            new VoiceInfo { Name = "zh-CN-XiaoshuangNeural", DisplayName = "晓双", Language = "zh-CN", Gender = "Female", Style = "可爱" },
            new VoiceInfo { Name = "zh-CN-XiaoxuanNeural", DisplayName = "晓萱", Language = "zh-CN", Gender = "Female", Style = "温暖" },
            new VoiceInfo { Name = "zh-CN-XiaoyouNeural", DisplayName = "晓悠", Language = "zh-CN", Gender = "Female", Style = "舒缓" },
            new VoiceInfo { Name = "zh-CN-YunxiNeural", DisplayName = "云希", Language = "zh-CN", Gender = "Male", Style = "专业" },
            new VoiceInfo { Name = "zh-CN-YunyangNeural", DisplayName = "云扬", Language = "zh-CN", Gender = "Male", Style = "阳光" },
            new VoiceInfo { Name = "zh-CN-YunfengNeural", DisplayName = "云枫", Language = "zh-CN", Gender = "Male", Style = "沉稳" },
            new VoiceInfo { Name = "zh-CN-YunhaoNeural", DisplayName = "云皓", Language = "zh-CN", Gender = "Male", Style = "活力" },
            new VoiceInfo { Name = "zh-CN-YunjianNeural", DisplayName = "云健", Language = "zh-CN", Gender = "Male", Style = "成熟" },
        };

        public EdgeTTSService(ILogger<EdgeTTSService> logger, IConfiguration configuration)
        {
            _logger = logger;
            _configuration = configuration;
            _outputPath = _configuration["RealtimeDigitalHuman:EdgeTTS:OutputPath"] ?? "temp";
            _defaultVoice = _configuration["RealtimeDigitalHuman:EdgeTTS:DefaultVoice"] ?? "zh-CN-XiaoxiaoNeural";

            // 确保输出目录存在
            Directory.CreateDirectory(_outputPath);
        }

        /// <summary>
        /// 文本转语音（完整）
        /// </summary>
        public async Task<TTSResponse> TextToSpeechAsync(TTSRequest request)
        {
            var stopwatch = Stopwatch.StartNew();
            string outputFile = "";

            try
            {
                _logger.LogInformation("开始文本转语音: {Text}, 语音: {Voice}", 
                    request.Text.Length > 50 ? request.Text.Substring(0, 50) + "..." : request.Text, 
                    request.Voice);

                // 生成输出文件名
                var fileName = $"tts_{Guid.NewGuid()}.mp3";
                outputFile = Path.Combine(_outputPath, fileName);

                // 构建edge-tts命令
                var arguments = BuildEdgeTTSArguments(request.Text, request.Voice, request.Rate, request.Pitch, outputFile);
                
                // 执行edge-tts
                var result = await RunEdgeTTSCommandAsync(arguments);
                
                if (!result.Success)
                {
                    throw new Exception($"Edge TTS执行失败: {result.Error}");
                }

                // 验证输出文件
                if (!File.Exists(outputFile))
                {
                    throw new Exception("TTS输出文件生成失败");
                }

                var fileInfo = new FileInfo(outputFile);
                stopwatch.Stop();

                return new TTSResponse
                {
                    Success = true,
                    AudioPath = outputFile,
                    AudioUrl = $"/audio/{fileName}",
                    FileSize = fileInfo.Length,
                    ProcessingTime = (int)stopwatch.ElapsedMilliseconds
                };
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "文本转语音失败");
                
                // 清理失败的文件
                if (!string.IsNullOrEmpty(outputFile) && File.Exists(outputFile))
                {
                    try { File.Delete(outputFile); } catch { }
                }

                return new TTSResponse
                {
                    Success = false,
                    ProcessingTime = (int)stopwatch.ElapsedMilliseconds
                };
            }
        }

        /// <summary>
        /// 流式文本转语音
        /// </summary>
        public async IAsyncEnumerable<AudioChunkResponse> TextToSpeechStreamAsync(TTSStreamRequest request)
        {
            var tempFile = "";
            
            try
            {
                _logger.LogInformation("开始流式文本转语音: {Text}, 语音: {Voice}", 
                    request.Text.Length > 50 ? request.Text.Substring(0, 50) + "..." : request.Text,
                    request.Voice);

                // 先生成完整的音频文件
                var ttsRequest = new TTSRequest
                {
                    Text = request.Text,
                    Voice = request.Voice,
                    Rate = request.Rate,
                    Pitch = request.Pitch,
                    OutputFormat = request.OutputFormat
                };

                var ttsResult = await TextToSpeechAsync(ttsRequest);
                if (!ttsResult.Success)
                {
                    yield break;
                }

                tempFile = ttsResult.AudioPath;

                // 读取文件并分块发送
                const int chunkSize = 4096; // 4KB chunks
                using var fileStream = new FileStream(tempFile, FileMode.Open, FileAccess.Read);
                var buffer = new byte[chunkSize];
                int bytesRead;
                int chunkIndex = 0;

                while ((bytesRead = await fileStream.ReadAsync(buffer, 0, chunkSize)) > 0)
                {
                    var chunk = new byte[bytesRead];
                    Array.Copy(buffer, chunk, bytesRead);

                    yield return new AudioChunkResponse
                    {
                        AudioData = chunk,
                        ChunkIndex = chunkIndex++,
                        IsComplete = fileStream.Position >= fileStream.Length,
                        TotalDuration = ttsResult.Duration
                    };

                    // 模拟流式延迟
                    await Task.Delay(10);
                }
            }
            finally
            {
                // 清理临时文件
                if (!string.IsNullOrEmpty(tempFile) && File.Exists(tempFile))
                {
                    try { File.Delete(tempFile); } catch { }
                }
            }
        }

        /// <summary>
        /// 获取可用的语音列表
        /// </summary>
        public async Task<List<VoiceInfo>> GetAvailableVoicesAsync()
        {
            return await Task.FromResult(_chineseVoices);
        }

        /// <summary>
        /// 获取指定语言的语音列表
        /// </summary>
        public async Task<List<VoiceInfo>> GetVoicesByLanguageAsync(string language)
        {
            return await Task.FromResult(_chineseVoices.Where(v => v.Language == language).ToList());
        }

        /// <summary>
        /// 健康检查
        /// </summary>
        public async Task<bool> IsHealthyAsync()
        {
            try
            {
                // 检查edge-tts是否可用
                var result = await RunEdgeTTSCommandAsync("--help");
                return result.Success;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Edge TTS健康检查失败");
                return false;
            }
        }

        /// <summary>
        /// 构建edge-tts命令参数
        /// </summary>
        private string BuildEdgeTTSArguments(string text, string voice, string rate, string pitch, string outputFile)
        {
            var args = new List<string>();

            // 基本参数
            args.Add($"--voice \"{voice}\"");
            args.Add($"--text \"{text.Replace("\"", "\\\"")}\"");
            args.Add($"--write-media \"{outputFile}\"");

            // 可选参数
            if (!string.IsNullOrEmpty(rate) && rate != "1.0")
            {
                args.Add($"--rate \"{rate}\"");
            }

            if (!string.IsNullOrEmpty(pitch) && pitch != "0Hz")
            {
                args.Add($"--pitch \"{pitch}\"");
            }

            return string.Join(" ", args);
        }

        /// <summary>
        /// 运行edge-tts命令
        /// </summary>
        private async Task<(bool Success, string Output, string Error)> RunEdgeTTSCommandAsync(string arguments)
        {
            try
            {
                // 使用配置的Python路径（SadTalker虚拟环境）
                var pythonPath = _configuration["RealtimeDigitalHuman:SadTalker:PythonPath"] ?? 
                    _configuration["RealtimeDigitalHuman:Whisper:PythonPath"] ?? 
                    "python";

                var processInfo = new ProcessStartInfo
                {
                    FileName = pythonPath,
                    Arguments = $"-m edge_tts {arguments}",
                    RedirectStandardOutput = true,
                    RedirectStandardError = true,
                    UseShellExecute = false,
                    CreateNoWindow = true,
                    WorkingDirectory = _outputPath,
                    StandardOutputEncoding = System.Text.Encoding.UTF8,
                    StandardErrorEncoding = System.Text.Encoding.UTF8
                };

                // 设置环境变量
                processInfo.Environment["PYTHONIOENCODING"] = "utf-8";
                processInfo.Environment["PYTHONUNBUFFERED"] = "1";
                processInfo.Environment["PYTHONUTF8"] = "1";

                using var process = Process.Start(processInfo);
                if (process == null)
                {
                    return (false, "", "无法启动edge-tts进程");
                }

                var outputBuilder = new StringBuilder();
                var errorBuilder = new StringBuilder();

                // 异步读取输出
                var outputTask = process.StandardOutput.ReadToEndAsync();
                var errorTask = process.StandardError.ReadToEndAsync();

                // 等待进程完成（最多30秒）
                var completed = await process.WaitForExitAsync(TimeSpan.FromSeconds(30));
                
                if (!completed)
                {
                    try { process.Kill(true); } catch { }
                    return (false, "", "edge-tts执行超时");
                }

                var output = await outputTask;
                var error = await errorTask;

                return (process.ExitCode == 0, output, error);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "运行edge-tts命令失败");
                return (false, "", ex.Message);
            }
        }

        /// <summary>
        /// 清理过期的音频文件
        /// </summary>
        public async Task CleanupExpiredAudioFilesAsync()
        {
            try
            {
                var cutoffTime = DateTime.Now.AddHours(-24); // 保留24小时内的文件
                var files = Directory.GetFiles(_outputPath, "tts_*.mp3");

                foreach (var file in files)
                {
                    var fileInfo = new FileInfo(file);
                    if (fileInfo.CreationTime < cutoffTime)
                    {
                        try
                        {
                            File.Delete(file);
                            _logger.LogDebug("已清理过期音频文件: {File}", file);
                        }
                        catch (Exception ex)
                        {
                            _logger.LogWarning(ex, "清理音频文件失败: {File}", file);
                        }
                    }
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "清理过期音频文件失败");
            }
        }
    }
}