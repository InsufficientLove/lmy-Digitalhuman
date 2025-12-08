# 🚀 快速开始 - MuseTalk 实时推理

## 30秒快速启动

```bash
# 1. 预处理视频
python preprocess_assets.py --video ./data/video/idle.mp4

# 2. 启动服务
./start_realtime_service.sh

# 3. 测试接口
curl http://localhost:8000/
```

---

## 📁 文件说明

| 文件 | 说明 |
|------|------|
| `preprocess_assets.py` | 离线预处理：提取人脸坐标 |
| `main_realtime.py` | 实时推理服务：FastAPI + FP16 |
| `start_realtime_service.sh` | 一键启动脚本 |
| `test_realtime_system.py` | 自动化测试脚本 |
| `requirements_realtime.txt` | Python 依赖 |
| `README_REALTIME.md` | 详细文档 |

---

## 🔧 关键配置

### 环境变量

```bash
# MuseTalk 路径
export MUSE_TALK_DIR=/opt/musetalk/repo/MuseTalk

# 默认视频
export AVATAR_VIDEO_PATH=./data/video/idle.mp4

# 服务端口
export PORT=8000

# 启用 torch.compile (可选)
export USE_TORCH_COMPILE=1
```

### 批处理大小

```python
# RTX 4090D (24GB VRAM)
batch_size = 8   # 平衡模式（推荐）
batch_size = 16  # 高速模式（显存充足时）
batch_size = 4   # 保守模式（显存紧张时）
```

---

## 🎯 API 速查

### 1. 健康检查
```bash
curl http://localhost:8000/
```

### 2. 实时推理（MJPEG流）
```bash
curl -X POST "http://localhost:8000/stream" \
  -F "audio=@input.wav" \
  -F "asset_id=idle" \
  -F "fps=25" \
  -F "batch_size=8" \
  -o output.mjpeg
```

### 3. 加载资产
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

---

## 🐛 故障排查

### 问题 1: 显存不足
```bash
# 降低批处理大小
batch_size=4
```

### 问题 2: 推理慢
```bash
# 启用 torch.compile
export USE_TORCH_COMPILE=1
```

### 问题 3: 服务无法启动
```bash
# 检查依赖
pip install -r requirements_realtime.txt

# 检查 GPU
nvidia-smi
```

---

## 📊 性能监控

```bash
# GPU 监控
watch -n 1 nvidia-smi

# 进程监控
htop

# 服务日志
tail -f /var/log/musetalk_service.log
```

---

## 🔗 集成示例

### Python 客户端
```python
import requests

# 发送音频
with open('input.wav', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/stream',
        files={'audio': f},
        data={'asset_id': 'idle', 'fps': 25}
    )

# 保存视频流
with open('output.mjpeg', 'wb') as out:
    for chunk in response.iter_content(8192):
        out.write(chunk)
```

### JavaScript 客户端
```javascript
// 发送音频
const formData = new FormData();
formData.append('audio', audioBlob, 'input.wav');
formData.append('asset_id', 'idle');
formData.append('fps', 25);

const response = await fetch('http://localhost:8000/stream', {
    method: 'POST',
    body: formData
});

// 显示视频流
const videoUrl = URL.createObjectURL(await response.blob());
videoElement.src = videoUrl;
```

### C# 客户端
```csharp
using var client = new HttpClient();
using var content = new MultipartFormDataContent();

content.Add(new ByteArrayContent(audioData), "audio", "input.wav");
content.Add(new StringContent("idle"), "asset_id");
content.Add(new StringContent("25"), "fps");

var response = await client.PostAsync(
    "http://localhost:8000/stream", 
    content
);

var stream = await response.Content.ReadAsStreamAsync();
```

---

## 📚 更多资源

- 详细文档：[README_REALTIME.md](./README_REALTIME.md)
- 测试脚本：`python test_realtime_system.py`
- 启动脚本：`./start_realtime_service.sh`

---

**硬件要求**：2x NVIDIA RTX 4090D (24GB VRAM)  
**软件要求**：Python 3.9+, PyTorch 2.0+, CUDA 11.8+

---

**祝使用愉快！🎉**
