using LmyDigitalHuman.Services;
using System.Collections.Concurrent;
using System.Threading.Channels;
using LmyDigitalHuman.Models;

namespace LmyDigitalHuman.Services.Core
{

    public class RealtimePipelineService : IRealtimePipelineService
    {
        private readonly ILogger<RealtimePipelineService> _logger;
        private readonly IGPUResourceManager _gpuResourceManager;
        private readonly IWhisperNetService _whisperService;
        private readonly ILocalLLMService _llmService;
        private readonly IEdgeTTSService _ttsService;
        private readonly IMuseTalkService _museTalkService;
        
        private readonly ConcurrentDictionary<string, RealtimePipelineSession> _activeSessions;
        private readonly SemaphoreSlim _sessionLock;

        public event EventHandler<RealtimeResultEventArgs>? OnRealtimeResult;

        public RealtimePipelineService(
            ILogger<RealtimePipelineService> logger,
            IGPUResourceManager gpuResourceManager,
            IWhisperNetService whisperService,
            ILocalLLMService llmService,
            IEdgeTTSService ttsService,
            IMuseTalkService museTalkService)
        {
            _logger = logger;
            _gpuResourceManager = gpuResourceManager;
            _whisperService = whisperService;
            _llmService = llmService;
            _ttsService = ttsService;
            _museTalkService = museTalkService;
            
            _activeSessions = new ConcurrentDictionary<string, RealtimePipelineSession>();
            _sessionLock = new SemaphoreSlim(1, 1);
        }

        public async Task<string> StartRealtimeSessionAsync(string sessionId, RealtimePipelineConfig config)
        {
            await _sessionLock.WaitAsync();
            try
            {
                if (_activeSessions.ContainsKey(sessionId))
                {
                    throw new InvalidOperationException($"会话 {sessionId} 已存在");
                }

                // 分配GPU资源
                var audioGpu = await _gpuResourceManager.AllocateGPUAsync(GPUWorkloadType.AudioProcessing);
                var llmGpu = await _gpuResourceManager.AllocateGPUAsync(GPUWorkloadType.LLMInference);
                var videoGpu = await _gpuResourceManager.AllocateGPUAsync(GPUWorkloadType.VideoGeneration);

                // 创建流水线会话
                var session = new RealtimePipelineSession
                {
                    SessionId = sessionId,
                    Config = config,
                    AudioGpuId = audioGpu,
                    LLMGpuId = llmGpu,
                    VideoGpuId = videoGpu,
                    StartTime = DateTime.UtcNow,
                    IsActive = true,
                    CancellationTokenSource = new CancellationTokenSource()
                };

                // 创建处理通道
                var channelOptions = new BoundedChannelOptions(100)
                {
                    FullMode = BoundedChannelFullMode.Wait,
                    SingleReader = true,
                    SingleWriter = false
                };

                session.AudioChannel = Channel.CreateBounded<AudioChunk>(channelOptions);
                session.TextChannel = Channel.CreateBounded<TextChunk>(channelOptions);
                session.TTSChannel = Channel.CreateBounded<TTSChunk>(channelOptions);
                session.VideoChannel = Channel.CreateBounded<VideoChunk>(channelOptions);

                // 启动流水线处理任务
                _ = Task.Run(() => ProcessAudioPipelineAsync(session), session.CancellationTokenSource.Token);
                _ = Task.Run(() => ProcessLLMPipelineAsync(session), session.CancellationTokenSource.Token);
                _ = Task.Run(() => ProcessTTSPipelineAsync(session), session.CancellationTokenSource.Token);
                _ = Task.Run(() => ProcessVideoPipelineAsync(session), session.CancellationTokenSource.Token);

                _activeSessions[sessionId] = session;
                
                _logger.LogInformation($"启动实时会话 {sessionId}，分配GPU: Audio={audioGpu}, LLM={llmGpu}, Video={videoGpu}");
                return sessionId;
            }
            finally
            {
                _sessionLock.Release();
            }
        }

        public async Task ProcessAudioStreamAsync(string sessionId, Stream audioStream)
        {
            if (!_activeSessions.TryGetValue(sessionId, out var session))
            {
                throw new InvalidOperationException($"会话 {sessionId} 不存在");
            }

            try
            {
                // 将音频流分块处理
                var buffer = new byte[4096]; // 4KB chunks for low latency
                var audioData = new List<byte>();

                int bytesRead;
                while ((bytesRead = await audioStream.ReadAsync(buffer, 0, buffer.Length)) > 0)
                {
                    audioData.AddRange(buffer.Take(bytesRead));

                    // 当累积足够数据时，发送到音频处理通道
                    if (audioData.Count >= 16000) // 约1秒的16kHz音频
                    {
                        var audioChunk = new AudioChunk
                        {
                            Data = audioData.ToArray(),
                            Timestamp = DateTime.UtcNow,
                            ChunkId = Guid.NewGuid().ToString()
                        };

                        await session.AudioChannel.Writer.WriteAsync(audioChunk);
                        audioData.Clear();
                    }
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, $"处理会话 {sessionId} 音频流失败");
            }
        }

        public async Task StopRealtimeSessionAsync(string sessionId)
        {
            if (_activeSessions.TryRemove(sessionId, out var session))
            {
                session.IsActive = false;
                session.CancellationTokenSource.Cancel();

                // 释放GPU资源
                await _gpuResourceManager.ReleaseGPUAsync(session.AudioGpuId, GPUWorkloadType.AudioProcessing);
                await _gpuResourceManager.ReleaseGPUAsync(session.LLMGpuId, GPUWorkloadType.LLMInference);
                await _gpuResourceManager.ReleaseGPUAsync(session.VideoGpuId, GPUWorkloadType.VideoGeneration);

                // 关闭通道
                session.AudioChannel.Writer.Complete();
                session.TextChannel.Writer.Complete();
                session.TTSChannel.Writer.Complete();
                session.VideoChannel.Writer.Complete();

                session.CancellationTokenSource.Dispose();
                
                _logger.LogInformation($"停止实时会话 {sessionId}");
            }
        }

        public async Task<RealtimePipelineStatus> GetSessionStatusAsync(string sessionId)
        {
            if (_activeSessions.TryGetValue(sessionId, out var session))
            {
                return new RealtimePipelineStatus
                {
                    SessionId = sessionId,
                    IsActive = session.IsActive,
                    StartTime = session.StartTime,
                    Duration = DateTime.UtcNow - session.StartTime,
                    AudioGpuId = session.AudioGpuId,
                    LLMGpuId = session.LLMGpuId,
                    VideoGpuId = session.VideoGpuId,
                    ProcessedAudioChunks = session.ProcessedAudioChunks,
                    ProcessedTextChunks = session.ProcessedTextChunks,
                    ProcessedTTSChunks = session.ProcessedTTSChunks,
                    ProcessedVideoChunks = session.ProcessedVideoChunks,
                    AverageLatency = session.GetAverageLatency(),
                    LastActivity = session.LastActivity
                };
            }

            throw new InvalidOperationException($"会话 {sessionId} 不存在");
        }

        private async Task ProcessAudioPipelineAsync(RealtimePipelineSession session)
        {
            try
            {
                await foreach (var audioChunk in session.AudioChannel.Reader.ReadAllAsync(session.CancellationTokenSource.Token))
                {
                    var startTime = DateTime.UtcNow;

                    // 使用Whisper进行语音识别
                    var audioPath = await SaveAudioChunkAsync(audioChunk);
                    var recognitionResult = await _whisperService.TranscribeAsync(audioPath);

                    if (!string.IsNullOrEmpty(recognitionResult.Text))
                    {
                        var textChunk = new TextChunk
                        {
                            Text = recognitionResult.Text,
                            Timestamp = DateTime.UtcNow,
                            ChunkId = audioChunk.ChunkId,
                            ProcessingLatency = (DateTime.UtcNow - startTime).TotalMilliseconds
                        };

                        await session.TextChannel.Writer.WriteAsync(textChunk);
                        session.ProcessedAudioChunks++;
                        session.LastActivity = DateTime.UtcNow;

                        _logger.LogDebug($"会话 {session.SessionId} 语音识别完成: {recognitionResult.Text} (延迟: {textChunk.ProcessingLatency}ms)");
                    }

                    // 清理临时文件
                    File.Delete(audioPath);
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, $"会话 {session.SessionId} 音频处理流水线异常");
            }
        }

        private async Task ProcessLLMPipelineAsync(RealtimePipelineSession session)
        {
            try
            {
                await foreach (var textChunk in session.TextChannel.Reader.ReadAllAsync(session.CancellationTokenSource.Token))
                {
                    var startTime = DateTime.UtcNow;

                    // 使用LLM生成回复
                    var llmRequest = new LocalLLMRequest
                    {
                        Message = textChunk.Text,
                        MaxTokens = 100, // 限制token数量以降低延迟
                        Temperature = 0.7f
                    };

                    var llmResponse = await _llmService.GenerateResponseAsync(llmRequest);

                    if (!string.IsNullOrEmpty(llmResponse.ResponseText))
                    {
                        var ttsChunk = new TTSChunk
                        {
                            Text = llmResponse.ResponseText,
                            Timestamp = DateTime.UtcNow,
                            ChunkId = textChunk.ChunkId,
                            ProcessingLatency = (DateTime.UtcNow - startTime).TotalMilliseconds
                        };

                        await session.TTSChannel.Writer.WriteAsync(ttsChunk);
                        session.ProcessedTextChunks++;
                        session.LastActivity = DateTime.UtcNow;

                        _logger.LogDebug($"会话 {session.SessionId} LLM推理完成: {llmResponse.ResponseText} (延迟: {ttsChunk.ProcessingLatency}ms)");
                    }
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, $"会话 {session.SessionId} LLM处理流水线异常");
            }
        }

        private async Task ProcessTTSPipelineAsync(RealtimePipelineSession session)
        {
            try
            {
                await foreach (var ttsChunk in session.TTSChannel.Reader.ReadAllAsync(session.CancellationTokenSource.Token))
                {
                    var startTime = DateTime.UtcNow;

                    // 使用Edge-TTS生成语音
                    var ttsRequest = new TTSRequest
                    {
                        Text = ttsChunk.Text,
                        Voice = session.Config.VoiceId,
                        OutputFormat = "audio-16khz-32kbitrate-mono-mp3"
                    };

                    var ttsResponse = await _ttsService.ConvertTextToSpeechAsync(ttsRequest.Text, ttsRequest.Voice);

                    var videoChunk = new VideoChunk
                    {
                        AudioPath = ttsResponse.AudioPath,
                        Text = ttsChunk.Text,
                        Timestamp = DateTime.UtcNow,
                        ChunkId = ttsChunk.ChunkId,
                        ProcessingLatency = (DateTime.UtcNow - startTime).TotalMilliseconds
                    };

                    await session.VideoChannel.Writer.WriteAsync(videoChunk);
                    session.ProcessedTTSChunks++;
                    session.LastActivity = DateTime.UtcNow;

                    _logger.LogDebug($"会话 {session.SessionId} TTS合成完成 (延迟: {videoChunk.ProcessingLatency}ms)");
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, $"会话 {session.SessionId} TTS处理流水线异常");
            }
        }

        private async Task ProcessVideoPipelineAsync(RealtimePipelineSession session)
        {
            try
            {
                await foreach (var videoChunk in session.VideoChannel.Reader.ReadAllAsync(session.CancellationTokenSource.Token))
                {
                    var startTime = DateTime.UtcNow;

                    // 使用MuseTalk生成视频
                    var config = new MuseTalkConfig
                    {
                        BatchSize = 1, // 实时模式使用小批次
                        UseFloat16 = true,
                        NumInferenceSteps = 10, // 减少推理步数以降低延迟
                        Resolution = 256 // 使用较低分辨率
                    };

                    var videoPath = await _museTalkService.GenerateRealtimeVideoAsync(
                        session.Config.TemplateImagePath, 
                        videoChunk.AudioPath, 
                        config);

                    var result = new RealtimeResult
                    {
                        SessionId = session.SessionId,
                        ChunkId = videoChunk.ChunkId,
                        VideoPath = videoPath,
                        AudioPath = videoChunk.AudioPath,
                        Text = videoChunk.Text,
                        Timestamp = DateTime.UtcNow,
                        TotalLatency = (DateTime.UtcNow - startTime).TotalMilliseconds
                    };

                    // 触发实时结果事件
                    OnRealtimeResult?.Invoke(this, new RealtimeResultEventArgs 
                    { 
                        SessionId = sessionId,
                        Type = "video",
                        Data = result
                    });

                    session.ProcessedVideoChunks++;
                    session.LastActivity = DateTime.UtcNow;
                    session.AddLatencyMeasurement(result.TotalLatency);

                    _logger.LogDebug($"会话 {session.SessionId} 视频生成完成 (延迟: {result.TotalLatency}ms)");
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, $"会话 {session.SessionId} 视频处理流水线异常");
            }
        }

        private async Task<string> SaveAudioChunkAsync(AudioChunk audioChunk)
        {
            var tempPath = Path.Combine("temp", $"audio_{audioChunk.ChunkId}.wav");
            Directory.CreateDirectory(Path.GetDirectoryName(tempPath)!);
            
            await File.WriteAllBytesAsync(tempPath, audioChunk.Data);
            return tempPath;
        }
    }

    // 数据模型
    public class RealtimePipelineSession
    {
        public string SessionId { get; set; } = string.Empty;
        public RealtimePipelineConfig Config { get; set; } = new();
        public int AudioGpuId { get; set; }
        public int LLMGpuId { get; set; }
        public int VideoGpuId { get; set; }
        public DateTime StartTime { get; set; }
        public DateTime LastActivity { get; set; }
        public bool IsActive { get; set; }
        public CancellationTokenSource CancellationTokenSource { get; set; } = new();

        public Channel<AudioChunk> AudioChannel { get; set; } = null!;
        public Channel<TextChunk> TextChannel { get; set; } = null!;
        public Channel<TTSChunk> TTSChannel { get; set; } = null!;
        public Channel<VideoChunk> VideoChannel { get; set; } = null!;

        public int ProcessedAudioChunks { get; set; }
        public int ProcessedTextChunks { get; set; }
        public int ProcessedTTSChunks { get; set; }
        public int ProcessedVideoChunks { get; set; }

        private readonly List<double> _latencyMeasurements = new();

        public void AddLatencyMeasurement(double latency)
        {
            lock (_latencyMeasurements)
            {
                _latencyMeasurements.Add(latency);
                if (_latencyMeasurements.Count > 100) // 保持最近100次测量
                {
                    _latencyMeasurements.RemoveAt(0);
                }
            }
        }

        public double GetAverageLatency()
        {
            lock (_latencyMeasurements)
            {
                return _latencyMeasurements.Count > 0 ? _latencyMeasurements.Average() : 0;
            }
        }
    }

    // 使用IRealtimePipelineService中定义的RealtimePipelineConfig

    public class AudioChunk
    {
        public byte[] Data { get; set; } = Array.Empty<byte>();
        public DateTime Timestamp { get; set; }
        public string ChunkId { get; set; } = string.Empty;
    }

    public class TextChunk
    {
        public string Text { get; set; } = string.Empty;
        public DateTime Timestamp { get; set; }
        public string ChunkId { get; set; } = string.Empty;
        public double ProcessingLatency { get; set; }
    }

    public class TTSChunk
    {
        public string Text { get; set; } = string.Empty;
        public DateTime Timestamp { get; set; }
        public string ChunkId { get; set; } = string.Empty;
        public double ProcessingLatency { get; set; }
    }

    public class VideoChunk
    {
        public string AudioPath { get; set; } = string.Empty;
        public string Text { get; set; } = string.Empty;
        public DateTime Timestamp { get; set; }
        public string ChunkId { get; set; } = string.Empty;
        public double ProcessingLatency { get; set; }
    }

    public class RealtimeResult
    {
        public string SessionId { get; set; } = string.Empty;
        public string ChunkId { get; set; } = string.Empty;
        public string VideoPath { get; set; } = string.Empty;
        public string AudioPath { get; set; } = string.Empty;
        public string Text { get; set; } = string.Empty;
        public DateTime Timestamp { get; set; }
        public double TotalLatency { get; set; }
    }
}