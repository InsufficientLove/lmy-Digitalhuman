using FlowithRealizationAPI.Services;
using Serilog;
using Serilog.Events;
using Microsoft.Extensions.FileProviders;
using Microsoft.AspNetCore.Diagnostics.HealthChecks;

var builder = WebApplication.CreateBuilder(args);

// 配置Serilog
Log.Logger = new LoggerConfiguration()
    .MinimumLevel.Debug()
    .MinimumLevel.Override("Microsoft", LogEventLevel.Information)
    .Enrich.FromLogContext()
    .WriteTo.File("logs/realtime-digital-human-.log", 
        rollingInterval: RollingInterval.Day,
        outputTemplate: "{Timestamp:yyyy-MM-dd HH:mm:ss.fff zzz} [{Level:u3}] {Message:lj}{NewLine}{Exception}")
    .CreateLogger();

builder.Host.UseSerilog();

// Add services to the container.
builder.Services.AddControllers();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen(c =>
{
    c.SwaggerDoc("v1", new Microsoft.OpenApi.Models.OpenApiInfo 
    { 
        Title = "FlowithRealizationAPI", 
        Version = "v1" 
    });
});

// Register realtime digital human services
builder.Services.AddSingleton<IRealtimeDigitalHumanService, RealtimeDigitalHumanService>();

// Register Whisper service (Python implementation only)
builder.Services.AddSingleton<IWhisperService, WhisperService>();

// Register local LLM services
builder.Services.AddSingleton<ILocalLLMService, OllamaService>();

// Register digital human template services
builder.Services.AddSingleton<IDigitalHumanTemplateService, DigitalHumanTemplateService>();

// Add HttpClient for services
builder.Services.AddHttpClient();

// Add memory cache
builder.Services.AddMemoryCache();

// Add health checks
builder.Services.AddHealthChecks()
    .AddCheck("RealtimeDigitalHuman", () => 
        Microsoft.Extensions.Diagnostics.HealthChecks.HealthCheckResult.Healthy("实时数字人服务正常"));

// Configure CORS
builder.Services.AddCors(options =>
{
    options.AddPolicy("AllowLocalhost",
        policy =>
        {
            policy.WithOrigins(
                    "http://localhost:3000", 
                    "https://localhost:3000",
                    "http://localhost:5109",
                    "https://localhost:5109",
                    "http://localhost:7135",
                    "https://localhost:7135"
                )
                  .AllowAnyHeader()
                  .AllowAnyMethod()
                  .AllowCredentials();
        });
});

var app = builder.Build();

// Configure the HTTP request pipeline.
if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

app.UseHttpsRedirection();
app.UseCors("AllowLocalhost");

// 静态文件服务
app.UseStaticFiles();

// 提供videos目录的静态文件访问
app.UseStaticFiles(new StaticFileOptions
{
    FileProvider = new PhysicalFileProvider(
        Path.Combine(Directory.GetCurrentDirectory(), "wwwroot", "videos")),
    RequestPath = "/videos"
});

// 提供temp目录的静态文件访问
app.UseStaticFiles(new StaticFileOptions
{
    FileProvider = new PhysicalFileProvider(
        Path.Combine(Directory.GetCurrentDirectory(), "temp")),
    RequestPath = "/temp"
});

// 提供templates目录的静态文件访问
app.UseStaticFiles(new StaticFileOptions
{
    FileProvider = new PhysicalFileProvider(
        Path.Combine(Directory.GetCurrentDirectory(), "wwwroot", "templates")),
    RequestPath = "/templates"
});

app.UseAuthorization();

app.MapControllers();

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
app.MapGet("/", () => Results.Redirect("/realtime-digital-human.html"));

// 记录启动信息
app.Logger.LogInformation("🚀 实时数字人API服务启动成功");
app.Logger.LogInformation("📱 访问地址: https://localhost:7135");
app.Logger.LogInformation("📊 健康检查: https://localhost:7135/health");
app.Logger.LogInformation("📖 API文档: https://localhost:7135/swagger");

// 记录Whisper配置信息
app.Logger.LogInformation("🎤 Whisper提供程序: Python");

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
