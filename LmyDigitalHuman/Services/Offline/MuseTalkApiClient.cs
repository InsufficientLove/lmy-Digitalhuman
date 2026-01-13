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
        public async Task<(bool Success, string? Message)> PreprocessTemplateAsync(string templateId, string imagePath)
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
                
                _logger.LogInformation("发送模板预处理请求: TemplateId={TemplateId}, ImagePath={ImagePath}", templateId, imagePath);
                
                var response = await _httpClient.PostAsync("/api/preprocess_template", content);
                var responseText = await response.Content.ReadAsStringAsync();
                
                _logger.LogInformation("模板预处理响应: StatusCode={StatusCode}, Content={Content}", 
                    response.StatusCode, responseText);
                
                if (response.IsSuccessStatusCode)
                {
                    try
                    {
                        var result = JsonSerializer.Deserialize<JsonElement>(responseText);
                        
                        if (result.TryGetProperty("success", out var successProp) && successProp.GetBoolean())
                        {
                            var message = result.TryGetProperty("message", out var msgProp) 
                                ? msgProp.GetString() 
                                : "Success";
                            _logger.LogInformation("✅ 模板预处理成功: {TemplateId}, Message={Message}", templateId, message);
                            return (true, message);
                        }
                        else
                        {
                            var message = result.TryGetProperty("message", out var msgProp) 
                                ? msgProp.GetString() 
                                : "Unknown error";
                            _logger.LogError("模板预处理失败: {Message}", message);
                            return (false, message);
                        }
                    }
                    catch (JsonException)
                    {
                        // 如果响应不是JSON格式，返回原始文本
                        _logger.LogInformation("✅ 模板预处理成功: {TemplateId}", templateId);
                        return (true, responseText);
                    }
                }
                
                _logger.LogError("模板预处理HTTP请求失败: StatusCode={StatusCode}, Response={Response}", 
                    response.StatusCode, responseText);
                return (false, $"HTTP {response.StatusCode}: {responseText}");
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "预处理模板时发生错误");
                return (false, ex.Message);
            }
        }

        /// <summary>
        /// 预处理视频模板
        /// </summary>
        public async Task<(bool Success, string? BboxPath, string? Message)> PreprocessVideoAsync(string templateId, string videoPath)
        {
            try
            {
                _logger.LogInformation("发送视频预处理请求: TemplateId={TemplateId}, VideoPath={VideoPath}", templateId, videoPath);
                
                var request = new
                {
                    template_id = templateId,
                    video_path = videoPath,
                    force = false
                };

                var json = JsonSerializer.Serialize(request);
                var content = new StringContent(json, Encoding.UTF8, "application/json");
                
                var response = await _httpClient.PostAsync("/api/preprocess_video", content);
                
                var responseText = await response.Content.ReadAsStringAsync();
                _logger.LogInformation("视频预处理响应: StatusCode={StatusCode}, Content={Content}", 
                    response.StatusCode, responseText);
                
                if (response.IsSuccessStatusCode)
                {
                    var result = JsonSerializer.Deserialize<JsonElement>(responseText);
                    
                    if (result.TryGetProperty("success", out var successProp) && successProp.GetBoolean())
                    {
                        string? bboxPath = null;
                        string? message = null;
                        
                        if (result.TryGetProperty("bbox_path", out var bboxPathProp))
                        {
                            bboxPath = bboxPathProp.GetString();
                        }
                        
                        if (result.TryGetProperty("message", out var messageProp))
                        {
                            message = messageProp.GetString();
                        }
                        
                        _logger.LogInformation("✅ 视频模板预处理成功: {TemplateId}, BboxPath={BboxPath}", templateId, bboxPath);
                        return (true, bboxPath, message);
                    }
                    else
                    {
                        var message = result.TryGetProperty("message", out var msgProp) 
                            ? msgProp.GetString() 
                            : "Unknown error";
                        _logger.LogError("视频预处理失败: {Message}", message);
                        return (false, null, message);
                    }
                }
                
                _logger.LogError("视频预处理HTTP请求失败: StatusCode={StatusCode}, Response={Response}", 
                    response.StatusCode, responseText);
                return (false, null, $"HTTP {response.StatusCode}: {responseText}");
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "预处理视频模板时发生错误");
                return (false, null, ex.Message);
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
                // #region agent log
                await System.IO.File.AppendAllTextAsync(@"f:\AICode\Digitalhuman\lmy-DigitalhumanV5\lmy-Digitalhuman\.cursor\debug.log", System.Text.Json.JsonSerializer.Serialize(new{sessionId="debug-session",runId="initial",hypothesisId="A,B",location="MuseTalkApiClient.cs:176",message="StartSessionAsync准备发送到Python",data=new{templateId,sessionId},timestamp=DateTimeOffset.UtcNow.ToUnixTimeMilliseconds()})+"\n");
                // #endregion
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
                        // 路径适配：Python返回的是 /videos/xxx.mp4，C#容器也挂载了 /videos 目录
                        string actualVideoPath = videoPath;
                        
                        // 如果Python返回的是 /videos/ 路径（统一配置）
                        if (videoPath.StartsWith("/videos/"))
                        {
                            // 直接使用，因为两个容器都挂载了相同的 /videos 目录
                            actualVideoPath = videoPath;
                            
                            // 验证文件是否存在
                            if (!File.Exists(actualVideoPath))
                            {
                                _logger.LogWarning("⚠️ 视频文件不存在: {VideoPath}", actualVideoPath);
                                // 尝试等待一小段时间（异步写入可能需要时间）
                                await Task.Delay(500);
                                
                                if (!File.Exists(actualVideoPath))
                                {
                                    _logger.LogError("❌ 视频文件仍不存在: {VideoPath}", actualVideoPath);
                                    return null;
                                }
                            }
                            
                            _logger.LogInformation("✅ 视频文件已验证: {VideoPath}", actualVideoPath);
                        }
                        // 兼容旧的 /opt/musetalk/videos/ 路径（向后兼容）
                        else if (videoPath.StartsWith("/opt/musetalk/videos/"))
                        {
                            var fileName = Path.GetFileName(videoPath);
                            actualVideoPath = Path.Combine("/videos", fileName);
                            
                            // 验证文件存在性
                            if (!File.Exists(actualVideoPath))
                            {
                                _logger.LogWarning("⚠️ 视频文件不存在（旧路径格式）: {VideoPath}", actualVideoPath);
                                return null;
                            }
                        }
                        else
                        {
                            // 其他路径格式，提取文件名并在 /videos 查找
                            var fileName = Path.GetFileName(videoPath);
                            actualVideoPath = Path.Combine("/videos", fileName);
                            
                            if (!File.Exists(actualVideoPath))
                            {
                                _logger.LogWarning("⚠️ 未知路径格式，无法定位视频: {VideoPath}", videoPath);
                                return null;
                            }
                        }
                        
                        // 如果需要，复制到指定输出路径
                        if (!string.IsNullOrEmpty(outputPath) && actualVideoPath != outputPath)
                        {
                            try
                            {
                                var outputDir = Path.GetDirectoryName(outputPath);
                                if (!string.IsNullOrEmpty(outputDir))
                                {
                                    Directory.CreateDirectory(outputDir);
                                }
                                
                                File.Copy(actualVideoPath, outputPath, true);
                                _logger.LogInformation("✅ 视频已复制到: {OutputPath}", outputPath);
                                return outputPath;
                            }
                            catch (Exception ex)
                            {
                                _logger.LogError(ex, "❌ 复制视频文件失败: {Source} -> {Dest}", actualVideoPath, outputPath);
                                // 复制失败，返回原始路径
                                return actualVideoPath;
                            }
                        }
                        
                        return actualVideoPath;
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