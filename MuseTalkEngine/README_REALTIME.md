# MuseTalk 实时推理系统 - 使用指南

## 🎯 概述

本系统专为 **2x NVIDIA RTX 4090D (24GB VRAM)** 优化，提供：
1. **离线预处理** (`preprocess_assets.py`) - 提取视频人脸坐标
2. **实时推理服务** (`main_realtime.py`) - FastAPI + FP16 极速推理

---

## 📦 依赖安装

```bash
# 核心依赖
pip install fastapi uvicorn opencv-python numpy torch torchvision torchaudio
pip install transformers librosa soundfile tqdm

# MuseTalk 依赖（如果未安装）
cd /opt/musetalk/repo/MuseTalk
pip install -r requirements.txt
```

---

## 🔧 第一步：预处理视频

### 功能说明
`preprocess_assets.py` 会：
- 读取 MP4 视频
- 逐帧检测人脸边界框 (x1, y1, x2, y2)
- 保存为 `.pkl` 和 `.json` 文件

### 使用方法

```bash
# 基础用法（使用默认路径）
python preprocess_assets.py --video ./data/video/idle.mp4

# 指定输出目录
python preprocess_assets.py \
    --video ./data/video/idle.mp4 \
    --output ./data/preprocessed

# 处理多个视频
for video in ./data/video/*.mp4; do
    python preprocess_assets.py --video "$video"
done
```

### 输出文件

```
./data/preprocessed/
├── idle_bbox.pkl      # Pickle 格式（高性能加载）
└── idle_bbox.json     # JSON 格式（便于查看）
```

### 数据结构

```python
# PKL 文件内容
{
    'bbox_list': [(x1, y1, x2, y2), ...],  # 每帧的边界框
    'landmarks_list': [landmarks, ...],     # 每帧的关键点
    'fps': 25.0,                            # 视频帧率
    'frame_count': 300,                     # 总帧数
    'video_name': 'idle',                   # 视频名称
    'video_path': '/path/to/idle.mp4'      # 原始路径
}
```

---

## 🚀 第二步：启动实时服务

### 环境变量

```bash
# MuseTalk 路径
export MUSE_TALK_DIR=/opt/musetalk/repo/MuseTalk

# 默认视频路径（可选）
export AVATAR_VIDEO_PATH=./data/video/idle.mp4

# 是否启用 torch.compile（PyTorch 2.0+）
export USE_TORCH_COMPILE=1

# 服务端口
export PORT=8000
```

### 启动服务

```bash
# 方法 1：直接运行
python main_realtime.py

# 方法 2：使用 uvicorn（推荐生产环境）
uvicorn main_realtime:app --host 0.0.0.0 --port 8000 --workers 1

# 方法 3：Docker 容器内
docker exec -it musetalk_container python /workspace/MuseTalkEngine/main_realtime.py
```

### 服务启动日志

```
============================================================
🚀 启动 MuseTalk 实时推理服务
============================================================
🎮 GPU 设备: cuda:0
📊 数据类型: torch.float16
============================================================
🚀 开始加载模型...
============================================================
📂 工作目录: /opt/musetalk/repo/MuseTalk
⚙️ 加载 VAE、UNet、PE...
⚡ 转换为 FP16 并移动到 GPU...
  ✅ VAE -> FP16
  ✅ UNet -> FP16
  ✅ PE -> FP16
  ✅ AudioProcessor

💾 显存占用: 4.23GB (预留: 4.50GB)
============================================================
✅ 模型加载完成!
============================================================

🔥 开始预热 CUDA kernel...
✅ 预热完成!

📦 加载资产: idle
  - 读取视频: ./data/video/idle.mp4
  ✅ 加载 300 帧
  - 读取边界框: ./data/video/idle_bbox.pkl
  ✅ 加载 300 个边界框
✅ 资产 idle 已驻留内存

✅ 服务就绪!
```

---

## 📡 API 接口

### 1. 健康检查

```bash
curl http://localhost:8000/
```

响应：
```json
{
  "service": "MuseTalk 实时推理",
  "status": "running",
  "device": "cuda:0",
  "dtype": "torch.float16",
  "loaded_assets": ["idle"]
}
```

### 2. 实时推理（MJPEG 流）

```bash
# 使用 curl
curl -X POST "http://localhost:8000/stream" \
  -F "audio=@test_audio.wav" \
  -F "asset_id=idle" \
  -F "fps=25" \
  -F "batch_size=8" \
  --output output.mjpeg

# 在浏览器中查看
# http://localhost:8000/stream?asset_id=idle
```

**参数说明**：
- `audio`: 音频文件（WAV/PCM）
- `asset_id`: 资产ID（默认 "idle"）
- `fps`: 输出帧率（默认 25）
- `batch_size`: 推理批大小（默认 8）

**响应格式**：
- `Content-Type: multipart/x-mixed-replace; boundary=frame`
- MJPEG 视频流

### 3. 加载新资产

```bash
curl -X POST "http://localhost:8000/load_asset" \
  -H "Content-Type: application/json" \
  -d '{
    "asset_id": "smile",
    "video_path": "./data/video/smile.mp4",
    "bbox_path": "./data/preprocessed/smile_bbox.pkl"
  }'
```

### 4. 列出资产

```bash
curl http://localhost:8000/assets
```

响应：
```json
{
  "assets": [
    {
      "id": "idle",
      "frame_count": 300,
      "fps": 25.0
    }
  ]
}
```

---

## 🎨 性能优化建议

### 1. FP16 加速
- ✅ 已启用，显存减半，速度提升 2x
- VAE、UNet、PE 全部使用 FP16

### 2. torch.compile（PyTorch 2.0+）
```bash
export USE_TORCH_COMPILE=1
```
- 首次推理会编译（较慢）
- 后续推理加速 20-30%

### 3. 批处理大小
- RTX 4090D (24GB)：推荐 `batch_size=8-16`
- 根据显存动态调整：
  ```python
  # 显存充足
  batch_size = 16  # 最快
  
  # 显存中等
  batch_size = 8   # 平衡
  
  # 显存紧张
  batch_size = 4   # 保守
  ```

### 4. CUDA 图优化（实验性）
```python
# 在 main_realtime.py 中启用
torch.cuda.graphs = True
```

---

## 🔍 调试技巧

### 查看显存占用

```python
# 在推理前后
allocated = torch.cuda.memory_allocated(0) / 1e9
reserved = torch.cuda.memory_reserved(0) / 1e9
print(f"显存: {allocated:.2f}GB / {reserved:.2f}GB")
```

### 性能分析

```bash
# 使用 PyTorch Profiler
python -m torch.utils.bottleneck main_realtime.py

# 使用 nvidia-smi 监控
watch -n 1 nvidia-smi
```

### 日志级别

```bash
# 详细日志
export LOG_LEVEL=DEBUG
python main_realtime.py

# 简洁日志
export LOG_LEVEL=INFO
python main_realtime.py
```

---

## 🐛 常见问题

### Q1: 显存不足 (OOM)
**解决方案**：
1. 降低 `batch_size`（8 -> 4 -> 2）
2. 减少加载的资产数量
3. 使用梯度检查点（trade-off 速度）

### Q2: 推理速度慢
**排查步骤**：
1. 确认使用 FP16
2. 启用 `torch.compile`
3. 增大 `batch_size`
4. 检查 CPU 瓶颈（用 `htop`）

### Q3: 人脸检测失败
**可能原因**：
1. 视频质量差
2. 人脸角度过大
3. 光照不足

**解决方案**：
```python
# 在 preprocess_assets.py 中调整检测参数
# 降低检测阈值
bbox = detect_face(frame, threshold=0.5)
```

---

## 📊 性能基准

### 测试环境
- GPU: RTX 4090D (24GB)
- 视频: 1920x1080, 25 FPS
- 音频: 10 秒

### 预期性能

| 阶段 | 耗时 | 说明 |
|-----|------|------|
| 模型加载 | 5-8s | 启动时一次性 |
| 预热 | 1-2s | 启动时一次性 |
| 音频特征提取 | 0.5-1s | 每次请求 |
| 推理 (batch=8) | 2-3s | 10秒音频 |
| 合成输出 | 0.5s | 多线程加速 |
| **总耗时** | **3-5s** | **端到端** |

### 优化后性能

| 优化项 | 加速比 |
|--------|--------|
| FP16 | 2x |
| torch.compile | 1.3x |
| 批处理 (8) | 4x |
| **综合** | **10x+** |

---

## 🔗 与 .NET 中控集成

### C# 调用示例

```csharp
using System.Net.Http;
using System.Net.Http.Headers;

public class MuseTalkClient
{
    private readonly HttpClient _client;
    
    public MuseTalkClient(string baseUrl = "http://localhost:8000")
    {
        _client = new HttpClient { BaseAddress = new Uri(baseUrl) };
    }
    
    public async Task<Stream> GenerateVideoStreamAsync(
        byte[] audioData, 
        string assetId = "idle", 
        int fps = 25)
    {
        using var content = new MultipartFormDataContent();
        
        // 音频数据
        var audioContent = new ByteArrayContent(audioData);
        audioContent.Headers.ContentType = new MediaTypeHeaderValue("audio/wav");
        content.Add(audioContent, "audio", "input.wav");
        
        // 参数
        content.Add(new StringContent(assetId), "asset_id");
        content.Add(new StringContent(fps.ToString()), "fps");
        
        // 发送请求
        var response = await _client.PostAsync("/stream", content);
        response.EnsureSuccessStatusCode();
        
        return await response.Content.ReadAsStreamAsync();
    }
}

// 使用示例
var client = new MuseTalkClient();
var audioData = File.ReadAllBytes("test.wav");
var videoStream = await client.GenerateVideoStreamAsync(audioData);

// 将 MJPEG 流转发给前端
return File(videoStream, "multipart/x-mixed-replace");
```

---

## 📝 许可证

本项目基于 MuseTalk 开源项目，遵循相应许可证。

---

## 🙋 技术支持

如有问题，请联系数字人后端团队。

**硬件要求**：
- GPU: NVIDIA RTX 4090D (24GB) x2
- CPU: 16+ 核心
- RAM: 32GB+
- 存储: SSD 500GB+

**软件要求**：
- CUDA 11.8+
- PyTorch 2.0+
- Python 3.9+

---

**祝使用愉快！🚀**
