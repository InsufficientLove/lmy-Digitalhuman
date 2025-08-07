#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
from pathlib import Path
import shutil
from datetime import datetime

def fix_syntax_error():
    """修复Python语法错误"""
    print("MuseTalk Python语法错误修复工具")
    print("=" * 50)
    
    script_dir = Path(__file__).parent
    service_file = script_dir / "MuseTalkEngine" / "ultra_fast_realtime_inference_v2.py"
    backup_file = script_dir / "MuseTalkEngine" / "ultra_fast_realtime_inference_v2.py.backup_20250807_111121"
    
    if not service_file.exists():
        print(f"❌ 服务文件不存在: {service_file}")
        return False
    
    if not backup_file.exists():
        print(f"❌ 备份文件不存在: {backup_file}")
        return False
    
    print(f"✅ 找到服务文件: {service_file}")
    print(f"✅ 找到备份文件: {backup_file}")
    
    try:
        # 恢复到备份文件
        print("恢复到原始备份文件...")
        shutil.copy2(backup_file, service_file)
        print("✅ 已恢复到备份文件")
        
        # 读取文件内容
        with open(service_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print("正在应用正确的修复...")
        
        # 首先添加兼容性函数 - 在类定义后的第一个方法前
        compatibility_function = """
    def safe_model_to_device(self, model, device, model_name="Model"):
        \"\"\"安全地将模型移动到设备并设置为eval模式\"\"\"
        try:
            # 检查是否有.to()方法
            if hasattr(model, 'to') and callable(getattr(model, 'to')):
                model = model.to(device)
            elif hasattr(model, 'model') and hasattr(model.model, 'to'):
                model.model = model.model.to(device)
            else:
                print(f"警告: {model_name}对象没有.to()方法，跳过设备转移")
            
            # 检查是否有.half()方法
            if hasattr(model, 'half') and callable(getattr(model, 'half')):
                model = model.half()
            elif hasattr(model, 'model') and hasattr(model.model, 'half'):
                model.model = model.model.half()
            else:
                print(f"警告: {model_name}对象没有.half()方法，跳过半精度转换")
            
            # 检查是否有.eval()方法
            if hasattr(model, 'eval') and callable(getattr(model, 'eval')):
                model = model.eval()
            elif hasattr(model, 'model') and hasattr(model.model, 'eval'):
                model.model = model.model.eval()
            else:
                print(f"警告: {model_name}对象没有.eval()方法，跳过eval模式设置")
            
            return model
        except Exception as e:
            print(f"错误: {model_name}设备转移失败: {e}")
            return model
"""
        
        # 在类的__init__方法前插入兼容性函数
        init_pattern = "    def __init__(self"
        if init_pattern in content:
            parts = content.split(init_pattern, 1)
            content = parts[0] + compatibility_function + "\n" + init_pattern + parts[1]
            print("✅ 已添加兼容性函数")
        
        # 替换模型优化代码
        old_code = """                    # 优化模型 - 半精度+编译优化
                    print(f"GPU{device_id} 开始模型优化...")
                    vae = vae.to(device).half().eval()
                    unet = unet.to(device).half().eval()
                    pe = pe.to(device).half().eval()"""
        
        new_code = """                    # 优化模型 - 半精度+编译优化 (兼容性修复)
                    print(f"GPU{device_id} 开始模型优化...")
                    vae = self.safe_model_to_device(vae, device, "VAE")
                    unet = self.safe_model_to_device(unet, device, "UNet")
                    pe = self.safe_model_to_device(pe, device, "PE")"""
        
        if old_code in content:
            content = content.replace(old_code, new_code)
            print("✅ 已替换模型优化代码")
        else:
            print("⚠️ 未找到完整代码块，尝试逐行替换...")
            content = content.replace(
                "vae = vae.to(device).half().eval()",
                "vae = self.safe_model_to_device(vae, device, \"VAE\")"
            )
            content = content.replace(
                "unet = unet.to(device).half().eval()",
                "unet = self.safe_model_to_device(unet, device, \"UNet\")"
            )
            content = content.replace(
                "pe = pe.to(device).half().eval()",
                "pe = self.safe_model_to_device(pe, device, \"PE\")"
            )
            print("✅ 已完成逐行替换")
        
        # 写入修复后的文件
        with open(service_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ 语法错误修复完成")
        return True
        
    except Exception as e:
        print(f"❌ 修复失败: {e}")
        return False

def main():
    if fix_syntax_error():
        print("\n🎉 语法错误修复完成！")
        print("现在可以重新启动MuseTalk服务了")
    else:
        print("\n❌ 修复失败")

if __name__ == "__main__":
    main()