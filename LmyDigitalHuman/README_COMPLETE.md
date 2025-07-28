# 🚀 数字人系统 - MuseTalk完整解决方案

## 📋 项目简介

这是一个基于MuseTalk的数字人系统，支持实时高质量唇形同步。本项目解决了Windows环境下dlib安装的各种问题，提供了完整的自动化安装方案。

### ✨ 主要特性

- 🎯 **智能环境检测**: 自动检测系统环境，智能配置安装路径
- 🔧 **自动依赖安装**: 自动下载和安装Visual Studio、CMake等必需组件
- 🎭 **多重dlib安装策略**: 预编译包 → 源码编译 → 兼容版本 → 替代方案
- 🔄 **智能回退机制**: dlib → MediaPipe → OpenCV，确保人脸检测功能可用
- 🖥️ **通用兼容性**: 支持任何Windows服务器，无需预装环境
- 🚫 **窗口不关闭**: 安装过程中即使出错也不会关闭窗口，方便查看错误信息

## 🛠️ 系统要求

- Windows 10/11 或 Windows Server 2016+
- Python 3.8+ (脚本会自动检测，如未安装会提示下载)
- 至少10GB可用磁盘空间
- 网络连接（用于下载依赖）

## 🚀 快速开始

### 方法一：一键安装（推荐）

1. 下载项目到本地
2. 双击运行 `install_complete_universal.bat`
3. 等待安装完成（首次安装可能需要30-60分钟）
4. 安装完成后运行 `activate_env.bat` 激活环境

### 方法二：手动安装

如果自动安装失败，可以按以下步骤手动安装：

1. 安装Python 3.8+: https://www.python.org/downloads/
2. 安装Visual Studio 2022 Community: https://visualstudio.microsoft.com/
3. 安装CMake: https://cmake.org/download/
4. 运行安装脚本

## 📁 文件结构

```
LmyDigitalHuman/
├── install_complete_universal.bat     # 🎯 主安装脚本
├── fix_dlib_vs_cmake_only.bat        # dlib专用修复脚本
├── musetalk_service_complete.py       # 🚀 完整服务文件
├── README_COMPLETE.md                 # 📖 完整说明文档
└── 其他配置文件...
```

## 🎯 dlib安装解决方案

本项目采用四重策略确保dlib安装成功：

### 策略1: 预编译包安装
```bash
pip install dlib -i https://pypi.tuna.tsinghua.edu.cn/simple/
```

### 策略2: 源码编译
- 自动配置VS2022编译环境
- 使用CMake从源码编译dlib
- 优化编译参数，禁用不必要的功能

### 策略3: 兼容版本
- 尝试安装dlib 19.22.1, 19.21.1, 19.20.1等兼容版本
- 逐个测试直到找到可用版本

### 策略4: 替代方案
- 安装MediaPipe作为高质量替代
- 安装face_recognition库
- 使用OpenCV Haar级联作为基础方案

## 🔧 使用方法

### 启动服务

1. 激活环境：
```bash
# 双击运行或命令行执行
activate_env.bat
```

2. 测试环境：
```bash
python test_environment.py
```

3. 启动MuseTalk服务：
```bash
python musetalk_service_complete.py
```

### API接口

服务启动后，可以通过以下接口使用：

#### 健康检查
```bash
GET http://localhost:5000/health
```

#### 人脸检测
```bash
POST http://localhost:5000/detect_faces
Content-Type: multipart/form-data
Body: image file
```

#### 生成数字人视频
```bash
POST http://localhost:5000/generate
Content-Type: application/json
Body: {
  "video_path": "input.mp4",
  "audio_path": "audio.wav",
  "output_path": "output.mp4"
}
```

#### 系统信息
```bash
GET http://localhost:5000/info
```

## 🐛 常见问题解决

### Q1: dlib安装失败
**A**: 脚本已包含多重安装策略，如果仍然失败：
1. 检查是否正确安装了Visual Studio和CMake
2. 尝试手动运行 `fix_dlib_vs_cmake_only.bat`
3. 查看安装日志中的具体错误信息

### Q2: Visual Studio未找到
**A**: 脚本会自动下载安装VS Build Tools，如果失败：
1. 手动下载安装Visual Studio 2022 Community
2. 确保勾选"C++桌面开发"工作负载
3. 重新运行安装脚本

### Q3: CMake未找到
**A**: 脚本会自动安装CMake，如果失败：
1. 手动从 https://cmake.org/download/ 下载安装
2. 安装时选择"添加到系统PATH"
3. 重启命令提示符

### Q4: 网络连接问题
**A**: 脚本使用清华大学镜像源，如果仍有问题：
1. 检查网络连接
2. 尝试使用VPN
3. 手动配置其他镜像源

### Q5: 磁盘空间不足
**A**: 
1. 清理磁盘空间，至少保留10GB
2. 修改脚本中的BASE_DIR变量指向其他盘符
3. 删除不必要的临时文件

## 📊 性能优化

### GPU加速
- 自动检测NVIDIA GPU并安装CUDA版本的PyTorch
- 支持GPU加速推理，显著提升处理速度

### 内存优化
- 智能选择人脸检测器，平衡质量和性能
- 支持批处理和流式处理

### 模型优化
- 支持模型量化和优化
- 可配置推理精度（FP32/FP16）

## 🔄 更新日志

### v2025-01-28 终极版
- ✅ 完全解决dlib安装问题
- ✅ 支持任何Windows服务器自动安装
- ✅ 添加智能环境检测
- ✅ 实现多重安装策略
- ✅ 添加完整的错误处理和日志
- ✅ 支持GPU自动检测和配置
- ✅ 窗口保持打开，方便查看错误信息

### v2025-01-27
- 基础MuseTalk集成
- 初步dlib安装支持

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

1. Fork本项目
2. 创建功能分支
3. 提交更改
4. 创建Pull Request

## 📄 许可证

本项目采用MIT许可证，详见LICENSE文件。

## 🙏 致谢

- [MuseTalk](https://github.com/TMElyralab/MuseTalk) - 核心数字人技术
- [dlib](http://dlib.net/) - 人脸检测库
- [MediaPipe](https://mediapipe.dev/) - 替代人脸检测方案
- 清华大学镜像源 - 提供快速的包下载服务

## 📞 支持

如有问题，请：
1. 查看本文档的常见问题部分
2. 检查安装日志中的错误信息
3. 提交Issue到GitHub仓库

---

**🏆 现在您拥有了最完整的MuseTalk数字人系统安装方案！**