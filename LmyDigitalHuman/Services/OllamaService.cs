using LmyDigitalHuman.Models;
using System.Text.Json;
using System.Text;

namespace LmyDigitalHuman.Services
{
    public class OllamaService : ILocalLLMService
    {
        private readonly HttpClient _httpClient;
        private readonly ILogger<OllamaService> _logger;
        private readonly IConfiguration _configuration;
        private readonly string _baseUrl;

        public OllamaService(
            HttpClient httpClient,
            ILogger<OllamaService> logger,
            IConfiguration configuration)
        {
            _httpClient = httpClient;
            _logger = logger;
            _configuration = configuration;
            _baseUrl = _configuration["LocalLLM:BaseUrl"] ?? "http://localhost:11434";
            
            // 设置超时时间
            _httpClient.Timeout = TimeSpan.FromSeconds(
                _configuration.GetValue<int>("LocalLLM:Timeout", 30000) / 1000);
        }

        public async Task<List<LocalLLMModel>> GetAvailableModelsAsync()
        {
            try
            {
                var response = await _httpClient.GetAsync($"{_baseUrl}/api/tags");
                response.EnsureSuccessStatusCode();
                
                var content = await response.Content.ReadAsStringAsync();
                var tagsResponse = JsonSerializer.Deserialize<OllamaTagsResponse>(content);
                
                return tagsResponse?.Models?.Select(m => new LocalLLMModel
                {
                    Name = m.Name,
                    DisplayName = m.Name,
                    Description = $"Ollama模型: {m.Name}",
                    Version = m.Modified?.ToString("yyyy-MM-dd") ?? "unknown",
                    Size = FormatBytes(m.Size),
                    Language = DetermineLanguage(m.Name),
                    Capabilities = new List<string> { "chat", "completion" },
                    IsLoaded = true,
                    Status = "ready"
                }).ToList() ?? new List<LocalLLMModel>();
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "获取可用模型失败");
                return new List<LocalLLMModel>();
            }
        }

        public async Task<LocalLLMResponse> GenerateResponseAsync(LocalLLMRequest request)
        {
            return await ChatAsync(request);
        }

        public async Task<LocalLLMResponse> ChatAsync(LocalLLMRequest request)
        {
            var startTime = DateTime.Now;
            
            try
            {
                _logger.LogInformation("开始Ollama对话，模型: {ModelName}, 消息: {Message}", 
                    request.ModelName, request.Message);

                var payload = new
                {
                    model = request.ModelName,
                    prompt = BuildPrompt(request),
                    stream = false,
                    options = new
                    {
                        temperature = request.Temperature,
                        top_p = request.TopP,
                        top_k = request.TopK,
                        num_predict = request.MaxTokens
                    }
                };

                var json = JsonSerializer.Serialize(payload);
                var content = new StringContent(json, Encoding.UTF8, "application/json");
                
                var response = await _httpClient.PostAsync($"{_baseUrl}/api/generate", content);
                response.EnsureSuccessStatusCode();

                var responseContent = await response.Content.ReadAsStringAsync();
                var result = JsonSerializer.Deserialize<OllamaResponse>(responseContent);

                var processingTime = DateTime.Now - startTime;

                return new LocalLLMResponse
                {
                    Success = true,
                    Response = result?.Response ?? "",
                    ModelName = request.ModelName,
                    ConversationId = request.ConversationId,
                    TokensUsed = result?.PromptEvalCount + result?.EvalCount ?? 0,
                    ProcessingTime = $"{processingTime.TotalMilliseconds:F0}ms",
                    Metadata = new Dictionary<string, object>
                    {
                        ["prompt_eval_count"] = result?.PromptEvalCount ?? 0,
                        ["eval_count"] = result?.EvalCount ?? 0,
                        ["total_duration"] = result?.TotalDuration ?? 0
                    }
                };
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Ollama对话失败");
                return new LocalLLMResponse
                {
                    Success = false,
                    Message = $"对话失败: {ex.Message}",
                    ProcessingTime = $"{(DateTime.Now - startTime).TotalMilliseconds:F0}ms"
                };
            }
        }

        public async IAsyncEnumerable<LocalLLMStreamResponse> ChatStreamAsync(LocalLLMRequest request)
        {
            var payload = new
            {
                model = request.ModelName,
                prompt = BuildPrompt(request),
                stream = true,
                options = new
                {
                    temperature = request.Temperature,
                    top_p = request.TopP,
                    top_k = request.TopK,
                    num_predict = request.MaxTokens
                }
            };

            var json = JsonSerializer.Serialize(payload);
            var content = new StringContent(json, Encoding.UTF8, "application/json");

            using var response = await _httpClient.PostAsync($"{_baseUrl}/api/generate", content);
            response.EnsureSuccessStatusCode();

            using var stream = await response.Content.ReadAsStreamAsync();
            using var reader = new StreamReader(stream);

            int tokenIndex = 0;
            string? line;
            while ((line = await reader.ReadLineAsync()) != null)
            {
                if (string.IsNullOrWhiteSpace(line)) continue;

                OllamaResponse? result = null;
                try
                {
                    result = JsonSerializer.Deserialize<OllamaResponse>(line);
                }
                catch (JsonException)
                {
                    // 忽略JSON解析错误
                    continue;
                }

                if (result != null)
                {
                    yield return new LocalLLMStreamResponse
                    {
                        Delta = result.Response ?? "",
                        IsComplete = result.Done,
                        ConversationId = request.ConversationId,
                        TokenIndex = tokenIndex++
                    };

                    if (result.Done) break;
                }
            }
        }

        public async Task<ModelStatus> GetModelStatusAsync(string modelName)
        {
            try
            {
                var models = await GetAvailableModelsAsync();
                var model = models.FirstOrDefault(m => m.Name == modelName);
                
                if (model == null)
                {
                    return new ModelStatus
                    {
                        ModelName = modelName,
                        IsLoaded = false,
                        IsReady = false,
                        Status = "not_found",
                        Error = "模型不存在"
                    };
                }

                return new ModelStatus
                {
                    ModelName = modelName,
                    IsLoaded = true,
                    IsReady = true,
                    Status = "ready",
                    LoadedAt = DateTime.Now
                };
            }
            catch (Exception ex)
            {
                return new ModelStatus
                {
                    ModelName = modelName,
                    IsLoaded = false,
                    IsReady = false,
                    Status = "error",
                    Error = ex.Message
                };
            }
        }

        public async Task<bool> LoadModelAsync(string modelName)
        {
            try
            {
                // Ollama模型在首次调用时自动加载
                var testRequest = new LocalLLMRequest
                {
                    ModelName = modelName,
                    Message = "Hello",
                    MaxTokens = 1
                };

                var response = await ChatAsync(testRequest);
                return response.Success;
            }
            catch
            {
                return false;
            }
        }

        public async Task<bool> UnloadModelAsync(string modelName)
        {
            // Ollama不支持手动卸载模型
            return true;
        }

        public async Task<ModelPerformanceStats> GetModelPerformanceAsync(string modelName)
        {
            return new ModelPerformanceStats
            {
                ModelName = modelName,
                TotalRequests = 0,
                AverageResponseTime = 0.0,
                AverageTokensPerSecond = 0,
                TotalTokensGenerated = 0,
                LastRequestTime = DateTime.Now,
                SuccessRate = 1.0
            };
        }

        public async Task<bool> HealthCheckAsync()
        {
            try
            {
                var response = await _httpClient.GetAsync($"{_baseUrl}/api/tags");
                return response.IsSuccessStatusCode;
            }
            catch
            {
                return false;
            }
        }

        private string BuildPrompt(LocalLLMRequest request)
        {
            var prompt = new StringBuilder();
            
            if (!string.IsNullOrEmpty(request.SystemPrompt))
            {
                prompt.AppendLine($"System: {request.SystemPrompt}");
            }

            // 添加历史对话
            foreach (var msg in request.History)
            {
                prompt.AppendLine($"{msg.Role}: {msg.Content}");
            }

            prompt.AppendLine($"User: {request.Message}");
            prompt.Append("Assistant:");

            return prompt.ToString();
        }

        private string DetermineLanguage(string modelName)
        {
            var lowerName = modelName.ToLower();
            if (lowerName.Contains("qwen") || lowerName.Contains("chatglm") || lowerName.Contains("baichuan"))
                return "zh-CN";
            if (lowerName.Contains("llama") || lowerName.Contains("gemma") || lowerName.Contains("mistral"))
                return "en-US";
            return "multi";
        }

        private string FormatBytes(long bytes)
        {
            if (bytes == 0) return "0 B";
            
            string[] sizes = { "B", "KB", "MB", "GB", "TB" };
            int i = 0;
            double dblBytes = bytes;
            
            while (dblBytes >= 1024 && i < sizes.Length - 1)
            {
                dblBytes /= 1024;
                i++;
            }
            
            return $"{dblBytes:F1} {sizes[i]}";
        }
    }

    // Ollama API响应模型
    public class OllamaResponse
    {
        public string Response { get; set; } = "";
        public bool Done { get; set; } = false;
        public int PromptEvalCount { get; set; } = 0;
        public int EvalCount { get; set; } = 0;
        public long TotalDuration { get; set; } = 0;
    }

    public class OllamaTagsResponse
    {
        public List<OllamaModel> Models { get; set; } = new();
    }

    public class OllamaModel
    {
        public string Name { get; set; } = "";
        public long Size { get; set; } = 0;
        public DateTime? Modified { get; set; }
    }
} 