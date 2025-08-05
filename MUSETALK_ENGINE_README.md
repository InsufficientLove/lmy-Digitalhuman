# MuseTalk Engine 目录结构说明

## 📁 目录结构

为了避免覆盖您本地的 MuseTalk 文件夹及其模型数据，我们采用了新的目录结构：

```
/workspace/
├── MuseTalk/                    # 原始 MuseTalk 目录（包含模型数据）
│   ├── models/
│   │   ├── musetalk/
│   │   │   ├── musetalk.json
│   │   │   └── pytorch_model.bin
│   │   └── whisper/
│   └── [其他模型文件...]
├── MuseTalkEngine/              # 新的代码目录
│   ├── enhanced_musetalk_inference_v4.py
│   ├── enhanced_musetalk_preprocessing.py
│   ├── integrated_musetalk_service.py
│   ├── ultra_fast_realtime_inference.py
│   ├── optimized_musetalk_inference_v3.py
│   └── start_persistent_service.py
├── sync_musetalk_engine.py      # 同步脚本
└── start_musetalk_engine.bat    # 启动脚本
```

## 🔧 核心特性

### 1. 路径自动适配
- `MuseTalkEngine` 目录中的所有文件已自动配置为读取 `../MuseTalk/` 目录中的模型
- 默认模型路径：
  - UNet 配置: `../MuseTalk/models/musetalk/musetalk.json`
  - UNet 权重: `../MuseTalk/models/musetalk/pytorch_model.bin`
  - Whisper 模型: `../MuseTalk/models/whisper/`

### 2. 同步管理
使用 `sync_musetalk_engine.py` 脚本管理文件同步：

```bash
# 查看同步状态
python sync_musetalk_engine.py --status

# 将 MuseTalkEngine 的文件同步到 MuseTalk 目录
python sync_musetalk_engine.py --to-musetalk

# 从 MuseTalk 目录同步文件到 MuseTalkEngine
python sync_musetalk_engine.py --from-musetalk
```

## 🚀 使用方法

### 方法一：直接使用 MuseTalkEngine（推荐）
```bash
cd MuseTalkEngine
python enhanced_musetalk_inference_v4.py --template_id your_template --audio_path input.wav --output_path output.mp4
```

### 方法二：使用启动脚本
```bash
# Windows
start_musetalk_engine.bat

# Linux/Mac
chmod +x start_musetalk_engine.sh
./start_musetalk_engine.sh
```

### 方法三：同步后使用原目录
```bash
# 同步到原目录
python sync_musetalk_engine.py --to-musetalk

# 使用原目录
cd MuseTalk
python enhanced_musetalk_inference_v4.py --template_id your_template --audio_path input.wav --output_path output.mp4
```

## 📋 Git 工作流程

### 拉取更新时
```bash
# 1. 拉取最新代码
git pull

# 2. 如果需要，从 MuseTalk 同步到 MuseTalkEngine
python sync_musetalk_engine.py --from-musetalk

# 3. 或者直接使用 MuseTalkEngine 目录
cd MuseTalkEngine
```

### 提交更改时
```bash
# 1. 在 MuseTalkEngine 目录中进行开发
cd MuseTalkEngine
# [进行代码修改...]

# 2. 如果需要同步到 MuseTalk 目录
cd ..
python sync_musetalk_engine.py --to-musetalk

# 3. 提交更改
git add .
git commit -m "更新 MuseTalk 功能"
git push
```

## 🔄 同步脚本功能

`sync_musetalk_engine.py` 提供以下功能：

1. **智能路径转换**：
   - `MuseTalkEngine → MuseTalk`: 将 `../MuseTalk/models/` 转换为 `models/`
   - `MuseTalk → MuseTalkEngine`: 将 `models/` 转换为 `../MuseTalk/models/`

2. **自动备份**：
   - 同步前自动备份目标文件
   - 备份文件格式: `文件名.backup.YYYYMMDD_HHMMSS`

3. **状态监控**：
   - 比较文件差异
   - 显示同步状态
   - 检测文件完整性

## ⚠️ 注意事项

1. **模型数据保护**：
   - 原 `MuseTalk` 目录中的模型数据不会被覆盖
   - 拉取代码更新时只会更新 `MuseTalkEngine` 目录

2. **路径配置**：
   - 确保从 `MuseTalkEngine` 目录运行脚本
   - 或使用绝对路径指定模型位置

3. **同步管理**：
   - 建议在开发时使用 `MuseTalkEngine` 目录
   - 需要使用原目录时再进行同步

4. **版本控制**：
   - Git 仓库中包含两个目录的文件
   - 可以选择性地提交和更新

## 🎯 优势

1. **数据安全**：保护原有模型数据不被意外覆盖
2. **灵活切换**：可以在两种目录结构间自由切换
3. **向后兼容**：完全兼容原有的使用方式
4. **开发友好**：新功能开发不影响稳定版本

## 🆘 故障排除

### 问题：找不到模型文件
```bash
# 检查路径配置
ls -la ../MuseTalk/models/musetalk/
ls -la ../MuseTalk/models/whisper/

# 或使用绝对路径
python enhanced_musetalk_inference_v4.py --unet_config /absolute/path/to/MuseTalk/models/musetalk/musetalk.json
```

### 问题：同步失败
```bash
# 检查目录结构
python sync_musetalk_engine.py --status

# 手动检查文件
ls -la MuseTalk/
ls -la MuseTalkEngine/
```

### 问题：权限错误
```bash
# 确保脚本有执行权限
chmod +x sync_musetalk_engine.py
chmod +x start_musetalk_engine.sh
```

---

**作者**: Claude Sonnet  
**版本**: 1.0  
**更新日期**: 2024年12月