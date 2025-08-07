#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
from pathlib import Path

# 设置路径
script_dir = Path(__file__).parent
musetalk_path = script_dir / "MuseTalk"
engine_path = script_dir / "MuseTalkEngine"

# 添加路径
sys.path.insert(0, str(musetalk_path))
sys.path.insert(0, str(engine_path))

# 切换工作目录
if musetalk_path.exists():
    os.chdir(musetalk_path)
    print(f"工作目录: {musetalk_path}")
else:
    print(f"❌ MuseTalk目录不存在: {musetalk_path}")
    sys.exit(1)

# 测试导入
try:
    print("测试导入 ultra_fast_realtime_inference_v2...")
    from ultra_fast_realtime_inference_v2 import start_ultra_fast_service, global_service
    print("✅ 导入成功")
    
    print("测试模型初始化...")
    result = global_service.initialize_models_ultra_fast()
    print(f"初始化结果: {result}")
    
except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()