using Whisper.net;
using LmyDigitalHuman.Services;
using LmyDigitalHuman.Models;
using System.Diagnostics;

namespace LmyDigitalHuman.Services.Core
{
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

                // 获取模型路径配置 - 使用挂载的模型目录
                var modelSize = _configuration["RealtimeDigitalHuman:WhisperNet:ModelSize"] ?? "Large";
                var modelFileName = GetModelFileName(modelSize);
                var modelPath = Path.Combine("/models/whisper", modelFileName);

                // 检查模型文件是否存在
                if (!File.Exists(modelPath))
                {
                    _logger.LogError("Whisper模型文件不存在: {ModelPath}", modelPath);
                    _logger.LogError("请手动下载模型文件并放置到宿主机的 /opt/musetalk/models/whisper/ 目录");
                    _logger.LogError("下载地址: {Url}", GetModelDownloadUrl(modelSize));
                    _logger.LogError("文件名应为: {FileName}", modelFileName);
                    
                    throw new FileNotFoundException(
                        $"Whisper模型文件不存在: {modelPath}. " +
                        $"请从 {GetModelDownloadUrl(modelSize)} 下载模型文件，" +
                        $"并将其放置到宿主机的 /opt/musetalk/models/whisper/{modelFileName}");
                }

                _logger.LogInformation("找到Whisper模型文件: {ModelPath}", modelPath);

                // 创建Whisper工厂和处理器
                _whisperFactory = WhisperFactory.FromPath(modelPath);
                _whisperProcessor = _whisperFactory.CreateBuilder()
                    .WithLanguage("zh") // 默认中文
                    .Build();

                _isInitialized = true;
                _logger.LogInformation("Whisper.NET 初始化成功，使用模型: {ModelSize} ({ModelPath})", modelSize, modelPath);
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

        // 移除了自动下载功能，改为提示用户手动下载模型
        // 模型应该被放置在宿主机的 /opt/musetalk/models/whisper/ 目录
        // 容器内映射为 /models/whisper/ 目录

        private string GetModelFileName(string modelSize)
        {
            // 根据模型大小返回对应的文件名
            return modelSize.ToLower() switch
            {
                "tiny" => "ggml-tiny.bin",
                "base" => "ggml-base.bin",
                "small" => "ggml-small.bin",
                "medium" => "ggml-medium.bin",
                "large" => "ggml-large-v3.bin",
                _ => "ggml-base.bin"
            };
        }

        private string GetModelDownloadUrl(string modelSize)
        {
            // Whisper模型下载地址
            var baseUrl = "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/";
            var fileName = GetModelFileName(modelSize);
            return $"{baseUrl}{fileName}";
        }

        public void Dispose()
        {
            _whisperProcessor?.Dispose();
            _whisperFactory?.Dispose();
            _initSemaphore?.Dispose();
            _isInitialized = false;
        }
    }
}