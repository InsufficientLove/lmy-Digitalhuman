using System;
using System.IO;
using System.Threading.Tasks;
using LmyDigitalHuman.Models;

namespace LmyDigitalHuman.Services
{
    /// <summary>
    /// 实时处理管道服务接口
    /// </summary>
    public interface IRealtimePipelineService
    {
        Task<string> StartRealtimeSessionAsync(string sessionId, RealtimePipelineConfig config);
        Task ProcessAudioStreamAsync(string sessionId, Stream audioStream);
        Task StopRealtimeSessionAsync(string sessionId);
        Task<RealtimePipelineStatus> GetSessionStatusAsync(string sessionId);
        event EventHandler<RealtimeResultEventArgs> OnRealtimeResult;
    }
    
    public class RealtimePipelineConfig
    {
        public string TemplateId { get; set; }
        public string Voice { get; set; }
        public bool EnableWhisper { get; set; }
        public bool EnableMuseTalk { get; set; }
        public int MaxConcurrentTasks { get; set; }
    }
    
    public class RealtimePipelineStatus
    {
        public string SessionId { get; set; }
        public bool IsActive { get; set; }
        public int ProcessedFrames { get; set; }
        public double ProcessingTime { get; set; }
    }
    
    public class RealtimeResultEventArgs : EventArgs
    {
        public string SessionId { get; set; }
        public string Type { get; set; }
        public object Data { get; set; }
    }
}