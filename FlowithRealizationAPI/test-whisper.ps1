# Whisper Speech Recognition Test Script
# For testing openai-whisper installation and functionality

Write-Host "🔍 Starting Whisper Speech Recognition Test..." -ForegroundColor Green

# 1. Check Python environment
Write-Host "`n📋 Checking Python environment..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python version: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python first: https://www.python.org/downloads/" -ForegroundColor Red
    exit 1
}

# 2. Check pip
Write-Host "`n📋 Checking pip..." -ForegroundColor Yellow
try {
    $pipVersion = pip --version 2>&1
    Write-Host "✅ pip version: $pipVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ pip not installed" -ForegroundColor Red
    exit 1
}

# 3. Check if openai-whisper is installed
Write-Host "`n📋 Checking openai-whisper installation status..." -ForegroundColor Yellow
try {
    $whisperInfo = pip show openai-whisper 2>&1
    if ($whisperInfo -match "Version:") {
        Write-Host "✅ openai-whisper is installed" -ForegroundColor Green
        Write-Host $whisperInfo -ForegroundColor Cyan
    } else {
        Write-Host "❌ openai-whisper not installed" -ForegroundColor Red
        Write-Host "Installing openai-whisper..." -ForegroundColor Yellow
        pip install openai-whisper
    }
} catch {
    Write-Host "❌ Failed to check whisper installation status" -ForegroundColor Red
}

# 4. Test whisper command
Write-Host "`n📋 Testing whisper command..." -ForegroundColor Yellow
try {
    $whisperHelp = whisper --help 2>&1
    if ($whisperHelp -match "usage:") {
        Write-Host "✅ whisper command available" -ForegroundColor Green
    } else {
        Write-Host "❌ whisper command not available" -ForegroundColor Red
        Write-Host "Trying python -m whisper..." -ForegroundColor Yellow
        $pythonWhisper = python -m whisper --help 2>&1
        if ($pythonWhisper -match "usage:") {
            Write-Host "✅ python -m whisper available" -ForegroundColor Green
        } else {
            Write-Host "❌ python -m whisper also not available" -ForegroundColor Red
        }
    }
} catch {
    Write-Host "❌ Failed to test whisper command" -ForegroundColor Red
}

# 5. Create test audio file
Write-Host "`n📋 Checking test audio file..." -ForegroundColor Yellow
$testAudioPath = "test_audio.wav"
if (Test-Path $testAudioPath) {
    Write-Host "✅ Test audio file exists: $testAudioPath" -ForegroundColor Green
} else {
    Write-Host "⚠️  Test audio file does not exist, please manually create a WAV file for testing" -ForegroundColor Yellow
    Write-Host "   Filename: $testAudioPath" -ForegroundColor Cyan
}

# 6. If test audio exists, perform transcription test
if (Test-Path $testAudioPath) {
    Write-Host "`n📋 Starting speech transcription test..." -ForegroundColor Yellow
    try {
        $startTime = Get-Date
        Write-Host "Executing command: whisper `"$testAudioPath`" --model base --language zh --output_format json" -ForegroundColor Cyan
        
        $result = whisper "$testAudioPath" --model base --language zh --output_format json 2>&1
        
        $endTime = Get-Date
        $duration = ($endTime - $startTime).TotalSeconds
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Speech transcription successful! Time taken: $duration seconds" -ForegroundColor Green
            Write-Host "Transcription result:" -ForegroundColor Cyan
            Write-Host $result -ForegroundColor White
        } else {
            Write-Host "❌ Speech transcription failed" -ForegroundColor Red
            Write-Host "Error message:" -ForegroundColor Red
            Write-Host $result -ForegroundColor Red
        }
    } catch {
        Write-Host "❌ Speech transcription test failed: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# 7. Check environment variables
Write-Host "`n📋 Checking environment variables..." -ForegroundColor Yellow
$path = $env:PATH
if ($path -match "Python") {
    Write-Host "✅ PATH contains Python path" -ForegroundColor Green
} else {
    Write-Host "⚠️  PATH may be missing Python path" -ForegroundColor Yellow
}

Write-Host "`n🎯 Test completed!" -ForegroundColor Green
Write-Host "If you encounter issues, please ensure:" -ForegroundColor Cyan
Write-Host "1. Python is properly installed" -ForegroundColor White
Write-Host "2. openai-whisper is installed: pip install openai-whisper" -ForegroundColor White
Write-Host "3. whisper command is available in PATH" -ForegroundColor White
Write-Host "4. Sufficient disk space and memory" -ForegroundColor White 