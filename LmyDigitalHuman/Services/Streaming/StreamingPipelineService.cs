using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Text.Json;
using System.Threading;
using System.Threading.Channels;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;

namespace LmyDigitalHuman.Services.Streaming
{
    /// <summary>
    /// 流式管道服务 - 协调LLM、TTS、MuseTalk的流式处理
    /// </summary>
    public class StreamingPipelineService
    {
        private readonly StreamingOllamaService _ollamaService;
        private readonly IEdgeTTSService _ttsService;
        private readonly IMuseTalkService _museTalkService;
        private readonly ILogger<StreamingPipelineService> _logger;
        private readonly IConfiguration _configuration;

        public StreamingPipelineService(
            StreamingOllamaService ollamaService,
            IEdgeTTSService ttsService,
            IMuseTalkService museTalkService,
            IConfiguration configuration,
            ILogger<StreamingPipelineService> logger)
        {
            _ollamaService = ollamaService;
            _ttsService = ttsService;
            _museTalkService = museTalkService;
            _configuration = configuration;
            _logger = logger;
        }

        /// <summary>
        /// 流式处理对话
        /// </summary>
        public async IAsyncEnumerable<StreamSegment> ProcessStreamAsync(
            string templateId,
            string userInput,
            string voice = "zh-CN-XiaoxiaoNeural",
            CancellationToken cancellationToken = default)
        {
            _logger.LogInformation("开始流式处理: Template={TemplateId}, Input={Input}", 
                templateId, userInput);

            var segmentIndex = 0;
            var audioTasks = new List<Task<string>>();
            var videoChannel = Channel.CreateUnbounded<StreamSegment>();

            // 启动视频生成任务
            var videoTask = Task.Run(async () =>
            {
                await foreach (var audioPath in ConsumeAudioQueue(audioTasks, cancellationToken))
                {
                    try
                    {
                        // 生成视频段
                        var videoPath = await GenerateVideoSegmentAsync(
                            templateId, 
                            audioPath, 
                            segmentIndex++);

                        if (!string.IsNullOrEmpty(videoPath))
                        {
                            await videoChannel.Writer.WriteAsync(new StreamSegment
                            {
                                Index = segmentIndex - 1,
                                VideoPath = videoPath,
                                AudioPath = audioPath,
                                Timestamp = DateTime.UtcNow
                            });
                        }
                    }
                    catch (Exception ex)
                    {
                        _logger.LogError(ex, "视频生成失败: Segment={Index}", segmentIndex);
                    }
                }

                videoChannel.Writer.Complete();
            });

            // 流式生成文本和音频
            await foreach (var sentence in _ollamaService.GenerateStreamAsync(userInput, cancellationToken))
            {
                if (string.IsNullOrWhiteSpace(sentence))
                    continue;

                _logger.LogDebug("生成句子: {Sentence}", sentence);

                // 异步生成音频
                var audioTask = GenerateAudioAsync(sentence, voice, segmentIndex);
                audioTasks.Add(audioTask);
            }

            // 等待所有音频生成完成
            await Task.WhenAll(audioTasks);

            // 输出视频段
            await foreach (var segment in videoChannel.Reader.ReadAllAsync(cancellationToken))
            {
                yield return segment;
            }

            await videoTask;
            _logger.LogInformation("流式处理完成: 共{Count}段", segmentIndex);
        }

        /// <summary>
        /// 生成音频
        /// </summary>
        private async Task<string> GenerateAudioAsync(string text, string voice, int index)
        {
            try
            {
                var audioDir = _configuration["Paths:Audio"] ?? "/app/wwwroot/audio";
                var fileName = $"segment_{DateTime.Now:yyyyMMddHHmmss}_{index}.mp3";
                var audioPath = Path.Combine(audioDir, fileName);

                // 使用TTS生成音频
                await _ttsService.GenerateAudioAsync(text, voice, audioPath);
                
                _logger.LogDebug("音频生成完成: {Path}", audioPath);
                return audioPath;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "音频生成失败: {Text}", text);
                return null;
            }
        }

        /// <summary>
        /// 生成视频段
        /// </summary>
        private async Task<string> GenerateVideoSegmentAsync(
            string templateId, 
            string audioPath, 
            int index)
        {
            try
            {
                // 调用MuseTalk生成视频
                var result = await _museTalkService.GenerateVideoAsync(
                    templateId,
                    audioPath,
                    new VideoGenerationOptions
                    {
                        BatchSize = 25,  // 小批次快速处理
                        SkipFrames = 2,   // 跳帧加速
                        Streaming = true  // 流式模式
                    });

                if (result.Success)
                {
                    _logger.LogDebug("视频段生成完成: {Path}", result.VideoPath);
                    return result.VideoPath;
                }

                return null;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "视频生成失败");
                return null;
            }
        }

        /// <summary>
        /// 消费音频队列
        /// </summary>
        private async IAsyncEnumerable<string> ConsumeAudioQueue(
            List<Task<string>> audioTasks,
            CancellationToken cancellationToken)
        {
            var processedCount = 0;
            
            while (true)
            {
                // 等待新的音频任务
                while (processedCount < audioTasks.Count)
                {
                    var task = audioTasks[processedCount];
                    var audioPath = await task;
                    
                    if (!string.IsNullOrEmpty(audioPath))
                    {
                        yield return audioPath;
                    }
                    
                    processedCount++;
                }

                // 检查是否还有更多任务
                await Task.Delay(100, cancellationToken);
                
                if (processedCount >= audioTasks.Count && audioTasks.All(t => t.IsCompleted))
                {
                    break;
                }
            }
        }
    }

    /// <summary>
    /// 流段数据
    /// </summary>
    public class StreamSegment
    {
        public int Index { get; set; }
        public string VideoPath { get; set; }
        public string AudioPath { get; set; }
        public DateTime Timestamp { get; set; }
    }

    /// <summary>
    /// 视频生成选项
    /// </summary>
    public class VideoGenerationOptions
    {
        public int BatchSize { get; set; } = 6;
        public int SkipFrames { get; set; } = 1;
        public bool Streaming { get; set; } = false;
    }
}