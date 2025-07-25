using Microsoft.AspNetCore.Mvc;
using LmyDigitalHuman.Services;
using LmyDigitalHuman.Models;

namespace LmyDigitalHuman.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    public class WhisperTestController : ControllerBase
    {
        private readonly IWhisperService _whisperService;
        private readonly ILogger<WhisperTestController> _logger;

        public WhisperTestController(
            IWhisperService whisperService,
            ILogger<WhisperTestController> logger)
        {
            _whisperService = whisperService;
            _logger = logger;
        }

        /// <summary>
        /// 测试Whisper服务状态
        /// </summary>
        [HttpGet("health")]
        public async Task<IActionResult> HealthCheck()
        {
            try
            {
                var isHealthy = await _whisperService.IsServiceHealthyAsync();
                var supportedFormats = await _whisperService.GetSupportedFormatsAsync();
                var availableModels = await _whisperService.GetAvailableModelsAsync();

                return Ok(new
                {
                    success = true,
                    isHealthy = isHealthy,
                    supportedFormats = supportedFormats,
                    availableModels = availableModels,
                    timestamp = DateTime.Now
                });
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Whisper健康检查失败");
                return StatusCode(500, new { error = "Whisper健康检查失败", details = ex.Message });
            }
        }

        /// <summary>
        /// 测试语音转文本功能
        /// </summary>
        [HttpPost("transcribe")]
        public async Task<IActionResult> Transcribe([FromForm] IFormFile audioFile)
        {
            try
            {
                if (audioFile == null || audioFile.Length == 0)
                {
                    return BadRequest(new { error = "音频文件不能为空" });
                }

                _logger.LogInformation("开始Whisper测试转录，文件: {FileName}, 大小: {Size} bytes", 
                    audioFile.FileName, audioFile.Length);

                var stopwatch = System.Diagnostics.Stopwatch.StartNew();
                var result = await _whisperService.TranscribeAsync(audioFile);
                stopwatch.Stop();

                return Ok(new
                {
                    success = true,
                    transcription = new
                    {
                        text = result.Text,
                        confidence = result.Confidence,
                        language = result.Language,
                        processingTime = result.ProcessingTime,
                        totalTime = stopwatch.ElapsedMilliseconds
                    },
                    fileInfo = new
                    {
                        fileName = audioFile.FileName,
                        fileSize = audioFile.Length,
                        contentType = audioFile.ContentType
                    },
                    timestamp = DateTime.Now
                });
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Whisper测试转录失败");
                return StatusCode(500, new { error = "Whisper测试转录失败", details = ex.Message });
            }
        }

        /// <summary>
        /// 批量测试语音转文本功能
        /// </summary>
        [HttpPost("transcribe-batch")]
        public async Task<IActionResult> TranscribeBatch([FromForm] List<IFormFile> audioFiles)
        {
            try
            {
                if (audioFiles == null || audioFiles.Count == 0)
                {
                    return BadRequest(new { error = "音频文件列表不能为空" });
                }

                _logger.LogInformation("开始Whisper批量测试转录，文件数量: {Count}", audioFiles.Count);

                var stopwatch = System.Diagnostics.Stopwatch.StartNew();
                var results = await _whisperService.TranscribeBatchAsync(audioFiles);
                stopwatch.Stop();

                var successCount = results.Count(r => !string.IsNullOrEmpty(r.Text));
                var failureCount = results.Count - successCount;

                return Ok(new
                {
                    success = true,
                    summary = new
                    {
                        totalFiles = audioFiles.Count,
                        successCount = successCount,
                        failureCount = failureCount,
                        successRate = (double)successCount / audioFiles.Count * 100,
                        totalTime = stopwatch.ElapsedMilliseconds
                    },
                    results = results.Select((result, index) => new
                    {
                        fileIndex = index,
                        fileName = audioFiles[index].FileName,
                        transcription = new
                        {
                            text = result.Text,
                            confidence = result.Confidence,
                            language = result.Language,
                            processingTime = result.ProcessingTime
                        }
                    }).ToList(),
                    timestamp = DateTime.Now
                });
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Whisper批量测试转录失败");
                return StatusCode(500, new { error = "Whisper批量测试转录失败", details = ex.Message });
            }
        }

        /// <summary>
        /// 获取系统环境信息
        /// </summary>
        [HttpGet("environment")]
        public IActionResult GetEnvironmentInfo()
        {
            try
            {
                var environmentInfo = new
                {
                    os = Environment.OSVersion.ToString(),
                    platform = Environment.OSVersion.Platform.ToString(),
                    machineName = Environment.MachineName,
                    processorCount = Environment.ProcessorCount,
                    workingSet = Environment.WorkingSet,
                    currentDirectory = Environment.CurrentDirectory,
                    pythonPath = GetPythonPath(),
                    whisperPath = GetWhisperPath(),
                    timestamp = DateTime.Now
                };

                return Ok(new { success = true, environment = environmentInfo });
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "获取环境信息失败");
                return StatusCode(500, new { error = "获取环境信息失败", details = ex.Message });
            }
        }

        private string GetPythonPath()
        {
            try
            {
                var process = new System.Diagnostics.Process
                {
                    StartInfo = new System.Diagnostics.ProcessStartInfo
                    {
                        FileName = "where",
                        Arguments = "python",
                        RedirectStandardOutput = true,
                        UseShellExecute = false,
                        CreateNoWindow = true
                    }
                };
                process.Start();
                var output = process.StandardOutput.ReadToEnd();
                process.WaitForExit();
                return output.Trim();
            }
            catch
            {
                return "未找到";
            }
        }

        private string GetWhisperPath()
        {
            try
            {
                var process = new System.Diagnostics.Process
                {
                    StartInfo = new System.Diagnostics.ProcessStartInfo
                    {
                        FileName = "where",
                        Arguments = "whisper",
                        RedirectStandardOutput = true,
                        UseShellExecute = false,
                        CreateNoWindow = true
                    }
                };
                process.Start();
                var output = process.StandardOutput.ReadToEnd();
                process.WaitForExit();
                return output.Trim();
            }
            catch
            {
                return "未找到";
            }
        }
    }
} 