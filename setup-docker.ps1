# Docker Engine 安装脚本 (Windows Server 2019)
# 适用于关闭Hyper-V的环境

param(
    [switch]$DisableHyperV = $false
)

Write-Host "========================================" -ForegroundColor Green
Write-Host "Docker Engine 安装脚本" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# 检查管理员权限
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "❌ 需要管理员权限！" -ForegroundColor Red
    Read-Host "按任意键退出"
    exit 1
}

try {
    # 1. 关闭Hyper-V (如果需要)
    if ($DisableHyperV) {
        Write-Host "🔧 [1/4] 关闭Hyper-V..." -ForegroundColor Yellow
        Disable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V-All -NoRestart
        Write-Host "✅ Hyper-V已关闭 (需要重启生效)" -ForegroundColor Green
    } else {
        Write-Host "ℹ️  [1/4] 跳过Hyper-V设置" -ForegroundColor Cyan
    }

    # 2. 启用容器功能
    Write-Host "📦 [2/4] 启用容器功能..." -ForegroundColor Yellow
    $containerFeature = Get-WindowsFeature -Name Containers
    if ($containerFeature.InstallState -ne "Installed") {
        Install-WindowsFeature -Name Containers -Restart:$false
        Write-Host "✅ 容器功能已启用" -ForegroundColor Green
    } else {
        Write-Host "✅ 容器功能已存在" -ForegroundColor Green
    }

    # 3. 下载并安装Docker Engine
    Write-Host "🐳 [3/4] 安装Docker Engine..." -ForegroundColor Yellow
    
    # 使用Chocolatey安装（更简单）
    if (!(Get-Command choco -ErrorAction SilentlyContinue)) {
        Write-Host "安装Chocolatey..." -ForegroundColor Yellow
        Set-ExecutionPolicy Bypass -Scope Process -Force
        [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
        iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
    }
    
    # 安装Docker
    choco install docker-engine -y
    choco install docker-compose -y
    
    Write-Host "✅ Docker Engine安装完成" -ForegroundColor Green

    # 4. 启动Docker服务
    Write-Host "🚀 [4/4] 启动Docker服务..." -ForegroundColor Yellow
    Start-Service docker
    Set-Service docker -StartupType Automatic
    Write-Host "✅ Docker服务已启动" -ForegroundColor Green

    # 验证安装
    Write-Host ""
    Write-Host "🧪 验证安装..." -ForegroundColor Yellow
    $dockerVersion = & docker --version
    $composeVersion = & docker-compose --version
    
    Write-Host "Docker: $dockerVersion" -ForegroundColor Cyan
    Write-Host "Docker Compose: $composeVersion" -ForegroundColor Cyan
    
    # 测试运行
    Write-Host "测试运行 hello-world..." -ForegroundColor Yellow
    & docker run hello-world
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "========================================" -ForegroundColor Green
        Write-Host "🎉 Docker Engine 安装成功！" -ForegroundColor Green
        Write-Host "========================================" -ForegroundColor Green
        Write-Host ""
        Write-Host "下一步：运行 deploy-app.bat 部署应用" -ForegroundColor Yellow
    }

} catch {
    Write-Host "❌ 安装失败: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Read-Host "按任意键退出"