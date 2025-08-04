using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.SignalR;
using LmyDigitalHuman.Services;
using LmyDigitalHuman.Models;
using System.ComponentModel.DataAnnotations;

namespace LmyDigitalHuman.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    public class ConversationController : ControllerBase
    {
        private readonly IConversationService _conversationService;
        private readonly IAudioPipelineService _audioPipelineService;
        private readonly IDigitalHumanTemplateService _templateService;
        private readonly ILogger<ConversationController> _logger;
        private readonly IHubContext<ConversationHub> _hubContext;

        public ConversationController(
            IConversationService conversationService,
            IAudioPipelineService audioPipelineService,
            IDigitalHumanTemplateService templateService,
            ILogger<ConversationController> logger,
            IHubContext<ConversationHub> hubContext)
        {
            _conversationService = conversationService;
            _audioPipelineService = audioPipelineService;
            _templateService = templateService;
            _logger = logger;
            _hubContext = hubContext;
        }

        /// <summary>
        /// 生成欢迎视频 - 选择模板时调用
        /// </summary>
        [HttpPost("welcome")]
        public async Task<IActionResult> GenerateWelcomeVideo([FromBody] WelcomeVideoRequest request)
        {
            try
            {
                if (string.IsNullOrWhiteSpace(request.TemplateId))
                {
                    return BadRequest(new { error = "模板ID不能为空" });
                }

                _logger.LogInformation("生成欢迎视频: TemplateId={TemplateId} (跳过TTS音频生成)", request.TemplateId);

                var response = await _conversationService.GenerateWelcomeVideoAsync(request);
                
                if (response.Success)
                {
                    return Ok(response);
                }
                else
                {
                    return BadRequest(new { error = response.Message });
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "生成欢迎视频失败");
                return StatusCode(500, new { error = "生成欢迎视频失败", details = ex.Message });
            }
        }

        /// <summary>
        /// 文本对话 - 非实时
        /// </summary>
        [HttpPost("text")]
        public async Task<IActionResult> ProcessTextConversation([FromBody] TextConversationRequest request)
        {
            try
            {
                if (string.IsNullOrWhiteSpace(request.TemplateId))
                {
                    return BadRequest(new { error = "模板ID不能为空" });
                }

                if (string.IsNullOrWhiteSpace(request.Text))
                {
                    return BadRequest(new { error = "输入文本不能为空" });
                }

                _logger.LogInformation("处理文本对话: TemplateId={TemplateId}, Text={Text}", 
                    request.TemplateId, request.Text[..Math.Min(50, request.Text.Length)]);

                var response = await _conversationService.ProcessTextConversationAsync(request);
                
                if (response.Success)
                {
                    return Ok(response);
                }
                else
                {
                    return BadRequest(new { error = response.Message });
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "文本对话处理失败");
                return StatusCode(500, new { error = "文本对话处理失败", details = ex.Message });
            }
        }

        /// <summary>
        /// 音频对话 - 非实时
        /// </summary>
        [HttpPost("audio")]
        public async Task<IActionResult> ProcessAudioConversation([FromForm] AudioConversationFormRequest request)
        {
            try
            {
                if (string.IsNullOrWhiteSpace(request.TemplateId))
                {
                    return BadRequest(new { error = "模板ID不能为空" });
                }

                if (request.AudioFile == null || request.AudioFile.Length == 0)
                {
                    return BadRequest(new { error = "音频文件不能为空" });
                }

                _logger.LogInformation("处理音频对话: TemplateId={TemplateId}, AudioSize={AudioSize}", 
                    request.TemplateId, request.AudioFile.Length);

                // 保存音频文件
                var audioPath = Path.Combine("temp", $"audio_{Guid.NewGuid():N}.wav");
                Directory.CreateDirectory(Path.GetDirectoryName(audioPath)!);
                
                using (var fileStream = new FileStream(audioPath, FileMode.Create))
                {
                    await request.AudioFile.CopyToAsync(fileStream);
                }

                var conversationRequest = new AudioConversationRequest
                {
                    TemplateId = request.TemplateId,
                    AudioPath = audioPath,
                    ConversationId = request.ConversationId,
                    ResponseMode = request.ResponseMode,
                    Quality = request.Quality,
                    EnableEmotionDetection = request.EnableEmotionDetection,
                    UseCache = request.UseCache,
                    CustomParameters = request.CustomParameters
                };

                var response = await _conversationService.ProcessAudioConversationAsync(conversationRequest);
                
                // 清理临时音频文件
                try
                {
                    if (System.IO.File.Exists(audioPath))
                    {
                        System.IO.File.Delete(audioPath);
                    }
                }
                catch (Exception ex)
                {
                    _logger.LogWarning(ex, "清理临时音频文件失败: {AudioPath}", audioPath);
                }

                if (response.Success)
                {
                    return Ok(response);
                }
                else
                {
                    return BadRequest(new { error = response.Message });
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "音频对话处理失败");
                return StatusCode(500, new { error = "音频对话处理失败", details = ex.Message });
            }
        }

        /// <summary>
        /// 批量文本对话
        /// </summary>
        [HttpPost("batch/text")]
        public async Task<IActionResult> ProcessBatchTextConversations([FromBody] BatchTextConversationRequest request)
        {
            try
            {
                if (request.Requests == null || !request.Requests.Any())
                {
                    return BadRequest(new { error = "批量请求不能为空" });
                }

                if (request.Requests.Count > 10) // 限制批量大小
                {
                    return BadRequest(new { error = "批量请求数量不能超过10个" });
                }

                _logger.LogInformation("处理批量文本对话: Count={Count}", request.Requests.Count);

                var responses = await _conversationService.ProcessBatchConversationsAsync(request.Requests);
                
                return Ok(new { results = responses });
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "批量文本对话处理失败");
                return StatusCode(500, new { error = "批量文本对话处理失败", details = ex.Message });
            }
        }

        /// <summary>
        /// 开始实时对话
        /// </summary>
        [HttpPost("realtime/start")]
        public async Task<IActionResult> StartRealtimeConversation([FromBody] StartRealtimeConversationRequest request)
        {
            try
            {
                if (string.IsNullOrWhiteSpace(request.TemplateId))
                {
                    return BadRequest(new { error = "模板ID不能为空" });
                }

                _logger.LogInformation("开始实时对话: TemplateId={TemplateId}", request.TemplateId);

                var response = await _conversationService.StartRealtimeConversationAsync(request);
                
                if (response.Success)
                {
                    return Ok(response);
                }
                else
                {
                    return BadRequest(new { error = response.Message });
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "启动实时对话失败");
                return StatusCode(500, new { error = "启动实时对话失败", details = ex.Message });
            }
        }

        /// <summary>
        /// 结束实时对话
        /// </summary>
        [HttpPost("realtime/end/{conversationId}")]
        public async Task<IActionResult> EndRealtimeConversation(string conversationId)
        {
            try
            {
                if (string.IsNullOrWhiteSpace(conversationId))
                {
                    return BadRequest(new { error = "对话ID不能为空" });
                }

                _logger.LogInformation("结束实时对话: ConversationId={ConversationId}", conversationId);

                var success = await _conversationService.EndRealtimeConversationAsync(conversationId);
                
                if (success)
                {
                    return Ok(new { message = "实时对话已结束" });
                }
                else
                {
                    return NotFound(new { error = "对话不存在或已结束" });
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "结束实时对话失败");
                return StatusCode(500, new { error = "结束实时对话失败", details = ex.Message });
            }
        }

        /// <summary>
        /// 获取对话上下文
        /// </summary>
        [HttpGet("context/{conversationId}")]
        public async Task<IActionResult> GetConversationContext(string conversationId)
        {
            try
            {
                if (string.IsNullOrWhiteSpace(conversationId))
                {
                    return BadRequest(new { error = "对话ID不能为空" });
                }

                var context = await _conversationService.GetConversationContextAsync(conversationId);
                
                return Ok(context);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "获取对话上下文失败");
                return StatusCode(500, new { error = "获取对话上下文失败", details = ex.Message });
            }
        }

        /// <summary>
        /// 清理对话上下文
        /// </summary>
        [HttpDelete("context/{conversationId}")]
        public async Task<IActionResult> ClearConversationContext(string conversationId)
        {
            try
            {
                if (string.IsNullOrWhiteSpace(conversationId))
                {
                    return BadRequest(new { error = "对话ID不能为空" });
                }

                var success = await _conversationService.ClearConversationContextAsync(conversationId);
                
                if (success)
                {
                    return Ok(new { message = "对话上下文已清理" });
                }
                else
                {
                    return NotFound(new { error = "对话上下文不存在" });
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "清理对话上下文失败");
                return StatusCode(500, new { error = "清理对话上下文失败", details = ex.Message });
            }
        }

        /// <summary>
        /// 获取对话历史
        /// </summary>
        [HttpGet("history")]
        public async Task<IActionResult> GetConversationHistory(
            [FromQuery] string? conversationId = null, 
            [FromQuery] int limit = 50)
        {
            try
            {
                if (limit > 100)
                {
                    return BadRequest(new { error = "限制数量不能超过100" });
                }

                var history = await _conversationService.GetConversationHistoryAsync(conversationId, limit);
                
                return Ok(new { history = history });
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "获取对话历史失败");
                return StatusCode(500, new { error = "获取对话历史失败", details = ex.Message });
            }
        }

        /// <summary>
        /// 获取对话统计信息
        /// </summary>
        [HttpGet("statistics")]
        public async Task<IActionResult> GetConversationStatistics()
        {
            try
            {
                var statistics = await _conversationService.GetConversationStatisticsAsync();
                
                return Ok(statistics);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "获取对话统计信息失败");
                return StatusCode(500, new { error = "获取对话统计信息失败", details = ex.Message });
            }
        }

        /// <summary>
        /// 预加载模板用于对话
        /// </summary>
        [HttpPost("preload/{templateId}")]
        public async Task<IActionResult> PreloadTemplateForConversation(string templateId)
        {
            try
            {
                if (string.IsNullOrWhiteSpace(templateId))
                {
                    return BadRequest(new { error = "模板ID不能为空" });
                }

                _logger.LogInformation("预加载模板: TemplateId={TemplateId}", templateId);

                var success = await _conversationService.PreloadTemplateForConversationAsync(templateId);
                
                if (success)
                {
                    return Ok(new { message = "模板预加载成功" });
                }
                else
                {
                    return BadRequest(new { error = "模板预加载失败" });
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "预加载模板失败");
                return StatusCode(500, new { error = "预加载模板失败", details = ex.Message });
            }
        }
    }



    /// <summary>
    /// 音频对话表单请求（用于文件上传）
    /// </summary>
    public class AudioConversationFormRequest
    {
        [Required]
        public string TemplateId { get; set; } = string.Empty;

        [Required]
        public IFormFile AudioFile { get; set; } = default!;

        public string? ConversationId { get; set; }
        public string ResponseMode { get; set; } = "fast";
        public string Quality { get; set; } = "medium";
        public bool EnableEmotionDetection { get; set; } = true;
        public bool UseCache { get; set; } = true;
        public Dictionary<string, object>? CustomParameters { get; set; }
    }

    /// <summary>
    /// 批量文本对话请求
    /// </summary>
    public class BatchTextConversationRequest
    {
        [Required]
        public List<TextConversationRequest> Requests { get; set; } = new();
    }

    /// <summary>
    /// SignalR Hub for real-time conversation
    /// </summary>
    public class ConversationHub : Hub
    {
        private readonly IConversationService _conversationService;
        private readonly ILogger<ConversationHub> _logger;

        public ConversationHub(
            IConversationService conversationService,
            ILogger<ConversationHub> logger)
        {
            _conversationService = conversationService;
            _logger = logger;
        }

        public async Task JoinConversation(string conversationId)
        {
            await Groups.AddToGroupAsync(Context.ConnectionId, conversationId);
            _logger.LogInformation("客户端加入对话组: ConnectionId={ConnectionId}, ConversationId={ConversationId}", 
                Context.ConnectionId, conversationId);
        }

        public async Task LeaveConversation(string conversationId)
        {
            await Groups.RemoveFromGroupAsync(Context.ConnectionId, conversationId);
            _logger.LogInformation("客户端离开对话组: ConnectionId={ConnectionId}, ConversationId={ConversationId}", 
                Context.ConnectionId, conversationId);
        }

        public async Task SendRealtimeAudio(string conversationId, byte[] audioData, bool isEndOfSpeech)
        {
            try
            {
                var request = new ProcessRealtimeAudioRequest
                {
                    ConversationId = conversationId,
                    AudioData = audioData,
                    IsEndOfSpeech = isEndOfSpeech,
                    AudioFormat = "wav"
                };

                var response = await _conversationService.ProcessRealtimeAudioAsync(request);
                
                // 向对话组中的所有客户端发送响应
                await Clients.Group(conversationId).SendAsync("ReceiveConversationResponse", response);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "处理实时音频失败: ConversationId={ConversationId}", conversationId);
                await Clients.Caller.SendAsync("ReceiveError", "处理实时音频失败: " + ex.Message);
            }
        }

        public override async Task OnDisconnectedAsync(Exception? exception)
        {
            _logger.LogInformation("客户端断开连接: ConnectionId={ConnectionId}", Context.ConnectionId);
            await base.OnDisconnectedAsync(exception);
        }
    }
}