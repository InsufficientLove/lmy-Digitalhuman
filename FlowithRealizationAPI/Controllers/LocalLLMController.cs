using Microsoft.AspNetCore.Mvc;
using FlowithRealizationAPI.Services;
using FlowithRealizationAPI.Models;
using System.ComponentModel.DataAnnotations;

namespace FlowithRealizationAPI.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    public class LocalLLMController : ControllerBase
    {
        private readonly ILocalLLMService _llmService;
        private readonly ILogger<LocalLLMController> _logger;

        public LocalLLMController(
            ILocalLLMService llmService,
            ILogger<LocalLLMController> logger)
        {
            _llmService = llmService;
            _logger = logger;
        }

        /// <summary>
        /// 获取可用的本地模型列表
        /// </summary>
        [HttpGet("models")]
        public async Task<IActionResult> GetModels()
        {
            try
            {
                _logger.LogInformation("获取可用模型列表");
                
                var models = await _llmService.GetAvailableModelsAsync();
                
                return Ok(new { success = true, models });
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "获取模型列表失败");
                return StatusCode(500, new { error = "获取模型列表失败", details = ex.Message });
            }
        }

        /// <summary>
        /// 文本对话
        /// </summary>
        [HttpPost("chat")]
        public async Task<IActionResult> Chat([FromBody] LocalLLMRequest request)
        {
            try
            {
                if (string.IsNullOrWhiteSpace(request.Message))
                {
                    return BadRequest(new { error = "消息内容不能为空" });
                }

                _logger.LogInformation("开始LLM对话，模型: {ModelName}, 消息: {Message}", 
                    request.ModelName, request.Message);

                var response = await _llmService.ChatAsync(request);
                
                return Ok(response);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "LLM对话失败");
                return StatusCode(500, new { error = "对话失败", details = ex.Message });
            }
        }

        /// <summary>
        /// 流式对话
        /// </summary>
        [HttpPost("chat/stream")]
        public async Task<IActionResult> ChatStream([FromBody] LocalLLMRequest request)
        {
            try
            {
                if (string.IsNullOrWhiteSpace(request.Message))
                {
                    return BadRequest(new { error = "消息内容不能为空" });
                }

                _logger.LogInformation("开始LLM流式对话，模型: {ModelName}", request.ModelName);

                // 设置流式响应
                Response.Headers["Content-Type"] = "text/event-stream";
                Response.Headers["Cache-Control"] = "no-cache";
                Response.Headers["Connection"] = "keep-alive";
                Response.Headers["Access-Control-Allow-Origin"] = "*";

                await foreach (var chunk in _llmService.ChatStreamAsync(request))
                {
                    var data = System.Text.Json.JsonSerializer.Serialize(chunk);
                    await Response.WriteAsync($"data: {data}\n\n");
                    await Response.Body.FlushAsync();
                }

                return new EmptyResult();
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "LLM流式对话失败");
                return StatusCode(500, new { error = "流式对话失败", details = ex.Message });
            }
        }

        /// <summary>
        /// 获取模型状态
        /// </summary>
        [HttpGet("models/{modelName}/status")]
        public async Task<IActionResult> GetModelStatus(string modelName)
        {
            try
            {
                if (string.IsNullOrWhiteSpace(modelName))
                {
                    return BadRequest(new { error = "模型名称不能为空" });
                }

                _logger.LogInformation("获取模型状态: {ModelName}", modelName);

                var status = await _llmService.GetModelStatusAsync(modelName);
                
                return Ok(new { success = true, status });
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "获取模型状态失败");
                return StatusCode(500, new { error = "获取模型状态失败", details = ex.Message });
            }
        }

        /// <summary>
        /// 加载模型
        /// </summary>
        [HttpPost("models/{modelName}/load")]
        public async Task<IActionResult> LoadModel(string modelName)
        {
            try
            {
                if (string.IsNullOrWhiteSpace(modelName))
                {
                    return BadRequest(new { error = "模型名称不能为空" });
                }

                _logger.LogInformation("加载模型: {ModelName}", modelName);

                var result = await _llmService.LoadModelAsync(modelName);
                
                if (result)
                {
                    return Ok(new { success = true, message = "模型加载成功" });
                }
                else
                {
                    return BadRequest(new { error = "模型加载失败" });
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "加载模型失败");
                return StatusCode(500, new { error = "加载模型失败", details = ex.Message });
            }
        }

        /// <summary>
        /// 卸载模型
        /// </summary>
        [HttpPost("models/{modelName}/unload")]
        public async Task<IActionResult> UnloadModel(string modelName)
        {
            try
            {
                if (string.IsNullOrWhiteSpace(modelName))
                {
                    return BadRequest(new { error = "模型名称不能为空" });
                }

                _logger.LogInformation("卸载模型: {ModelName}", modelName);

                var result = await _llmService.UnloadModelAsync(modelName);
                
                if (result)
                {
                    return Ok(new { success = true, message = "模型卸载成功" });
                }
                else
                {
                    return BadRequest(new { error = "模型卸载失败" });
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "卸载模型失败");
                return StatusCode(500, new { error = "卸载模型失败", details = ex.Message });
            }
        }

        /// <summary>
        /// 获取模型性能统计
        /// </summary>
        [HttpGet("models/{modelName}/performance")]
        public async Task<IActionResult> GetModelPerformance(string modelName)
        {
            try
            {
                if (string.IsNullOrWhiteSpace(modelName))
                {
                    return BadRequest(new { error = "模型名称不能为空" });
                }

                var performance = await _llmService.GetModelPerformanceAsync(modelName);
                
                return Ok(new { success = true, performance });
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "获取模型性能统计失败");
                return StatusCode(500, new { error = "获取性能统计失败", details = ex.Message });
            }
        }

        /// <summary>
        /// 健康检查
        /// </summary>
        [HttpGet("health")]
        public async Task<IActionResult> HealthCheck()
        {
            try
            {
                var isHealthy = await _llmService.HealthCheckAsync();
                
                if (isHealthy)
                {
                    return Ok(new { success = true, status = "healthy", message = "LLM服务正常" });
                }
                else
                {
                    return StatusCode(503, new { success = false, status = "unhealthy", message = "LLM服务不可用" });
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "LLM健康检查失败");
                return StatusCode(500, new { error = "健康检查失败", details = ex.Message });
            }
        }
    }
} 