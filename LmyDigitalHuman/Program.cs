using LmyDigitalHuman.Services;
using Microsoft.AspNetCore.SignalR;
using Microsoft.Extensions.FileProviders;
using Serilog;
using Serilog.Events;
using System.Runtime.InteropServices;

// 配置 Serilog
Log.Logger = new LoggerConfiguration()
    .MinimumLevel.Debug()
    .MinimumLevel.Override("Microsoft", LogEventLevel.Information)
    .MinimumLevel.Override("Microsoft.AspNetCore", LogEventLevel.Warning)
    .Enrich.FromLogContext()
    .WriteTo.Console(outputTemplate: "[{Timestamp:HH:mm:ss} {Level:u3}] {Message:lj}{NewLine}{Exception}")
    .WriteTo.File("logs/app-.log", 
        rollingInterval: RollingInterval.Day,
        outputTemplate: "[{Timestamp:yyyy-MM-dd HH:mm:ss} {Level:u3}] {Message:lj}{NewLine}{Exception}")
    .CreateLogger();

try
{
    Log.Information("Starting LmyDigitalHuman application...");
    
    var builder = WebApplication.CreateBuilder(args);

    // 使用 Serilog
    builder.Host.UseSerilog();

    // 加载环境特定的配置
    var environment = builder.Environment.EnvironmentName;
    if (RuntimeInformation.IsOSPlatform(OSPlatform.Linux))
    {
        builder.Configuration.AddJsonFile("appsettings.Linux.json", optional: true, reloadOnChange: true);
    }
    if (environment == "Docker")
    {
        builder.Configuration.AddJsonFile("appsettings.Docker.json", optional: true, reloadOnChange: true);
    }

    // Add services to the container.
    builder.Services.AddControllers();
    builder.Services.AddEndpointsApiExplorer();
    builder.Services.AddSwaggerGen();

    // 添加 SignalR
    builder.Services.AddSignalR(options =>
    {
        options.EnableDetailedErrors = true;
        options.MaximumReceiveMessageSize = 102400000; // 100MB
    });

    // 添加 CORS
    builder.Services.AddCors(options =>
    {
        options.AddPolicy("AllowAll", policy =>
        {
            policy.AllowAnyOrigin()
                  .AllowAnyMethod()
                  .AllowAnyHeader();
        });
    });

    // 添加 HttpClient
    builder.Services.AddHttpClient();

    // 添加内存缓存
    builder.Services.AddMemoryCache();

    // 注册核心服务
    builder.Services.AddSingleton<IWhisperNetService, WhisperNetService>();
    builder.Services.AddSingleton<IStreamingTTSService, StreamingTTSService>();
    
    // 持久化MuseTalk客户端（与 musetalk-python 通信）
    builder.Services.AddSingleton<PersistentMuseTalkClient>();
    
    // 使用极致优化MuseTalk服务（轻量实现）作为默认 IMuseTalkService
    builder.Services.AddSingleton<IMuseTalkService, OptimizedMuseTalkService>();
    
    // 注册其他服务
    builder.Services.AddSingleton<IEdgeTTSService, EdgeTTSService>();
    builder.Services.AddSingleton<IAudioPipelineService, AudioPipelineService>();
    builder.Services.AddSingleton<IConversationService, ConversationService>();
    builder.Services.AddSingleton<IDigitalHumanTemplateService, DigitalHumanTemplateService>();
    builder.Services.AddSingleton<ILocalLLMService, OllamaService>();
    
    // 注册辅助服务
    builder.Services.AddSingleton<IPathManager, PathManager>();
    builder.Services.AddSingleton<IPythonEnvironmentService, PythonEnvironmentService>();
    builder.Services.AddSingleton<IGPUResourceManager, GPUResourceManager>();
    builder.Services.AddSingleton<GlobalMuseTalkClient>();

    // 配置静态文件目录
    builder.Services.AddDirectoryBrowser();

    var app = builder.Build();

    // Configure the HTTP request pipeline.
    if (app.Environment.IsDevelopment() || environment == "Docker")
    {
        app.UseSwagger();
        app.UseSwaggerUI();
    }

    // 使用 CORS
    app.UseCors("AllowAll");

    // 启用静态文件服务
    app.UseStaticFiles();
    
    // 为templates目录单独配置静态文件服务
    app.UseStaticFiles(new StaticFileOptions
    {
        FileProvider = new PhysicalFileProvider(
            Path.Combine(builder.Environment.ContentRootPath, "wwwroot", "templates")),
        RequestPath = "/templates"
    });
    
    app.UseDirectoryBrowser();

    app.UseRouting();
    app.UseAuthorization();

    app.MapControllers();
    app.MapHub<LmyDigitalHuman.Controllers.ConversationHub>("/conversationHub");

    // 健康检查端点
    app.MapGet("/health", () => Results.Ok(new { status = "healthy", timestamp = DateTime.UtcNow }));

    // 初始化服务
    using (var scope = app.Services.CreateScope())
    {
        var whisperService = scope.ServiceProvider.GetRequiredService<IWhisperNetService>();
        var initTask = whisperService.InitializeAsync();
        initTask.Wait();
        
        Log.Information("Services initialized successfully");
    }

    Log.Information("Application started successfully");
    app.Run();
}
catch (Exception ex)
{
    Log.Fatal(ex, "Application terminated unexpectedly");
}
finally
{
    Log.CloseAndFlush();
}