#!/usr/bin/env python3
import os
import re

# 修复1: 删除WhisperNetService.cs中的重复SpeechToTextResponse定义
whisper_file = "/workspace/LmyDigitalHuman/Services/Core/WhisperNetService.cs"
if os.path.exists(whisper_file):
    with open(whisper_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找并删除重复的类定义
    pattern = r'    // 扩展的响应模型\s*\n\s*public class SpeechToTextResponse\s*\{[^}]*\}\s*\n\}'
    content = re.sub(pattern, '}', content, flags=re.DOTALL)
    
    with open(whisper_file, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Fixed {whisper_file}")

# 修复2: 删除RealtimePipelineService.cs中的重复类定义
realtime_file = "/workspace/LmyDigitalHuman/Services/Core/RealtimePipelineService.cs"
if os.path.exists(realtime_file):
    with open(realtime_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 删除重复的RealtimePipelineConfig定义
    pattern = r'public class RealtimePipelineConfig\s*\{[^}]*TemplateImagePath[^}]*\}'
    content = re.sub(pattern, '// 使用IRealtimePipelineService中定义的RealtimePipelineConfig', content, flags=re.DOTALL)
    
    # 删除其他可能重复的类定义
    patterns = [
        r'public class AudioChunk\s*\{[^}]*\}',
        r'public class RealtimePipelineStatus\s*\{[^}]*SessionId[^}]*\}',
        r'public class RealtimeResultEventArgs\s*:\s*EventArgs\s*\{[^}]*\}'
    ]
    
    for pattern in patterns:
        if re.search(pattern, content, flags=re.DOTALL):
            content = re.sub(pattern, '', content, flags=re.DOTALL)
    
    with open(realtime_file, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Fixed {realtime_file}")

print("Compilation fixes applied!")