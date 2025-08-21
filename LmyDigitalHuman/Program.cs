using Microsoft.AspNetCore.SignalR;
using Microsoft.Extensions.FileProviders;
using Serilog;
using Serilog.Events;
using System.Runtime.InteropServices;
using LmyDigitalHuman; // 使用ServiceRegistration扩展方法

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

    // 加载Docker环境配置
    var environment = builder.Environment.EnvironmentName;
    if (environment == "Docker")
    {
        builder.Configuration.AddJsonFile("appsettings.Docker.json", optional: false, reloadOnChange: true);
    }

    // 注册所有服务（使用扩展方法）
    builder.Services.AddWebServices();
    builder.Services.AddApplicationServices(builder.Environment);

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
    
    // 确保必要的目录存在
    var wwwrootPath = Path.Combine(builder.Environment.ContentRootPath, "wwwroot");
    var templatesPath = Path.Combine(wwwrootPath, "templates");
    var videosPath = Path.Combine(wwwrootPath, "videos");
    var audioPath = Path.Combine(wwwrootPath, "audio");
    
    // 创建所有必要的目录
    foreach (var path in new[] { wwwrootPath, templatesPath, videosPath, audioPath })
    {
        if (!Directory.Exists(path))
        {
            Directory.CreateDirectory(path);
            Log.Information("Created directory: {Path}", path);
        }
    }
    
    // 为templates目录单独配置静态文件服务
    app.UseStaticFiles(new StaticFileOptions
    {
        FileProvider = new PhysicalFileProvider(templatesPath),
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
        var whisperService = scope.ServiceProvider.GetRequiredService<LmyDigitalHuman.Services.IWhisperNetService>();
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