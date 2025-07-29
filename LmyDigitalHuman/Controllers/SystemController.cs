using Microsoft.AspNetCore.Mvc;
using System.Diagnostics;

namespace LmyDigitalHuman.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    public class SystemController : ControllerBase
    {
        private readonly ILogger<SystemController> _logger;

        public SystemController(ILogger<SystemController> logger)
        {
            _logger = logger;
        }

        /// <summary>
        /// 获取GPU信息
        /// </summary>
        [HttpGet("gpu-info")]
        public async Task<IActionResult> GetGpuInfo()
        {
            try
            {
                var gpuInfo = await GetGpuInformationAsync();
                return Ok(gpuInfo);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "获取GPU信息失败");
                return Ok(new { count = 1, mode = "single", error = ex.Message });
            }
        }

        /// <summary>
        /// 获取系统状态
        /// </summary>
        [HttpGet("status")]
        public IActionResult GetSystemStatus()
        {
            try
            {
                var status = new
                {
                    timestamp = DateTime.UtcNow,
                    uptime = Environment.TickCount64,
                    memoryUsage = GC.GetTotalMemory(false),
                    processorCount = Environment.ProcessorCount,
                    osVersion = Environment.OSVersion.ToString(),
                    dotnetVersion = Environment.Version.ToString()
                };

                return Ok(status);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "获取系统状态失败");
                return StatusCode(500, new { error = ex.Message });
            }
        }

        private async Task<object> GetGpuInformationAsync()
        {
            try
            {
                // 使用nvidia-smi检查GPU数量
                var processStartInfo = new ProcessStartInfo
                {
                    FileName = "nvidia-smi",
                    Arguments = "--list-gpus",
                    RedirectStandardOutput = true,
                    RedirectStandardError = true,
                    UseShellExecute = false,
                    CreateNoWindow = true
                };

                using var process = Process.Start(processStartInfo);
                if (process == null)
                {
                    return new { count = 1, mode = "single", error = "无法启动nvidia-smi" };
                }

                var output = await process.StandardOutput.ReadToEndAsync();
                var error = await process.StandardError.ReadToEndAsync();
                await process.WaitForExitAsync();

                if (process.ExitCode == 0 && !string.IsNullOrEmpty(output))
                {
                    var gpuLines = output.Split('\n', StringSplitOptions.RemoveEmptyEntries);
                    var gpuCount = gpuLines.Length;

                    // 获取详细GPU信息
                    var detailedInfo = await GetDetailedGpuInfoAsync();

                    return new
                    {
                        count = gpuCount,
                        mode = gpuCount >= 4 ? "quad" : "single",
                        gpus = detailedInfo,
                        raw_output = output.Trim()
                    };
                }
                else
                {
                    _logger.LogWarning("nvidia-smi执行失败: {Error}", error);
                    return new { count = 1, mode = "single", error = "nvidia-smi执行失败" };
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "检查GPU信息时发生异常");
                return new { count = 1, mode = "single", error = ex.Message };
            }
        }

        private async Task<List<object>> GetDetailedGpuInfoAsync()
        {
            try
            {
                var processStartInfo = new ProcessStartInfo
                {
                    FileName = "nvidia-smi",
                    Arguments = "--query-gpu=index,name,memory.total,memory.used,temperature.gpu,power.draw,utilization.gpu --format=csv,noheader,nounits",
                    RedirectStandardOutput = true,
                    UseShellExecute = false,
                    CreateNoWindow = true
                };

                using var process = Process.Start(processStartInfo);
                if (process == null) return new List<object>();

                var output = await process.StandardOutput.ReadToEndAsync();
                await process.WaitForExitAsync();

                if (process.ExitCode != 0) return new List<object>();

                var gpuList = new List<object>();
                var lines = output.Split('\n', StringSplitOptions.RemoveEmptyEntries);

                foreach (var line in lines)
                {
                    var parts = line.Split(',').Select(p => p.Trim()).ToArray();
                    if (parts.Length >= 7)
                    {
                        gpuList.Add(new
                        {
                            index = int.TryParse(parts[0], out var idx) ? idx : 0,
                            name = parts[1],
                            memoryTotal = int.TryParse(parts[2], out var memTotal) ? memTotal : 0,
                            memoryUsed = int.TryParse(parts[3], out var memUsed) ? memUsed : 0,
                            temperature = int.TryParse(parts[4], out var temp) ? temp : 0,
                            powerDraw = float.TryParse(parts[5], out var power) ? power : 0,
                            utilization = int.TryParse(parts[6], out var util) ? util : 0
                        });
                    }
                }

                return gpuList;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "获取详细GPU信息失败");
                return new List<object>();
            }
        }
    }
}