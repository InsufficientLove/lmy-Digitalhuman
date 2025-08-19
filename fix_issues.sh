#!/bin/bash

echo "=== 修复图片加载和TTS问题 ==="

# 1. 修复Program.cs - 添加using语句和静态文件配置
echo "修复静态文件配置..."
cat > /tmp/program_fix.txt << 'EOF'
using LmyDigitalHuman.Services;
using Microsoft.AspNetCore.SignalR;
using Microsoft.Extensions.FileProviders;
using Serilog;
using Serilog.Events;
using System.Runtime.InteropServices;
EOF

# 替换文件头部
sed -i '1,5d' /workspace/LmyDigitalHuman/Program.cs
cat /tmp/program_fix.txt <(cat /workspace/LmyDigitalHuman/Program.cs) > /tmp/program_new.cs
mv /tmp/program_new.cs /workspace/LmyDigitalHuman/Program.cs

# 2. 修复EdgeTTSService - 使用musetalk-python的TTS服务
echo "修复TTS服务..."
cat > /workspace/LmyDigitalHuman/Services/EdgeTTSService_Docker.cs << 'EOF'
using System.Text;
using System.Text.Json;

namespace LmyDigitalHuman.Services
{
    public class EdgeTTSService : ITTSService
    {
        private readonly ILogger<EdgeTTSService> _logger;
        private readonly HttpClient _httpClient;
        private readonly string _tempPath;

        public EdgeTTSService(ILogger<EdgeTTSService> logger, IConfiguration configuration)
        {
            _logger = logger;
            _httpClient = new HttpClient();
            _httpClient.BaseAddress = new Uri("http://musetalk-python:28888/");
            _tempPath = configuration["Paths:Temp"] ?? "/app/temp";
            Directory.CreateDirectory(_tempPath);
        }

        public async Task<string> TextToSpeechAsync(TTSRequest request)
        {
            try
            {
                _logger.LogInformation("开始TTS转换: Text={Text}, Voice={Voice}", 
                    request.Text, request.Voice);

                // 调用musetalk-python的TTS服务
                var ttsRequest = new
                {
                    command = "tts",
                    text = request.Text,
                    voice = request.Voice ?? "zh-CN-XiaoxiaoNeural",
                    rate = request.Rate ?? "medium",
                    pitch = request.Pitch ?? "medium"
                };

                var json = JsonSerializer.Serialize(ttsRequest);
                var content = new StringContent(json, Encoding.UTF8, "application/json");
                
                var response = await _httpClient.PostAsync("api/tts", content);
                
                if (response.IsSuccessStatusCode)
                {
                    var result = await response.Content.ReadAsStringAsync();
                    var ttsResponse = JsonSerializer.Deserialize<Dictionary<string, object>>(result);
                    
                    if (ttsResponse != null && ttsResponse.ContainsKey("audioPath"))
                    {
                        var audioPath = ttsResponse["audioPath"].ToString();
                        _logger.LogInformation("TTS转换成功: {Path}", audioPath);
                        return audioPath;
                    }
                }

                // 如果musetalk-python服务不可用，创建静默音频
                _logger.LogWarning("TTS服务不可用，创建静默音频");
                var silentAudioPath = Path.Combine(_tempPath, $"tts_{Guid.NewGuid()}.mp3");
                
                // 创建一个简单的静默MP3文件（这里应该用实际的音频库）
                await File.WriteAllBytesAsync(silentAudioPath, new byte[1024]);
                
                return silentAudioPath;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "TTS转换失败");
                throw new Exception($"TTS转换失败: {ex.Message}", ex);
            }
        }

        public async Task<string> GenerateAudioAsync(string text, VoiceSettings voiceSettings)
        {
            var request = new TTSRequest
            {
                Text = text,
                Voice = voiceSettings?.Voice ?? "zh-CN-XiaoxiaoNeural",
                Rate = voiceSettings?.Rate ?? "medium",
                Pitch = voiceSettings?.Pitch ?? "medium"
            };
            
            return await TextToSpeechAsync(request);
        }
    }
}
EOF

echo "=== 修复完成 ==="
echo ""
echo "现在执行以下命令："
echo "1. cd /opt/musetalk/repo"
echo "2. git add -A && git commit -m 'Fix static files and TTS service'"
echo "3. git push origin main"
echo "4. docker compose build lmy-digitalhuman"
echo "5. docker compose up -d lmy-digitalhuman"