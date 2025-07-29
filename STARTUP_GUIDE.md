# 数字人系统启动指南

## 🚀 快速启动

### Windows 系统

1. **生产环境启动**
   ```bash
   startup.bat
   ```

2. **开发环境启动**（支持热重载）
   ```bash
   dev-start.bat
   ```

3. **Docker容器启动**
   ```bash
   docker-start.bat
   ```

### Linux/macOS 系统

1. **生产环境启动**
   ```bash
   ./startup.sh
   ```

2. **开发环境启动**（支持热重载）
   ```bash
   ./dev-start.sh
   ```

3. **Docker容器启动**
   ```bash
   ./docker-start.sh
   ```

## 📋 前置要求

### 基础环境
- **.NET 8.0 SDK** - [下载地址](https://dotnet.microsoft.com/download/dotnet/8.0)
- **Git** - 用于代码管理
- **Visual Studio 2022** 或 **VS Code** - 推荐开发工具

### 可选环境
- **Docker Desktop** - 用于容器化部署
- **Python 3.8+** - 用于MuseTalk服务
- **CUDA** - 用于GPU加速（推荐）

## 🌐 访问地址

启动成功后，可通过以下地址访问系统：

- **HTTPS**: https://localhost:7001
- **HTTP**: http://localhost:5001
- **Docker**: http://localhost:8080

## 🛠️ 手动启动

如果启动脚本无法使用，可以手动执行以下命令：

```bash
# 1. 还原NuGet包
dotnet restore LmyDigitalHuman/LmyDigitalHuman.csproj

# 2. 编译项目
dotnet build LmyDigitalHuman/LmyDigitalHuman.csproj --configuration Release

# 3. 启动项目
cd LmyDigitalHuman
dotnet run --configuration Release --urls "https://localhost:7001;http://localhost:5001"
```

## 🐛 常见问题

### 1. 端口被占用
如果端口7001或5001被占用，可以修改启动脚本中的端口号，或者停止占用端口的进程。

### 2. .NET SDK未安装
请访问 [.NET官网](https://dotnet.microsoft.com/download/dotnet/8.0) 下载并安装.NET 8.0 SDK。

### 3. 编译错误
- 确保所有NuGet包已正确还原
- 检查代码是否有语法错误
- 确认项目文件完整性

### 4. 权限问题（Linux/macOS）
如果遇到权限问题，请执行：
```bash
chmod +x *.sh
```

## 📝 开发说明

- **生产模式**: 编译后运行，性能更好，适合部署
- **开发模式**: 支持热重载，代码修改后自动重启，适合开发调试
- **Docker模式**: 容器化运行，环境隔离，适合部署和分发

## 🔧 配置文件

主要配置文件位于：
- `LmyDigitalHuman/appsettings.json` - 开发环境配置
- `LmyDigitalHuman/appsettings.Production.json` - 生产环境配置

## 📞 技术支持

如果遇到问题，请检查：
1. 系统日志输出
2. 配置文件设置
3. 网络连接状态
4. 依赖服务状态