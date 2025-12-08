# 🚀 MuseTalk 服务器部署清单

## 📋 执行顺序

### ⭐ Step 1: 重构项目结构
```bash
cd /opt/musetalk/repo
./restructure_project.sh
```

**验证**：
```bash
ls -la backend_python/
ls -la backend_dotnet/
```

---

### ⭐ Step 2: 配置模型路径
```bash
cd backend_python

# 查看实际模型目录
ls -lh /opt/musetalk/models/

# 编辑配置
nano config_paths.py

# 验证配置
python config_paths.py
```

---

### ⭐⭐⭐ Step 3: 运行环境检查（最关键！）
```bash
python scripts/check_env.py
```

**期望结果**：
- ✅ Python 版本: >= 3.9
- ✅ 依赖库: 全部安装
- ✅ CUDA: 可用
- ✅ GPU: 2x RTX 4090D
- ✅ 模型文件: 全部存在
- ✅ 总结: 所有检查通过

如果有红色❌：
1. 依赖缺失 → `pip install -r requirements_realtime.txt`
2. 模型缺失 → 修改 `config_paths.py`
3. CUDA 不可用 → 检查驱动

---

### ⭐ Step 4: 启动服务
```bash
./scripts/start_realtime_service.sh
```

---

### ⭐ Step 5: 验证服务
```bash
curl http://localhost:8000/
```

---

## 🔍 故障排查

| 问题 | 症状 | 解决方案 |
|------|------|----------|
| 依赖缺失 | `ImportError` | `pip install -r requirements_realtime.txt` |
| CUDA 不可用 | `CUDA not available` | 检查 `nvidia-smi` |
| 模型缺失 | `FileNotFoundError` | 修改 `config_paths.py` |
| 端口占用 | `Address already in use` | `pkill -f main_realtime.py` |
| 显存不足 | `CUDA out of memory` | 降低 `batch_size` |

---

## 📦 关键文件

- ✅ `restructure_project.sh` - 目录重构
- ✅ `config_paths.py` - 路径配置
- ✅ `scripts/check_env.py` - 环境检查 ⭐⭐⭐
- ✅ `main_realtime_patched.py` - 服务入口（已适配路径）

---

## 🎯 一键部署命令

```bash
# 在 /opt/musetalk/repo 目录下执行

# 1. 重构
./restructure_project.sh && \

# 2. 进入 Python 目录
cd backend_python && \

# 3. 检查环境
python scripts/check_env.py && \

# 4. 启动服务
./scripts/start_realtime_service.sh
```

---

## 📞 需要帮助？

运行环境检查：
```bash
python scripts/check_env.py
```

查看详细错误信息，按照提示修复。

---

**祝部署顺利！🎉**
