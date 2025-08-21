using LmyDigitalHuman.Services;
using System.Threading.Tasks;

namespace LmyDigitalHuman.Services
{
    public interface IPythonEnvironmentService
    {
        Task<bool> CheckPythonEnvironmentAsync();
        Task<bool> CheckMuseTalkModelsAsync();
        Task<string> GetPythonVersionAsync();
        Task<bool> CheckGPUAvailabilityAsync();
        Task<string> GetSystemInfoAsync();
    }
}