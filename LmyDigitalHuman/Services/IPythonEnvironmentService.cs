using System.Threading.Tasks;

namespace LmyDigitalHuman.Services
{
    /// <summary>
    /// Python环境管理服务接口
    /// </summary>
    public interface IPythonEnvironmentService
    {
        Task<bool> CheckPythonEnvironmentAsync();
        Task<bool> CheckMuseTalkModelsAsync();
        Task<string> GetPythonVersionAsync();
        Task<bool> CheckGPUAvailabilityAsync();
        Task<string> GetSystemInfoAsync();
        
        // 额外的方法（从DiagnosticsController中发现的）
        Task<object> GetAllAvailablePythonEnvironmentsAsync();
        Task<string> GetRecommendedPythonPathAsync();
        Task<object> ValidatePythonEnvironmentAsync(string pythonPath);
    }
}