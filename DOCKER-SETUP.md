# Windows Server 2019 Docker 部署指南

## 🎯 目标
在Windows Server 2019上实现：
1. **VS2022调试** - 使用系统Python环境进行开发调试
2. **Docker部署** - 使用容器化环境对外提供服务

## 📋 前置条件检查

运行环境检查脚本：
```cmd
check-server-environment.bat
```

## 🔧 Docker Desktop 安装

### 1. 下载 Docker Desktop for Windows
- 官方下载：https://www.docker.com/products/docker-desktop
- 选择 Windows 版本

### 2. 安装要求
- Windows Server 2019 (版本 1809 或更高)
- 启用 Hyper-V 功能
- 启用 Windows 容器功能

### 3. 启用必需的 Windows 功能
以管理员身份运行 PowerShell：
```powershell
# 启用 Hyper-V
Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V -All

# 启用容器功能
Enable-WindowsOptionalFeature -Online -FeatureName Containers -All

# 重启服务器
Restart-Computer
```

### 4. 安装 Docker Desktop
1. 运行下载的安装程序
2. 选择"使用 Windows 容器而不是 Linux 容器"（可选，但推荐用Linux容器）
3. 完成安装后重启

### 5. 验证安装
```cmd
docker --version
docker-compose --version
```

## 🏗️ 项目配置

### 开发环境配置
```json
// appsettings.Development.json
{
  "DigitalHuman": {
    "EdgeTTS": {
      "PythonPath": "python"  // 使用系统Python
    }
  }
}
```

### Docker环境配置
```json
// appsettings.Docker.json  
{
  "DigitalHuman": {
    "EdgeTTS": {
      "PythonPath": "venv_musetalk/bin/python"  // 使用容器内Python
    }
  }
}
```

## 🚀 部署流程

### 方案A：VS调试模式
1. 在VS2022中打开解决方案
2. 确保系统已安装 `edge-tts`：
   ```cmd
   pip install edge-tts
   ```
3. 按F5启动调试
4. 访问：http://localhost:5000

### 方案B：Docker部署模式
1. 运行Docker部署：
   ```cmd
   deploy-docker.bat
   ```
2. 等待构建和启动完成
3. 访问：http://localhost:5000

## 🔄 双模式工作流

```
开发阶段              生产部署
    ↓                     ↓
VS2022调试     →     Docker容器化
(系统Python)        (容器Python)
    ↓                     ↓
本地测试              对外服务
```

## 🌐 端口说明

| 服务 | VS调试模式 | Docker模式 | 说明 |
|------|-----------|------------|------|
| 数字人API | 5000/5001 | 5000 | 主要API接口 |
| Ollama | 11434 | 11434 | LLM服务 |
| Nginx | - | 80 | 反向代理(生产模式) |

## 🔍 故障排除

### 常见问题1：Docker启动失败
**解决方案：**
1. 确保Hyper-V已启用
2. 检查Windows容器功能
3. 重启Docker Desktop

### 常见问题2：VS调试时Python包找不到
**解决方案：**
```cmd
# 检查Python环境
python --version
python -c "import edge_tts"

# 如果失败，安装包
pip install edge-tts
```

### 常见问题3：端口冲突
**解决方案：**
- VS调试默认使用5000/5001端口
- Docker使用5000端口
- 确保同时只运行一种模式

## 📊 资源使用建议

### 开发环境（VS调试）
- 内存：4GB 最低，8GB 推荐
- CPU：较低占用
- 磁盘：项目文件 + 模型文件

### 生产环境（Docker）
- 内存：8GB 最低，16GB 推荐
- CPU：多核推荐（GPU支持更佳）
- 磁盘：容器镜像 + 数据卷

## 🎯 最佳实践

1. **开发时**：使用VS调试模式，快速迭代
2. **测试时**：使用Docker模式，验证容器化
3. **生产时**：仅使用Docker模式，稳定可靠

## 📝 快速命令参考

```cmd
# 环境检查
check-server-environment.bat

# Docker部署
deploy-docker.bat

# 查看Docker状态
docker-compose ps

# 查看日志
docker-compose logs digitalhuman

# 停止Docker服务
docker-compose down

# VS调试
# 在VS2022中按F5即可
```

## 💡 提示

- 🔧 **开发调试**：VS + 系统Python = 快速开发
- 🐳 **生产部署**：Docker + 容器Python = 稳定运行
- 🚀 **无缝切换**：配置分离，环境隔离
- 📊 **监控诊断**：`/api/diagnostics/python-environments`

现在您可以在同一台服务器上享受VS调试的便利和Docker部署的稳定性！