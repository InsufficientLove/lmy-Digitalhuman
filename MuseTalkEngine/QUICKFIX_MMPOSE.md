# QuickFix: ModuleNotFoundError: No module named 'mmpose'

## 问题描述

```
ModuleNotFoundError: No module named 'mmpose'
```

这是OpenMMLab依赖缺失导致的。MuseTalkEngine需要以下OpenMMLab包：
- `mmengine`
- `mmcv`
- `mmdet`
- `mmpose`

---

## 快速修复

### 方案1：自动修复脚本（推荐）

运行环境检查和自动修复脚本：

```bash
cd /opt/musetalk/repo/MuseTalkEngine
python3 scripts/check_and_fix_deps.py
```

脚本会：
1. 检查所有依赖状态
2. 自动安装缺失的包
3. 验证修复结果

---

### 方案2：Bash脚本（快速）

```bash
cd /opt/musetalk/repo/MuseTalkEngine
bash scripts/install_mmlab.sh
```

---

### 方案3：手动安装（完全控制）

按顺序执行以下命令：

```bash
# 1. 安装openmim（OpenMMLab包管理器）
pip install -U openmim

# 2. 安装mmengine
mim install mmengine

# 3. 安装mmcv（固定版本2.1.0）
mim install "mmcv==2.1.0"

# 4. 安装mmdet
mim install "mmdet>=3.1.0"

# 5. 安装mmpose
mim install "mmpose>=1.1.0"
```

---

### 方案4：国内加速（使用清华源）

如果在中国网络环境下安装较慢，先配置镜像源：

```bash
# 配置清华源
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 然后执行方案1、2或3
```

---

## 验证安装

安装完成后，验证依赖：

```bash
python3 -c "import mmengine; print('✅ mmengine:', mmengine.__version__)"
python3 -c "import mmcv; print('✅ mmcv:', mmcv.__version__)"
python3 -c "import mmdet; print('✅ mmdet:', mmdet.__version__)"
python3 -c "import mmpose; print('✅ mmpose:', mmpose.__version__)"
```

预期输出：
```
✅ mmengine: 0.10.x
✅ mmcv: 2.x.x
✅ mmdet: 3.x.x
✅ mmpose: 1.x.x
```

---

## Docker用户

如果在Docker环境中，需要重新构建镜像：

```bash
cd /workspace
docker-compose build musetalk
docker-compose up -d musetalk
```

Dockerfile已包含OpenMMLab依赖安装，重新构建会自动安装。

---

## 为什么会缺失？

OpenMMLab依赖在`requirements.txt`中被注释掉（第12-17行），因为：
1. 设计为通过Docker的`openmim`安装（更可靠）
2. 避免pip直接安装导致版本冲突

但如果：
- 在非Docker环境运行
- Docker镜像未重新构建
- 基础镜像缺失依赖

就会出现此错误。

---

## 长期解决方案

为了避免将来出现此问题，建议：

### 选项A：使用Docker（推荐）
```bash
# 重新构建镜像
docker-compose build musetalk

# 所有依赖自动安装
```

### 选项B：首次运行前执行检查脚本
```bash
# 在启动服务前运行
python3 scripts/check_and_fix_deps.py

# 然后启动服务
python3 streaming/api_service.py
```

---

## 故障排除

### 问题1：mmcv版本兼容性错误
```
AssertionError: MMCV==2.2.0 is used but incompatible.
Please install mmcv>=2.0.0rc4, <2.2.0.
```

**原因**：mmcv 2.2.0与mmdet不兼容。

**解决**：
```bash
# 方案A：使用修复脚本
bash scripts/fix_mmcv_version.sh

# 方案B：手动修复
pip uninstall mmcv -y
mim install "mmcv==2.1.0"
mim install "mmdet>=3.1.0"
mim install "mmpose>=1.1.0"
```

### 问题2：mim命令未找到
```bash
# 先安装openmim
pip install -U openmim
```

### 问题3：pip安装超时
```bash
# 使用国内镜像源
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 或使用代理
pip install --proxy=http://proxy.example.com:8080 openmim
```

### 问题4：CUDA版本不匹配
```bash
# 检查CUDA版本
nvidia-smi

# 确保mmcv与CUDA版本匹配
# CUDA 11.8
mim install "mmcv>=2.0.1" -f https://download.openmmlab.com/mmcv/dist/cu118/torch2.1.0/index.html

# CUDA 12.1
mim install "mmcv>=2.0.1" -f https://download.openmmlab.com/mmcv/dist/cu121/torch2.1.0/index.html
```

### 问题5：权限不足
```bash
# 使用sudo（如果在系统级Python）
sudo pip install -U openmim

# 或使用--user（用户级安装）
pip install --user openmim
```

---

## 联系支持

如果以上方法都无法解决，请提供以下信息：

```bash
# 系统信息
uname -a
python3 --version
pip list | grep -E "torch|mmcv|mmpose"

# 错误日志
python3 streaming/api_service.py 2>&1 | tee error.log
```

---

**最后更新**: 2026-01-04  
**状态**: ✅ 已测试
