using Microsoft.AspNetCore.Mvc;
using FlowithRealizationAPI.Services;
using FlowithRealizationAPI.Models;
using Newtonsoft.Json;
using Microsoft.Extensions.DependencyInjection;

namespace FlowithRealizationAPI.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    public class RealtimeDigitalHumanController : ControllerBase
    {
        private readonly IRealtimeDigitalHumanService _realtimeService;
        private readonly IWhisperService _whisperService;
        private readonly ILogger<RealtimeDigitalHumanController> _logger;

        public RealtimeDigitalHumanController(
            IRealtimeDigitalHumanService realtimeService,
            IWhisperService whisperService,
            ILogger<RealtimeDigitalHumanController> logger)
        {
            _realtimeService = realtimeService;
            _whisperService = whisperService;
            _logger = logger;
        }

        /// <summary>
        /// 语音转文本 - 使用本地Whisper，免费且高精度
        /// </summary>
        [HttpPost("speech-to-text")]
        public async Task<IActionResult> SpeechToText([FromForm] IFormFile audioFile)
        {
            try
            {
                if (audioFile == null || audioFile.Length == 0)
                {
                    return BadRequest(new { error = "音频文件不能为空" });
                }

                _logger.LogInformation("开始语音转文本，文件大小: {Size} bytes", audioFile.Length);

                var result = await _whisperService.TranscribeAsync(audioFile);
                
                return Ok(new
                {
                    success = true,
                    text = result.Text,
                    confidence = result.Confidence,
                    language = result.Language,
                    processingTime = result.ProcessingTime
                });
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "语音转文本失败");
                return StatusCode(500, new { error = "语音转文本失败", details = ex.Message });
            }
        }

        /// <summary>
        /// 立即响应对话 - 混合策略：预渲染视频 + 实时合成
        /// </summary>
        [HttpPost("instant-chat")]
        public async Task<IActionResult> InstantChat([FromBody] InstantChatRequest request)
        {
            try
            {
                if (string.IsNullOrWhiteSpace(request.Text))
                {
                    return BadRequest(new { error = "输入文本不能为空" });
                }

                _logger.LogInformation("开始立即响应对话，输入文本: {Text}", request.Text);

                // 使用模板服务生成视频
                var templateService = HttpContext.RequestServices.GetRequiredService<IDigitalHumanTemplateService>();
                var generateRequest = new GenerateWithTemplateRequest
                {
                    TemplateId = request.AvatarId,
                    Text = request.Text,
                    ResponseMode = request.ResponseMode,
                    Quality = request.Quality,
                    Emotion = "neutral" // 可以根据文本分析情感
                };

                var result = await templateService.GenerateWithTemplateAsync(generateRequest);
                
                if (result.Success)
                {
                    // 转换为即时聊天响应格式
                    var instantResponse = new InstantChatResponse
                    {
                        Success = true,
                        ResponseText = request.Text, // 这里可以添加AI回复文本
                        VideoUrl = result.VideoUrl,
                        AudioUrl = result.AudioUrl,
                        Metadata = new ResponseMetadata
                        {
                            ResponseType = result.ResponseMode,
                            ProcessingTime = 0, // 可以从result中解析
                            VideoDuration = 0,
                            Quality = new VideoQualityInfo
                            {
                                Resolution = "1280x720", // 默认分辨率
                                Fps = 30,
                                Bitrate = 0,
                                Codec = "H.264",
                                FileSize = 0
                            },
                            AvatarId = request.AvatarId
                        }
                    };

                    return Ok(instantResponse);
                }
                else
                {
                    return BadRequest(new { error = result.Message });
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "立即响应对话失败");
                return StatusCode(500, new { error = "立即响应对话失败", details = ex.Message });
            }
        }

        /// <summary>
        /// 完整语音对话流程：语音输入 → 文本转换 → 立即响应 → 数字人视频
        /// </summary>
        [HttpPost("voice-chat")]
        public async Task<IActionResult> VoiceChat([FromForm] VoiceChatRequest request)
        {
            try
            {
                if (request.AudioFile == null || request.AudioFile.Length == 0)
                {
                    return BadRequest(new { error = "音频文件不能为空" });
                }

                _logger.LogInformation("开始完整语音对话流程");

                // 1. 语音转文本
                var transcriptionResult = await _whisperService.TranscribeAsync(request.AudioFile);
                
                // 2. 立即响应对话
                var chatRequest = new InstantChatRequest
                {
                    Text = transcriptionResult.Text,
                    AvatarId = request.AvatarId,
                    ResponseMode = request.ResponseMode,
                    Quality = request.Quality
                };

                var chatResult = await _realtimeService.ProcessInstantChatAsync(chatRequest);

                return Ok(new
                {
                    success = true,
                    transcription = new
                    {
                        text = transcriptionResult.Text,
                        confidence = transcriptionResult.Confidence,
                        language = transcriptionResult.Language,
                        processingTime = transcriptionResult.ProcessingTime
                    },
                    response = chatResult
                });
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "完整语音对话流程失败");
                return StatusCode(500, new { error = "完整语音对话流程失败", details = ex.Message });
            }
        }

        /// <summary>
        /// 创建自定义数字人头像
        /// </summary>
        [HttpPost("create-avatar")]
        public async Task<IActionResult> CreateAvatar([FromForm] CreateDigitalHumanTemplateRequest request)
        {
            try
            {
                if (request.ImageFile == null || request.ImageFile.Length == 0)
                {
                    return BadRequest(new { error = "头像图片不能为空" });
                }

                if (string.IsNullOrWhiteSpace(request.TemplateName))
                {
                    return BadRequest(new { error = "模板名称不能为空" });
                }

                _logger.LogInformation("开始创建自定义数字人头像: {TemplateName}, 性别: {Gender}", request.TemplateName, request.Gender);

                // 使用模板服务创建数字人
                var templateService = HttpContext.RequestServices.GetRequiredService<IDigitalHumanTemplateService>();
                var result = await templateService.CreateTemplateAsync(request);

                if (result.Success)
                {
                    // 转换为头像响应格式
                    var avatarResponse = new CreateAvatarResponse
                    {
                        Success = true,
                        AvatarId = result.TemplateId,
                        Message = result.Message,
                        ProcessingTime = 0, // 暂时设为0，后续可以从result中解析
                        Avatar = new DigitalHumanAvatar
                        {
                            Id = result.TemplateId,
                            Name = result.Template?.TemplateName ?? request.TemplateName,
                            Description = result.Template?.Description ?? request.Description,
                            PreviewImageUrl = result.Template?.ImagePath ?? "",
                            PreviewVideoUrl = result.Template?.PreviewVideoPath ?? "",
                            Style = result.Template?.Style ?? request.Style,
                            IsCustom = true,
                            CreatedAt = result.Template?.CreatedAt ?? DateTime.Now,
                            Capabilities = new AvatarCapabilities
                            {
                                SupportsEmotion = result.Template?.EnableEmotion ?? true,
                                SupportsLipSync = true,
                                SupportsHeadMovement = true,
                                SupportedLanguages = new List<string> { "zh-CN" },
                                SupportedEmotions = new List<string> { "neutral", "happy", "sad", "angry", "surprised" }
                            }
                        }
                    };

                    _logger.LogInformation("数字人头像创建成功: {AvatarId}, 性别: {Gender}", result.TemplateId, request.Gender);
                    return Ok(avatarResponse);
                }
                else
                {
                    _logger.LogError("数字人头像创建失败: {Message}", result.Message);
                    return BadRequest(new { error = result.Message });
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "创建自定义数字人头像失败");
                return StatusCode(500, new { error = "创建自定义数字人头像失败", details = ex.Message });
            }
        }

        /// <summary>
        /// 获取可用的数字人头像列表
        /// </summary>
        [HttpGet("avatars")]
        public async Task<IActionResult> GetAvatars()
        {
            _logger.LogInformation("开始加载数字人头像列表");

            try
            {
                // 使用模板服务获取模板列表
                var templateService = HttpContext.RequestServices.GetRequiredService<IDigitalHumanTemplateService>();
                var templatesRequest = new GetTemplatesRequest
                {
                    Page = 1,
                    PageSize = 100,
                    SortBy = "created_desc"
                };
                
                var templatesResult = await templateService.GetTemplatesAsync(templatesRequest);
                
                // 转换为头像格式
                var avatars = templatesResult.Templates.Select(template => new DigitalHumanAvatar
                {
                    Id = template.TemplateId,
                    Name = template.TemplateName,
                    Description = template.Description,
                    PreviewImageUrl = template.ImagePath,
                    PreviewVideoUrl = template.PreviewVideoPath,
                    Style = template.Style,
                    IsCustom = true,
                    CreatedAt = template.CreatedAt,
                    Capabilities = new AvatarCapabilities
                    {
                        SupportsEmotion = template.EnableEmotion,
                        SupportsLipSync = true,
                        SupportsHeadMovement = true,
                        SupportedLanguages = new List<string> { "zh-CN" },
                        SupportedEmotions = new List<string> { "neutral", "happy", "sad", "angry", "surprised" }
                    }
                }).ToList();
                
                _logger.LogInformation("成功加载 {Count} 个头像", avatars.Count);
                
                return Ok(new
                {
                    success = true,
                    avatars = avatars
                });
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "加载数字人头像列表失败");
                return Ok(new
                {
                    success = false,
                    avatars = new List<object>(),
                    message = "加载头像列表失败"
                });
            }
        }

        /// <summary>
        /// 获取预渲染视频库状态
        /// </summary>
        [HttpGet("prerendered-status")]
        public async Task<IActionResult> GetPrerenderedStatus()
        {
            try
            {
                var status = await _realtimeService.GetPrerenderedStatusAsync();
                return Ok(new { success = true, status });
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "获取预渲染视频库状态失败");
                return StatusCode(500, new { error = "获取预渲染视频库状态失败", details = ex.Message });
            }
        }

        /// <summary>
        /// 系统健康检查
        /// </summary>
        [HttpGet("health")]
        public async Task<IActionResult> HealthCheck()
        {
            try
            {
                var health = await _realtimeService.GetSystemHealthAsync();
                return Ok(health);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "系统健康检查失败");
                return StatusCode(500, new { error = "系统健康检查失败", details = ex.Message });
            }
        }
    }
}