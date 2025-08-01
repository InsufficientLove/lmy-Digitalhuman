# Windows Server 配置分析脚本
# 帮助决定Docker安装策略

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Windows Server Docker 配置分析" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查管理员权限
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "❌ 需要管理员权限运行此脚本" -ForegroundColor Red
    Read-Host "按任意键退出"
    exit 1
}

Write-Host "🔍 正在分析服务器配置..." -ForegroundColor Yellow
Write-Host ""

# 1. 检查Hyper-V状态
Write-Host "[1] Hyper-V 状态检查" -ForegroundColor Green
$hypervFeature = Get-WindowsFeature -Name Hyper-V
$hypervInstalled = $hypervFeature.InstallState -eq "Installed"

if ($hypervInstalled) {
    Write-Host "✅ Hyper-V 已安装" -ForegroundColor Green
    
    # 检查是否有运行的VM
    try {
        $runningVMs = Get-VM | Where-Object {$_.State -eq "Running"}
        if ($runningVMs.Count -gt 0) {
            Write-Host "⚠️  发现 $($runningVMs.Count) 个正在运行的虚拟机:" -ForegroundColor Yellow
            foreach ($vm in $runningVMs) {
                Write-Host "   - $($vm.Name) ($($vm.State))" -ForegroundColor White
            }
            $hasRunningVMs = $true
        } else {
            Write-Host "ℹ️  没有正在运行的虚拟机" -ForegroundColor Cyan
            $hasRunningVMs = $false
        }
    } catch {
        Write-Host "ℹ️  无法检查虚拟机状态（可能没有配置VM）" -ForegroundColor Cyan
        $hasRunningVMs = $false
    }
} else {
    Write-Host "❌ Hyper-V 未安装" -ForegroundColor Red
    $hasRunningVMs = $false
}

# 2. 检查容器功能
Write-Host ""
Write-Host "[2] 容器功能检查" -ForegroundColor Green
$containerFeature = Get-WindowsFeature -Name Containers
$containerInstalled = $containerFeature.InstallState -eq "Installed"

if ($containerInstalled) {
    Write-Host "✅ 容器功能已启用" -ForegroundColor Green
} else {
    Write-Host "❌ 容器功能未启用" -ForegroundColor Red
}

# 3. 检查现有Docker安装
Write-Host ""
Write-Host "[3] Docker 安装检查" -ForegroundColor Green
try {
    $dockerVersion = & docker --version 2>$null
    if ($dockerVersion) {
        Write-Host "✅ Docker 已安装: $dockerVersion" -ForegroundColor Green
        $dockerInstalled = $true
    } else {
        Write-Host "❌ Docker 未安装" -ForegroundColor Red
        $dockerInstalled = $false
    }
} catch {
    Write-Host "❌ Docker 未安装" -ForegroundColor Red
    $dockerInstalled = $false
}

# 4. 检查服务器角色
Write-Host ""
Write-Host "[4] 服务器角色分析" -ForegroundColor Green
$installedRoles = Get-WindowsFeature | Where-Object {$_.InstallState -eq "Installed" -and $_.FeatureType -eq "Role"}
Write-Host "已安装的服务器角色:" -ForegroundColor Cyan
foreach ($role in $installedRoles) {
    Write-Host "   - $($role.DisplayName)" -ForegroundColor White
}

# 5. 系统资源检查
Write-Host ""
Write-Host "[5] 系统资源检查" -ForegroundColor Green
$totalRAM = [math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1GB, 2)
$cpu = Get-CimInstance Win32_Processor
Write-Host "内存: $totalRAM GB" -ForegroundColor Cyan
Write-Host "CPU: $($cpu.Name) ($($cpu.NumberOfCores) 核心)" -ForegroundColor Cyan

# 6. 分析和建议
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "📋 配置建议" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

if ($hasRunningVMs) {
    Write-Host ""
    Write-Host "🚨 重要发现：您有正在运行的虚拟机" -ForegroundColor Red
    Write-Host ""
    Write-Host "推荐方案：" -ForegroundColor Yellow
    Write-Host "✅ 保持 Hyper-V 启用" -ForegroundColor Green
    Write-Host "✅ 使用 Windows 容器模式" -ForegroundColor Green
    Write-Host "✅ Docker 可以与 Hyper-V 共存" -ForegroundColor Green
    Write-Host ""
    Write-Host "执行步骤：" -ForegroundColor Yellow
    Write-Host "1. 不要关闭 Hyper-V" -ForegroundColor White
    Write-Host "2. 启用容器功能" -ForegroundColor White
    Write-Host "3. 安装 Docker Engine" -ForegroundColor White
    Write-Host "4. 配置为 Windows 容器模式" -ForegroundColor White
    
} elseif ($hypervInstalled -and -not $hasRunningVMs) {
    Write-Host ""
    Write-Host "💡 您的情况：Hyper-V已安装但未使用" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "两种选择：" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "方案A - 保持现状（推荐）：" -ForegroundColor Green
    Write-Host "✅ 保持 Hyper-V 启用" -ForegroundColor White
    Write-Host "✅ 启用容器功能" -ForegroundColor White
    Write-Host "✅ 安装 Docker Engine" -ForegroundColor White
    Write-Host "✅ 未来可以随时使用VM" -ForegroundColor White
    Write-Host ""
    Write-Host "方案B - 精简配置：" -ForegroundColor Cyan
    Write-Host "⚠️  关闭 Hyper-V" -ForegroundColor White
    Write-Host "✅ 启用容器功能" -ForegroundColor White
    Write-Host "✅ 安装 Docker Engine" -ForegroundColor White
    Write-Host "⚠️  无法使用虚拟机" -ForegroundColor White
    
} else {
    Write-Host ""
    Write-Host "✅ 标准服务器配置" -ForegroundColor Green
    Write-Host ""
    Write-Host "推荐方案：" -ForegroundColor Yellow
    Write-Host "✅ 启用容器功能" -ForegroundColor Green
    Write-Host "✅ 安装 Docker Engine" -ForegroundColor Green
    Write-Host "ℹ️  可选择是否启用 Hyper-V" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "🎯 推荐的下一步操作" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

if ($hasRunningVMs) {
    Write-Host "运行: install-docker-with-hyperv.bat" -ForegroundColor Yellow
} else {
    Write-Host "选择以下之一：" -ForegroundColor Yellow
    Write-Host "- install-docker-with-hyperv.bat (保持Hyper-V)" -ForegroundColor White
    Write-Host "- install-docker-server.bat (标准安装)" -ForegroundColor White
}

Write-Host ""
Write-Host "⚠️  重要提醒：" -ForegroundColor Red
Write-Host "- 如果您计划使用虚拟机，保持Hyper-V启用" -ForegroundColor White
Write-Host "- 如果这是纯Docker服务器，可以选择精简配置" -ForegroundColor White
Write-Host "- 变更前请备份重要数据" -ForegroundColor White

Write-Host ""
Read-Host "按任意键退出"