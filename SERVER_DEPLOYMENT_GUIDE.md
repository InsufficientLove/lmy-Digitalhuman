# MuseTalk 服务器部署指南

## 📋 概述

本指南帮助你在 **Ubuntu 22.04 + CUDA 12.9** 服务器上部署 MuseTalk 实时推理系统。

**硬件要求**：
- GPU: NVIDIA RTX 4090D (24GB VRAM) x2
- CPU: 16+ 核心
- RAM: 32GB+
- 存储: SSD 500GB+

**服务器环境**：
- OS: Ubuntu 22.04
- CUDA: 12.9
- Python: 3.9+
- 模型路径: `/opt/musetalk/models/`
- 代码路径: `/opt/musetalk/repo/`

---

## 🚀 三步部署流程

### Step 1: 重构项目结构 ⭐

将混乱的 Python 和 C# 文件分离到独立目录。

```bash
# 在服务器上执行
cd /opt/musetalk/repo

# 下载重构脚本
wget https://raw.githubusercontent.com/你的仓库/restructure_project.sh
# 或者从本地上传

# 执行重构
chmod +x restructure_project.sh
./restructure_project.sh
```

**预期结果**：

```
/opt/musetalk/repo/
├── backend_python/       # ✅ Python 后端
│   ├── main_realtime.py
│   ├── preprocess_assets.py
│   ├── config_paths.py   # 路径配置
│   ├── scripts/
│   │   ├── check_env.py  # 环境检查 ⭐⭐⭐
│   │   └── start_realtime_service.sh
│   └── ...
├── backend_dotnet/       # ✅ C# 后端
└── legacy/               # ✅ 遗留代码
```

---

### Step 2: 配置模型路径 ⭐

修改 `config_paths.py` 指向你的模型目录。

```bash
cd /opt/musetalk/repo/backend_python

# 1. 先查看你的模型目录结构
ls -lh /opt/musetalk/models/

# 你应该看到类似这样的结构：
# /opt/musetalk/models/
# ├── musetalk/
# │   ├── pytorch_model.bin
# │   └── musetalk.json
# ├── sd-vae-ft-mse/  (或 sd-vae/)
# ├── whisper/
# │   └── tiny.pt (或 base.pt, small.pt 等)
# └── dwpose/

# 2. 编辑配置文件
nano config_paths.py
```

**关键配置项**（根据实际情况修改）：

```python
# config_paths.py 中的关键部分

# UNet 模型
UNET_PATH = MODEL_ROOT / "musetalk" / "pytorch_model.bin"
# 如果文件名不同，改为：
# UNET_PATH = MODEL_ROOT / "musetalk" / "unet.pth"

# VAE 模型
VAE_PATH = MODEL_ROOT / "sd-vae-ft-mse"
# 如果目录名不同，改为：
# VAE_PATH = MODEL_ROOT / "sd-vae"

# Whisper 模型
WHISPER_MODEL = WHISPER_DIR / "tiny.pt"
# 如果使用更大模型，改为：
# WHISPER_MODEL = WHISPER_DIR / "base.pt"
```

**验证配置**：

```bash
python config_paths.py
```

应该输出：

```
============================================================
📁 MuseTalk 路径配置
============================================================
模型根目录:  /opt/musetalk/models
...
✅ 所有关键路径验证通过
============================================================
```

---

### Step 3: 运行环境检查 ⭐⭐⭐

这是最关键的一步！在启动服务前，先运行自检脚本。

```bash
cd /opt/musetalk/repo/backend_python
python scripts/check_env.py
```

**检查内容**：

1. ✅ Python 版本 (>= 3.9)
2. ✅ 依赖库（torch, fastapi, opencv 等）
3. ✅ CUDA 环境（GPU 可用性、显存）
4. ✅ 模型文件（路径完整性）
5. ✅ MuseTalk 源码（关键模块）
6. ✅ 工作空间（关键文件）

**预期输出**：

```
╔═══════════════════════════════════════════════════════════╗
║        MuseTalk 环境自检脚本                              ║
╚═══════════════════════════════════════════════════════════╝

============================================================
🐍 Python 版本检查
============================================================
当前版本: Python 3.10.12
✅ Python 版本符合要求 (>= 3.9)

============================================================
📦 依赖库检查
============================================================
✅ torch                - PyTorch 深度学习框架
✅ fastapi              - FastAPI Web 框架
...
✅ 所有 20 个依赖库已安装

============================================================
🎮 CUDA 环境检查
============================================================
✅ CUDA 可用
   CUDA 版本: 12.9
   GPU 数量: 2

   GPU 0: NVIDIA GeForce RTX 4090D
   └─ 显存: 24.0 GB
   └─ 状态: 可用
✅ GPU 0 测试通过

   GPU 1: NVIDIA GeForce RTX 4090D
   └─ 显存: 24.0 GB
   └─ 状态: 可用
✅ GPU 1 测试通过

============================================================
📁 模型文件检查
============================================================
✅ 成功导入 config_paths.py
✅ 模型根目录          - /opt/musetalk/models
✅ UNet 模型           - /opt/musetalk/models/musetalk/pytorch_model.bin (1234.5 MB)
✅ VAE 目录            - /opt/musetalk/models/sd-vae-ft-mse (5 个文件)
✅ Whisper 目录        - /opt/musetalk/models/whisper (3 个文件)
✅ 所有 6 个模型路径验证通过

============================================================
📊 检查报告
============================================================
总检查项: 6
通过: 6
失败: 0

✅ 🎉 所有检查通过！环境配置完美！

ℹ️  下一步:
   1. python main_realtime.py
   2. 或使用: ./scripts/start_realtime_service.sh
```

---

## 🔧 常见问题解决

### 问题 1: 依赖库缺失

**症状**：
```
❌ torch                - PyTorch 深度学习框架 [缺失]
```

**解决方案**：
```bash
cd /opt/musetalk/repo/backend_python
pip install -r requirements_realtime.txt
```

---

### 问题 2: CUDA 不可用

**症状**：
```
❌ CUDA 不可用
```

**解决方案**：

1. 检查 NVIDIA 驱动：
```bash
nvidia-smi
```

2. 检查 CUDA Toolkit：
```bash
nvcc --version
```

3. 检查 PyTorch CUDA 版本：
```bash
python -c "import torch; print(torch.version.cuda)"
```

4. 如果 PyTorch 是 CPU 版本，重新安装：
```bash
pip uninstall torch torchvision torchaudio
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

---

### 问题 3: 模型文件不存在

**症状**：
```
❌ UNet 模型           - /opt/musetalk/models/musetalk/pytorch_model.bin [不存在]
```

**解决方案**：

1. 检查实际文件名：
```bash
ls -lh /opt/musetalk/models/musetalk/
```

2. 根据实际文件名修改 `config_paths.py`：
```python
# 如果文件是 unet.pth
UNET_PATH = MODEL_ROOT / "musetalk" / "unet.pth"

# 如果文件是 model.safetensors
UNET_PATH = MODEL_ROOT / "musetalk" / "model.safetensors"
```

3. 重新运行检查：
```bash
python scripts/check_env.py
```

---

### 问题 4: Whisper 模型版本不匹配

**症状**：
```
❌ Whisper 目录        - /opt/musetalk/models/whisper [不存在]
```

**解决方案**：

1. 检查 Whisper 目录：
```bash
ls -lh /opt/musetalk/models/whisper/
```

2. 可能的文件名：
   - `tiny.pt` (最小，最快)
   - `base.pt` (推荐)
   - `small.pt`
   - `medium.pt`
   - `large.pt` (最大，最慢)

3. 修改 `config_paths.py`：
```python
# 使用实际存在的模型
WHISPER_MODEL = WHISPER_DIR / "base.pt"
```

---

## 🎯 启动服务

环境检查全部通过后，启动服务：

```bash
cd /opt/musetalk/repo/backend_python

# 方式 1: 使用启动脚本（推荐）
./scripts/start_realtime_service.sh

# 方式 2: 直接运行
python main_realtime.py

# 方式 3: 后台运行
nohup python main_realtime.py > service.log 2>&1 &
```

---

## 📊 验证服务

```bash
# 1. 健康检查
curl http://localhost:8000/

# 应该返回：
{
  "service": "MuseTalk 实时推理",
  "status": "running",
  "device": "cuda:0",
  "dtype": "torch.float16",
  "loaded_assets": ["idle"],
  "model_paths": {
    "unet": "/opt/musetalk/models/musetalk/pytorch_model.bin",
    "vae": "/opt/musetalk/models/sd-vae-ft-mse",
    "whisper": "/opt/musetalk/models/whisper"
  }
}

# 2. 测试推理
curl -X POST "http://localhost:8000/stream" \
  -F "audio=@test.wav" \
  -F "asset_id=idle" \
  -o output.mjpeg
```

---

## 📝 文件清单

**核心文件** (必须)：
- ✅ `restructure_project.sh` - 重构脚本
- ✅ `config_paths.py` - 路径配置
- ✅ `scripts/check_env.py` - 环境检查 ⭐⭐⭐
- ✅ `main_realtime.py` (或 `main_realtime_patched.py`) - 服务入口

**配置文件**：
- `configs/.env.example` - 环境变量模板
- `requirements_realtime.txt` - Python 依赖

**文档**：
- `README_REALTIME.md` - 完整文档
- `QUICKSTART.md` - 快速开始
- `SERVER_DEPLOYMENT_GUIDE.md` - 本文档

---

## 🔄 更新代码

如果代码有更新：

```bash
cd /opt/musetalk/repo
git pull origin main

# 重新运行环境检查
cd backend_python
python scripts/check_env.py

# 重启服务
pkill -f main_realtime.py
python main_realtime.py
```

---

## 📞 技术支持

### 遇到问题？

1. **先运行环境检查**：`python scripts/check_env.py`
2. **查看日志**：`tail -f service.log`
3. **检查 GPU**：`nvidia-smi`
4. **查看进程**：`ps aux | grep python`

### 调试模式

```bash
# 启用详细日志
export LOG_LEVEL=DEBUG
python main_realtime.py
```

---

## ✅ 部署检查清单

- [ ] 服务器满足硬件要求
- [ ] CUDA 12.9 已安装
- [ ] 模型文件已下载到 `/opt/musetalk/models/`
- [ ] 执行了 `restructure_project.sh`
- [ ] 修改了 `config_paths.py`
- [ ] 运行了 `check_env.py` 并全部通过 ⭐
- [ ] 成功启动了服务
- [ ] 健康检查接口返回正常

---

**部署完成！祝运行顺利！🚀**

如有任何问题，请参考 `README_REALTIME.md` 或运行 `check_env.py` 获取详细诊断。
