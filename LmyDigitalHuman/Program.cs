using LmyDigitalHuman.Services;
using Serilog;
using Serilog.Events;
using Microsoft.Extensions.FileProviders;
using Microsoft.AspNetCore.Diagnostics.HealthChecks;

// 设置控制台编码为UTF-8
Console.OutputEncoding = System.Text.Encoding.UTF8;

var builder = WebApplication.CreateBuilder(args);

// 配置Serilog
Log.Logger = new LoggerConfiguration()
    .MinimumLevel.Debug()
    .MinimumLevel.Override("Microsoft", LogEventLevel.Information)
    .Enrich.FromLogContext()
    .WriteTo.File("logs/realtime-digital-human-.log", 
        rollingInterval: RollingInterval.Day,
        outputTemplate: "{Timestamp:yyyy-MM-dd HH:mm:ss.fff zzz} [{Level:u3}] {Message:lj}{NewLine}{Exception}",
        encoding: System.Text.Encoding.UTF8)
    .CreateLogger();

builder.Host.UseSerilog();



// Add services to the container.
builder.Services.AddControllers();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen(c =>
{
    c.SwaggerDoc("v1", new Microsoft.OpenApi.Models.OpenApiInfo 
    { 
        Title = "LmyDigitalHuman", 
        Version = "v1" 
    });
});

// Register services
builder.Services.AddSingleton<IPathManager, PathManager>();  // 路径管理服务 - 必须最先注册
builder.Services.AddSingleton<IWhisperNetService, WhisperNetService>();
builder.Services.AddSingleton<IStreamingTTSService, StreamingTTSService>();
builder.Services.AddSingleton<IMuseTalkService, MuseTalkService>();
builder.Services.AddSingleton<IMuseTalkCommercialService, MuseTalkCommercialService>();
builder.Services.AddSingleton<ILocalLLMService, OllamaService>();
builder.Services.AddSingleton<IDigitalHumanTemplateService, DigitalHumanTemplateService>();
builder.Services.AddSingleton<IEdgeTTSService, EdgeTTSService>();
builder.Services.AddSingleton<IConversationService, ConversationService>();
builder.Services.AddSingleton<IAudioPipelineService, AudioPipelineService>();

// 超低延迟实时服务
builder.Services.AddSingleton<IGPUResourceManager, GPUResourceManager>();
builder.Services.AddSingleton<IRealtimePipelineService, RealtimePipelineService>();

// Add memory caching
builder.Services.AddMemoryCache();

// Add SignalR for real-time communication
builder.Services.AddSignalR();

// Add HttpClient for services
builder.Services.AddHttpClient();



// Add health checks
builder.Services.AddHealthChecks()
    .AddCheck("DigitalHuman", () => 
        Microsoft.Extensions.Diagnostics.HealthChecks.HealthCheckResult.Healthy("数字人服务正常"));

// Configure CORS
builder.Services.AddCors(options =>
{
    options.AddPolicy("AllowAll",
        policy =>
        {
            policy.AllowAnyOrigin()
                  .AllowAnyHeader()
                  .AllowAnyMethod();
        });
});

var app = builder.Build();

// Configure the HTTP request pipeline.
if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}





app.UseCors("AllowAll");

// 确保必要的目录存在
var wwwrootPath = Path.Combine(Directory.GetCurrentDirectory(), "wwwroot");
var videosPath = Path.Combine(wwwrootPath, "videos");
var tempPath = Path.Combine(Directory.GetCurrentDirectory(), "temp");
var templatesPath = Path.Combine(wwwrootPath, "templates");
var imagesPath = Path.Combine(wwwrootPath, "images");

Directory.CreateDirectory(videosPath);
Directory.CreateDirectory(tempPath);
Directory.CreateDirectory(templatesPath);
Directory.CreateDirectory(imagesPath);

// 静态文件服务
app.UseStaticFiles();

// 提供temp目录的静态文件访问（用于音频和临时文件）
app.UseStaticFiles(new StaticFileOptions
{
    FileProvider = new PhysicalFileProvider(tempPath),
    RequestPath = "/temp"
});

app.UseAuthorization();

app.MapControllers();

// Map SignalR Hubs
app.MapHub<LmyDigitalHuman.Controllers.ConversationHub>("/conversationHub");

// 健康检查端点
app.MapHealthChecks("/health", new HealthCheckOptions
{
    ResponseWriter = async (context, report) =>
    {
        context.Response.ContentType = "application/json";
        var result = new
        {
            status = report.Status.ToString(),
            checks = report.Entries.Select(e => new
            {
                name = e.Key,
                status = e.Value.Status.ToString(),
                description = e.Value.Description
            })
        };
        await context.Response.WriteAsync(System.Text.Json.JsonSerializer.Serialize(result));
    }
});

// 默认页面重定向
app.MapGet("/", () => Results.Redirect("/digital-human-test.html"));

// 记录启动信息
app.Logger.LogInformation("🚀 数字人API服务启动成功");
app.Logger.LogInformation("📱 HTTP访问地址: http://localhost:5000");
app.Logger.LogInformation("📊 健康检查: http://localhost:5000/health");
app.Logger.LogInformation("📖 API文档: http://localhost:5000/swagger");



try
{
    app.Run();
}
catch (Exception ex)
{
    Log.Fatal(ex, "应用启动失败");
}
finally
{
    Log.CloseAndFlush();
}
