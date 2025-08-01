# Docker Engine 手动安装指南 (Windows Server 2019)

## 方法1: 手动下载安装

### 步骤1: 下载Docker Engine
```powershell
# 创建下载目录
New-Item -ItemType Directory -Path "C:\docker" -Force

# 下载Docker Engine (使用稳定版本)
$dockerUrl = "https://download.docker.com/win/static/stable/x86_64/docker-24.0.7.zip"
$dockerZip = "C:\docker\docker.zip"

# 如果有代理问题，先设置代理
# [System.Net.WebRequest]::DefaultWebProxy = [System.Net.WebRequest]::GetSystemWebProxy()

Invoke-WebRequest -Uri $dockerUrl -OutFile $dockerZip -UseBasicParsing
```

### 步骤2: 解压和安装
```powershell
# 解压Docker
Expand-Archive -Path "C:\docker\docker.zip" -DestinationPath "C:\Program Files" -Force

# 添加到系统PATH
$dockerPath = "C:\Program Files\docker"
$currentPath = [Environment]::GetEnvironmentVariable("Path", "Machine")
if ($currentPath -notlike "*$dockerPath*") {
    [Environment]::SetEnvironmentVariable("Path", "$currentPath;$dockerPath", "Machine")
}

# 刷新当前会话的PATH
$env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine")
```

### 步骤3: 注册Docker服务
```powershell
# 注册Docker服务
& "C:\Program Files\docker\dockerd.exe" --register-service

# 启动服务
Start-Service docker
Set-Service docker -StartupType Automatic
```

## 方法2: 使用winget安装

```powershell
# 安装winget (如果没有)
# 下载: https://github.com/microsoft/winget-cli/releases

# 使用winget安装Docker
winget install Docker.DockerDesktop
```

## 方法3: 直接从GitHub下载

```powershell
# 从GitHub下载Docker二进制文件
$githubUrl = "https://github.com/docker/docker-ce/releases/download/v24.0.7/docker-24.0.7.tgz"
# 注意：这是Linux版本，Windows需要.zip文件
```

## 验证安装

```powershell
# 检查Docker版本
docker --version

# 测试运行
docker run hello-world
```

## 故障排除

### 如果遇到代理问题：
```powershell
# 清除代理设置
$env:http_proxy = $null
$env:https_proxy = $null
[System.Net.WebRequest]::DefaultWebProxy = $null
```

### 如果遇到SSL问题：
```powershell
# 启用TLS 1.2
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
```