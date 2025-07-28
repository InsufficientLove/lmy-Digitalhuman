# 🚀 数字人便携式环境部署指南

## 📥 **第一步：拉取最新代码**

```cmd
# 在您的本地项目目录执行
git pull origin main
```

## 🎯 **第二步：运行安装脚本**

```cmd
# 进入项目目录
cd LmyDigitalHuman

# 运行便携式环境安装脚本
setup_portable_environment.bat
```

**这个脚本会自动：**
- ✅ 检测您的Python环境
- ✅ 创建便携式目录：`F:\AI\DigitalHuman_Portable`
- ✅ 安装所有必要依赖（包括PyTorch CUDA版本）
- ✅ 下载MuseTalk源码和模型
- ✅ 创建启动脚本和配置工具
- ✅ 自动检测GPU配置（单卡/双卡）

## 🔧 **第三步：配置和启动**

安装完成后，会在 `F:\AI\DigitalHuman_Portable\scripts\` 目录生成以下脚本：

### **配置GPU（如需要）**
```cmd
cd F:\AI\DigitalHuman_Portable\scripts
configure_gpu.bat
```

### **检查环境**
```cmd
check_environment.bat
```

### **启动MuseTalk服务**
```cmd
start_musetalk.bat
```

### **启动.NET应用**
```cmd
# 在项目目录
cd LmyDigitalHuman
dotnet run
```

## 🌐 **第四步：验证服务**

- **MuseTalk服务**: http://localhost:8000/health
- **.NET应用**: https://localhost:7135
- **数字人界面**: https://localhost:7135/realtime-digital-human.html

## 🚚 **环境迁移（可选）**

如果需要在其他机器上部署：

```cmd
# 在源机器上
migrate_environment.bat
# 选择 "1. 📦 打包当前环境"

# 将生成的压缩包复制到目标机器
# 在目标机器上解压并运行 deploy.bat
```

## 🔧 **目录结构**

```
F:\AI\DigitalHuman_Portable\
├── venv\                    # Python虚拟环境
├── MuseTalk\               # MuseTalk源码
├── models\                 # 预训练模型
├── scripts\                # 启动脚本
│   ├── start_musetalk.bat
│   ├── check_environment.bat
│   └── configure_gpu.bat
├── config\                 # 配置文件
└── logs\                   # 日志文件
```

## ⚠️ **注意事项**

1. **Python版本**: 需要Python 3.10.11
2. **GPU驱动**: 如有NVIDIA显卡，确保安装了CUDA 11.8驱动
3. **磁盘空间**: 至少需要10GB空间（包含模型文件）
4. **网络**: 首次安装需要下载模型，确保网络连接稳定

## 🆘 **故障排除**

### **常见问题**

1. **Python未安装**
   - 下载安装Python 3.10.11: https://www.python.org/downloads/release/python-31011/
   - 安装时勾选"Add Python to PATH"

2. **dlib安装失败**
   - 脚本会自动尝试预编译版本
   - 如仍失败，可能需要安装Visual Studio Build Tools

3. **CUDA版本问题**
   - 运行 `nvidia-smi` 检查CUDA版本
   - 脚本会自动检测并安装对应版本

4. **端口占用**
   - 检查8000端口是否被占用：`netstat -ano | findstr :8000`
   - 如需要，可以修改配置文件中的端口

## 📞 **技术支持**

如遇到问题，请提供以下信息：
- 运行 `check_environment.bat` 的输出结果
- 错误日志（位于 `F:\AI\DigitalHuman_Portable\logs\`）
- 系统配置（GPU型号、Python版本等）

---

**预计安装时间**: 15-30分钟（取决于网络速度）  
**硬件需求**: RTX系列显卡推荐，也支持CPU模式