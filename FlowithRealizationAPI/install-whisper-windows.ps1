# Windows环境下安装OpenAI Whisper的PowerShell脚本

Write-Host "正在安装 OpenAI Whisper for Windows..." -ForegroundColor Green
Write-Host ""

# 定义Python路径
$pythonPath = "F:\AI\Python\python.exe"

try {
    # 检查Python是否可用
    Write-Host "[1/4] 检查Python环境..." -ForegroundColor Yellow
    $pythonVersion = & $pythonPath --version 2>&1
    Write-Host "Python版本: $pythonVersion" -ForegroundColor Cyan
    
    # 升级pip
    Write-Host ""
    Write-Host "[2/4] 升级pip..." -ForegroundColor Yellow
    & $pythonPath -m pip install --upgrade pip
    
    # 安装openai-whisper
    Write-Host ""
    Write-Host "[3/4] 安装 openai-whisper..." -ForegroundColor Yellow
    & $pythonPath -m pip install openai-whisper
    
    # 验证安装
    Write-Host ""
    Write-Host "[4/4] 验证安装..." -ForegroundColor Yellow
    $whisperHelp = & $pythonPath -m whisper --help 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "✅ OpenAI Whisper 安装成功！" -ForegroundColor Green
        Write-Host ""
        Write-Host "注意事项:" -ForegroundColor Yellow
        Write-Host "- 确保 FFmpeg 已安装并在 PATH 中" -ForegroundColor White
        Write-Host "- 如果没有 FFmpeg，请从 https://ffmpeg.org/download.html 下载" -ForegroundColor White
        Write-Host "- 或使用 winget install ffmpeg 安装" -ForegroundColor White
    } else {
        throw "Whisper验证失败"
    }
    
} catch {
    Write-Host ""
    Write-Host "❌ 安装失败: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    Write-Host "可能的解决方案:" -ForegroundColor Yellow
    Write-Host "1. 检查Python路径是否正确: $pythonPath" -ForegroundColor White
    Write-Host "2. 确保Python和pip正常工作" -ForegroundColor White
    Write-Host "3. 检查网络连接" -ForegroundColor White
    exit 1
}

Write-Host ""
Write-Host "按任意键继续..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")