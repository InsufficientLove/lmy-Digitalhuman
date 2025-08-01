# 简化版Docker安装脚本
param(
    [switch]$DisableHyperV = $false
)

Write-Host "Docker Engine 安装脚本" -ForegroundColor Green
Write-Host "======================" -ForegroundColor Green
Write-Host ""

# 检查管理员权限
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")
if (-not $isAdmin) {
    Write-Host "错误：需要管理员权限" -ForegroundColor Red
    Write-Host "请右键点击PowerShell选择'以管理员身份运行'" -ForegroundColor Yellow
    Read-Host "按任意键退出"
    exit 1
}

Write-Host "管理员权限检查通过" -ForegroundColor Green
Write-Host ""

try {
    # 步骤1：处理Hyper-V
    if ($DisableHyperV) {
        Write-Host "步骤1: 关闭Hyper-V..." -ForegroundColor Yellow
        $feature = Get-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V-All
        if ($feature.State -eq "Enabled") {
            Disable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V-All -NoRestart
            Write-Host "Hyper-V已关闭 (需要重启)" -ForegroundColor Green
        } else {
            Write-Host "Hyper-V已经关闭" -ForegroundColor Green
        }
    } else {
        Write-Host "步骤1: 保持Hyper-V设置" -ForegroundColor Cyan
    }

    # 步骤2：启用容器功能
    Write-Host ""
    Write-Host "步骤2: 启用Windows容器功能..." -ForegroundColor Yellow
    $containers = Get-WindowsOptionalFeature -Online -FeatureName Containers
    if ($containers.State -ne "Enabled") {
        Enable-WindowsOptionalFeature -Online -FeatureName Containers -All -NoRestart
        Write-Host "容器功能已启用" -ForegroundColor Green
    } else {
        Write-Host "容器功能已启用" -ForegroundColor Green
    }

    # 步骤3：安装Chocolatey
    Write-Host ""
    Write-Host "步骤3: 检查Chocolatey..." -ForegroundColor Yellow
    $choco = Get-Command choco -ErrorAction SilentlyContinue
    if (-not $choco) {
        Write-Host "安装Chocolatey..." -ForegroundColor Yellow
        Set-ExecutionPolicy Bypass -Scope Process -Force
        [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
        Invoke-Expression ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
        Write-Host "Chocolatey安装完成" -ForegroundColor Green
    } else {
        Write-Host "Chocolatey已安装" -ForegroundColor Green
    }

    # 步骤4：安装Docker
    Write-Host ""
    Write-Host "步骤4: 安装Docker..." -ForegroundColor Yellow
    $docker = Get-Command docker -ErrorAction SilentlyContinue
    if (-not $docker) {
        choco install docker-engine -y
        Write-Host "Docker安装完成" -ForegroundColor Green
    } else {
        Write-Host "Docker已安装" -ForegroundColor Green
    }

    # 步骤5：安装Docker Compose
    Write-Host ""
    Write-Host "步骤5: 安装Docker Compose..." -ForegroundColor Yellow
    $compose = Get-Command docker-compose -ErrorAction SilentlyContinue
    if (-not $compose) {
        choco install docker-compose -y
        Write-Host "Docker Compose安装完成" -ForegroundColor Green
    } else {
        Write-Host "Docker Compose已安装" -ForegroundColor Green
    }

    # 步骤6：启动服务
    Write-Host ""
    Write-Host "步骤6: 启动Docker服务..." -ForegroundColor Yellow
    Start-Service docker -ErrorAction SilentlyContinue
    Set-Service docker -StartupType Automatic
    Write-Host "Docker服务已启动" -ForegroundColor Green

    # 验证安装
    Write-Host ""
    Write-Host "验证安装..." -ForegroundColor Yellow
    Start-Sleep -Seconds 2
    
    try {
        $dockerVer = docker --version
        Write-Host "Docker: $dockerVer" -ForegroundColor Green
    } catch {
        Write-Host "Docker版本检查失败" -ForegroundColor Yellow
    }
    
    try {
        $composeVer = docker-compose --version
        Write-Host "Docker Compose: $composeVer" -ForegroundColor Green
    } catch {
        Write-Host "Docker Compose版本检查失败" -ForegroundColor Yellow
    }

    Write-Host ""
    Write-Host "=============" -ForegroundColor Green
    Write-Host "安装完成！" -ForegroundColor Green
    Write-Host "=============" -ForegroundColor Green
    Write-Host ""
    
    if ($DisableHyperV) {
        Write-Host "重要提示：" -ForegroundColor Yellow
        Write-Host "1. 需要重启计算机使Hyper-V设置生效" -ForegroundColor Yellow
        Write-Host "2. 重启后运行: deploy-app.bat" -ForegroundColor Cyan
    } else {
        Write-Host "下一步：运行 deploy-app.bat 部署应用" -ForegroundColor Cyan
    }

} catch {
    Write-Host ""
    Write-Host "安装失败: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "建议检查网络连接后重试" -ForegroundColor Yellow
}

Write-Host ""
Read-Host "按回车键退出"