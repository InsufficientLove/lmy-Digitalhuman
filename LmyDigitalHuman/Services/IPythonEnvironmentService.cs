using System.Collections.Generic;
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
        
        // 完整的方法签名
        Task<PythonEnvironmentInfo> DetectBestPythonEnvironmentAsync();
        Task<bool> ValidatePythonEnvironmentAsync(string pythonPath, params string[] requiredPackages);
        Task<string> GetRecommendedPythonPathAsync();
        Task<List<PythonEnvironmentInfo>> GetAllAvailablePythonEnvironmentsAsync();
    }
    
    public class PythonEnvironmentInfo
    {
        public string PythonPath { get; set; } = "";
        public string Version { get; set; } = "";
        public bool IsVirtualEnv { get; set; }
        public string VirtualEnvPath { get; set; } = "";
        public List<string> InstalledPackages { get; set; } = new();
        public bool IsValid { get; set; }
        public string ErrorMessage { get; set; } = "";
        public int Priority { get; set; } // 优先级，数字越小优先级越高
    }
}