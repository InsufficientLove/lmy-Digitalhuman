# 🔧 修复 Diffusers 导入错误

## 问题诊断

```
ImportError: cannot import name 'cached_download' from 'huggingface_hub'
```

**原因**：`huggingface_hub` 版本太新（0.34+），移除了 `cached_download` API，但 `diffusers==0.24.0` 还在使用旧 API。

---

## 解决方案（二选一）

### ✅ 方案 1：升级 diffusers（推荐）

```bash
pip install --upgrade diffusers
```

**优点**：
- 使用最新功能
- 兼容新版依赖
- 长期维护

### ⚠️ 方案 2：降级 huggingface_hub

```bash
pip install huggingface_hub==0.20.0
```

**缺点**：
- 可能影响其他包（transformers）
- 不推荐

---

## 快速修复

```bash
# 执行修复
pip install --upgrade diffusers

# 验证
python3 -c "import diffusers; print(f'✅ Diffusers {diffusers.__version__}')"

# 继续安装
cd /opt/musetalk/repo
bash install_dependencies.sh
```

---

## 版本兼容表

| diffusers | huggingface_hub | 状态 |
|-----------|-----------------|------|
| 0.24.0    | 0.19.4 - 0.20.x | ✅ 兼容 |
| 0.24.0    | 0.34.x+         | ❌ 不兼容 |
| 0.30.0+   | 0.34.x+         | ✅ 兼容 |

---

**修复后即可继续！** 🎯
