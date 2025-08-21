using System.Collections.Generic;
using System.Threading.Tasks;

namespace LmyDigitalHuman.Services
{
    /// <summary>
    /// GPU资源管理服务接口
    /// </summary>
    public interface IGPUResourceManager
    {
        Task<GPUInfo> GetGPUInfoAsync();
        Task<bool> CheckGPUAvailabilityAsync();
        Task<int> GetAvailableGPUCountAsync();
        Task<long> GetAvailableGPUMemoryAsync(int gpuIndex = 0);
        Task<double> GetGPUUtilizationAsync(int gpuIndex = 0);
        
        // 额外的方法（从RealtimePipelineService中发现的）
        Task<int> AllocateGPUAsync(int preferredGpu, GPUWorkloadType workloadType);
        Task ReleaseGPUAsync(int gpuId, GPUWorkloadType workloadType);
    }

    public class GPUInfo
    {
        public int Count { get; set; }
        public List<GPUDevice> Devices { get; set; } = new List<GPUDevice>();
    }

    public class GPUDevice
    {
        public int Index { get; set; }
        public string Name { get; set; }
        public long TotalMemory { get; set; }
        public long UsedMemory { get; set; }
        public long FreeMemory { get; set; }
        public double Utilization { get; set; }
    }
    
    public enum GPUWorkloadType
    {
        Whisper,
        MuseTalk,
        General
    }
}