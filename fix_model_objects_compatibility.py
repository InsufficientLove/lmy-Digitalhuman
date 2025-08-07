#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
from pathlib import Path
import shutil
from datetime import datetime

def backup_file(file_path):
    """备份文件"""
    backup_path = f"{file_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(file_path, backup_path)
    print(f"✅ 原文件已备份到: {backup_path}")
    return backup_path

def fix_model_objects_compatibility():
    """修复模型对象的兼容性问题"""
    print("MuseTalk 模型对象兼容性修复工具")
    print("=" * 50)
    
    script_dir = Path(__file__).parent
    service_file = script_dir / "MuseTalkEngine" / "ultra_fast_realtime_inference_v2.py"
    
    if not service_file.exists():
        print(f"❌ 服务文件不存在: {service_file}")
        return False
    
    print(f"✅ 找到服务文件: {service_file}")
    
    # 备份原文件
    backup_path = backup_file(service_file)
    
    try:
        # 读取原文件内容
        with open(service_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否已经修复过
        if "# MODEL_OBJECTS_COMPATIBILITY_FIXED" in content:
            print("✅ 文件已经修复过，无需重复修复")
            return True
        
        print("正在修复模型对象兼容性...")
        
        # 定义新的兼容性处理函数
        compatibility_function = '''    
    def safe_model_to_device(model, device, model_name="Model"):
        """安全地将模型移动到设备并设置为eval模式"""
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
'''
        
        # 找到类定义的位置插入兼容性函数
        class_pattern = "class UltraFastRealtimeInferenceV2:"
        if class_pattern in content:
            # 在类定义后插入兼容性函数
            parts = content.split(class_pattern, 1)
            if len(parts) == 2:
                # 找到类定义后的第一个方法定义位置
                after_class = parts[1]
                lines = after_class.split('\n')
                insert_index = 0
                for i, line in enumerate(lines):
                    if line.strip().startswith('def ') and i > 0:
                        insert_index = i
                        break
                
                # 插入兼容性函数
                lines.insert(insert_index, "    # MODEL_OBJECTS_COMPATIBILITY_FIXED: 添加模型对象兼容性处理函数")
                lines.insert(insert_index + 1, compatibility_function)
                
                content = parts[0] + class_pattern + '\n'.join(lines)
                print("✅ 已添加模型对象兼容性处理函数")
        
        # 替换模型优化代码
        old_optimization_code = '''                    # 优化模型 - 半精度+编译优化
                    print(f"GPU{device_id} 开始模型优化...")
                    vae = vae.to(device).half().eval()
                    unet = unet.to(device).half().eval()
                    pe = pe.to(device).half().eval()'''
        
        new_optimization_code = '''                    # MODEL_OBJECTS_COMPATIBILITY_FIXED: 兼容性模型优化
                    print(f"GPU{device_id} 开始模型优化...")
                    vae = self.safe_model_to_device(vae, device, "VAE")
                    unet = self.safe_model_to_device(unet, device, "UNet") 
                    pe = self.safe_model_to_device(pe, device, "PE")'''
        
        if old_optimization_code in content:
            content = content.replace(old_optimization_code, new_optimization_code)
            print("✅ 已替换模型优化代码为兼容性版本")
        else:
            # 如果之前已经部分修复过，尝试更精确的替换
            print("⚠️ 未找到完整的优化代码块，尝试逐行替换...")
            
            # 查找并替换各种可能的模型优化代码
            patterns_to_replace = [
                # 原始代码
                ("vae = vae.to(device).half().eval()", "vae = self.safe_model_to_device(vae, device, \"VAE\")"),
                ("unet = unet.to(device).half().eval()", "unet = self.safe_model_to_device(unet, device, \"UNet\")"),
                ("pe = pe.to(device).half().eval()", "pe = self.safe_model_to_device(pe, device, \"PE\")"),
                
                # 之前可能修复的代码
                ("if hasattr(vae, 'to') and callable(getattr(vae, 'to')):", "# 使用新的兼容性函数\n                    if True:  # 旧代码注释"),
                ("if hasattr(unet, 'to') and callable(getattr(unet, 'to')):", "# 使用新的兼容性函数\n                    if True:  # 旧代码注释"),
                ("if hasattr(pe, 'to') and callable(getattr(pe, 'to')):", "# 使用新的兼容性函数\n                    if True:  # 旧代码注释"),
            ]
            
            for old_pattern, new_pattern in patterns_to_replace:
                if old_pattern in content:
                    content = content.replace(old_pattern, new_pattern)
                    print(f"✅ 已替换: {old_pattern[:30]}...")
        
        # 清理重复的兼容性代码块
        lines = content.split('\n')
        cleaned_lines = []
        skip_until_else = False
        
        for i, line in enumerate(lines):
            if skip_until_else:
                if line.strip().startswith('else:') or line.strip().startswith('# 检查UNet对象') or line.strip().startswith('# 检查PE对象'):
                    continue
                elif not line.strip().startswith('vae') and not line.strip().startswith('elif') and not line.strip().startswith('print(f"警告: VAE'):
                    skip_until_else = False
                    cleaned_lines.append(line)
                continue
            
            if ('if hasattr(vae,' in line and 'to' in line) or 'elif hasattr(vae,' in line:
                # 发现旧的VAE处理代码，跳过整个代码块
                skip_until_else = True
                continue
            elif 'vae = self.safe_model_to_device(vae, device, "VAE")' in line:
                # 如果已经有新的代码，保留
                cleaned_lines.append(line)
            elif 'if True:  # 旧代码注释' in line:
                # 跳过注释行
                continue
            else:
                cleaned_lines.append(line)
        
        content = '\n'.join(cleaned_lines)
        
        # 写入修复后的文件
        with open(service_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ 模型对象兼容性修复完成")
        print(f"备份文件: {backup_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ 修复失败: {e}")
        # 恢复备份
        if backup_path and os.path.exists(backup_path):
            shutil.copy2(backup_path, service_file)
            print("已恢复原文件")
        return False

def main():
    print("开始修复MuseTalk模型对象兼容性问题...")
    
    if fix_model_objects_compatibility():
        print("\n🎉 修复完成！")
        print("\n修复内容:")
        print("- 添加了safe_model_to_device()函数，兼容不同的模型对象结构")
        print("- 修复了VAE/UNet/PE对象的.to()、.half()、.eval()方法调用")
        print("- 支持直接调用和通过.model属性调用两种模式")
        print("- 添加了详细的错误处理和警告信息")
        print("\n建议步骤:")
        print("1. 重新启动MuseTalk服务")
        print("2. 观察GPU初始化是否成功")
        print("3. 检查端口28888是否可达")
        
    else:
        print("\n❌ 修复失败")
        print("请检查错误信息或手动修改配置文件")

if __name__ == "__main__":
    main()