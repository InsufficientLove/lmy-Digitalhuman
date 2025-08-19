using System.Text;

namespace LmyDigitalHuman.Services
{
    /// <summary>
    /// 简化的TTS服务，在Docker环境中使用
    /// </summary>
    public class SimpleTTSService : ITTSService
    {
        private readonly ILogger<SimpleTTSService> _logger;
        private readonly string _tempPath;
        private readonly string _audioPath;

        public SimpleTTSService(ILogger<SimpleTTSService> logger, IConfiguration configuration)
        {
            _logger = logger;
            _tempPath = configuration["Paths:Temp"] ?? "/app/temp";
            _audioPath = configuration["Paths:Audio"] ?? "/app/wwwroot/audio";
            
            Directory.CreateDirectory(_tempPath);
            Directory.CreateDirectory(_audioPath);
        }

        public async Task<string> TextToSpeechAsync(TTSRequest request)
        {
            try
            {
                _logger.LogInformation("SimpleTTS: 生成音频 - {Text}", request.Text);
                
                // 生成音频文件路径
                var fileName = $"tts_{Guid.NewGuid()}.mp3";
                var audioFilePath = Path.Combine(_audioPath, fileName);
                
                // 创建一个最小的有效MP3文件（静默音频）
                // 这是一个有效的MP3帧，包含静默数据
                var mp3Data = GenerateSilentMp3(1.0); // 1秒静默
                
                await File.WriteAllBytesAsync(audioFilePath, mp3Data);
                
                _logger.LogInformation("SimpleTTS: 音频文件已创建 - {Path}", audioFilePath);
                return audioFilePath;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "SimpleTTS: 生成音频失败");
                throw new Exception($"TTS生成失败: {ex.Message}", ex);
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

        /// <summary>
        /// 生成静默MP3数据
        /// </summary>
        private byte[] GenerateSilentMp3(double durationSeconds)
        {
            // 简单的MP3静默帧
            // MPEG-1 Layer 3, 44100Hz, 128kbps, 单声道
            var frameHeader = new byte[] { 0xFF, 0xFB, 0x90, 0x00 };
            
            // 每帧持续时间约26ms (1152采样/44100Hz)
            var framesNeeded = (int)(durationSeconds * 38.46); // 约38.46帧/秒
            
            var mp3Data = new List<byte>();
            
            // ID3v2标签头（可选，但让文件更兼容）
            mp3Data.AddRange(new byte[] { 
                0x49, 0x44, 0x33, 0x04, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00 
            });
            
            // 添加静默帧
            for (int i = 0; i < framesNeeded; i++)
            {
                mp3Data.AddRange(frameHeader);
                // 添加417字节的静默数据（MPEG-1 Layer 3帧大小）
                mp3Data.AddRange(new byte[413]);
            }
            
            return mp3Data.ToArray();
        }
    }
}