# 🚨 快速修复指南

## 问题诊断

你遇到了两个问题：
1. ❌ `python` 命令不存在 → 使用 `python3`
2. ❌ `check_env.py` 文件路径错误 → 文件还在 `MuseTalkEngine/` 目录

---

## 🔧 解决方案（2选1）

### 方案 A：先运行环境检查（推荐）⭐

**优点**：快速看到环境状态，知道缺什么

```bash
# 1. 回到代码根目录
cd /opt/musetalk/repo

# 2. 文件还在 MuseTalkEngine/ 目录下
python3 MuseTalkEngine/check_env.py

# 3. 查看输出，如果有红色错误，按提示修复
```

---

### 方案 B：先重构再检查

```bash
# 1. 回到代码根目录
cd /opt/musetalk/repo

# 2. 运行重构脚本
chmod +x restructure_project.sh
./restructure_project.sh

# 3. 进入新的 Python 目录
cd backend_python

# 4. 运行环境检查
python3 scripts/check_env.py
```

---

## 📋 关于模型路径配置

### 第一步：查看你的模型目录

```bash
# 查看模型根目录
ls -lh /opt/musetalk/models/

# 应该看到类似这样的输出：
# drwxr-xr-x  musetalk/
# drwxr-xr-x  sd-vae-ft-mse/  或  sd-vae/
# drwxr-xr-x  whisper/
# drwxr-xr-x  dwpose/

# 查看具体文件
ls -lh /opt/musetalk/models/musetalk/
# 找到 UNet 模型文件名（可能是 pytorch_model.bin, unet.pth 等）

ls -lh /opt/musetalk/models/whisper/
# 找到 Whisper 模型文件名（可能是 tiny.pt, base.pt, small.pt 等）
```

### 第二步：配置路径

**在重构前**：编辑 `MuseTalkEngine/config_paths.py`

**在重构后**：编辑 `backend_python/config_paths.py`

```bash
# 编辑配置文件
nano MuseTalkEngine/config_paths.py
# 或
nano backend_python/config_paths.py
```

**需要修改的关键行**：

```python
# 1. UNet 模型路径
# 找到这一行，根据实际文件名修改
UNET_PATH = MODEL_ROOT / "musetalk" / "pytorch_model.bin"

# 常见的其他文件名：
# UNET_PATH = MODEL_ROOT / "musetalk" / "unet.pth"
# UNET_PATH = MODEL_ROOT / "musetalk" / "model.safetensors"
# UNET_PATH = MODEL_ROOT / "musetalk" / "diffusion_pytorch_model.bin"

# 2. VAE 目录
# 找到这一行，根据实际目录名修改
VAE_PATH = MODEL_ROOT / "sd-vae-ft-mse"

# 常见的其他目录名：
# VAE_PATH = MODEL_ROOT / "sd-vae"
# VAE_PATH = MODEL_ROOT / "vae"

# 3. Whisper 模型
# 找到这一行，根据实际文件名修改
WHISPER_MODEL = WHISPER_DIR / "tiny.pt"

# 常见的其他文件名：
# WHISPER_MODEL = WHISPER_DIR / "base.pt"
# WHISPER_MODEL = WHISPER_DIR / "small.pt"
# WHISPER_MODEL = WHISPER_DIR / "medium.pt"
# WHISPER_MODEL = WHISPER_DIR / "large-v2.pt"
```

### 第三步：验证配置

```bash
# 重构前
python3 MuseTalkEngine/config_paths.py

# 重构后
cd backend_python
python3 config_paths.py
```

**期望输出**：

```
============================================================
📁 MuseTalk 路径配置
============================================================
模型根目录:  /opt/musetalk/models
代码根目录:  /opt/musetalk/repo

核心模型路径:
  UNet:      /opt/musetalk/models/musetalk/pytorch_model.bin
  VAE:       /opt/musetalk/models/sd-vae-ft-mse
  Whisper:   /opt/musetalk/models/whisper

✅ 所有关键路径验证通过
============================================================
```

---

## 🎯 完整流程（推荐）

```bash
# 1. 回到代码根目录
cd /opt/musetalk/repo

# 2. 查看模型目录（记录实际文件名）
echo "=== 模型目录结构 ==="
ls -lh /opt/musetalk/models/
echo ""
echo "=== UNet 模型文件 ==="
ls -lh /opt/musetalk/models/musetalk/
echo ""
echo "=== VAE 目录 ==="
ls -lh /opt/musetalk/models/ | grep -i vae
echo ""
echo "=== Whisper 文件 ==="
ls -lh /opt/musetalk/models/whisper/

# 3. 根据上面的输出，编辑配置文件
nano MuseTalkEngine/config_paths.py

# 4. 验证配置
python3 MuseTalkEngine/config_paths.py

# 5. 运行环境检查
python3 MuseTalkEngine/check_env.py

# 6. 如果检查通过，运行重构
./restructure_project.sh

# 7. 进入新目录
cd backend_python

# 8. 再次检查（确保重构后一切正常）
python3 scripts/check_env.py

# 9. 启动服务
python3 main_realtime.py
```

---

## 📝 常见模型文件名对照表

### UNet 模型

| 实际文件名 | 配置写法 |
|-----------|---------|
| `pytorch_model.bin` | `UNET_PATH = MODEL_ROOT / "musetalk" / "pytorch_model.bin"` |
| `unet.pth` | `UNET_PATH = MODEL_ROOT / "musetalk" / "unet.pth"` |
| `model.safetensors` | `UNET_PATH = MODEL_ROOT / "musetalk" / "model.safetensors"` |
| `diffusion_pytorch_model.bin` | `UNET_PATH = MODEL_ROOT / "musetalk" / "diffusion_pytorch_model.bin"` |

### VAE 目录

| 实际目录名 | 配置写法 |
|-----------|---------|
| `sd-vae-ft-mse/` | `VAE_PATH = MODEL_ROOT / "sd-vae-ft-mse"` |
| `sd-vae/` | `VAE_PATH = MODEL_ROOT / "sd-vae"` |
| `vae/` | `VAE_PATH = MODEL_ROOT / "vae"` |

### Whisper 模型

| 实际文件名 | 配置写法 | 大小 |
|-----------|---------|-----|
| `tiny.pt` | `WHISPER_MODEL = WHISPER_DIR / "tiny.pt"` | 最小 |
| `base.pt` | `WHISPER_MODEL = WHISPER_DIR / "base.pt"` | 推荐 |
| `small.pt` | `WHISPER_MODEL = WHISPER_DIR / "small.pt"` | 中等 |
| `medium.pt` | `WHISPER_MODEL = WHISPER_DIR / "medium.pt"` | 较大 |
| `large-v2.pt` | `WHISPER_MODEL = WHISPER_DIR / "large-v2.pt"` | 最大 |

---

## 🔍 如果找不到某个模型

### 1. 搜索模型文件

```bash
# 搜索 UNet 模型
find /opt/musetalk/models -name "*unet*" -o -name "*pytorch_model*"

# 搜索 VAE 目录
find /opt/musetalk/models -type d -name "*vae*"

# 搜索 Whisper 文件
find /opt/musetalk/models -name "*.pt"
```

### 2. 检查是否真的缺失

如果确实没有某个模型，需要下载：

```bash
# 示例：下载 Whisper base 模型（如果缺失）
cd /opt/musetalk/models/whisper
wget https://openaipublic.azureedge.net/main/whisper/models/base.pt
```

---

## 💡 小技巧

### 创建 python 软链接（可选）

如果每次输入 `python3` 太麻烦：

```bash
# 检查是否已安装 python-is-python3
python --version

# 如果报错，安装软链接包
sudo apt update
sudo apt install python-is-python3

# 之后就可以直接用 python 了
python scripts/check_env.py
```

---

## 🆘 仍然有问题？

运行这个命令，把输出发给我：

```bash
cd /opt/musetalk/repo

echo "=== 当前目录 ==="
pwd
ls -la

echo ""
echo "=== 模型目录 ==="
ls -lh /opt/musetalk/models/ 2>/dev/null || echo "模型目录不存在"

echo ""
echo "=== UNet 目录 ==="
ls -lh /opt/musetalk/models/musetalk/ 2>/dev/null || echo "UNet目录不存在"

echo ""
echo "=== VAE 目录 ==="
find /opt/musetalk/models -type d -name "*vae*" 2>/dev/null

echo ""
echo "=== Whisper 目录 ==="
ls -lh /opt/musetalk/models/whisper/ 2>/dev/null || echo "Whisper目录不存在"

echo ""
echo "=== Python 版本 ==="
python3 --version
```

把输出内容发给我，我会帮你生成准确的配置！
