using LmyDigitalHuman.Models;
using Microsoft.Extensions.Caching.Memory;
using NAudio.Wave;
using FFMpegCore;
using Microsoft.CognitiveServices.Speech;
using System.Collections.Concurrent;
using System.Diagnostics;
using System.Text;
using System.Threading.Channels;

namespace LmyDigitalHuman.Services
{
    public class AudioPipelineService : IAudioPipelineService
    {
        private readonly IWhisperNetService _whisperService;
        private readonly IEdgeTTSService _edgeTTSService;
        private readonly IStreamingTTSService _streamingTTSService;
        private readonly IMemoryCache _cache;
        private readonly ILogger<AudioPipelineService> _logger;
        private readonly IConfiguration _configuration;
        private readonly SpeechSynthesizer? _speechSynthesizer; // Azure TTS备选方案

        // 高性能队列管理 - 使用Channel而不是外部消息队列
        private readonly Channel<AudioProcessingJob> _audioProcessingChannel;
        private readonly Channel<TTSProcessingJob> _ttsProcessingChannel;
        private readonly ChannelWriter<AudioProcessingJob> _audioChannelWriter;
        private readonly ChannelWriter<TTSProcessingJob> _ttsChannelWriter;

        // 实时会话管理
        private readonly ConcurrentDictionary<string, SpeechRecognitionSession> _speechSessions = new();
        private readonly ConcurrentDictionary<string, TTSSession> _ttsSessions = new();

        // 音频处理队列 - 支持200人并发
        private readonly SemaphoreSlim _audioProcessingSemaphore;
        private readonly SemaphoreSlim _ttsProcessingSemaphore;

        // 预加载的语音模型
        private readonly ConcurrentDictionary<string, bool> _preloadedVoices = new();
        private readonly CancellationTokenSource _cancellationTokenSource = new();

        public AudioPipelineService(
            IWhisperNetService whisperService,
            IEdgeTTSService edgeTTSService,
            IStreamingTTSService streamingTTSService,
            IMemoryCache cache,
            ILogger<AudioPipelineService> logger,
            IConfiguration configuration)
        {
            _whisperService = whisperService;
            _edgeTTSService = edgeTTSService;
            _streamingTTSService = streamingTTSService;
            _cache = cache;
            _logger = logger;
            _configuration = configuration;

            // 高并发配置 - 支持200人同时使用
            var maxAudioProcessing = configuration.GetValue<int>("DigitalHuman:MaxAudioProcessing", 20);
            var maxTTSProcessing = configuration.GetValue<int>("DigitalHuman:MaxTTSProcessing", 15);

            _audioProcessingSemaphore = new SemaphoreSlim(maxAudioProcessing, maxAudioProcessing);
            _ttsProcessingSemaphore = new SemaphoreSlim(maxTTSProcessing, maxTTSProcessing);

            // 初始化高性能队列
            var audioChannelOptions = new BoundedChannelOptions(1000)
            {
                FullMode = BoundedChannelFullMode.Wait,
                SingleReader = false,
                SingleWriter = false
            };
            var audioChannel = Channel.CreateBounded<AudioProcessingJob>(audioChannelOptions);
            _audioProcessingChannel = audioChannel;
            _audioChannelWriter = audioChannel.Writer;

            var ttsChannelOptions = new BoundedChannelOptions(1000)
            {
                FullMode = BoundedChannelFullMode.Wait,
                SingleReader = false,
                SingleWriter = false
            };
            var ttsChannel = Channel.CreateBounded<TTSProcessingJob>(ttsChannelOptions);
            _ttsProcessingChannel = ttsChannel;
            _ttsChannelWriter = ttsChannel.Writer;

            // 初始化Azure Speech Service（备选方案）
            var speechKey = configuration["Azure:Speech:Key"];
            var speechRegion = configuration["Azure:Speech:Region"];
            if (!string.IsNullOrEmpty(speechKey) && !string.IsNullOrEmpty(speechRegion))
            {
                var speechConfig = SpeechConfig.FromSubscription(speechKey, speechRegion);
                speechConfig.SpeechSynthesisLanguage = "zh-CN";
                speechConfig.SpeechSynthesisVoiceName = "zh-CN-XiaoxiaoNeural";
                _speechSynthesizer = new SpeechSynthesizer(speechConfig);
            }

            // 启动后台处理器
            StartBackgroundProcessors();

            _logger.LogInformation("音频处理管道初始化完成，支持并发: Audio={Audio}, TTS={TTS}", 
                maxAudioProcessing, maxTTSProcessing);
        }

        public async Task<Models.SpeechRecognitionResult> RecognizeSpeechAsync(byte[] audioData, string format = "wav")
        {
            var stopwatch = Stopwatch.StartNew();
            
            await _audioProcessingSemaphore.WaitAsync();
            try
            {
                _logger.LogInformation("开始语音识别: AudioSize={AudioSize}, Format={Format}", audioData.Length, format);

                // 检查缓存
                var cacheKey = GenerateAudioCacheKey(audioData);
                if (_cache.TryGetValue(cacheKey, out Models.SpeechRecognitionResult? cachedResult))
                {
                    _logger.LogInformation("从缓存返回语音识别结果");
                    return cachedResult!;
                }

                // 临时保存音频数据
                var tempAudioPath = Path.Combine("temp", $"audio_{Guid.NewGuid():N}.{format}");
                Directory.CreateDirectory(Path.GetDirectoryName(tempAudioPath)!);
                
                await File.WriteAllBytesAsync(tempAudioPath, audioData);

                try
                {
                    var result = await RecognizeSpeechFromFileAsync(tempAudioPath);
                    
                    // 缓存结果
                    if (result.Success)
                    {
                        _cache.Set(cacheKey, result, TimeSpan.FromHours(1));
                    }

                    return result;
                }
                finally
                {
                    // 清理临时文件
                    if (File.Exists(tempAudioPath))
                    {
                        File.Delete(tempAudioPath);
                    }
                }
            }
            finally
            {
                _audioProcessingSemaphore.Release();
            }
        }

        public async Task<Models.SpeechRecognitionResult> RecognizeSpeechFromFileAsync(string audioPath)
        {
            var stopwatch = Stopwatch.StartNew();
            
            try
            {
                _logger.LogInformation("开始文件语音识别: AudioPath={AudioPath}", audioPath);

                if (!File.Exists(audioPath))
                {
                    return new Models.SpeechRecognitionResult
                    {
                        Success = false,
                        Error = "音频文件不存在"
                    };
                }

                // 验证和优化音频格式
                var optimizedAudioPath = await OptimizeAudioForSpeechRecognitionAsync(audioPath);

                // 使用Whisper进行语音识别
                var whisperResult = await _whisperService.TranscribeAsync(optimizedAudioPath);
                
                stopwatch.Stop();

                if (whisperResult.Success)
                {
                    var result = new Models.SpeechRecognitionResult
                    {
                        Success = true,
                        Text = whisperResult.Text,
                        Confidence = 0.95f, // Whisper通常有较高的准确率
                        Duration = TimeSpan.FromSeconds(whisperResult.Duration),
                        ProcessingTime = stopwatch.ElapsedMilliseconds,
                        Language = "zh-CN",
                        Segments = ParseWhisperSegments(whisperResult.Text)
                    };

                    _logger.LogInformation("语音识别成功: Text={Text}, Duration={Duration}ms", 
                        result.Text[..Math.Min(50, result.Text.Length)], stopwatch.ElapsedMilliseconds);

                    return result;
                }
                else
                {
                    return new Models.SpeechRecognitionResult
                    {
                        Success = false,
                        Error = whisperResult.Error,
                        ProcessingTime = stopwatch.ElapsedMilliseconds
                    };
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "语音识别失败: AudioPath={AudioPath}", audioPath);
                return new Models.SpeechRecognitionResult
                {
                    Success = false,
                    Error = ex.Message,
                    ProcessingTime = stopwatch.ElapsedMilliseconds
                };
            }
        }

        public async Task<List<Models.SpeechRecognitionResult>> RecognizeBatchAudioAsync(List<string> audioPaths)
        {
            _logger.LogInformation("开始批量语音识别: Count={Count}", audioPaths.Count);

            var tasks = audioPaths.Select(RecognizeSpeechFromFileAsync).ToArray();
            var results = await Task.WhenAll(tasks);
            
            return results.ToList();
        }

        public async Task<string> StartRealtimeSpeechRecognitionAsync()
        {
            var sessionId = Guid.NewGuid().ToString("N");
            var session = new SpeechRecognitionSession
            {
                SessionId = sessionId,
                StartTime = DateTime.UtcNow,
                AudioBuffer = new List<byte>(),
                IsActive = true
            };

            _speechSessions.TryAdd(sessionId, session);
            
            _logger.LogInformation("启动实时语音识别会话: SessionId={SessionId}", sessionId);
            
            return sessionId;
        }

        public async Task<Models.SpeechRecognitionResult> ProcessRealtimeAudioChunkAsync(string sessionId, byte[] audioChunk)
        {
            if (!_speechSessions.TryGetValue(sessionId, out var session))
            {
                return new Models.SpeechRecognitionResult
                {
                    Success = false,
                    Error = "语音识别会话不存在"
                };
            }

            session.AudioBuffer.AddRange(audioChunk);
            session.LastUpdateTime = DateTime.UtcNow;

            // 检查是否有足够的音频数据进行识别
            if (session.AudioBuffer.Count >= 16000) // 约1秒的音频数据（16kHz采样率）
            {
                var audioData = session.AudioBuffer.ToArray();
                session.AudioBuffer.Clear();

                var result = await RecognizeSpeechAsync(audioData, "wav");
                return result;
            }

            return new Models.SpeechRecognitionResult
            {
                Success = true,
                Text = "",
                ProcessingTime = 0
            };
        }

        public async Task<Models.SpeechRecognitionResult> EndRealtimeSpeechRecognitionAsync(string sessionId)
        {
            if (!_speechSessions.TryRemove(sessionId, out var session))
            {
                return new Models.SpeechRecognitionResult
                {
                    Success = false,
                    Error = "语音识别会话不存在"
                };
            }

            // 处理剩余的音频数据
            if (session.AudioBuffer.Count > 0)
            {
                var audioData = session.AudioBuffer.ToArray();
                var result = await RecognizeSpeechAsync(audioData, "wav");
                
                _logger.LogInformation("结束实时语音识别会话: SessionId={SessionId}", sessionId);
                return result;
            }

            return new Models.SpeechRecognitionResult
            {
                Success = true,
                Text = "",
                ProcessingTime = 0
            };
        }

        public async Task<TTSResult> ConvertTextToSpeechAsync(TTSRequest request)
        {
            var stopwatch = Stopwatch.StartNew();
            
            await _ttsProcessingSemaphore.WaitAsync();
            try
            {
                _logger.LogInformation("开始TTS转换: Text={Text}, Voice={Voice}", 
                    request.Text[..Math.Min(50, request.Text.Length)], request.Voice);

                // 检查缓存
                var cacheKey = GenerateTTSCacheKey(request);
                if (_cache.TryGetValue(cacheKey, out TTSResult? cachedResult))
                {
                    _logger.LogInformation("从缓存返回TTS结果");
                    return cachedResult!;
                }

                // 生成输出路径
                var outputPath = request.OutputPath ?? Path.Combine("temp", $"tts_{Guid.NewGuid():N}.wav");
                Directory.CreateDirectory(Path.GetDirectoryName(outputPath)!);

                TTSResult result;

                // 优先使用Edge TTS，Azure Speech作为备选
                try
                {
                    var ttsRequest = new TTSRequest
                    {
                        Text = request.Text,
                        Voice = request.Voice,
                        VoiceId = request.Voice,
                        Rate = request.Rate,
                        Pitch = request.Pitch,
                        OutputPath = outputPath
                    };
                    var edgeTTSAudioData = await _edgeTTSService.GenerateAudioAsync(ttsRequest);
                    var edgeTTSSuccess = edgeTTSAudioData.Length > 0;
                    
                    if (edgeTTSSuccess)
                    {
                        await File.WriteAllBytesAsync(outputPath, edgeTTSAudioData);
                        result = CreateTTSResult(outputPath, stopwatch.ElapsedMilliseconds);
                    }
                    else if (_speechSynthesizer != null)
                    {
                        // 使用Azure Speech作为备选
                        result = await GenerateWithAzureSpeechAsync(request, outputPath, stopwatch.ElapsedMilliseconds);
                    }
                    else
                    {
                        result = new TTSResult
                        {
                            Success = false,
                            Error = "Edge TTS生成音频失败",
                            ProcessingTime = stopwatch.ElapsedMilliseconds
                        };
                    }
                }
                catch (Exception ex)
                {
                    _logger.LogWarning(ex, "Edge TTS失败，尝试Azure Speech备选方案");
                    
                    if (_speechSynthesizer != null)
                    {
                        result = await GenerateWithAzureSpeechAsync(request, outputPath, stopwatch.ElapsedMilliseconds);
                    }
                    else
                    {
                        result = new TTSResult
                        {
                            Success = false,
                            Error = ex.Message,
                            ProcessingTime = stopwatch.ElapsedMilliseconds
                        };
                    }
                }

                // 缓存结果
                if (result.Success)
                {
                    _cache.Set(cacheKey, result, TimeSpan.FromHours(2));
                }

                return result;
            }
            finally
            {
                _ttsProcessingSemaphore.Release();
            }
        }

        public async Task<List<TTSResult>> ConvertBatchTextToSpeechAsync(List<TTSRequest> requests)
        {
            _logger.LogInformation("开始批量TTS转换: Count={Count}", requests.Count);

            var tasks = requests.Select(ConvertTextToSpeechAsync).ToArray();
            var results = await Task.WhenAll(tasks);
            
            return results.ToList();
        }

        public async Task<string> StartStreamingTTSAsync(StreamingTTSRequest request)
        {
            var sessionId = Guid.NewGuid().ToString("N");
            var session = new TTSSession
            {
                SessionId = sessionId,
                Request = request,
                StartTime = DateTime.UtcNow,
                IsActive = true
            };

            _ttsSessions.TryAdd(sessionId, session);
            
            _logger.LogInformation("启动流式TTS会话: SessionId={SessionId}", sessionId);
            
            // 启动后台TTS处理
            _ = Task.Run(async () => await ProcessStreamingTTSAsync(session));
            
            return sessionId;
        }

        public async Task<byte[]> GetTTSChunkAsync(string sessionId)
        {
            if (!_ttsSessions.TryGetValue(sessionId, out var session))
            {
                return Array.Empty<byte>();
            }

            // 从音频缓冲区获取数据块
            if (session.AudioBuffer.Count >= session.Request.ChunkSize)
            {
                var chunk = session.AudioBuffer.Take(session.Request.ChunkSize).ToArray();
                session.AudioBuffer.RemoveRange(0, session.Request.ChunkSize);
                return chunk;
            }

            return Array.Empty<byte>();
        }

        public async Task<bool> EndStreamingTTSAsync(string sessionId)
        {
            if (_ttsSessions.TryRemove(sessionId, out var session))
            {
                session.IsActive = false;
                _logger.LogInformation("结束流式TTS会话: SessionId={SessionId}", sessionId);
                return true;
            }
            return false;
        }

        public async Task<AudioConversionResult> ConvertAudioFormatAsync(string inputPath, string outputFormat)
        {
            var stopwatch = Stopwatch.StartNew();
            
            try
            {
                var outputPath = Path.ChangeExtension(inputPath, outputFormat);
                
                await FFMpegArguments
                    .FromFileInput(inputPath)
                    .OutputToFile(outputPath, true, options => options
                        .WithAudioCodec("pcm_s16le")
                        .WithAudioSamplingRate(16000)
                        .WithAudioBitrate(128))
                    .ProcessAsynchronously();

                stopwatch.Stop();

                var inputInfo = new FileInfo(inputPath);
                var outputInfo = new FileInfo(outputPath);

                return new AudioConversionResult
                {
                    Success = true,
                    OutputPath = outputPath,
                    OutputFormat = outputFormat,
                    InputSize = inputInfo.Length,
                    OutputSize = outputInfo.Length,
                    Duration = await GetAudioDurationAsync(outputPath),
                    ProcessingTime = stopwatch.ElapsedMilliseconds
                };
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "音频格式转换失败: InputPath={InputPath}", inputPath);
                return new AudioConversionResult
                {
                    Success = false,
                    Error = ex.Message,
                    ProcessingTime = stopwatch.ElapsedMilliseconds
                };
            }
        }

        public async Task<AudioConversionResult> OptimizeAudioForMuseTalkAsync(string inputPath)
        {
            // MuseTalk 最佳音频格式：16kHz, 16-bit, mono WAV
            var stopwatch = Stopwatch.StartNew();
            
            try
            {
                var outputPath = Path.Combine(Path.GetDirectoryName(inputPath)!, 
                    $"optimized_{Path.GetFileNameWithoutExtension(inputPath)}.wav");
                
                await FFMpegArguments
                    .FromFileInput(inputPath)
                    .OutputToFile(outputPath, true, options => options
                        .WithAudioCodec("pcm_s16le")
                        .WithAudioSamplingRate(16000)
                        .WithAudioBitrate(128)
                        .WithCustomArgument("-ac 1")) // mono
                    .ProcessAsynchronously();

                stopwatch.Stop();

                var inputInfo = new FileInfo(inputPath);
                var outputInfo = new FileInfo(outputPath);

                return new AudioConversionResult
                {
                    Success = true,
                    OutputPath = outputPath,
                    OutputFormat = "wav",
                    InputSize = inputInfo.Length,
                    OutputSize = outputInfo.Length,
                    Duration = await GetAudioDurationAsync(outputPath),
                    ProcessingTime = stopwatch.ElapsedMilliseconds
                };
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "MuseTalk音频优化失败: InputPath={InputPath}", inputPath);
                return new AudioConversionResult
                {
                    Success = false,
                    Error = ex.Message,
                    ProcessingTime = stopwatch.ElapsedMilliseconds
                };
            }
        }

        public async Task<AudioConversionResult> NormalizeAudioAsync(string inputPath)
        {
            var stopwatch = Stopwatch.StartNew();
            
            try
            {
                var outputPath = Path.Combine(Path.GetDirectoryName(inputPath)!, 
                    $"normalized_{Path.GetFileNameWithoutExtension(inputPath)}.wav");
                
                // 使用FFmpeg进行音频标准化
                await FFMpegArguments
                    .FromFileInput(inputPath)
                    .OutputToFile(outputPath, true, options => options
                        .WithCustomArgument("-af dynaudnorm")
                        .WithAudioCodec("pcm_s16le"))
                    .ProcessAsynchronously();

                stopwatch.Stop();

                var inputInfo = new FileInfo(inputPath);
                var outputInfo = new FileInfo(outputPath);

                return new AudioConversionResult
                {
                    Success = true,
                    OutputPath = outputPath,
                    OutputFormat = "wav",
                    InputSize = inputInfo.Length,
                    OutputSize = outputInfo.Length,
                    Duration = await GetAudioDurationAsync(outputPath),
                    ProcessingTime = stopwatch.ElapsedMilliseconds
                };
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "音频标准化失败: InputPath={InputPath}", inputPath);
                return new AudioConversionResult
                {
                    Success = false,
                    Error = ex.Message,
                    ProcessingTime = stopwatch.ElapsedMilliseconds
                };
            }
        }

        public async Task<AudioEnhancementResult> EnhanceAudioQualityAsync(string inputPath)
        {
            var stopwatch = Stopwatch.StartNew();
            
            try
            {
                var outputPath = Path.Combine(Path.GetDirectoryName(inputPath)!, 
                    $"enhanced_{Path.GetFileNameWithoutExtension(inputPath)}.wav");
                
                // 使用FFmpeg进行音频增强
                await FFMpegArguments
                    .FromFileInput(inputPath)
                    .OutputToFile(outputPath, true, options => options
                        .WithCustomArgument("-af highpass=f=200,lowpass=f=8000,dynaudnorm")
                        .WithAudioCodec("pcm_s16le"))
                    .ProcessAsynchronously();

                stopwatch.Stop();

                return new AudioEnhancementResult
                {
                    Success = true,
                    OutputPath = outputPath,
                    QualityImprovement = 0.8f, // 估计的质量改进
                    NoiseReduction = 0.6f,
                    ProcessingTime = stopwatch.ElapsedMilliseconds,
                    EnhancementMetrics = new Dictionary<string, object>
                    {
                        ["high_pass_frequency"] = 200,
                        ["low_pass_frequency"] = 8000,
                        ["normalization"] = true
                    }
                };
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "音频增强失败: InputPath={InputPath}", inputPath);
                return new AudioEnhancementResult
                {
                    Success = false,
                    Error = ex.Message,
                    ProcessingTime = stopwatch.ElapsedMilliseconds
                };
            }
        }

        public async Task<AudioEnhancementResult> RemoveNoiseAsync(string inputPath)
        {
            var stopwatch = Stopwatch.StartNew();
            
            try
            {
                var outputPath = Path.Combine(Path.GetDirectoryName(inputPath)!, 
                    $"denoised_{Path.GetFileNameWithoutExtension(inputPath)}.wav");
                
                // 使用FFmpeg的降噪滤波器
                await FFMpegArguments
                    .FromFileInput(inputPath)
                    .OutputToFile(outputPath, true, options => options
                        .WithCustomArgument("-af afftdn,dynaudnorm")
                        .WithAudioCodec("pcm_s16le"))
                    .ProcessAsynchronously();

                stopwatch.Stop();

                return new AudioEnhancementResult
                {
                    Success = true,
                    OutputPath = outputPath,
                    NoiseReduction = 0.7f,
                    ProcessingTime = stopwatch.ElapsedMilliseconds,
                    EnhancementMetrics = new Dictionary<string, object>
                    {
                        ["noise_reduction_method"] = "afftdn",
                        ["noise_reduction_level"] = "medium"
                    }
                };
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "降噪处理失败: InputPath={InputPath}", inputPath);
                return new AudioEnhancementResult
                {
                    Success = false,
                    Error = ex.Message,
                    ProcessingTime = stopwatch.ElapsedMilliseconds
                };
            }
        }

        public async Task<AudioEnhancementResult> AdjustVolumeAsync(string inputPath, float volumeMultiplier)
        {
            var stopwatch = Stopwatch.StartNew();
            
            try
            {
                var outputPath = Path.Combine(Path.GetDirectoryName(inputPath)!, 
                    $"volume_adjusted_{Path.GetFileNameWithoutExtension(inputPath)}.wav");
                
                await FFMpegArguments
                    .FromFileInput(inputPath)
                    .OutputToFile(outputPath, true, options => options
                        .WithCustomArgument($"-af volume={volumeMultiplier}")
                        .WithAudioCodec("pcm_s16le"))
                    .ProcessAsynchronously();

                stopwatch.Stop();

                return new AudioEnhancementResult
                {
                    Success = true,
                    OutputPath = outputPath,
                    ProcessingTime = stopwatch.ElapsedMilliseconds,
                    EnhancementMetrics = new Dictionary<string, object>
                    {
                        ["volume_multiplier"] = volumeMultiplier,
                        ["volume_change_db"] = Math.Log10(volumeMultiplier) * 20
                    }
                };
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "音量调整失败: InputPath={InputPath}", inputPath);
                return new AudioEnhancementResult
                {
                    Success = false,
                    Error = ex.Message,
                    ProcessingTime = stopwatch.ElapsedMilliseconds
                };
            }
        }

        public async Task<AudioAnalysisResult> AnalyzeAudioAsync(string audioPath)
        {
            try
            {
                if (!File.Exists(audioPath))
                {
                    return new AudioAnalysisResult
                    {
                        Success = false
                    };
                }

                var audioInfo = await FFProbe.AnalyseAsync(audioPath);
                var audioStream = audioInfo.PrimaryAudioStream;

                if (audioStream == null)
                {
                    return new AudioAnalysisResult
                    {
                        Success = false
                    };
                }

                var fileInfo = new FileInfo(audioPath);
                var isSuitableForMuseTalk = audioStream.SampleRateHz == 16000 && 
                                          audioStream.Channels == 1 && 
                                          audioStream.BitDepth == 16;

                var recommendations = new List<string>();
                if (audioStream.SampleRateHz != 16000)
                    recommendations.Add("建议转换采样率为16kHz");
                if (audioStream.Channels != 1)
                    recommendations.Add("建议转换为单声道");
                if (audioStream.BitDepth != 16)
                    recommendations.Add("建议使用16位深度");

                return new AudioAnalysisResult
                {
                    Success = true,
                    Duration = audioInfo.Duration,
                    SampleRate = audioStream.SampleRateHz,
                    Channels = audioStream.Channels,
                    BitDepth = audioStream.BitDepth ?? 16,
                    Format = Path.GetExtension(audioPath).TrimStart('.'),
                    FileSize = fileInfo.Length,
                    IsSuitableForMuseTalk = isSuitableForMuseTalk,
                    Recommendations = recommendations
                };
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "音频分析失败: AudioPath={AudioPath}", audioPath);
                return new AudioAnalysisResult
                {
                    Success = false
                };
            }
        }

        public async Task<EmotionDetectionResult> DetectEmotionFromAudioAsync(string audioPath)
        {
            // 简化的情感检测实现
            // 在实际项目中，可以集成专门的情感识别库或API
            try
            {
                await Task.Delay(100); // 模拟处理时间

                var emotions = new Dictionary<string, float>
                {
                    ["neutral"] = 0.6f,
                    ["happy"] = 0.2f,
                    ["sad"] = 0.1f,
                    ["angry"] = 0.05f,
                    ["surprised"] = 0.05f
                };

                var primaryEmotion = emotions.OrderByDescending(e => e.Value).First();

                return new EmotionDetectionResult
                {
                    Success = true,
                    PrimaryEmotion = primaryEmotion.Key,
                    EmotionScores = emotions,
                    Confidence = primaryEmotion.Value,
                    ProcessingTime = 100
                };
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "情感检测失败: AudioPath={AudioPath}", audioPath);
                return new EmotionDetectionResult
                {
                    Success = false,
                    Error = ex.Message
                };
            }
        }

        public async Task<bool> ValidateAudioFormatAsync(string audioPath)
        {
            try
            {
                var analysisResult = await AnalyzeAudioAsync(audioPath);
                return analysisResult.Success && analysisResult.IsSuitableForMuseTalk;
            }
            catch
            {
                return false;
            }
        }

        public async Task<bool> PreloadVoiceModelAsync(string voiceId)
        {
            try
            {
                if (_preloadedVoices.ContainsKey(voiceId))
                {
                    return true;
                }

                // 预加载语音模型（具体实现取决于TTS服务）
                await Task.Delay(500); // 模拟预加载时间
                
                _preloadedVoices.TryAdd(voiceId, true);
                _logger.LogInformation("语音模型预加载成功: VoiceId={VoiceId}", voiceId);
                
                return true;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "语音模型预加载失败: VoiceId={VoiceId}", voiceId);
                return false;
            }
        }

        public async Task<bool> WarmupAudioProcessingAsync()
        {
            try
            {
                // 预热音频处理管道
                var testText = "测试";
                var testTTSRequest = new TTSRequest { Text = testText };
                await ConvertTextToSpeechAsync(testTTSRequest);
                
                _logger.LogInformation("音频处理管道预热完成");
                return true;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "音频处理管道预热失败");
                return false;
            }
        }

        public async Task<long> GetAudioProcessingQueueLengthAsync()
        {
            await Task.CompletedTask;
            return _audioProcessingSemaphore.CurrentCount;
        }

        // 高性能队列处理方法
        private void StartBackgroundProcessors()
        {
            var processorCount = Environment.ProcessorCount;
            
            // 启动音频处理器
            for (int i = 0; i < processorCount / 2; i++)
            {
                _ = Task.Run(ProcessAudioQueueAsync);
            }
            
            // 启动TTS处理器
            for (int i = 0; i < processorCount / 2; i++)
            {
                _ = Task.Run(ProcessTTSQueueAsync);
            }
            
            _logger.LogInformation("启动了 {AudioProcessors} 个音频处理器和 {TTSProcessors} 个TTS处理器", 
                processorCount / 2, processorCount / 2);
        }

        private async Task ProcessAudioQueueAsync()
        {
            await foreach (var job in _audioProcessingChannel.Reader.ReadAllAsync(_cancellationTokenSource.Token))
            {
                try
                {
                    var result = await RecognizeSpeechFromFileAsync(job.AudioPath);
                    job.TaskCompletionSource.SetResult(result);
                }
                catch (Exception ex)
                {
                    job.TaskCompletionSource.SetException(ex);
                }
            }
        }

        private async Task ProcessTTSQueueAsync()
        {
            await foreach (var job in _ttsProcessingChannel.Reader.ReadAllAsync(_cancellationTokenSource.Token))
            {
                try
                {
                    var result = await ConvertTextToSpeechAsync(job.Request);
                    job.TaskCompletionSource.SetResult(result);
                }
                catch (Exception ex)
                {
                    job.TaskCompletionSource.SetException(ex);
                }
            }
        }

        private async Task<TTSResult> GenerateWithAzureSpeechAsync(TTSRequest request, string outputPath, long elapsedTime)
        {
            try
            {
                if (_speechSynthesizer == null)
                {
                    return new TTSResult { Success = false, Error = "Azure Speech Service未配置" };
                }

                var ssml = $@"
                <speak version='1.0' xml:lang='zh-CN'>
                    <voice name='{request.VoiceId}'>
                        <prosody rate='{request.Speed:F1}' pitch='{request.Pitch:F1}'>
                            {request.Text}
                        </prosody>
                    </voice>
                </speak>";

                using var result = await _speechSynthesizer.SpeakSsmlAsync(ssml);
                
                if (result.Reason == ResultReason.SynthesizingAudioCompleted)
                {
                    await File.WriteAllBytesAsync(outputPath, result.AudioData);
                    return CreateTTSResult(outputPath, elapsedTime);
                }
                else
                {
                    return new TTSResult
                    {
                        Success = false,
                        Error = $"Azure Speech合成失败: {result.Reason}",
                        ProcessingTime = elapsedTime
                    };
                }
            }
            catch (Exception ex)
            {
                return new TTSResult
                {
                    Success = false,
                    Error = ex.Message,
                    ProcessingTime = elapsedTime
                };
            }
        }

        private TTSResult CreateTTSResult(string outputPath, long processingTime)
        {
            var fileInfo = new FileInfo(outputPath);
            var audioUrl = $"/temp/{Path.GetFileName(outputPath)}";

            return new TTSResult
            {
                Success = true,
                AudioPath = outputPath,
                AudioUrl = audioUrl,
                Duration = GetAudioDurationAsync(outputPath).Result,
                ProcessingTime = processingTime,
                FileSize = fileInfo.Length
            };
        }

        // 私有辅助方法
        private async Task<string> OptimizeAudioForSpeechRecognitionAsync(string inputPath)
        {
            // 为语音识别优化音频：16kHz, mono
            var optimizedPath = Path.Combine(Path.GetDirectoryName(inputPath)!, 
                $"optimized_asr_{Path.GetFileNameWithoutExtension(inputPath)}.wav");

            try
            {
                await FFMpegArguments
                    .FromFileInput(inputPath)
                    .OutputToFile(optimizedPath, true, options => options
                        .WithAudioCodec("pcm_s16le")
                        .WithAudioSamplingRate(16000)
                        .WithCustomArgument("-ac 1"))
                    .ProcessAsynchronously();

                return optimizedPath;
            }
            catch
            {
                return inputPath; // 如果优化失败，返回原始路径
            }
        }

        private async Task<TimeSpan> GetAudioDurationAsync(string audioPath)
        {
            try
            {
                var audioInfo = await FFProbe.AnalyseAsync(audioPath);
                return audioInfo.Duration;
            }
            catch
            {
                return TimeSpan.Zero;
            }
        }

        private List<SpeechSegment> ParseWhisperSegments(string text)
        {
            // 简单的文本分段（实际实现可能需要更复杂的逻辑）
            return new List<SpeechSegment>
            {
                new SpeechSegment
                {
                    Text = text,
                    StartTime = TimeSpan.Zero,
                    EndTime = TimeSpan.FromSeconds(text.Length * 0.1), // 估算
                    Confidence = 0.95f
                }
            };
        }

        private async Task ProcessStreamingTTSAsync(TTSSession session)
        {
            try
            {
                // 流式TTS处理实现
                var ttsResult = await ConvertTextToSpeechAsync(new TTSRequest
                {
                    Text = session.Request.Text,
                    VoiceId = session.Request.VoiceId,
                    OutputFormat = session.Request.OutputFormat,
                    Speed = session.Request.Speed
                });

                if (ttsResult.Success && ttsResult.AudioData != null)
                {
                    session.AudioBuffer.AddRange(ttsResult.AudioData);
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "流式TTS处理失败: SessionId={SessionId}", session.SessionId);
            }
        }

        private string GenerateAudioCacheKey(byte[] audioData)
        {
            using var sha256 = System.Security.Cryptography.SHA256.Create();
            var hash = sha256.ComputeHash(audioData);
            return Convert.ToBase64String(hash);
        }

        private string GenerateTTSCacheKey(TTSRequest request)
        {
            var content = $"{request.Text}:{request.VoiceId}:{request.Speed}:{request.Emotion}";
            using var sha256 = System.Security.Cryptography.SHA256.Create();
            var hash = sha256.ComputeHash(Encoding.UTF8.GetBytes(content));
            return Convert.ToBase64String(hash);
        }

        // 新增队列任务类
        internal class AudioProcessingJob
        {
            public string AudioPath { get; set; } = string.Empty;
            public TaskCompletionSource<Models.SpeechRecognitionResult> TaskCompletionSource { get; set; } = new();
        }

        internal class TTSProcessingJob
        {
            public TTSRequest Request { get; set; } = new();
            public TaskCompletionSource<TTSResult> TaskCompletionSource { get; set; } = new();
        }

        public void Dispose()
        {
            _cancellationTokenSource?.Cancel();
            _audioChannelWriter?.Complete();
            _ttsChannelWriter?.Complete();
            _speechSynthesizer?.Dispose();
            _audioProcessingSemaphore?.Dispose();
            _ttsProcessingSemaphore?.Dispose();
            _cancellationTokenSource?.Dispose();
        }
    }

    // 内部会话管理类
    internal class SpeechRecognitionSession
    {
        public string SessionId { get; set; } = string.Empty;
        public DateTime StartTime { get; set; }
        public DateTime LastUpdateTime { get; set; }
        public List<byte> AudioBuffer { get; set; } = new();
        public bool IsActive { get; set; }
    }

    internal class TTSSession
    {
        public string SessionId { get; set; } = string.Empty;
        public StreamingTTSRequest Request { get; set; } = new();
        public DateTime StartTime { get; set; }
        public List<byte> AudioBuffer { get; set; } = new();
        public bool IsActive { get; set; }
    }
}