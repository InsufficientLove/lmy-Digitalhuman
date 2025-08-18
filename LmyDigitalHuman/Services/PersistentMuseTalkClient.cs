using System.Net.Sockets;
using System.Text;
using System.Text.Json;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Configuration;

namespace LmyDigitalHuman.Services
{
    /// <summary>
    /// 持久化MuseTalk客户端
    /// 通过TCP Socket与Python持久化服务通信，避免每次推理都启动新的Python进程
    /// </summary>
    public class PersistentMuseTalkClient : IDisposable
    {
        private readonly ILogger<PersistentMuseTalkClient> _logger;
        private readonly IConfiguration _configuration;
        private readonly string _host;
        private readonly int _port;
        private readonly int _connectionTimeout;
        private readonly int _responseTimeout;
        
        private TcpClient? _tcpClient;
        private NetworkStream? _stream;
        private readonly object _lockObject = new object();
        private bool _isConnected = false;
        private DateTime _lastPingTime = DateTime.MinValue;
        private readonly TimeSpan _pingInterval = TimeSpan.FromMinutes(1);

        public PersistentMuseTalkClient(
            ILogger<PersistentMuseTalkClient> logger,
            IConfiguration configuration)
        {
            _logger = logger;
            _configuration = configuration;
            
            // 从配置读取连接参数
            _host = _configuration.GetValue<string>("PersistentMuseTalk:Host") ?? "127.0.0.1";
            _port = _configuration.GetValue<int>("PersistentMuseTalk:Port", 58080);
            _connectionTimeout = _configuration.GetValue<int>("PersistentMuseTalk:ConnectionTimeout", 5000);
            _responseTimeout = _configuration.GetValue<int>("PersistentMuseTalk:ResponseTimeout", 30000);
            
            _logger.LogInformation("初始化持久化MuseTalk客户端");
            _logger.LogInformation("📡 目标地址: {Host}:{Port}", _host, _port);
        }

        /// <summary>
        /// 确保连接到持久化服务
        /// </summary>
        private async Task EnsureConnectedAsync()
        {
            lock (_lockObject)
            {
                if (_isConnected && _tcpClient?.Connected == true)
                {
                    // 检查是否需要发送ping
                    if (DateTime.Now - _lastPingTime > _pingInterval)
                    {
                        _ = Task.Run(async () => await PingAsync());
                    }
                    return;
                }

                // 需要重新连接
                Disconnect();
                Connect();
            }
        }

        /// <summary>
        /// 连接到持久化服务
        /// </summary>
        private void Connect()
        {
            try
            {
                _logger.LogInformation("🔗 正在连接持久化MuseTalk服务...");
                
                _tcpClient = new TcpClient();
                _tcpClient.ReceiveTimeout = _responseTimeout;
                _tcpClient.SendTimeout = _connectionTimeout;
                
                var connectTask = _tcpClient.ConnectAsync(_host, _port);
                if (!connectTask.Wait(_connectionTimeout))
                {
                    throw new TimeoutException($"连接超时: {_host}:{_port}");
                }
                
                _stream = _tcpClient.GetStream();
                _isConnected = true;
                _lastPingTime = DateTime.Now;
                
                _logger.LogInformation("持久化MuseTalk服务连接成功");
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "连接持久化MuseTalk服务失败");
                Disconnect();
                throw;
            }
        }

        /// <summary>
        /// 断开连接
        /// </summary>
        private void Disconnect()
        {
            try
            {
                _stream?.Close();
                _tcpClient?.Close();
            }
            catch { }
            finally
            {
                _stream = null;
                _tcpClient = null;
                _isConnected = false;
            }
        }

        /// <summary>
        /// 发送请求并接收响应
        /// </summary>
        private async Task<T?> SendRequestAsync<T>(object request) where T : class
        {
            await EnsureConnectedAsync();
            
            if (_stream == null)
            {
                throw new InvalidOperationException("网络流未初始化");
            }

            try
            {
                // 序列化请求
                var requestJson = JsonSerializer.Serialize(request, new JsonSerializerOptions
                {
                    PropertyNamingPolicy = JsonNamingPolicy.CamelCase
                });
                
                // 添加换行符作为消息结束标记（Python服务端按行读取）
                requestJson += "\n";
                
                var requestBytes = Encoding.UTF8.GetBytes(requestJson);
                
                _logger.LogDebug("📤 发送请求: {RequestSize} bytes", requestBytes.Length);
                
                // 发送请求
                await _stream.WriteAsync(requestBytes);
                await _stream.FlushAsync();
                
                // 接收响应
                var buffer = new byte[65536]; // 64KB buffer
                var responseBuilder = new StringBuilder();
                var totalReceived = 0;
                
                using var cts = new CancellationTokenSource(_responseTimeout);
                
                while (!cts.Token.IsCancellationRequested)
                {
                    var bytesRead = await _stream.ReadAsync(buffer, cts.Token);
                    if (bytesRead == 0)
                        break;
                    
                    var chunk = Encoding.UTF8.GetString(buffer, 0, bytesRead);
                    responseBuilder.Append(chunk);
                    totalReceived += bytesRead;
                    
                    // 尝试解析JSON，如果成功说明响应完整
                    try
                    {
                        var responseJson = responseBuilder.ToString();
                        var response = JsonSerializer.Deserialize<T>(responseJson, new JsonSerializerOptions
                        {
                            PropertyNamingPolicy = JsonNamingPolicy.CamelCase
                        });
                        
                        _logger.LogDebug("📥 接收响应: {ResponseSize} bytes", totalReceived);
                        return response;
                    }
                    catch (JsonException)
                    {
                        // JSON不完整，继续接收
                    }
                }
                
                throw new TimeoutException("接收响应超时");
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "发送请求失败");
                Disconnect(); // 连接可能已损坏，断开重连
                throw;
            }
        }

        /// <summary>
        /// Ping测试连接
        /// </summary>
        public async Task<bool> PingAsync()
        {
            try
            {
                var request = new { command = "ping" };
                var response = await SendRequestAsync<PingResponse>(request);
                
                _lastPingTime = DateTime.Now;
                var success = response?.Success == true;
                
                if (success)
                {
                    _logger.LogDebug("🏓 Ping成功: {Message}", response?.Message);
                }
                else
                {
                    _logger.LogWarning("Ping失败");
                }
                
                return success;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Ping失败");
                return false;
            }
        }

        /// <summary>
        /// 数字人推理
        /// </summary>
        public async Task<InferenceResponse?> InferenceAsync(
            string templateId,
            string audioPath,
            string outputPath,
            string templateDir = "./wwwroot/templates",
            int fps = 25,
            int bboxShift = 0,
            string parsingMode = "jaw")
        {
            _logger.LogInformation("开始持久化推理: TemplateId={TemplateId}", templateId);
            
            var startTime = DateTime.Now;
            
            try
            {
                var request = new
                {
                    command = "inference",
                    template_id = templateId,
                    audio_path = audioPath,
                    output_path = outputPath,
                    template_dir = templateDir,
                    fps = fps,
                    bbox_shift = bboxShift,
                    parsing_mode = parsingMode
                };
                
                var response = await SendRequestAsync<InferenceResponse>(request);
                
                var totalTime = DateTime.Now - startTime;
                
                if (response?.Success == true)
                {
                    _logger.LogInformation("持久化推理完成: TemplateId={TemplateId}, 总耗时={TotalTime:F2}秒, 推理耗时={InferenceTime:F2}秒", 
                        templateId, totalTime.TotalSeconds, response.InferenceTime);
                }
                else
                {
                    _logger.LogError("持久化推理失败: TemplateId={TemplateId}, 错误={Error}", 
                        templateId, response?.Error);
                }
                
                return response;
            }
            catch (Exception ex)
            {
                var totalTime = DateTime.Now - startTime;
                _logger.LogError(ex, "持久化推理异常: TemplateId={TemplateId}, 总耗时={TotalTime:F2}秒", 
                    templateId, totalTime.TotalSeconds);
                throw;
            }
        }

        /// <summary>
        /// 预处理模板
        /// </summary>
        public async Task<PreprocessResponse?> PreprocessAsync(
            string templateId,
            string? templateImagePath = null,
            int bboxShift = 0,
            string parsingMode = "jaw")
        {
            _logger.LogInformation("开始预处理: TemplateId={TemplateId}", templateId);
            
            try
            {
                var request = new
                {
                    command = "preprocess",
                    template_id = templateId,
                    template_image_path = templateImagePath,
                    bbox_shift = bboxShift,
                    parsing_mode = parsingMode
                };
                
                var response = await SendRequestAsync<PreprocessResponse>(request);
                
                if (response?.Success == true)
                {
                    _logger.LogInformation("预处理完成: TemplateId={TemplateId}, 耗时={ProcessTime:F2}秒", 
                        templateId, response.ProcessTime);
                }
                else
                {
                    _logger.LogError("预处理失败: TemplateId={TemplateId}, 错误={Error}", 
                        templateId, response?.Error);
                }
                
                return response;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "预处理异常: TemplateId={TemplateId}", templateId);
                throw;
            }
        }

        /// <summary>
        /// 检查缓存状态
        /// </summary>
        public async Task<CheckCacheResponse?> CheckCacheAsync(string templateId)
        {
            try
            {
                var request = new { command = "check_cache", template_id = templateId };
                var response = await SendRequestAsync<CheckCacheResponse>(request);
                
                _logger.LogDebug("缓存检查: TemplateId={TemplateId}, 存在={CacheExists}", 
                    templateId, response?.CacheExists);
                
                return response;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "检查缓存异常: TemplateId={TemplateId}", templateId);
                throw;
            }
        }

        /// <summary>
        /// 获取服务状态
        /// </summary>
        public async Task<StatusResponse?> GetStatusAsync()
        {
            try
            {
                var request = new { command = "status" };
                var response = await SendRequestAsync<StatusResponse>(request);
                
                if (response?.Success == true)
                {
                    _logger.LogDebug("服务状态: {Status}, 模型已加载={ModelLoaded}", 
                        response.Status, response.ModelLoaded);
                }
                
                return response;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "获取状态异常");
                throw;
            }
        }

        public void Dispose()
        {
            Disconnect();
        }
    }

    // 响应数据模型
    public class PingResponse
    {
        public bool Success { get; set; }
        public string? Message { get; set; }
        public double Timestamp { get; set; }
        public bool ModelLoaded { get; set; }
    }

    public class InferenceResponse
    {
        public bool Success { get; set; }
        public string? ResultPath { get; set; }
        public double InferenceTime { get; set; }
        public string? TemplateId { get; set; }
        public string? Error { get; set; }
        public string? ErrorType { get; set; }
    }

    public class PreprocessResponse
    {
        public bool Success { get; set; }
        public double ProcessTime { get; set; }
        public string? TemplateId { get; set; }
        public string? Error { get; set; }
        public string? ErrorType { get; set; }
    }

    public class CheckCacheResponse
    {
        public bool Success { get; set; }
        public string? TemplateId { get; set; }
        public bool CacheExists { get; set; }
        public string? CachePath { get; set; }
        public string? MetadataPath { get; set; }
        public string? Error { get; set; }
        public string? ErrorType { get; set; }
    }

    public class StatusResponse
    {
        public bool Success { get; set; }
        public string? Status { get; set; }
        public bool ModelLoaded { get; set; }
        public string? Device { get; set; }
        public string? CacheDir { get; set; }
        public int ActiveThreads { get; set; }
        public double Uptime { get; set; }
        public string? Version { get; set; }
    }
}