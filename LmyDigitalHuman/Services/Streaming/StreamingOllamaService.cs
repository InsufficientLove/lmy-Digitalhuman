using System;
using LmyDigitalHuman.Services;
using System.Collections.Generic;
using System.IO;
using System.Net.Http;
using System.Runtime.CompilerServices;
using System.Text;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;

namespace LmyDigitalHuman.Services.Streaming
{
    /// <summary>
    /// 流式Ollama服务 - 支持逐句输出
    /// </summary>
    public class StreamingOllamaService
    {
        private readonly HttpClient _httpClient;
        private readonly ILogger<StreamingOllamaService> _logger;
        private readonly string _model;

        public StreamingOllamaService(
            HttpClient httpClient,
            IConfiguration configuration,
            ILogger<StreamingOllamaService> logger)
        {
            _httpClient = httpClient;
            _logger = logger;
            _model = configuration["Ollama:Model"] ?? "qwen2.5:latest";
        }

        /// <summary>
        /// 流式生成回答
        /// </summary>
        public async IAsyncEnumerable<string> GenerateStreamAsync(
            string prompt,
            [EnumeratorCancellation] CancellationToken cancellationToken = default)
        {
            _logger.LogInformation("开始流式生成: {Prompt}", prompt);

            var request = new
            {
                model = _model,
                prompt = prompt,
                stream = true
            };

            var json = JsonSerializer.Serialize(request);
            var content = new StringContent(json, Encoding.UTF8, "application/json");

            using var response = await _httpClient.PostAsync(
                "/api/generate",
                content,
                cancellationToken);

            response.EnsureSuccessStatusCode();

            using var stream = await response.Content.ReadAsStreamAsync();
            using var reader = new StreamReader(stream);

            var sentenceBuffer = new StringBuilder();
            var charCount = 0;

            while (!reader.EndOfStream && !cancellationToken.IsCancellationRequested)
            {
                var line = await reader.ReadLineAsync();
                if (string.IsNullOrWhiteSpace(line)) continue;

                try
                {
                    var responseObj = JsonSerializer.Deserialize<OllamaStreamResponse>(line);
                    if (responseObj == null) continue;

                    sentenceBuffer.Append(responseObj.Response);
                    charCount += responseObj.Response?.Length ?? 0;

                    // 检测句子结束或达到一定长度
                    if (IsSentenceEnd(responseObj.Response) || charCount >= 30)
                    {
                        var sentence = sentenceBuffer.ToString().Trim();
                        if (!string.IsNullOrEmpty(sentence))
                        {
                            _logger.LogDebug("输出句子: {Sentence}", sentence);
                            yield return sentence;
                            
                            sentenceBuffer.Clear();
                            charCount = 0;
                        }
                    }

                    if (responseObj.Done)
                    {
                        _logger.LogInformation("流式生成完成");
                        break;
                    }
                }
                catch (JsonException ex)
                {
                    _logger.LogWarning("解析响应失败: {Error}", ex.Message);
                }
            }

            // 输出剩余内容
            if (sentenceBuffer.Length > 0)
            {
                yield return sentenceBuffer.ToString().Trim();
            }
        }

        private bool IsSentenceEnd(string text)
        {
            if (string.IsNullOrEmpty(text)) return false;
            
            return text.Contains("。") || 
                   text.Contains("！") || 
                   text.Contains("？") ||
                   text.Contains(".") ||
                   text.Contains("!") ||
                   text.Contains("?") ||
                   text.Contains("；") ||
                   text.Contains(";");
        }

        private class OllamaStreamResponse
        {
            public string Model { get; set; }
            public string Response { get; set; }
            public bool Done { get; set; }
        }
    }
}