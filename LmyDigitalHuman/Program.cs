builder.Services.AddSingleton<IWhisperNetService, WhisperNetService>();
builder.Services.AddSingleton<IStreamingTTSService, StreamingTTSService>();
// 持久化MuseTalk客户端（与 musetalk-python 通信）
builder.Services.AddSingleton<PersistentMuseTalkClient>();
// 使用极致优化MuseTalk服务（轻量实现）作为默认 IMuseTalkService
builder.Services.AddSingleton<IMuseTalkService, OptimizedMuseTalkService>();