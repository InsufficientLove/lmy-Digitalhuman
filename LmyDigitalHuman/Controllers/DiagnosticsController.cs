using Microsoft.AspNetCore.Mvc;
using LmyDigitalHuman.Services;

namespace LmyDigitalHuman.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    public class DiagnosticsController : ControllerBase
    {
        private readonly IPythonEnvironmentService _pythonEnvironmentService;
        private readonly ILogger<DiagnosticsController> _logger;

        public DiagnosticsController(
            IPythonEnvironmentService pythonEnvironmentService,
            ILogger<DiagnosticsController> logger)
        {
            _pythonEnvironmentService = pythonEnvironmentService;
            _logger = logger;
        }

        /// <summary>
        /// 检查Python环境状态
        /// </summary>
        [HttpGet("python-environments")]
        public async Task<IActionResult> GetPythonEnvironments()
        {
            try
            {
                var environments = await _pythonEnvironmentService.GetAllAvailablePythonEnvironmentsAsync();
                var recommended = await _pythonEnvironmentService.GetRecommendedPythonPathAsync();
                
                return Ok(new
                {
                    RecommendedPath = recommended,
                    Environments = environments.Select(env => new
                    {
                        env.PythonPath,
                        env.Version,
                        env.IsVirtualEnv,
                        env.VirtualEnvPath,
                        env.IsValid,
                        env.ErrorMessage,
                        env.Priority,
                        InstalledPackagesCount = env.InstalledPackages.Count,
                        HasEdgeTTS = env.InstalledPackages.Contains("edge-tts"),
                        HasTorch = env.InstalledPackages.Contains("torch")
                    }).ToList()
                });
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "检查Python环境时发生错误");
                return StatusCode(500, new { Error = "检查Python环境失败", Details = ex.Message });
            }
        }

        /// <summary>
        /// 验证特定Python路径
        /// </summary>
        [HttpPost("validate-python")]
        public async Task<IActionResult> ValidatePython([FromBody] ValidatePythonRequest request)
        {
            try
            {
                if (string.IsNullOrEmpty(request.PythonPath))
                {
                    return BadRequest(new { Error = "Python路径不能为空" });
                }

                var isValid = await _pythonEnvironmentService.ValidatePythonEnvironmentAsync(
                    request.PythonPath, 
                    request.RequiredPackages ?? new[] { "edge_tts" });

                return Ok(new
                {
                    PythonPath = request.PythonPath,
                    IsValid = isValid,
                    TestedPackages = request.RequiredPackages ?? new[] { "edge_tts" }
                });
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "验证Python路径时发生错误: {PythonPath}", request.PythonPath);
                return StatusCode(500, new { Error = "验证Python路径失败", Details = ex.Message });
            }
        }

        /// <summary>
        /// 获取系统信息
        /// </summary>
        [HttpGet("system-info")]
        public IActionResult GetSystemInfo()
        {
            try
            {
                var info = new
                {
                    OperatingSystem = Environment.OSVersion.ToString(),
                    MachineName = Environment.MachineName,
                    UserName = Environment.UserName,
                    ProcessorCount = Environment.ProcessorCount,
                    WorkingDirectory = Directory.GetCurrentDirectory(),
                    Framework = System.Runtime.InteropServices.RuntimeInformation.FrameworkDescription,
                    Architecture = System.Runtime.InteropServices.RuntimeInformation.OSArchitecture.ToString(),
                    EnvironmentVariables = new
                    {
                        PYTHONPATH = Environment.GetEnvironmentVariable("PYTHONPATH"),
                        PATH = Environment.GetEnvironmentVariable("PATH")?.Split(';').Take(10).ToArray() // 只显示前10个PATH项
                    }
                };

                return Ok(info);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "获取系统信息时发生错误");
                return StatusCode(500, new { Error = "获取系统信息失败", Details = ex.Message });
            }
        }
    }

    public class ValidatePythonRequest
    {
        public string PythonPath { get; set; } = "";
        public string[]? RequiredPackages { get; set; }
    }
}