# MuseTalk 模型数据目录

这个目录用于存放 MuseTalk 的模型数据文件。

## 📁 目录结构

请将您的模型文件按以下结构放置：

```
MuseTalk/
├── models/
│   ├── musetalk/
│   │   ├── musetalk.json          # UNet 配置文件
│   │   └── pytorch_model.bin      # UNet 权重文件
│   └── whisper/                   # Whisper 模型目录
│       └── [whisper 模型文件...]
└── [其他模型文件和数据...]
```

## 🔧 使用说明

1. **模型文件**: 将您的 MuseTalk 模型文件放在相应目录中
2. **代码执行**: 所有 Python 代码现在在 `../MuseTalkEngine/` 目录中
3. **路径配置**: MuseTalkEngine 中的代码已自动配置为从此目录读取模型

## ⚠️ 重要提示

- 此目录专门用于存放模型数据
- Python 代码文件请使用 `../MuseTalkEngine/` 目录
- Git 更新不会覆盖此目录中的模型数据

## 🚀 快速开始

```bash
# 从 MuseTalkEngine 目录运行代码
cd ../MuseTalkEngine
python3 enhanced_musetalk_inference_v4.py --help
```

更多详细说明请参考 `../MUSETALK_ENGINE_README.md`