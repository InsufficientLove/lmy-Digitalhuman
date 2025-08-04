#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MuseTalk目录结构检查脚本
用于诊断MuseTalk目录是否包含所有必要的文件
"""

import os
import sys
from pathlib import Path

def check_musetalk_structure():
    """检查MuseTalk目录结构"""
    print("=" * 50)
    print("MuseTalk目录结构检查")
    print("=" * 50)
    
    # 获取当前脚本所在目录的父目录（项目根目录）
    current_dir = Path(__file__).parent.parent
    musetalk_dir = current_dir / "MuseTalk"
    
    print(f"检查目录: {musetalk_dir}")
    print(f"目录存在: {musetalk_dir.exists()}")
    
    if not musetalk_dir.exists():
        print("❌ MuseTalk目录不存在！")
        return False
    
    # 必需的文件和目录
    required_items = [
        # scripts包
        "scripts/__init__.py",
        "scripts/inference.py",
        "scripts/preprocess.py",
        "scripts/realtime_inference.py",
        
        # 配置文件
        "configs/inference/test.yaml",
        
        # 模型目录（可能为空）
        "models",
        
        # 其他重要文件
        "requirements.txt",
        "README.md",
    ]
    
    missing_items = []
    existing_items = []
    
    for item in required_items:
        item_path = musetalk_dir / item
        if item_path.exists():
            existing_items.append(item)
            print(f"✅ {item}")
        else:
            missing_items.append(item)
            print(f"❌ {item}")
    
    print("\n" + "=" * 50)
    print("检查结果汇总")
    print("=" * 50)
    print(f"✅ 存在的文件/目录: {len(existing_items)}")
    print(f"❌ 缺失的文件/目录: {len(missing_items)}")
    
    if missing_items:
        print("\n缺失的关键文件:")
        for item in missing_items:
            print(f"  - {item}")
        
        print("\n建议解决方案:")
        if "scripts/__init__.py" in missing_items or "scripts/inference.py" in missing_items:
            print("1. 您的MuseTalk目录可能不是完整的官方仓库")
            print("2. 建议重新下载官方MuseTalk仓库:")
            print("   git clone https://github.com/TMElyralab/MuseTalk.git")
            print("   然后替换您当前的MuseTalk目录")
        
        return False
    else:
        print("\n🎉 MuseTalk目录结构完整！")
        
        # 检查scripts.inference是否可以导入
        print("\n测试Python模块导入...")
        try:
            sys.path.insert(0, str(musetalk_dir))
            import scripts.inference
            print("✅ scripts.inference模块导入成功！")
            return True
        except ImportError as e:
            print(f"❌ scripts.inference模块导入失败: {e}")
            return False

if __name__ == "__main__":
    success = check_musetalk_structure()
    sys.exit(0 if success else 1)