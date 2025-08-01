# Windows Server 2019 Docker Engine 安装脚本
# 需要以管理员身份运行

Write-Host "========================================" -ForegroundColor Green
Write-Host "Windows Server Docker Engine 安装脚本" -ForegroundColor Green  
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# 检查管理员权限
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "❌ 此脚本需要管理员权限！请以管理员身份运行PowerShell" -ForegroundColor Red
    Read-Host "按任意键退出"
    exit 1
}

# 检查 Windows 版本
$osVersion = [System.Environment]::OSVersion.Version
Write-Host "🔍 检查系统版本: $($osVersion.ToString())" -ForegroundColor Yellow

if ($osVersion.Major -lt 10) {
    Write-Host "❌ 不支持的Windows版本，需要Windows Server 2016或更高版本" -ForegroundColor Red
    Read-Host "按任意键退出"
    exit 1
}

try {
    Write-Host ""
    Write-Host "📦 [1/5] 启用容器功能..." -ForegroundColor Yellow
    
    # 检查容器功能是否已启用
    $containerFeature = Get-WindowsFeature -Name Containers
    if ($containerFeature.InstallState -eq "Installed") {
        Write-Host "✅ 容器功能已启用" -ForegroundColor Green
    } else {
        Write-Host "正在启用容器功能..." -ForegroundColor Yellow
        Install-WindowsFeature -Name Containers -Restart:$false
        Write-Host "✅ 容器功能已启用" -ForegroundColor Green
    }

    Write-Host ""
    Write-Host "🐳 [2/5] 下载 Docker Engine..." -ForegroundColor Yellow
    
    # 获取最新版本
    $dockerReleases = Invoke-RestMethod -Uri "https://api.github.com/repos/docker/docker-ce/releases/latest"
    $latestVersion = $dockerReleases.tag_name.Substring(1)
    Write-Host "最新版本: $latestVersion" -ForegroundColor Cyan
    
    $dockerUrl = "https://download.docker.com/win/static/stable/x86_64/docker-$latestVersion.zip"
    $dockerZip = "$env:TEMP\docker.zip"
    
    Write-Host "正在下载: $dockerUrl" -ForegroundColor Yellow
    Invoke-WebRequest -Uri $dockerUrl -OutFile $dockerZip -UseBasicParsing
    Write-Host "✅ Docker Engine 下载完成" -ForegroundColor Green

    Write-Host ""
    Write-Host "📂 [3/5] 安装 Docker Engine..." -ForegroundColor Yellow
    
    # 解压到 Program Files
    $dockerPath = "$env:ProgramFiles\Docker"
    if (Test-Path $dockerPath) {
        Write-Host "移除旧版本..." -ForegroundColor Yellow
        Remove-Item $dockerPath -Recurse -Force
    }
    
    Expand-Archive -Path $dockerZip -DestinationPath $env:ProgramFiles -Force
    Rename-Item "$env:ProgramFiles\docker" "Docker"
    Remove-Item $dockerZip -Force
    
    # 添加到系统路径
    $currentPath = [Environment]::GetEnvironmentVariable("Path", [EnvironmentVariableTarget]::Machine)
    if ($currentPath -notlike "*$dockerPath*") {
        $newPath = "$currentPath;$dockerPath"
        [Environment]::SetEnvironmentVariable("Path", $newPath, [EnvironmentVariableTarget]::Machine)
        $env:Path = $newPath
        Write-Host "✅ Docker 路径已添加到系统PATH" -ForegroundColor Green
    }

    Write-Host ""
    Write-Host "🔧 [4/5] 配置 Docker 服务..." -ForegroundColor Yellow
    
    # 注册 Docker 服务
    & "$dockerPath\dockerd.exe" --register-service
    
    # 启动 Docker 服务
    Start-Service docker
    Set-Service docker -StartupType Automatic
    
    Write-Host "✅ Docker 服务已启动并设为自动启动" -ForegroundColor Green

    Write-Host ""
    Write-Host "🔗 [5/5] 安装 Docker Compose..." -ForegroundColor Yellow
    
    # 获取 Docker Compose 最新版本
    $composeReleases = Invoke-RestMethod -Uri "https://api.github.com/repos/docker/compose/releases/latest"
    $composeVersion = $composeReleases.tag_name
    $composeUrl = "https://github.com/docker/compose/releases/download/$composeVersion/docker-compose-windows-x86_64.exe"
    $composePath = "$dockerPath\docker-compose.exe"
    
    Write-Host "正在下载 Docker Compose $composeVersion..." -ForegroundColor Yellow
    Invoke-WebRequest -Uri $composeUrl -OutFile $composePath -UseBasicParsing
    Write-Host "✅ Docker Compose 安装完成" -ForegroundColor Green

    Write-Host ""
    Write-Host "🧪 验证安装..." -ForegroundColor Yellow
    
    # 验证 Docker
    $dockerVersion = & docker --version
    Write-Host "Docker: $dockerVersion" -ForegroundColor Cyan
    
    # 验证 Docker Compose  
    $composeVersion = & docker-compose --version
    Write-Host "Docker Compose: $composeVersion" -ForegroundColor Cyan
    
    # 测试 Docker
    Write-Host "正在测试 Docker..." -ForegroundColor Yellow
    & docker run hello-world
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "========================================" -ForegroundColor Green
        Write-Host "🎉 Docker 安装成功！" -ForegroundColor Green
        Write-Host "========================================" -ForegroundColor Green
        Write-Host ""
        Write-Host "下一步操作：" -ForegroundColor Yellow
        Write-Host "  1. 重新打开命令提示符（刷新PATH）" -ForegroundColor White
        Write-Host "  2. 运行: verify-docker-install.bat" -ForegroundColor White  
        Write-Host "  3. 运行: deploy-docker.bat" -ForegroundColor White
        Write-Host ""
    } else {
        Write-Host "❌ Docker 测试失败" -ForegroundColor Red
    }

} catch {
    Write-Host ""
    Write-Host "❌ 安装过程中发生错误：" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host ""
    Write-Host "故障排除建议：" -ForegroundColor Yellow
    Write-Host "  1. 确保以管理员身份运行" -ForegroundColor White
    Write-Host "  2. 检查网络连接" -ForegroundColor White
    Write-Host "  3. 禁用防病毒软件临时" -ForegroundColor White
    Write-Host "  4. 重启服务器后重试" -ForegroundColor White
}

Write-Host ""
Read-Host "按任意键退出"