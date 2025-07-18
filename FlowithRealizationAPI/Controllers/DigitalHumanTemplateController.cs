using Microsoft.AspNetCore.Mvc;
using FlowithRealizationAPI.Services;
using FlowithRealizationAPI.Models;
using System.ComponentModel.DataAnnotations;

namespace FlowithRealizationAPI.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    public class DigitalHumanTemplateController : ControllerBase
    {
        private readonly IDigitalHumanTemplateService _templateService;
        private readonly ILocalLLMService _llmService;
        private readonly ILogger<DigitalHumanTemplateController> _logger;

        public DigitalHumanTemplateController(
            IDigitalHumanTemplateService templateService,
            ILocalLLMService llmService,
            ILogger<DigitalHumanTemplateController> logger)
        {
            _templateService = templateService;
            _llmService = llmService;
            _logger = logger;
        }

        /// <summary>
        /// 创建数字人模板
        /// </summary>
        [HttpPost("create")]
        public async Task<IActionResult> CreateTemplate([FromForm] CreateDigitalHumanTemplateRequest request)
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

                _logger.LogInformation("开始创建数字人模板: {TemplateName}", request.TemplateName);

                var result = await _templateService.CreateTemplateAsync(request);
                
                if (result.Success)
                {
                    return Ok(result);
                }
                else
                {
                    return BadRequest(new { error = result.Message });
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "创建数字人模板失败");
                return StatusCode(500, new { error = "创建数字人模板失败", details = ex.Message });
            }
        }

        /// <summary>
        /// 获取模板列表
        /// </summary>
        [HttpGet("list")]
        public async Task<IActionResult> GetTemplates([FromQuery] GetTemplatesRequest request)
        {
            try
            {
                _logger.LogInformation("获取模板列表，页码: {Page}, 页大小: {PageSize}", request.Page, request.PageSize);

                var result = await _templateService.GetTemplatesAsync(request);
                
                return Ok(result);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "获取模板列表失败");
                return StatusCode(500, new { error = "获取模板列表失败", details = ex.Message });
            }
        }

        /// <summary>
        /// 获取模板详情
        /// </summary>
        [HttpGet("{templateId}")]
        public async Task<IActionResult> GetTemplate(string templateId)
        {
            try
            {
                if (string.IsNullOrWhiteSpace(templateId))
                {
                    return BadRequest(new { error = "模板ID不能为空" });
                }

                _logger.LogInformation("获取模板详情: {TemplateId}", templateId);

                var template = await _templateService.GetTemplateByIdAsync(templateId);
                
                if (template == null)
                {
                    return NotFound(new { error = "模板不存在" });
                }

                return Ok(new { success = true, template });
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "获取模板详情失败");
                return StatusCode(500, new { error = "获取模板详情失败", details = ex.Message });
            }
        }

        /// <summary>
        /// 使用模板生成视频
        /// </summary>
        [HttpPost("generate")]
        public async Task<IActionResult> GenerateWithTemplate([FromBody] GenerateWithTemplateRequest request)
        {
            try
            {
                if (string.IsNullOrWhiteSpace(request.TemplateId))
                {
                    return BadRequest(new { error = "模板ID不能为空" });
                }

                if (string.IsNullOrWhiteSpace(request.Text))
                {
                    return BadRequest(new { error = "生成文本不能为空" });
                }

                _logger.LogInformation("使用模板生成视频: {TemplateId}, 文本: {Text}", request.TemplateId, request.Text);

                var result = await _templateService.GenerateWithTemplateAsync(request);
                
                return Ok(result);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "使用模板生成视频失败");
                return StatusCode(500, new { error = "使用模板生成视频失败", details = ex.Message });
            }
        }

        /// <summary>
        /// 实时对话（非实时性交互）
        /// </summary>
        [HttpPost("chat")]
        public async Task<IActionResult> RealtimeConversation([FromForm] RealtimeConversationRequest request)
        {
            try
            {
                if (string.IsNullOrWhiteSpace(request.TemplateId))
                {
                    return BadRequest(new { error = "模板ID不能为空" });
                }

                if (request.InputType == "text" && string.IsNullOrWhiteSpace(request.Text))
                {
                    return BadRequest(new { error = "文本输入不能为空" });
                }

                if (request.InputType == "audio" && (request.AudioFile == null || request.AudioFile.Length == 0))
                {
                    return BadRequest(new { error = "音频文件不能为空" });
                }

                _logger.LogInformation("实时对话: {TemplateId}, 输入类型: {InputType}", request.TemplateId, request.InputType);

                var result = await _templateService.RealtimeConversationAsync(request);
                
                return Ok(result);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "实时对话失败");
                return StatusCode(500, new { error = "实时对话失败", details = ex.Message });
            }
        }

        /// <summary>
        /// 实时对话（流式响应）
        /// </summary>
        [HttpPost("stream-chat")]
        public async Task<IActionResult> StreamConversation([FromForm] RealtimeConversationRequest request)
        {
            try
            {
                if (string.IsNullOrWhiteSpace(request.TemplateId))
                {
                    return BadRequest(new { error = "模板ID不能为空" });
                }

                _logger.LogInformation("流式对话: {TemplateId}", request.TemplateId);

                // 设置流式响应头
                Response.Headers["Content-Type"] = "text/event-stream";
                Response.Headers["Cache-Control"] = "no-cache";
                Response.Headers["Connection"] = "keep-alive";

                // 这里实现流式响应逻辑
                await Response.WriteAsync("data: {\"status\":\"connected\"}\n\n");
                await Response.Body.FlushAsync();

                // 实际的流式对话实现
                var result = await _templateService.RealtimeConversationAsync(request);
                
                await Response.WriteAsync($"data: {System.Text.Json.JsonSerializer.Serialize(result)}\n\n");
                await Response.Body.FlushAsync();

                await Response.WriteAsync("data: {\"status\":\"completed\"}\n\n");
                await Response.Body.FlushAsync();

                return new EmptyResult();
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "流式对话失败");
                return StatusCode(500, new { error = "流式对话失败", details = ex.Message });
            }
        }

        /// <summary>
        /// 批量预渲染
        /// </summary>
        [HttpPost("batch-prerender")]
        public async Task<IActionResult> BatchPreRender([FromBody] BatchPreRenderRequest request)
        {
            try
            {
                if (string.IsNullOrWhiteSpace(request.TemplateId))
                {
                    return BadRequest(new { error = "模板ID不能为空" });
                }

                if (request.TextList == null || request.TextList.Count == 0)
                {
                    return BadRequest(new { error = "文本列表不能为空" });
                }

                _logger.LogInformation("批量预渲染: {TemplateId}, 文本数量: {Count}", request.TemplateId, request.TextList.Count);

                var result = await _templateService.BatchPreRenderAsync(request);
                
                return Ok(result);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "批量预渲染失败");
                return StatusCode(500, new { error = "批量预渲染失败", details = ex.Message });
            }
        }

        /// <summary>
        /// 获取模板统计信息
        /// </summary>
        [HttpGet("statistics")]
        public async Task<IActionResult> GetStatistics()
        {
            try
            {
                _logger.LogInformation("获取模板统计信息");

                var statistics = await _templateService.GetTemplateStatisticsAsync();
                
                return Ok(new { success = true, statistics });
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "获取模板统计信息失败");
                return StatusCode(500, new { error = "获取模板统计信息失败", details = ex.Message });
            }
        }

        /// <summary>
        /// 删除模板
        /// </summary>
        [HttpDelete("{templateId}")]
        public async Task<IActionResult> DeleteTemplate(string templateId)
        {
            try
            {
                if (string.IsNullOrWhiteSpace(templateId))
                {
                    return BadRequest(new { error = "模板ID不能为空" });
                }

                _logger.LogInformation("删除模板: {TemplateId}", templateId);

                var result = await _templateService.DeleteTemplateAsync(templateId);
                
                if (result)
                {
                    return Ok(new { success = true, message = "模板删除成功" });
                }
                else
                {
                    return NotFound(new { error = "模板不存在" });
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "删除模板失败");
                return StatusCode(500, new { error = "删除模板失败", details = ex.Message });
            }
        }

        /// <summary>
        /// 复制模板
        /// </summary>
        [HttpPost("{templateId}/clone")]
        public async Task<IActionResult> CloneTemplate(string templateId, [FromBody] CloneTemplateRequest request)
        {
            try
            {
                if (string.IsNullOrWhiteSpace(templateId))
                {
                    return BadRequest(new { error = "模板ID不能为空" });
                }

                if (string.IsNullOrWhiteSpace(request.NewName))
                {
                    return BadRequest(new { error = "新模板名称不能为空" });
                }

                _logger.LogInformation("复制模板: {TemplateId} -> {NewName}", templateId, request.NewName);

                var result = await _templateService.CloneTemplateAsync(templateId, request.NewName);
                
                return Ok(result);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "复制模板失败");
                return StatusCode(500, new { error = "复制模板失败", details = ex.Message });
            }
        }

        /// <summary>
        /// 获取模板预览
        /// </summary>
        [HttpGet("{templateId}/preview")]
        public async Task<IActionResult> GetTemplatePreview(string templateId)
        {
            try
            {
                if (string.IsNullOrWhiteSpace(templateId))
                {
                    return BadRequest(new { error = "模板ID不能为空" });
                }

                _logger.LogInformation("获取模板预览: {TemplateId}", templateId);

                var previewPath = await _templateService.GetTemplatePreviewAsync(templateId);
                
                if (string.IsNullOrEmpty(previewPath))
                {
                    return NotFound(new { error = "预览视频不存在" });
                }

                return Ok(new { success = true, previewUrl = previewPath });
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "获取模板预览失败");
                return StatusCode(500, new { error = "获取模板预览失败", details = ex.Message });
            }
        }

        /// <summary>
        /// 获取模板缓存状态
        /// </summary>
        [HttpGet("{templateId}/cache-status")]
        public async Task<IActionResult> GetTemplateCacheStatus(string templateId)
        {
            try
            {
                if (string.IsNullOrWhiteSpace(templateId))
                {
                    return BadRequest(new { error = "模板ID不能为空" });
                }

                var cacheStatus = await _templateService.GetTemplateCacheStatusAsync(templateId);
                
                return Ok(new { success = true, cacheStatus });
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "获取模板缓存状态失败");
                return StatusCode(500, new { error = "获取模板缓存状态失败", details = ex.Message });
            }
        }

        /// <summary>
        /// 清理模板缓存
        /// </summary>
        [HttpPost("{templateId}/clear-cache")]
        public async Task<IActionResult> ClearTemplateCache(string templateId)
        {
            try
            {
                if (string.IsNullOrWhiteSpace(templateId))
                {
                    return BadRequest(new { error = "模板ID不能为空" });
                }

                _logger.LogInformation("清理模板缓存: {TemplateId}", templateId);

                var result = await _templateService.ClearTemplateCacheAsync(templateId);
                
                if (result)
                {
                    return Ok(new { success = true, message = "缓存清理成功" });
                }
                else
                {
                    return BadRequest(new { error = "缓存清理失败" });
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "清理模板缓存失败");
                return StatusCode(500, new { error = "清理模板缓存失败", details = ex.Message });
            }
        }
    }

    /// <summary>
    /// 复制模板请求
    /// </summary>
    public class CloneTemplateRequest
    {
        [Required]
        public string NewName { get; set; } = string.Empty;
    }
} 