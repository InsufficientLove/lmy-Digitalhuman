#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
脚本同步工具
自动将工作区的optimized_musetalk_inference.py同步到本地MuseTalk目录
"""

import os
import shutil
import sys
from pathlib import Path

def sync_script():
    """同步脚本到本地MuseTalk目录"""
    # 当前工作区的脚本
    source_script = Path(__file__).parent / "optimized_musetalk_inference.py"
    
    # 本地MuseTalk目录
    local_musetalk = Path(__file__).parent / "MuseTalk"
    target_script = local_musetalk / "optimized_musetalk_inference.py"
    
    if not source_script.exists():
        print(f"❌ 源脚本不存在: {source_script}")
        return False
    
    if not local_musetalk.exists():
        print(f"❌ 本地MuseTalk目录不存在: {local_musetalk}")
        print("💡 请确保你的本地MuseTalk目录存在")
        return False
    
    try:
        # 复制脚本
        shutil.copy2(source_script, target_script)
        print(f"✅ 脚本已同步: {source_script} → {target_script}")
        
        # 显示文件信息
        source_stat = source_script.stat()
        target_stat = target_script.stat()
        print(f"📊 源文件大小: {source_stat.st_size} bytes")
        print(f"📊 目标文件大小: {target_stat.st_size} bytes")
        
        return True
        
    except Exception as e:
        print(f"❌ 同步失败: {e}")
        return False

if __name__ == "__main__":
    print("🔄 开始同步optimized_musetalk_inference.py...")
    success = sync_script()
    sys.exit(0 if success else 1)