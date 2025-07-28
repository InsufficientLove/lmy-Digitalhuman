# SadTalker 模型版本问题解决指南

## 🚨 问题描述

在运行时出现警告：
```
WARNING: The new version of the model will be updated by safetensor, you may need to download it mannully. We run the old version of the checkpoint this time!
```

## 📋 新版本 vs 旧版本区别

### 旧版本（当前使用）
- **格式**：`.pth` 文件（PyTorch原生格式）
- **安全性**：较低，可能包含恶意代码
- **加载速度**：较慢
- **文件大小**：较大
- **兼容性**：广泛支持

### 新版本（推荐）
- **格式**：`.safetensors` 文件（HuggingFace安全格式）
- **安全性**：高，只包含纯张量数据
- **加载速度**：更快
- **文件大小**：更小
- **兼容性**：需要较新的库版本

## 🔧 解决方案

### 方案1：下载新版本模型（推荐）

1. **检查当前模型目录**：
```bash
# 检查SadTalker模型目录
ls -la C:\AI\SadTalker\checkpoints\
```

2. **下载新版本模型**：
```bash
# 进入SadTalker目录
cd C:\AI\SadTalker

# 下载新版本模型
python scripts/download_models.py --safetensors
```

3. **或者手动下载**：
访问以下链接下载新版本模型：
- `auido2exp_00300-model.safetensors`
- `auido2pose_00140-model.safetensors`  
- `mapping_00229-model.safetensors`
- `mapping_00109-model.safetensors`
- `facevid2vid_00189-model.safetensors`

**下载地址**：
- HuggingFace: https://huggingface.co/vinthony/SadTalker/tree/main/checkpoints
- 百度网盘: https://pan.baidu.com/s/1kb1BCPaLOWX1JJb9Czbn6w (提取码: sadt)

### 方案2：更新依赖库

```bash
# 更新safetensors库
pip install safetensors --upgrade

# 更新transformers
pip install transformers --upgrade

# 更新torch
pip install torch torchvision torchaudio --upgrade
```

### 方案3：配置使用新模型

在 `appsettings.json` 中添加配置：
```json
{
  "RealtimeDigitalHuman": {
    "SadTalker": {
      "Path": "C:\\AI\\SadTalker",
      "UseSafeTensors": true,
      "ModelVersion": "v2"
    }
  }
}
```

## 📁 模型文件结构

```
C:\AI\SadTalker\checkpoints\
├── auido2exp_00300-model.pth          # 旧版本
├── auido2exp_00300-model.safetensors  # 新版本
├── auido2pose_00140-model.pth         # 旧版本  
├── auido2pose_00140-model.safetensors # 新版本
├── mapping_00229-model.pth            # 旧版本
├── mapping_00229-model.safetensors    # 新版本
├── mapping_00109-model.pth            # 旧版本
├── mapping_00109-model.safetensors    # 新版本
├── facevid2vid_00189-model.pth        # 旧版本
└── facevid2vid_00189-model.safetensors # 新版本
```

## 🎯 推荐操作步骤

1. **立即解决文件路径问题**（已修复）
   - 避免使用中文文件名
   - 确保路径正确

2. **下载新版本模型**
   ```bash
   # 方法1：使用脚本下载
   cd C:\AI\SadTalker
   python scripts/download_models.py --safetensors
   
   # 方法2：手动下载并放置到checkpoints目录
   ```

3. **验证模型文件**
   ```bash
   # 检查模型文件是否完整
   python scripts/verify_models.py
   ```

4. **测试运行**
   ```bash
   # 测试新模型
   python inference.py --driven_audio test.wav --source_image test.jpg --result_dir results --still
   ```

## ⚠️ 注意事项

1. **备份旧模型**：在下载新模型前，备份现有的 `.pth` 文件
2. **磁盘空间**：新模型需要额外的存储空间
3. **网络连接**：下载可能需要稳定的网络连接
4. **兼容性**：确保Python环境支持safetensors库

## 🐛 常见问题

### Q: 下载速度慢怎么办？
A: 使用国内镜像或百度网盘下载

### Q: 新模型不工作怎么办？
A: 检查safetensors库版本，确保 >= 0.3.0

### Q: 可以同时保留新旧模型吗？
A: 可以，SadTalker会优先使用safetensors格式

## 📞 技术支持

如果遇到问题，请：
1. 检查日志输出
2. 确认模型文件完整性
3. 验证Python环境配置
4. 查看SadTalker官方文档

---
**更新日期**: 2025-01-28  
**版本**: v1.0