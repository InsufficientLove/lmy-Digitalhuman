using System.Net.Http;
using System.Text;
using System.Text.Json;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Configuration;

namespace LmyDigitalHuman.Services.Offline
{
    /// <summary>
    /// MuseTalk HTTP API客户端
    /// 通过HTTP API与Python服务通信
    /// </summary>
    public class MuseTalkApiClient : IDisposable
    {
        private readonly ILogger<MuseTalkApiClient> _logger;
        private readonly IConfiguration _configuration;
        private readonly HttpClient _httpClient;
        private readonly string _baseUrl;
        private bool _isInitialized = false;

        public MuseTalkApiClient(
            ILogger<MuseTalkApiClient> logger,
            IConfiguration configuration,
            IHttpClientFactory httpClientFactory)
        {
            _logger = logger;
            _configuration = configuration;
            
            // 从配置读取API URL
            _baseUrl = _configuration.GetValue<string>("MuseTalk:ServiceUrl") ?? "http://musetalk-python:28888";
            
            _httpClient = httpClientFactory.CreateClient();
            _httpClient.BaseAddress = new Uri(_baseUrl);
            _httpClient.Timeout = TimeSpan.FromSeconds(_configuration.GetValue<int>("MuseTalk:Timeout", 300));
            
            _logger.LogInformation("初始化MuseTalk HTTP API客户端");
            _logger.LogInformation("📡 API地址: {BaseUrl}", _baseUrl);
        }

        /// <summary>
        /// 初始化服务
        /// </summary>
        public async Task<bool> InitializeAsync()
        {
            try
            {
                _logger.LogInformation("🚀 初始化MuseTalk服务...");
                
                var response = await _httpClient.PostAsync("/api/initialize", null);
                if (response.IsSuccessStatusCode)
                {
                    _isInitialized = true;
                    _logger.LogInformation("✅ MuseTalk服务初始化成功");
                    return true;
                }
                
                _logger.LogError("MuseTalk服务初始化失败: {StatusCode}", response.StatusCode);
                return false;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "初始化MuseTalk服务时发生错误");
                return false;
            }
        }

        /// <summary>
        /// 预处理模板
        /// </summary>
        public async Task<bool> PreprocessTemplateAsync(string templateId, string imagePath)
        {
            try
            {
                var request = new
                {
                    template_id = templateId,
                    image_path = imagePath
                };

                var json = JsonSerializer.Serialize(request);
                var content = new StringContent(json, Encoding.UTF8, "application/json");
                
                var response = await _httpClient.PostAsync("/api/preprocess_template", content);
                if (response.IsSuccessStatusCode)
                {
                    _logger.LogInformation("✅ 模板预处理成功: {TemplateId}", templateId);
                    return true;
                }
                
                var error = await response.Content.ReadAsStringAsync();
                _logger.LogError("模板预处理失败: {Error}", error);
                return false;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "预处理模板时发生错误");
                return false;
            }
        }

        /// <summary>
        /// 开始会话
        /// </summary>
        public async Task<string?> StartSessionAsync(string templateId)
        {
            try
            {
                var sessionId = Guid.NewGuid().ToString();
                var request = new
                {
                    session_id = sessionId,
                    template_id = templateId
                };

                var json = JsonSerializer.Serialize(request);
                var content = new StringContent(json, Encoding.UTF8, "application/json");
                
                var response = await _httpClient.PostAsync("/api/start_session", content);
                if (response.IsSuccessStatusCode)
                {
                    _logger.LogInformation("✅ 会话启动成功: {SessionId}", sessionId);
                    return sessionId;
                }
                
                var error = await response.Content.ReadAsStringAsync();
                _logger.LogError("启动会话失败: {Error}", error);
                return null;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "启动会话时发生错误");
                return null;
            }
        }

        /// <summary>
        /// 处理音频片段
        /// </summary>
        public async Task<string?> ProcessSegmentAsync(string sessionId, string audioPath, int segmentIndex = 0, bool isFinal = false)
        {
            try
            {
                var request = new
                {
                    session_id = sessionId,
                    audio_path = audioPath,
                    segment_index = segmentIndex,
                    is_final = isFinal
                };

                var json = JsonSerializer.Serialize(request);
                var content = new StringContent(json, Encoding.UTF8, "application/json");
                
                var response = await _httpClient.PostAsync("/api/process_segment", content);
                if (response.IsSuccessStatusCode)
                {
                    var result = await response.Content.ReadAsStringAsync();
                    var data = JsonSerializer.Deserialize<JsonElement>(result);
                    
                    if (data.TryGetProperty("video_path", out var videoPath))
                    {
                        _logger.LogInformation("✅ 片段处理成功: {VideoPath}", videoPath.GetString());
                        return videoPath.GetString();
                    }
                }
                
                var error = await response.Content.ReadAsStringAsync();
                _logger.LogError("处理片段失败: {Error}", error);
                return null;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "处理音频片段时发生错误");
                return null;
            }
        }

        /// <summary>
        /// 结束会话
        /// </summary>
        public async Task<bool> EndSessionAsync(string sessionId)
        {
            try
            {
                var response = await _httpClient.PostAsync($"/api/end_session/{sessionId}", null);
                if (response.IsSuccessStatusCode)
                {
                    _logger.LogInformation("✅ 会话结束: {SessionId}", sessionId);
                    return true;
                }
                
                return false;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "结束会话时发生错误");
                return false;
            }
        }

        /// <summary>
        /// 极速实时推理（完整流程）
        /// </summary>
        public async Task<string?> UltraFastInferenceAsync(string templateId, string audioPath, string outputPath)
        {
            try
            {
                // 确保服务已初始化
                if (!_isInitialized)
                {
                    await InitializeAsync();
                }

                // 开始会话
                var sessionId = await StartSessionAsync(templateId);
                if (string.IsNullOrEmpty(sessionId))
                {
                    _logger.LogError("无法启动会话");
                    return null;
                }

                try
                {
                    // 处理音频
                    var videoPath = await ProcessSegmentAsync(sessionId, audioPath, 0, true);
                    
                    if (!string.IsNullOrEmpty(videoPath))
                    {
                        // 如果需要，复制到指定输出路径
                        if (!string.IsNullOrEmpty(outputPath) && videoPath != outputPath)
                        {
                            if (File.Exists(videoPath))
                            {
                                File.Copy(videoPath, outputPath, true);
                                _logger.LogInformation("视频已复制到: {OutputPath}", outputPath);
                            }
                        }
                        
                        return videoPath;
                    }
                    
                    return null;
                }
                finally
                {
                    // 结束会话
                    await EndSessionAsync(sessionId);
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "极速推理失败");
                return null;
            }
        }

        /// <summary>
        /// 检查服务健康状态
        /// </summary>
        public async Task<bool> CheckHealthAsync()
        {
            try
            {
                var response = await _httpClient.GetAsync("/health");
                return response.IsSuccessStatusCode;
            }
            catch
            {
                return false;
            }
        }

        public void Dispose()
        {
            _httpClient?.Dispose();
        }
    }
}