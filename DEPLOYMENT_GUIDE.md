# 🚀 实时数字人环境部署指南

## 📋 环境要求

### 基础要求
- **操作系统**: Windows 10/11 (64位)
- **Python**: 3.10.11+ ⚠️ **必须升级到 3.10.11+**
- **CUDA**: 12.1+ ⚠️ **必须升级到 CUDA 12.1+**
- **.NET**: 8.0 ✅

### ⚠️ 重要版本要求
- **Python 3.10.11+**: vLLM和最新PyTorch需要
- **CUDA 12.1+**: TensorRT 8.6.1和PyTorch 2.1.0优化版本需要
- **NVIDIA驱动**: 535.0+ (支持CUDA 12.1)

### GPU配置选择

#### 🎮 单GPU配置 (性能阉割版)
- **适用场景**: 开发测试、演示Demo、资源受限
- **硬件要求**: 单张GTX/RTX GPU (8GB+显存)
- **性能预期**: 4-6秒端到端延迟
- **并发支持**: 1-5用户

#### 🚀 4GPU配置 (商用级)
- **适用场景**: 商用服务、高并发、直播带货
- **硬件要求**: 4x RTX4090 (96GB显存)
- **性能预期**: <370ms端到端延迟
- **并发支持**: 50用户同时在线

## 🛠️ 部署步骤

### 步骤1: 环境准备 (必须完成)

#### 🔧 升级到CUDA 12.1 (必需)
1. **卸载当前CUDA 11.8**
   ```bash
   # 控制面板 → 程序和功能 → 卸载CUDA相关程序
   ```

2. **安装CUDA 12.1**
   - 下载地址: https://developer.nvidia.com/cuda-12-1-0-download-archive
   - 选择: Windows → x86_64 → 10/11 → exe (network)

3. **更新NVIDIA驱动**
   - 最低版本: 535.0+
   - 推荐版本: 最新版本

4. **验证安装**
   ```bash
   nvcc --version  # 应显示 release 12.1
   nvidia-smi      # 应显示驱动版本 535.0+
   ```

### 步骤2: 选择部署模式

#### 🎮 单GPU部署 (演示级)
```bash
# 配置单GPU环境
setup-single-gpu.bat

# 启动服务
start-single-gpu.bat

# 访问地址
http://localhost:5000
```

**特点**:
- ✅ 低资源占用 (6-8GB显存)
- ✅ 稳定可靠运行
- ✅ 适合开发测试
- ⚠️ 延迟较高 (4-6秒)

#### 🚀 4GPU部署 (商用级)
```bash
# 配置4GPU商用环境
setup-quad-gpu-commercial.bat

# 启动商用服务
start-commercial.bat

# 性能监控
monitor-performance.bat

# 访问地址
http://localhost:5000
ws://localhost:5000/realtime (WebRTC)
```

**特点**:
- ✅ 超低延迟 (<370ms)
- ✅ 高并发支持 (50用户)
- ✅ WebRTC实时传输
- ✅ 企业级稳定性
- ⚠️ 资源需求高

## 🔧 配置详解

### GPU分配策略 (4GPU模式)

| GPU | 工作负载 | 模型 | 显存占用 | 并发数 |
|-----|---------|------|----------|--------|
| GPU 0 | 视频生成 | MuseTalk | 21.6GB | 4 |
| GPU 1 | LLM推理 | vLLM | 19.2GB | 8 |
| GPU 2 | 音频处理 | EdgeTTS+Whisper | 14.4GB | 12 |
| GPU 3 | 后处理 | TensorRT | 16.8GB | 6 |

### 性能对比表

| 组件 | 单GPU模式 | 4GPU模式 | 提升倍数 |
|------|-----------|----------|----------|
| 语音识别 | ~200ms | ~80ms | 2.5x |
| LLM推理 | ~800ms | ~150ms | 5.3x |
| TTS合成 | ~150ms | ~60ms | 2.5x |
| 视频生成 | ~3-5s | ~80ms | 37.5x |
| **总延迟** | **4-6s** | **370ms** | **16x** |

## 🌐 WebRTC前端集成

### HTML结构
```html
<!DOCTYPE html>
<html>
<head>
    <title>实时数字人</title>
    <script src="/js/webrtc-realtime.js"></script>
</head>
<body>
    <div id="videoContainer">
        <video id="remoteVideo" autoplay></video>
    </div>
    
    <div id="controls"></div>
    <div id="stats"></div>
</body>
</html>
```

### JavaScript集成
```javascript
// 自动检测GPU模式并初始化
const digitalHuman = new DigitalHumanManager();
await digitalHuman.init();

// 开始实时通话
await digitalHuman.startCall();

// 发送消息
digitalHuman.sendMessage("你好，数字人！");
```

## 📊 监控和维护

### 性能监控
```bash
# 实时GPU监控
monitor-performance.bat

# 压力测试
stress-test.bat

# 环境验证 - 在对应虚拟环境中验证
call venv_single\Scripts\activate.bat && python -c "import torch; print(f'PyTorch: {torch.__version__}, CUDA: {torch.cuda.is_available()}')"
call venv_commercial\Scripts\activate.bat && python -c "import torch; print(f'PyTorch: {torch.__version__}, CUDA: {torch.cuda.is_available()}')"
```

### 日志查看
```bash
# .NET应用日志
cd LmyDigitalHuman/logs

# Python环境日志
call venv/Scripts/activate.bat
python -c "import torch; print(torch.cuda.is_available())"
```

## 🔍 故障排除

### 常见问题

#### 1. CUDA版本不匹配
```bash
# 检查CUDA版本
nvcc --version
nvidia-smi

# 重新安装匹配的PyTorch版本
pip install torch==2.1.0 --index-url https://download.pytorch.org/whl/cu121
```

#### 2. 显存不足
```bash
# 检查显存使用
nvidia-smi

# 降低批处理大小
# 编辑 configs/single_gpu/config.yaml
batch_size: 1
resolution: 256
```

#### 3. Edge-TTS网络问题
```bash
# 测试Edge-TTS
test-edge-tts.bat

# 检查网络连接
ping speech.platform.bing.com
```

#### 4. WebRTC连接失败
```javascript
// 检查浏览器支持
console.log('WebRTC支持:', !!window.RTCPeerConnection);

// 检查HTTPS/HTTP
// WebRTC需要HTTPS或localhost
```

### 性能优化建议

#### 单GPU优化
- 降低分辨率: 256x256
- 减少推理步数: 10步
- 使用FP16精度
- 限制并发数: 1-2

#### 4GPU优化
- 启用NVLink连接
- 使用TensorRT加速
- 开启批处理优化
- 监控GPU温度

## 🚀 升级路径

### 从单GPU升级到4GPU
1. 安装额外GPU硬件
2. 运行4GPU配置脚本
3. 切换启动脚本
4. 验证性能提升

### 从CUDA 11.8升级到12.1
1. 备份当前环境
2. 卸载CUDA 11.8
3. 安装CUDA 12.1
4. 重新配置Python环境
5. 验证兼容性

## 📞 技术支持

### 自助诊断
```bash
# 完整环境检查
verify-environment.bat

# GPU状态检查
nvidia-smi

# Python环境检查
python -c "import torch, cv2, edge_tts; print('环境正常')"
```

### 日志收集
```bash
# 收集系统信息
systeminfo > system_info.txt
nvidia-smi > gpu_info.txt
python --version > python_info.txt
```

## 🎯 最佳实践

### 开发环境
- 使用单GPU配置
- 启用详细日志
- 定期备份模型

### 生产环境
- 使用4GPU配置
- 配置监控告警
- 定期性能测试
- 备份和恢复策略

### 安全考虑
- 配置防火墙规则
- 使用HTTPS证书
- 限制API访问
- 定期更新依赖

---

## 📝 快速参考

### 启动命令
```bash
# 单GPU模式
start-single-gpu.bat

# 4GPU商用模式  
start-commercial.bat
```

### 配置文件位置
```
configs/
├── single_gpu/config.yaml      # 单GPU配置
├── commercial/quad_gpu.yaml    # 4GPU配置
└── commercial/realtime.yaml    # WebRTC配置
```

### 访问地址
```
单GPU: http://localhost:5000
4GPU:  http://localhost:5000
WebRTC: ws://localhost:5000/realtime
监控:   http://localhost:5000/monitor
```

选择适合您的配置，开始您的实时数字人之旅！🎉