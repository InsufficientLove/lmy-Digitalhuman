# 🚀 安装指南（国内服务器优化版）

## 📋 目录
- [环境要求](#环境要求)
- [快速安装](#快速安装)
- [详细步骤](#详细步骤)
- [镜像源配置](#镜像源配置)
- [故障排查](#故障排查)

---

## 环境要求

### 硬件要求
- **GPU**: NVIDIA RTX 4090D x2 (24GB VRAM)
- **CPU**: 8 核心以上
- **内存**: 32GB+
- **磁盘**: 50GB+ SSD（推荐 NVMe）

### 软件要求
- **操作系统**: Ubuntu 22.04 LTS
- **Python**: 3.10+
- **CUDA**: 12.x
- **驱动**: NVIDIA Driver 535+

---

## 快速安装

### 一键安装（推荐）

```bash
# 1. 进入项目目录
cd /opt/musetalk/repo

# 2. 执行安装脚本（自动配置国内镜像）
bash install_dependencies.sh
```

**预计耗时**: 5-10 分钟（使用国内镜像）

**脚本功能**:
- ✅ 自动检测 Python 和 CUDA 环境
- ✅ 配置清华大学镜像源
- ✅ 安装 PyTorch 2.1.2 (CUDA 12.1)
- ✅ 安装所有依赖（锁定版本）
- ✅ 验证安装结果
- ✅ 显示下一步操作

---

## 详细步骤

### 第一步：系统准备

```bash
# 更新系统（可选）
sudo apt update
sudo apt upgrade -y

# 确认 CUDA 版本
nvidia-smi

# 确认 Python 版本
python3 --version  # 应该 >= 3.10
```

### 第二步：配置镜像源

安装脚本会自动配置，也可以手动设置：

```bash
# 创建 pip 配置目录
mkdir -p ~/.pip

# 配置清华镜像（推荐）
cat > ~/.pip/pip.conf << 'EOF'
[global]
index-url = https://pypi.tuna.tsinghua.edu.cn/simple
trusted-host = pypi.tuna.tsinghua.edu.cn

[install]
trusted-host = pypi.tuna.tsinghua.edu.cn
EOF

# 验证配置
cat ~/.pip/pip.conf
```

### 第三步：安装 PyTorch

```bash
# 使用国内镜像安装 PyTorch
python3 -m pip install torch==2.1.2 torchvision==0.16.2 torchaudio==2.1.2 \
    --index-url https://download.pytorch.org/whl/cu121 \
    -i https://pypi.tuna.tsinghua.edu.cn/simple
```

**重要提示**:
- PyTorch 包约 2-3GB，使用国内镜像约 3-5 分钟
- 如使用官方源可能需要 30+ 分钟
- 确保磁盘空间充足

### 第四步：验证 PyTorch

```bash
python3 << 'EOF'
import torch
print(f"PyTorch 版本: {torch.__version__}")
print(f"CUDA 可用: {torch.cuda.is_available()}")
print(f"CUDA 版本: {torch.version.cuda}")
print(f"GPU 数量: {torch.cuda.device_count()}")
for i in range(torch.cuda.device_count()):
    print(f"GPU {i}: {torch.cuda.get_device_name(i)}")
EOF
```

**预期输出**:
```
PyTorch 版本: 2.1.2+cu121
CUDA 可用: True
CUDA 版本: 12.1
GPU 数量: 2
GPU 0: NVIDIA GeForce RTX 4090D
GPU 1: NVIDIA GeForce RTX 4090D
```

### 第五步：安装其他依赖

```bash
cd /opt/musetalk/repo

# 使用锁定版本（推荐，避免冲突）
python3 -m pip install -r MuseTalkEngine/requirements_locked.txt \
    -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 第六步：验证安装

```bash
# 快速检查
bash quick_check.sh

# 完整验证
python3 MuseTalkEngine/check_env.py
```

**预期输出**:
```
========================================
🔍 MuseTalk 环境检查
========================================

✅ Python 3.10.12
✅ CUDA 12.1 (2 GPUs)
✅ NumPy 1.24.3
✅ PyTorch 2.1.2
✅ OpenCV 4.8.1.78
✅ FastAPI 0.104.1
...
✅ 所有检查通过！
```

### 第七步：配置模型路径

```bash
# 自动检测模型
python3 MuseTalkEngine/auto_detect_models.py

# 手动编辑配置（如需要）
vim MuseTalkEngine/config_paths.py
```

### 第八步：启动服务

```bash
cd MuseTalkEngine
bash start_realtime_service.sh
```

**服务启动成功提示**:
```
========================================
🚀 启动 MuseTalk 实时推理服务
========================================

✅ 环境检查通过
✅ 模型路径验证通过
✅ GPU 可用 (2 devices)

INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8080
```

### 第九步：测试 API

```bash
# 健康检查
curl http://localhost:8080/health

# 预期响应
{
  "status": "healthy",
  "gpu_available": true,
  "gpu_count": 2,
  "models_loaded": true
}
```

---

## 镜像源配置

### 国内镜像源列表

| 镜像源 | URL | 速度 | 稳定性 |
|--------|-----|------|--------|
| **清华大学 TUNA** | https://pypi.tuna.tsinghua.edu.cn/simple | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **阿里云** | https://mirrors.aliyun.com/pypi/simple | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **腾讯云** | https://mirrors.cloud.tencent.com/pypi/simple | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **华为云** | https://repo.huaweicloud.com/repository/pypi/simple | ⭐⭐⭐ | ⭐⭐⭐⭐ |

### 切换镜像源

#### 方法 1：修改配置文件（永久生效）

```bash
vim ~/.pip/pip.conf

# 替换为其他镜像源
[global]
index-url = https://mirrors.aliyun.com/pypi/simple
trusted-host = mirrors.aliyun.com
```

#### 方法 2：命令行参数（临时使用）

```bash
# 使用阿里云镜像
pip install numpy -i https://mirrors.aliyun.com/pypi/simple

# 使用腾讯云镜像
pip install numpy -i https://mirrors.cloud.tencent.com/pypi/simple
```

### PyTorch 专用镜像

PyTorch 使用独立的下载地址，也可配置镜像：

```bash
# 官方源（国外快）
--index-url https://download.pytorch.org/whl/cu121

# 清华镜像（国内快）
--index-url https://mirrors.tuna.tsinghua.edu.cn/pytorch/cu121
```

---

## 故障排查

### 问题 1：pip 下载速度慢

**症状**:
```
Downloading... (10kB/s)
```

**解决方案**:
```bash
# 确认镜像配置
cat ~/.pip/pip.conf

# 手动指定镜像
pip install <package> -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 问题 2：PyTorch CUDA 不可用

**症状**:
```python
torch.cuda.is_available()  # False
```

**解决方案**:
```bash
# 1. 确认 CUDA 驱动
nvidia-smi

# 2. 检查 PyTorch 版本
python3 -c "import torch; print(torch.version.cuda)"

# 3. 重新安装正确的 CUDA 版本
pip uninstall torch torchvision torchaudio
pip install torch==2.1.2 torchvision==0.16.2 torchaudio==2.1.2 \
    --index-url https://download.pytorch.org/whl/cu121
```

### 问题 3：依赖冲突

**症状**:
```
ERROR: pip's dependency resolver does not currently take into account...
```

**解决方案**:
```bash
# 使用锁定版本文件
pip install -r MuseTalkEngine/requirements_locked.txt --force-reinstall
```

### 问题 4：磁盘空间不足

**症状**:
```
No space left on device
```

**解决方案**:
```bash
# 清理 pip 缓存
pip cache purge

# 清理系统缓存
sudo apt clean
sudo apt autoremove

# 检查磁盘空间
df -h
```

### 问题 5：权限错误

**症状**:
```
Permission denied: '/usr/local/lib/python3.10'
```

**解决方案**:
```bash
# 使用 --user 标志
pip install <package> --user

# 或使用虚拟环境（推荐）
python3 -m venv venv
source venv/bin/activate
pip install <package>
```

### 问题 6：模型加载失败

**症状**:
```
FileNotFoundError: [Errno 2] No such file or directory: '/opt/musetalk/models/...'
```

**解决方案**:
```bash
# 1. 运行自动检测
python3 MuseTalkEngine/auto_detect_models.py

# 2. 手动验证路径
ls -lh /opt/musetalk/models/

# 3. 检查配置文件
cat MuseTalkEngine/config_paths.py
```

---

## 性能优化建议

### 1. 使用 NVMe SSD
- 模型加载速度提升 3-5 倍
- 推荐挂载 `/opt/musetalk/` 到 NVMe

### 2. 启用 Swap（可选）
```bash
# 创建 16GB swap
sudo fallocate -l 16G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### 3. 调整 GPU 频率
```bash
# 锁定最大频率（需要 root）
sudo nvidia-smi -pm 1
sudo nvidia-smi -lgc 2100
```

### 4. 优化网络（如使用 Docker）
```bash
# 修改 Docker DNS
sudo vim /etc/docker/daemon.json
{
  "dns": ["223.5.5.5", "223.6.6.6"]
}
```

---

## 验证清单

安装完成后，确认以下项目：

- [ ] Python 3.10+ 已安装
- [ ] CUDA 12.x 可用
- [ ] nvidia-smi 显示 2 个 GPU
- [ ] PyTorch 安装成功且 CUDA 可用
- [ ] 所有依赖库安装完成
- [ ] quick_check.sh 通过
- [ ] check_env.py 通过
- [ ] 模型路径配置正确
- [ ] API 服务可以启动
- [ ] /health 端点返回正常

---

## 下一步

✅ 安装完成后，参考：
- [快速入门指南](MuseTalkEngine/QUICKSTART.md)
- [API 使用文档](MuseTalkEngine/README_REALTIME.md)
- [部署检查清单](DEPLOYMENT_CHECKLIST.md)

---

## 获取帮助

- **GitHub Issues**: https://github.com/InsufficientLove/lmy-Digitalhuman/issues
- **文档**: [服务器部署说明.md](服务器部署说明.md)
- **FAQ**: [PROJECT_CLEANUP.md](PROJECT_CLEANUP.md)

---

**祝安装顺利！如有问题，请提交 Issue。** 🚀
