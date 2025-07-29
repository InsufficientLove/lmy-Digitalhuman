# 🧹 清理全局Python环境指南

## 问题背景

之前的版本可能在全局Python环境中安装了项目依赖，现在我们改用虚拟环境管理。为避免冲突，建议清理全局环境中的相关包。

## 🚀 自动清理（推荐）

运行自动清理脚本：
```bash
cleanup-global-python.bat
```

脚本会：
- ✅ 自动检测全局环境中的项目相关依赖
- ✅ 安全卸载不需要的包
- ✅ 保护系统关键包
- ✅ 提供详细的清理报告

## 🔧 手动清理

如果您prefer手动操作，可以按以下步骤进行：

### 1. 检查已安装的包
```bash
pip list
```

### 2. 查找项目相关的包
查找以下包是否存在：
```bash
pip show torch
pip show torchvision  
pip show torchaudio
pip show edge-tts
pip show opencv-python
pip show pillow
pip show scipy
pip show scikit-image
pip show librosa
pip show tqdm
pip show pydub
pip show numpy
```

### 3. 卸载项目相关包

#### 卸载PyTorch相关（通常占用空间最大）
```bash
pip uninstall torch torchvision torchaudio -y
```

#### 卸载Edge-TTS
```bash
pip uninstall edge-tts -y
```

#### 卸载图像处理包
```bash
pip uninstall opencv-python pillow scikit-image -y
```

#### 卸载科学计算包
```bash
pip uninstall scipy -y
```

#### 卸载音频处理包
```bash
pip uninstall librosa pydub -y
```

#### 卸载工具包
```bash
pip uninstall tqdm -y
```

#### 谨慎卸载numpy
```bash
# numpy可能被其他包依赖，先检查
pip show numpy
# 如果只被项目相关包依赖，可以卸载
pip uninstall numpy -y
```

#### 可选：卸载requests
```bash
# requests是常用库，其他项目可能需要
# 只有确定不需要时才卸载
pip uninstall requests -y
```

## 📍 常见Python安装位置

### Windows
- **用户安装**: `%APPDATA%\Python\Python3x\site-packages`
- **系统安装**: `C:\Python3x\Lib\site-packages`
- **Microsoft Store**: `%LOCALAPPDATA%\Packages\PythonSoftwareFoundation.Python.3.x_xxx\LocalCache\local-packages\Python3x\site-packages`

### 查找Python路径
```bash
python -c "import site; print(site.getsitepackages())"
```

## 🔍 验证清理结果

清理完成后，验证包是否已删除：
```bash
python -c "import torch"  # 应该报错 ModuleNotFoundError
python -c "import edge_tts"  # 应该报错 ModuleNotFoundError
```

## ⚠️ 注意事项

1. **备份重要数据**: 清理前确保项目数据已备份
2. **检查依赖**: 某些包可能被其他项目使用
3. **系统包**: 不要卸载系统自带的Python包
4. **虚拟环境**: 清理后使用虚拟环境管理依赖

## 🐍 清理后的步骤

1. **重新创建虚拟环境**:
   ```bash
   setup-environment.bat
   ```

2. **验证环境**:
   ```bash
   verify-environment.bat
   ```

3. **启动项目**:
   ```bash
   startup.bat
   ```

## 💡 最佳实践

- ✅ 使用虚拟环境管理项目依赖
- ✅ 保持全局Python环境简洁
- ✅ 定期清理不需要的包
- ✅ 使用requirements.txt管理依赖版本

## 🆘 遇到问题？

如果清理过程中遇到问题：

1. **权限问题**: 以管理员身份运行命令行
2. **包被占用**: 关闭所有Python进程后重试
3. **依赖冲突**: 使用 `pip uninstall --force` 强制卸载
4. **恢复环境**: 重新运行 `setup-environment.bat`

清理完成后，所有Python依赖将在独立的虚拟环境中管理，避免版本冲突和环境污染！