using LmyDigitalHuman.Services;
using System;
using System.Collections.Generic;
using System.Threading.Tasks;

namespace LmyDigitalHuman.Services
{
    public interface IGPUResourceManager
    {
        Task<GPUInfo> GetGPUInfoAsync();
        Task<bool> CheckGPUAvailabilityAsync();
        Task<int> GetAvailableGPUCountAsync();
        Task<long> GetAvailableGPUMemoryAsync(int gpuIndex = 0);
        Task<double> GetGPUUtilizationAsync(int gpuIndex = 0);
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
}