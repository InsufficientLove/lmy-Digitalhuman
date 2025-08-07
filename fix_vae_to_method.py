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

def fix_vae_to_method():
    """修复VAE对象的.to()方法问题"""
    print("MuseTalk VAE对象 .to() 方法修复工具")
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
        if "# VAE_TO_METHOD_FIXED" in content:
            print("✅ 文件已经修复过，无需重复修复")
            return True
        
        # 修复VAE对象的.to()方法调用
        print("正在修复VAE对象的.to()方法...")
        
        # 查找并替换问题代码
        old_vae_code = """                    # 优化模型 - 半精度+编译优化
                    print(f"GPU{device_id} 开始模型优化...")
                    vae = vae.to(device).half().eval()
                    unet = unet.to(device).half().eval()
                    pe = pe.to(device).half().eval()"""
        
        new_vae_code = """                    # VAE_TO_METHOD_FIXED: 修复VAE对象的.to()方法
                    print(f"GPU{device_id} 开始模型优化...")
                    # 检查VAE对象是否有.to()方法，如果没有则使用.model.to()
                    if hasattr(vae, 'to') and callable(getattr(vae, 'to')):
                        vae = vae.to(device).half().eval()
                    elif hasattr(vae, 'model') and hasattr(vae.model, 'to'):
                        vae.model = vae.model.to(device).half().eval()
                        vae = vae.eval()
                    else:
                        print(f"警告: VAE对象既没有.to()方法也没有.model属性，跳过设备转移")
                    
                    # 检查UNet对象
                    if hasattr(unet, 'to') and callable(getattr(unet, 'to')):
                        unet = unet.to(device).half().eval()
                    elif hasattr(unet, 'model') and hasattr(unet.model, 'to'):
                        unet.model = unet.model.to(device).half().eval()
                        unet = unet.eval()
                    else:
                        print(f"警告: UNet对象既没有.to()方法也没有.model属性，跳过设备转移")
                    
                    # 检查PE对象
                    if hasattr(pe, 'to') and callable(getattr(pe, 'to')):
                        pe = pe.to(device).half().eval()
                    elif hasattr(pe, 'model') and hasattr(pe.model, 'to'):
                        pe.model = pe.model.to(device).half().eval()
                        pe = pe.eval()
                    else:
                        print(f"警告: PE对象既没有.to()方法也没有.model属性，跳过设备转移")"""
        
        if old_vae_code in content:
            content = content.replace(old_vae_code, new_vae_code)
            print("✅ 已修复VAE/UNet/PE对象的.to()方法调用")
        else:
            print("⚠️ 未找到预期的VAE代码，尝试其他修复方式...")
            
            # 更精确的替换
            lines = content.split('\n')
            new_lines = []
            for i, line in enumerate(lines):
                if "vae = vae.to(device).half().eval()" in line:
                    # 替换VAE行
                    indent = len(line) - len(line.lstrip())
                    new_lines.append(' ' * indent + '# VAE_TO_METHOD_FIXED: 修复VAE对象的.to()方法')
                    new_lines.append(' ' * indent + 'if hasattr(vae, \'to\') and callable(getattr(vae, \'to\')):')
                    new_lines.append(' ' * indent + '    vae = vae.to(device).half().eval()')
                    new_lines.append(' ' * indent + 'elif hasattr(vae, \'model\') and hasattr(vae.model, \'to\'):')
                    new_lines.append(' ' * indent + '    vae.model = vae.model.to(device).half().eval()')
                    new_lines.append(' ' * indent + '    vae = vae.eval()')
                    new_lines.append(' ' * indent + 'else:')
                    new_lines.append(' ' * indent + '    print(f"警告: VAE对象既没有.to()方法也没有.model属性")')
                elif "unet = unet.to(device).half().eval()" in line:
                    # 替换UNet行
                    indent = len(line) - len(line.lstrip())
                    new_lines.append(' ' * indent + 'if hasattr(unet, \'to\') and callable(getattr(unet, \'to\')):')
                    new_lines.append(' ' * indent + '    unet = unet.to(device).half().eval()')
                    new_lines.append(' ' * indent + 'elif hasattr(unet, \'model\') and hasattr(unet.model, \'to\'):')
                    new_lines.append(' ' * indent + '    unet.model = unet.model.to(device).half().eval()')
                    new_lines.append(' ' * indent + '    unet = unet.eval()')
                    new_lines.append(' ' * indent + 'else:')
                    new_lines.append(' ' * indent + '    print(f"警告: UNet对象既没有.to()方法也没有.model属性")')
                elif "pe = pe.to(device).half().eval()" in line:
                    # 替换PE行
                    indent = len(line) - len(line.lstrip())
                    new_lines.append(' ' * indent + 'if hasattr(pe, \'to\') and callable(getattr(pe, \'to\')):')
                    new_lines.append(' ' * indent + '    pe = pe.to(device).half().eval()')
                    new_lines.append(' ' * indent + 'elif hasattr(pe, \'model\') and hasattr(pe.model, \'to\'):')
                    new_lines.append(' ' * indent + '    pe.model = pe.model.to(device).half().eval()')
                    new_lines.append(' ' * indent + '    pe = pe.eval()')
                    new_lines.append(' ' * indent + 'else:')
                    new_lines.append(' ' * indent + '    print(f"警告: PE对象既没有.to()方法也没有.model属性")')
                else:
                    new_lines.append(line)
            
            content = '\n'.join(new_lines)
            print("✅ 已使用行级替换修复VAE/UNet/PE对象")
        
        # 写入修复后的文件
        with open(service_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ VAE对象.to()方法修复完成")
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
    print("开始修复MuseTalk VAE对象的.to()方法问题...")
    
    if fix_vae_to_method():
        print("\n🎉 修复完成！")
        print("\n修复内容:")
        print("- 修复了VAE对象没有.to()方法的问题")
        print("- 添加了对象方法检查，兼容不同的VAE/UNet/PE对象结构")
        print("- 如果对象有.model属性，则使用.model.to()方法")
        print("\n建议步骤:")
        print("1. 重新启动MuseTalk服务")
        print("2. 观察是否还有VAE相关错误")
        
    else:
        print("\n❌ 修复失败")
        print("请检查错误信息或手动修改配置文件")
    
    print("\n按任意键退出...")
    try:
        input()
    except:
        pass

if __name__ == "__main__":
    main()