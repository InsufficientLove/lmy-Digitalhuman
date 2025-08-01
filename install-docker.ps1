# Docker Engine 安装脚本 for Windows Server 2019
param(
    [switch]$DisableHyperV = $false
)

Write-Host "=== Docker Engine 安装向导 ===" -ForegroundColor Green
Write-Host ""

# 检查管理员权限
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "需要管理员权限运行此脚本" -ForegroundColor Red
    Write-Host "请右键点击PowerShell，选择'以管理员身份运行'" -ForegroundColor Yellow
    Read-Host "按回车键退出"
    exit 1
}

Write-Host "管理员权限确认" -ForegroundColor Green

try {
    # 第1步：处理Hyper-V
    if ($DisableHyperV) {
        Write-Host ""
        Write-Host "第1步：关闭Hyper-V..." -ForegroundColor Yellow
        $hyperv = Get-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V-All
        if ($hyperv.State -eq "Enabled") {
            Disable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V-All -NoRestart
            Write-Host "Hyper-V已关闭（重启后生效）" -ForegroundColor Green
        } else {
            Write-Host "Hyper-V已经是关闭状态" -ForegroundColor Green
        }
    } else {
        Write-Host ""
        Write-Host "第1步：保持Hyper-V当前状态" -ForegroundColor Cyan
    }

    # 第2步：启用容器功能
    Write-Host ""
    Write-Host "第2步：启用Windows容器功能..." -ForegroundColor Yellow
    $containers = Get-WindowsOptionalFeature -Online -FeatureName Containers
    if ($containers.State -ne "Enabled") {
        Enable-WindowsOptionalFeature -Online -FeatureName Containers -All -NoRestart
        Write-Host "容器功能已启用" -ForegroundColor Green
    } else {
        Write-Host "容器功能已存在" -ForegroundColor Green
    }

    # 第3步：下载并安装Docker
    Write-Host ""
    Write-Host "第3步：安装Docker Engine..." -ForegroundColor Yellow
    
    # 检查Docker是否已安装
    $dockerExists = Get-Command docker -ErrorAction SilentlyContinue
    if ($dockerExists) {
        $version = & docker --version
        Write-Host "Docker已安装，版本：$version" -ForegroundColor Green
    } else {
        # 下载Docker安装包
        $dockerUrl = "https://download.docker.com/win/static/stable/x86_64/docker-24.0.7.zip"
        $dockerZip = "$env:TEMP\docker.zip"
        $dockerPath = "C:\Program Files\Docker"
        
        Write-Host "下载Docker..." -ForegroundColor Yellow
        Invoke-WebRequest -Uri $dockerUrl -OutFile $dockerZip
        
        # 解压Docker
        Write-Host "解压Docker..." -ForegroundColor Yellow
        if (Test-Path $dockerPath) {
            Remove-Item $dockerPath -Recurse -Force
        }
        New-Item -ItemType Directory -Path $dockerPath -Force | Out-Null
        Expand-Archive -Path $dockerZip -DestinationPath $dockerPath -Force
        
        # 添加到系统PATH
        $dockerBinPath = "$dockerPath\docker"
        $currentPath = [Environment]::GetEnvironmentVariable("Path", "Machine")
        if ($currentPath -notlike "*$dockerBinPath*") {
            $newPath = "$currentPath;$dockerBinPath"
            [Environment]::SetEnvironmentVariable("Path", $newPath, "Machine")
            $env:Path = "$env:Path;$dockerBinPath"
        }
        
        # 注册Docker服务
        Write-Host "注册Docker服务..." -ForegroundColor Yellow
        $dockerdPath = "$dockerBinPath\dockerd.exe"
        & $dockerdPath --register-service
        
        Write-Host "Docker安装完成" -ForegroundColor Green
    }

    # 第4步：安装Docker Compose
    Write-Host ""
    Write-Host "第4步：安装Docker Compose..." -ForegroundColor Yellow
    $composeExists = Get-Command docker-compose -ErrorAction SilentlyContinue
    if ($composeExists) {
        Write-Host "Docker Compose已安装" -ForegroundColor Green
    } else {
        $composeUrl = "https://github.com/docker/compose/releases/download/v2.23.3/docker-compose-windows-x86_64.exe"
        $composePath = "C:\Program Files\Docker\docker-compose.exe"
        
        Write-Host "下载Docker Compose..." -ForegroundColor Yellow
        Invoke-WebRequest -Uri $composeUrl -OutFile $composePath
        
        Write-Host "Docker Compose安装完成" -ForegroundColor Green
    }

    # 第5步：启动Docker服务
    Write-Host ""
    Write-Host "第5步：启动Docker服务..." -ForegroundColor Yellow
    Start-Service docker -ErrorAction SilentlyContinue
    Set-Service docker -StartupType Automatic
    Write-Host "Docker服务已启动" -ForegroundColor Green

    # 验证安装
    Write-Host ""
    Write-Host "验证安装..." -ForegroundColor Yellow
    Start-Sleep -Seconds 3
    
    $dockerVersion = & docker --version 2>$null
    if ($dockerVersion) {
        Write-Host "✓ $dockerVersion" -ForegroundColor Green
    }
    
    $composeVersion = & docker-compose --version 2>$null
    if ($composeVersion) {
        Write-Host "✓ $composeVersion" -ForegroundColor Green
    }

    Write-Host ""
    Write-Host "=== 安装完成 ===" -ForegroundColor Green
    Write-Host ""
    if ($DisableHyperV) {
        Write-Host "重要：需要重启计算机使Hyper-V关闭生效" -ForegroundColor Yellow
        Write-Host "重启后运行：deploy-app.bat" -ForegroundColor Cyan
    } else {
        Write-Host "可以直接运行：deploy-app.bat" -ForegroundColor Cyan
    }

} catch {
    Write-Host ""
    Write-Host "安装过程出错：$($_.Exception.Message)" -ForegroundColor Red
    Write-Host "请检查网络连接或手动安装Docker" -ForegroundColor Yellow
}

Write-Host ""
Read-Host "按回车键退出"