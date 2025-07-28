using LmyDigitalHuman.Models;
using System.Diagnostics;
using System.Text.RegularExpressions;
using System.Collections.Concurrent;

namespace LmyDigitalHuman.Services
{
    public interface IStreamingTTSService
    {
        IAsyncEnumerable<TTSChunkResponse> TextToSpeechStreamAsync(string text, string voice = "zh-CN-XiaoxiaoNeural");
        Task<TTSResponse> TextToSpeechAsync(string text, string voice = "zh-CN-XiaoxiaoNeural");
        IAsyncEnumerable<TTSChunkResponse> ProcessLLMStreamAsync(IAsyncEnumerable<string> textStream, string voice = "zh-CN-XiaoxiaoNeural");
    }

    public class StreamingTTSService : IStreamingTTSService
    {
        private readonly ILogger<StreamingTTSService> _logger;
        private readonly IConfiguration _configuration;
        private readonly IEdgeTTSService _edgeTTSService;
        private readonly ConcurrentQueue<TTSTask> _processingQueue = new();
        private readonly SemaphoreSlim _processingLock = new(3); // 最多3个并发任务

        public StreamingTTSService(
            ILogger<StreamingTTSService> logger, 
            IConfiguration configuration,
            IEdgeTTSService edgeTTSService)
        {
            _logger = logger;
            _configuration = configuration;
            _edgeTTSService = edgeTTSService;
        }

        public async IAsyncEnumerable<TTSChunkResponse> TextToSpeechStreamAsync(string text, string voice = "zh-CN-XiaoxiaoNeural")
        {
            _logger.LogInformation("开始流式TTS处理: {Text}", text.Substring(0, Math.Min(50, text.Length)));

            // 将文本分割成句子
            var sentences = SplitIntoSentences(text);
            var tasks = new List<Task<TTSChunkResponse>>();

            for (int i = 0; i < sentences.Count; i++)
            {
                var sentence = sentences[i].Trim();
                if (string.IsNullOrEmpty(sentence)) continue;

                var index = i;
                var task = ProcessSentenceAsync(sentence, voice, index);
                tasks.Add(task);

                // 每处理3个句子就等待一下，避免过度并发
                if (tasks.Count >= 3)
                {
                    var completedTask = await Task.WhenAny(tasks);
                    var result = await completedTask;
                    
                    if (result.Success)
                    {
                        yield return result;
                    }
                    
                    tasks.Remove(completedTask);
                }
            }

            // 处理剩余的任务
            while (tasks.Count > 0)
            {
                var completedTask = await Task.WhenAny(tasks);
                var result = await completedTask;
                
                if (result.Success)
                {
                    yield return result;
                }
                
                tasks.Remove(completedTask);
            }

            _logger.LogInformation("流式TTS处理完成");
        }

        public async IAsyncEnumerable<TTSChunkResponse> ProcessLLMStreamAsync(IAsyncEnumerable<string> textStream, string voice = "zh-CN-XiaoxiaoNeural")
        {
            var sentenceBuffer = "";
            var chunkIndex = 0;
            var activeTasks = new List<Task<TTSChunkResponse>>();

            await foreach (var textChunk in textStream)
            {
                sentenceBuffer += textChunk;
                
                // 检测完整的句子
                var sentences = SplitIntoSentences(sentenceBuffer);
                if (sentences.Count > 1)
                {
                    // 处理完整的句子（除了最后一个）
                    for (int i = 0; i < sentences.Count - 1; i++)
                    {
                        var sentence = sentences[i].Trim();
                        if (!string.IsNullOrEmpty(sentence) && sentence.Length > 3)
                        {
                            var task = ProcessSentenceAsync(sentence, voice, chunkIndex++);
                            activeTasks.Add(task);

                            // 检查是否有任务完成
                            var completedTasks = activeTasks.Where(t => t.IsCompleted).ToList();
                            foreach (var completedTask in completedTasks)
                            {
                                var result = await completedTask;
                                if (result.Success)
                                {
                                    yield return result;
                                }
                                activeTasks.Remove(completedTask);
                            }
                        }
                    }
                    
                    // 保留最后一个未完成的句子
                    sentenceBuffer = sentences[sentences.Count - 1];
                }

                // 限制并发任务数量
                if (activeTasks.Count > 5)
                {
                    var completedTask = await Task.WhenAny(activeTasks);
                    var result = await completedTask;
                    if (result.Success)
                    {
                        yield return result;
                    }
                    activeTasks.Remove(completedTask);
                }
            }

            // 处理最后的句子
            if (!string.IsNullOrEmpty(sentenceBuffer.Trim()))
            {
                var finalTask = ProcessSentenceAsync(sentenceBuffer.Trim(), voice, chunkIndex++);
                activeTasks.Add(finalTask);
            }

            // 等待所有剩余任务完成
            while (activeTasks.Count > 0)
            {
                var completedTask = await Task.WhenAny(activeTasks);
                var result = await completedTask;
                if (result.Success)
                {
                    yield return result;
                }
                activeTasks.Remove(completedTask);
            }
        }

        private async Task<TTSChunkResponse> ProcessSentenceAsync(string sentence, string voice, int index)
        {
            await _processingLock.WaitAsync();
            
            try
            {
                var stopwatch = Stopwatch.StartNew();
                _logger.LogDebug("开始处理TTS句子 {Index}: {Sentence}", index, sentence.Substring(0, Math.Min(20, sentence.Length)));

                var ttsRequest = new TTSRequest
                {
                    Text = sentence,
                    Voice = voice,
                    Rate = "1.0",
                    Pitch = "0Hz"
                };

                var result = await _edgeTTSService.TextToSpeechAsync(ttsRequest);
                stopwatch.Stop();

                if (result.Success)
                {
                    _logger.LogDebug("TTS句子 {Index} 处理完成，耗时: {Time}ms", index, stopwatch.ElapsedMilliseconds);
                    
                    return new TTSChunkResponse
                    {
                        Success = true,
                        AudioUrl = result.AudioUrl,
                        Text = sentence,
                        ChunkIndex = index,
                        Duration = result.Duration,
                        FileSize = result.FileSize,
                        ProcessingTime = stopwatch.ElapsedMilliseconds
                    };
                }
                else
                {
                    _logger.LogError("TTS句子 {Index} 处理失败: {Error}", index, result.Error);
                    return new TTSChunkResponse
                    {
                        Success = false,
                        Error = result.Error,
                        Text = sentence,
                        ChunkIndex = index,
                        ProcessingTime = stopwatch.ElapsedMilliseconds
                    };
                }
            }
            finally
            {
                _processingLock.Release();
            }
        }

        public async Task<TTSResponse> TextToSpeechAsync(string text, string voice = "zh-CN-XiaoxiaoNeural")
        {
            var request = new TTSRequest
            {
                Text = text,
                Voice = voice,
                Rate = "1.0",
                Pitch = "0Hz"
            };

            return await _edgeTTSService.TextToSpeechAsync(request);
        }

        private List<string> SplitIntoSentences(string text)
        {
            // 中文和英文句子分割
            var pattern = @"[。！？；!?;]+";
            var sentences = Regex.Split(text, pattern)
                .Where(s => !string.IsNullOrWhiteSpace(s))
                .Select(s => s.Trim())
                .Where(s => s.Length > 0)
                .ToList();

            // 如果没有找到句子分隔符，检查是否有足够长的文本
            if (sentences.Count <= 1 && text.Length > 50)
            {
                // 按逗号分割较长的文本
                var commaPattern = @"[，,]+";
                var commaSentences = Regex.Split(text, commaPattern)
                    .Where(s => !string.IsNullOrWhiteSpace(s) && s.Trim().Length > 10)
                    .Select(s => s.Trim())
                    .ToList();
                
                if (commaSentences.Count > 1)
                {
                    return commaSentences;
                }
            }

            return sentences.Count > 0 ? sentences : new List<string> { text };
        }

        private class TTSTask
        {
            public string Text { get; set; } = string.Empty;
            public string Voice { get; set; } = string.Empty;
            public int Index { get; set; }
            public TaskCompletionSource<TTSChunkResponse> TaskCompletionSource { get; set; } = new();
        }
    }

    public class TTSChunkResponse
    {
        public bool Success { get; set; }
        public string AudioUrl { get; set; } = string.Empty;
        public string Text { get; set; } = string.Empty;
        public int ChunkIndex { get; set; }
        public double Duration { get; set; }
        public long FileSize { get; set; }
        public long ProcessingTime { get; set; }
        public string Error { get; set; } = string.Empty;
    }
}