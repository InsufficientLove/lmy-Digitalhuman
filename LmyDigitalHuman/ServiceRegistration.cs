using LmyDigitalHuman.Services;
using LmyDigitalHuman.Services.Core;
using LmyDigitalHuman.Services.Offline;
using LmyDigitalHuman.Services.Streaming;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using System.Runtime.InteropServices;

namespace LmyDigitalHuman
{
    /// <summary>
    /// 服务注册扩展类
    /// </summary>
    public static class ServiceRegistration
    {
        /// <summary>
        /// 注册所有应用服务
        /// </summary>
        public static IServiceCollection AddApplicationServices(this IServiceCollection services, IHostEnvironment environment)
        {
            // ========== 核心基础服务 ==========
            services.AddSingleton<IPathManager, PathManager>();
            services.AddSingleton<IGPUResourceManager, GPUResourceManager>();
            
            // Python环境服务（根据环境选择）
            if (environment.EnvironmentName == "Docker")
            {
                services.AddSingleton<IPythonEnvironmentService, DockerPythonEnvironmentService>();
            }
            else
            {
                services.AddSingleton<IPythonEnvironmentService, PythonEnvironmentService>();
            }
            
            // ========== 语音识别和TTS服务 ==========
            services.AddSingleton<IWhisperNetService, WhisperNetService>();
            services.AddSingleton<IEdgeTTSService, EdgeTTSService>();
            services.AddSingleton<ITTSService, EdgeTTSService>(); // EdgeTTS同时实现ITTSService
            services.AddSingleton<IStreamingTTSService, StreamingTTSService>();
            
            // ========== 业务服务 ==========
            services.AddSingleton<IAudioPipelineService, AudioPipelineService>();
            services.AddSingleton<IConversationService, ConversationService>();
            services.AddSingleton<IDigitalHumanTemplateService, DigitalHumanTemplateService>();
            services.AddSingleton<ILocalLLMService, OllamaService>();
            services.AddSingleton<ITemplatePreprocessService, TemplatePreprocessService>();
            services.AddSingleton<IRealtimePipelineService, RealtimePipelineService>();
            
            // ========== MuseTalk服务和客户端 ==========
            services.AddSingleton<IMuseTalkService, OptimizedMuseTalkService>();
            services.AddSingleton<PersistentMuseTalkClient>();
            services.AddSingleton<GlobalMuseTalkClient>();
            
            return services;
        }
        
        /// <summary>
        /// 注册Web相关服务（SignalR、CORS等）
        /// </summary>
        public static IServiceCollection AddWebServices(this IServiceCollection services)
        {
            // 添加控制器
            services.AddControllers();
            services.AddEndpointsApiExplorer();
            services.AddSwaggerGen();
            
            // 添加 SignalR
            services.AddSignalR(options =>
            {
                options.EnableDetailedErrors = true;
                options.MaximumReceiveMessageSize = 102400000; // 100MB
            });
            
            // 添加 CORS
            services.AddCors(options =>
            {
                options.AddPolicy("AllowAll", policy =>
                {
                    policy.AllowAnyOrigin()
                          .AllowAnyMethod()
                          .AllowAnyHeader();
                });
            });
            
            // 添加 HttpClient
            services.AddHttpClient();
            
            // 添加内存缓存
            services.AddMemoryCache();
            
            // 配置静态文件目录
            services.AddDirectoryBrowser();
            
            return services;
        }
    }
}