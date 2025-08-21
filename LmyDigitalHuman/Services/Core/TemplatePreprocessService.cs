using LmyDigitalHuman.Services;
using System;
using System.Diagnostics;
using System.IO;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;

namespace LmyDigitalHuman.Services.Core
{
    public interface ITemplatePreprocessService
    {
        Task<bool> PreprocessTemplateAsync(string templateId, string imagePath);
        Task<bool> DeleteTemplateAsync(string templateId);
        Task<bool> VerifyTemplateAsync(string templateId);
    }

    public class TemplatePreprocessService : ITemplatePreprocessService
    {
        private readonly ILogger<TemplatePreprocessService> _logger;
        private readonly IConfiguration _configuration;
        private readonly string _pythonPath;
        private readonly string _scriptPath;
        private readonly string _templatesDir;

        public TemplatePreprocessService(ILogger<TemplatePreprocessService> logger, IConfiguration configuration)
        {
            _logger = logger;
            _configuration = configuration;
            
            // Docker环境路径
            _pythonPath = "python3";
            _scriptPath = "/opt/musetalk/repo/MuseTalkEngine/template_manager.py";
            // 使用统一的缓存目录
            _templatesDir = Environment.GetEnvironmentVariable("MUSE_TEMPLATE_CACHE_DIR") 
                ?? configuration["Paths:TemplateCache"] 
                ?? "/opt/musetalk/template_cache";
        }

        public async Task<bool> PreprocessTemplateAsync(string templateId, string imagePath)
        {
            try
            {
                _logger.LogInformation($"开始预处理模板: {templateId}");
                
                // 确保图片文件存在
                if (!File.Exists(imagePath))
                {
                    _logger.LogError($"图片文件不存在: {imagePath}");
                    return false;
                }

                // 调用Python脚本预处理
                var arguments = $"{_scriptPath} preprocess --template_id {templateId} --image_path {imagePath} --output_dir {_templatesDir}";
                
                var result = await RunPythonScriptAsync(arguments);
                
                if (result)
                {
                    _logger.LogInformation($"模板预处理成功: {templateId}");
                    
                    // 验证缓存文件是否生成
                    var cacheFile = Path.Combine(_templatesDir, templateId, $"{templateId}_preprocessed.pkl");
                    if (File.Exists(cacheFile))
                    {
                        var fileInfo = new FileInfo(cacheFile);
                        _logger.LogInformation($"缓存文件已生成: {cacheFile}, 大小: {fileInfo.Length / 1024 / 1024:F2} MB");
                    }
                }
                else
                {
                    _logger.LogError($"模板预处理失败: {templateId}");
                }
                
                return result;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, $"预处理模板异常: {templateId}");
                return false;
            }
        }

        public async Task<bool> DeleteTemplateAsync(string templateId)
        {
            try
            {
                _logger.LogInformation($"开始删除模板: {templateId}");
                
                // 调用Python脚本删除
                var arguments = $"{_scriptPath} delete --template_id {templateId} --output_dir {_templatesDir}";
                
                var result = await RunPythonScriptAsync(arguments);
                
                if (result)
                {
                    _logger.LogInformation($"模板删除成功: {templateId}");
                    
                    // 同时删除wwwroot中的相关文件
                    var wwwrootTemplateDir = Path.Combine("wwwroot", "templates");
                    var files = new[]
                    {
                        Path.Combine(wwwrootTemplateDir, $"{templateId}.jpg"),
                        Path.Combine(wwwrootTemplateDir, $"{templateId}.png"),
                        Path.Combine(wwwrootTemplateDir, $"{templateId}.json")
                    };
                    
                    foreach (var file in files)
                    {
                        if (File.Exists(file))
                        {
                            File.Delete(file);
                            _logger.LogInformation($"删除文件: {file}");
                        }
                    }
                }
                else
                {
                    _logger.LogError($"模板删除失败: {templateId}");
                }
                
                return result;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, $"删除模板异常: {templateId}");
                return false;
            }
        }

        public async Task<bool> VerifyTemplateAsync(string templateId)
        {
            try
            {
                _logger.LogInformation($"开始验证模板: {templateId}");
                
                // 调用Python脚本验证
                var arguments = $"{_scriptPath} verify --template_id {templateId} --output_dir {_templatesDir}";
                
                var result = await RunPythonScriptAsync(arguments);
                
                if (result)
                {
                    _logger.LogInformation($"模板验证通过: {templateId}");
                }
                else
                {
                    _logger.LogWarning($"模板验证失败: {templateId}");
                }
                
                return result;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, $"验证模板异常: {templateId}");
                return false;
            }
        }

        private async Task<bool> RunPythonScriptAsync(string arguments)
        {
            try
            {
                using var process = new Process
                {
                    StartInfo = new ProcessStartInfo
                    {
                        FileName = _pythonPath,
                        Arguments = arguments,
                        UseShellExecute = false,
                        RedirectStandardOutput = true,
                        RedirectStandardError = true,
                        CreateNoWindow = true
                    }
                };

                process.Start();
                
                // 异步读取输出
                var outputTask = process.StandardOutput.ReadToEndAsync();
                var errorTask = process.StandardError.ReadToEndAsync();
                
                await process.WaitForExitAsync();
                
                var output = await outputTask;
                var error = await errorTask;
                
                if (!string.IsNullOrEmpty(output))
                {
                    _logger.LogInformation($"Python输出: {output}");
                }
                
                if (!string.IsNullOrEmpty(error))
                {
                    _logger.LogError($"Python错误: {error}");
                }
                
                return process.ExitCode == 0;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "运行Python脚本失败");
                return false;
            }
        }
    }
}