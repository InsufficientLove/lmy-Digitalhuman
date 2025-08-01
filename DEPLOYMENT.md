# 数字人系统部署指南

## 概述

本指南详细说明了如何部署数字人系统，特别是如何正确处理Python虚拟环境和依赖项的问题。

## 1. Python环境问题分析

### 问题描述
在部署过程中，经常出现以下Python环境相关的错误：
- `EdgeTTS Python路径不存在`
- `系统找不到指定的文件`
- `Python环境不支持edge-tts`

### 根本原因
1. **虚拟环境未包含在发布包中**：`venv_musetalk` 目录包含的是平台特定的二进制文件，不应该包含在源代码中
2. **路径配置硬编码**：生产环境和开发环境的路径不同
3. **依赖包缺失**：系统Python环境可能缺少必需的包（如 `edge-tts`）

## 2. 推荐的部署策略

### 方案A：在目标服务器上重建虚拟环境（推荐）

#### 步骤1：准备Python环境
```bash
# 确保目标服务器安装了Python 3.8+
python --version

# 如果没有Python，安装Python（Windows）
# 下载并安装Python从 https://python.org
# 或使用包管理器安装
```

#### 步骤2：创建部署脚本
创建 `deploy-python-env.bat`（Windows）或 `deploy-python-env.sh`（Linux）：

```batch
@echo off
echo 正在设置Python虚拟环境...

REM 删除旧的虚拟环境（如果存在）
if exist "venv_musetalk" (
    echo 删除旧的虚拟环境...
    rmdir /s /q venv_musetalk
)

REM 创建新的虚拟环境
echo 创建虚拟环境...
python -m venv venv_musetalk

REM 激活虚拟环境
echo 激活虚拟环境...
call venv_musetalk\Scripts\activate.bat

REM 升级pip
echo 升级pip...
python -m pip install --upgrade pip

REM 安装必需的包
echo 安装必需的包...
pip install edge-tts
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
pip install -r requirements.txt

echo 虚拟环境设置完成！
pause
```

#### 步骤3：修改项目文件
确保 `.gitignore` 包含虚拟环境目录：
```
venv_musetalk/
env/
.venv/
```

#### 步骤4：部署流程
1. 部署应用程序代码（不包含虚拟环境）
2. 在目标服务器上运行部署脚本
3. 配置IIS或其他Web服务器

### 方案B：使用Docker容器（高级用户）

#### Dockerfile示例
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY . .

# 创建虚拟环境并安装依赖
RUN python -m venv venv_musetalk && \
    . venv_musetalk/bin/activate && \
    pip install --upgrade pip && \
    pip install edge-tts && \
    pip install -r requirements.txt

# 安装.NET运行时
RUN wget https://packages.microsoft.com/config/debian/11/packages-microsoft-prod.deb -O packages-microsoft-prod.deb && \
    dpkg -i packages-microsoft-prod.deb && \
    apt-get update && \
    apt-get install -y aspnetcore-runtime-8.0

EXPOSE 5000

CMD ["dotnet", "LmyDigitalHuman.dll"]
```

## 3. IIS部署配置

### 3.1 应用程序池配置
```xml
<system.webServer>
  <processModel>
    <environmentVariables>
      <add name="ASPNETCORE_ENVIRONMENT" value="Production" />
      <add name="PYTHONPATH" value="C:\inetpub\wwwroot\digitalhuman\venv_musetalk\Scripts" />
    </environmentVariables>
  </processModel>
</system.webServer>
```

### 3.2 权限配置
确保IIS应用程序池标识有以下权限：
- 对应用程序目录的读写权限
- 对虚拟环境目录的执行权限
- 对临时文件目录的写权限

## 4. 配置文件优化

### 4.1 智能路径检测
系统现在支持自动检测可用的Python环境，按以下优先级：
1. 项目虚拟环境 (`venv_musetalk/Scripts/python.exe`)
2. 配置文件指定的路径
3. 系统Python环境
4. 常见Python安装路径

### 4.2 配置文件示例

#### appsettings.Production.json
```json
{
  "DigitalHuman": {
    "MuseTalk": {
      "PythonPath": "venv_musetalk/Scripts/python.exe",
      "TimeoutMinutes": 30
    },
    "EdgeTTS": {
      "PythonPath": "venv_musetalk/Scripts/python.exe",
      "AutoInstallPackages": true,
      "TimeoutSeconds": 30
    }
  },
  "Paths": {
    "PythonFallbackPaths": [
      "C:/inetpub/wwwroot/digitalhuman/venv_musetalk/Scripts/python.exe",
      "C:/Python311/python.exe",
      "C:/Python310/python.exe",
      "python.exe",
      "python"
    ]
  }
}
```

## 5. 故障排除

### 5.1 常见错误及解决方案

#### 错误：Python路径不存在
**解决方案：**
1. 检查虚拟环境是否正确创建
2. 验证路径配置是否正确
3. 查看应用程序日志中的Python环境检测信息

#### 错误：edge-tts包不存在
**解决方案：**
1. 激活虚拟环境：`venv_musetalk\Scripts\activate.bat`
2. 安装edge-tts：`pip install edge-tts`
3. 或启用自动安装功能：`"AutoInstallPackages": true`

#### 错误：权限不足
**解决方案：**
1. 检查IIS应用程序池的用户权限
2. 确保用户有执行Python的权限
3. 考虑使用专用的服务账户

### 5.2 日志分析
关键日志信息：
```
检测到最佳Python环境: C:\...\python.exe (版本: 3.11.0, 虚拟环境: true)
EdgeTTS Python路径解析: venv_musetalk/Scripts/python.exe → C:\...\python.exe
成功安装edge-tts包
```

## 6. 维护建议

### 6.1 定期检查
- 监控Python环境状态
- 检查依赖包更新
- 验证路径配置的有效性

### 6.2 备份策略
- 备份配置文件
- 记录虚拟环境的包列表：`pip freeze > requirements.txt`
- 创建部署脚本的版本控制

### 6.3 性能优化
- 使用SSD存储虚拟环境
- 配置合适的超时时间
- 监控内存和CPU使用情况

## 7. 快速部署检查清单

- [ ] Python 3.8+ 已安装
- [ ] 虚拟环境已创建且包含必需的包
- [ ] 配置文件路径正确
- [ ] IIS权限配置正确
- [ ] 应用程序可以检测到Python环境
- [ ] edge-tts包可以正常导入
- [ ] 临时文件目录可写
- [ ] 日志记录正常工作

## 8. 联系支持

如果遇到部署问题，请提供以下信息：
- 操作系统版本
- Python版本
- 应用程序日志
- 配置文件内容
- 错误信息截图

---

**注意：**本部署指南假设您对IIS和Python有基本了解。如果您是初学者，建议先在测试环境中练习部署流程。