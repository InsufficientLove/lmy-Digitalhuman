using Whisper.net;
using LmyDigitalHuman.Models;
using System.Diagnostics;

namespace LmyDigitalHuman.Services
{
    public interface IWhisperNetService
    {
        Task<SpeechToTextResponse> TranscribeAsync(Stream audioStream, string language = "zh");
        Task<SpeechToTextResponse> TranscribeAsync(byte[] audioData, string language = "zh");
        Task<SpeechToTextResponse> TranscribeAsync(string audioFilePath, string language = "zh");
        Task<bool> InitializeAsync();
        void Dispose();
    }

    public class WhisperNetService : IWhisperNetService, IDisposable
    {
        private readonly ILogger<WhisperNetService> _logger;
        private readonly IConfiguration _configuration;
        private WhisperFactory? _whisperFactory;
        private WhisperProcessor? _whisperProcessor;
        private bool _isInitialized = false;
        private readonly SemaphoreSlim _initSemaphore = new(1, 1);

        public WhisperNetService(ILogger<WhisperNetService> logger, IConfiguration configuration)
        {
            _logger = logger;
            _configuration = configuration;
        }

        public async Task<bool> InitializeAsync()
        {
            if (_isInitialized) return true;

            await _initSemaphore.WaitAsync();
            try
            {
                if (_isInitialized) return true;

                _logger.LogInformation("正在初始化Whisper.NET...");

                // 获取模型路径配置
                var modelPath = _configuration["RealtimeDigitalHuman:WhisperNet:ModelPath"] ?? "Models/ggml-base.bin";
                var modelSize = _configuration["RealtimeDigitalHuman:WhisperNet:ModelSize"] ?? "Base";

                // 确保模型文件存在
                if (!File.Exists(modelPath))
                {
                    _logger.LogWarning("Whisper模型文件不存在: {ModelPath}, 尝试下载...", modelPath);
                    await DownloadModelAsync(modelPath, modelSize);
                }

                // 创建Whisper工厂和处理器
                _whisperFactory = WhisperFactory.FromPath(modelPath);
                _whisperProcessor = _whisperFactory.CreateBuilder()
                    .WithLanguage("zh") // 默认中文
                    .Build();

                _isInitialized = true;
                _logger.LogInformation("Whisper.NET 初始化成功");
                return true;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Whisper.NET 初始化失败");
                return false;
            }
            finally
            {
                _initSemaphore.Release();
            }
        }

        public async Task<SpeechToTextResponse> TranscribeAsync(Stream audioStream, string language = "zh")
        {
            var stopwatch = Stopwatch.StartNew();

            try
            {
                if (!_isInitialized && !await InitializeAsync())
                {
                    return new SpeechToTextResponse
                    {
                        Success = false,
                        Error = "Whisper.NET 未初始化",
                        ProcessingTime = stopwatch.ElapsedMilliseconds
                    };
                }

                _logger.LogInformation("开始语音识别，语言: {Language}", language);

                // 将音频流转换为字节数组
                using var memoryStream = new MemoryStream();
                await audioStream.CopyToAsync(memoryStream);
                var audioData = memoryStream.ToArray();

                return await TranscribeAsync(audioData, language);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "语音识别失败");
                stopwatch.Stop();
                
                return new SpeechToTextResponse
                {
                    Success = false,
                    Error = ex.Message,
                    ProcessingTime = stopwatch.ElapsedMilliseconds
                };
            }
        }

        public async Task<SpeechToTextResponse> TranscribeAsync(byte[] audioData, string language = "zh")
        {
            var stopwatch = Stopwatch.StartNew();

            try
            {
                if (!_isInitialized && !await InitializeAsync())
                {
                    return new SpeechToTextResponse
                    {
                        Success = false,
                        Error = "Whisper.NET 未初始化",
                        ProcessingTime = stopwatch.ElapsedMilliseconds
                    };
                }

                _logger.LogInformation("开始处理音频数据，大小: {Size} bytes", audioData.Length);

                // 转换音频格式为Whisper所需的格式
                var processedAudio = await PreprocessAudioAsync(audioData);

                // 执行语音识别
                var segments = new List<string>();
                float totalConfidence = 0f;
                int segmentCount = 0;

                await foreach (var segment in _whisperProcessor!.ProcessAsync(processedAudio))
                {
                    if (!string.IsNullOrWhiteSpace(segment.Text))
                    {
                        segments.Add(segment.Text.Trim());
                        totalConfidence += segment.Probability;
                        segmentCount++;
                        
                        _logger.LogDebug("识别片段: {Text} (置信度: {Confidence:F2})", 
                            segment.Text.Trim(), segment.Probability);
                    }
                }

                stopwatch.Stop();

                var result = string.Join(" ", segments);
                var avgConfidence = segmentCount > 0 ? totalConfidence / segmentCount : 0f;

                _logger.LogInformation("语音识别完成: 文本='{Text}', 置信度={Confidence:F2}, 耗时={Time}ms", 
                    result, avgConfidence, stopwatch.ElapsedMilliseconds);

                return new SpeechToTextResponse
                {
                    Success = true,
                    Text = result,
                    Confidence = avgConfidence,
                    ProcessingTime = stopwatch.ElapsedMilliseconds,
                    Language = language,
                    Segments = segments
                };
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "语音识别处理失败");
                stopwatch.Stop();
                
                return new SpeechToTextResponse
                {
                    Success = false,
                    Error = ex.Message,
                    ProcessingTime = stopwatch.ElapsedMilliseconds
                };
            }
        }

        public async Task<SpeechToTextResponse> TranscribeAsync(string audioFilePath, string language = "zh")
        {
            var stopwatch = Stopwatch.StartNew();

            try
            {
                if (!File.Exists(audioFilePath))
                {
                    return new SpeechToTextResponse
                    {
                        Success = false,
                        Error = $"音频文件不存在: {audioFilePath}",
                        ProcessingTime = stopwatch.ElapsedMilliseconds
                    };
                }

                _logger.LogInformation("开始处理音频文件: {FilePath}", audioFilePath);

                // 读取音频文件
                var audioData = await File.ReadAllBytesAsync(audioFilePath);
                
                // 调用现有的字节数组处理方法
                return await TranscribeAsync(audioData, language);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "处理音频文件失败: {FilePath}", audioFilePath);
                stopwatch.Stop();
                
                return new SpeechToTextResponse
                {
                    Success = false,
                    Error = ex.Message,
                    ProcessingTime = stopwatch.ElapsedMilliseconds
                };
            }
        }

        private async Task<float[]> PreprocessAudioAsync(byte[] audioData)
        {
            // 这里需要将音频数据转换为Whisper所需的16kHz单声道float数组
            // 可以使用NAudio或FFMpegCore来处理音频格式转换
            
            // 简化实现：假设输入已经是正确格式
            // 实际项目中需要添加音频格式转换逻辑
            
            var floatArray = new float[audioData.Length / 2]; // 假设16位音频
            for (int i = 0; i < floatArray.Length; i++)
            {
                var sample = BitConverter.ToInt16(audioData, i * 2);
                floatArray[i] = sample / 32768.0f; // 归一化到[-1, 1]
            }
            
            return floatArray;
        }

        private async Task DownloadModelAsync(string modelPath, string modelSize)
        {
            try
            {
                _logger.LogInformation("开始下载Whisper模型: {ModelSize}", modelSize);
                
                // 确保目录存在
                var directory = Path.GetDirectoryName(modelPath);
                if (!string.IsNullOrEmpty(directory))
                {
                    Directory.CreateDirectory(directory);
                }

                // 根据模型大小选择下载URL
                var modelUrl = GetModelDownloadUrl(modelSize);
                
                using var httpClient = new HttpClient();
                httpClient.Timeout = TimeSpan.FromMinutes(30); // 30分钟超时
                
                _logger.LogInformation("正在从 {Url} 下载模型...", modelUrl);
                
                var response = await httpClient.GetAsync(modelUrl);
                response.EnsureSuccessStatusCode();
                
                await using var fileStream = File.Create(modelPath);
                await response.Content.CopyToAsync(fileStream);
                
                _logger.LogInformation("模型下载完成: {ModelPath}", modelPath);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "下载Whisper模型失败");
                throw;
            }
        }

        private string GetModelDownloadUrl(string modelSize)
        {
            // Whisper模型下载地址
            var baseUrl = "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/";
            
            return modelSize.ToLower() switch
            {
                "tiny" => $"{baseUrl}ggml-tiny.bin",
                "base" => $"{baseUrl}ggml-base.bin",
                "small" => $"{baseUrl}ggml-small.bin",
                "medium" => $"{baseUrl}ggml-medium.bin",
                "large" => $"{baseUrl}ggml-large-v3.bin",
                _ => $"{baseUrl}ggml-base.bin"
            };
        }

        public void Dispose()
        {
            _whisperProcessor?.Dispose();
            _whisperFactory?.Dispose();
            _initSemaphore?.Dispose();
            _isInitialized = false;
        }
    }

    // 扩展的响应模型
    public class SpeechToTextResponse
    {
        public bool Success { get; set; }
        public string Text { get; set; } = string.Empty;
        public float Confidence { get; set; }
        public long ProcessingTime { get; set; }
        public string Language { get; set; } = "zh";
        public string Error { get; set; } = string.Empty;
        public List<string> Segments { get; set; } = new();
        public double Duration { get; internal set; }
    }
}