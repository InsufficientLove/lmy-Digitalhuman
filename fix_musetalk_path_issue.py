#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import torch
from pathlib import Path

class MuseTalkPathFixer:
    def __init__(self):
        self.script_dir = Path(__file__).parent
        print(f"当前脚本目录: {self.script_dir}")
        
    def diagnose_path_issue(self):
        """诊断MuseTalk路径问题"""
        print("=== MuseTalk 路径诊断 ===")
        
        # 检查当前工作目录
        current_dir = os.getcwd()
        print(f"当前工作目录: {current_dir}")
        
        # 检查预期的MuseTalk路径
        expected_musetalk_path = os.path.join(self.script_dir, '..', 'MuseTalk')
        expected_musetalk_path = os.path.abspath(expected_musetalk_path)
        print(f"预期MuseTalk路径: {expected_musetalk_path}")
        
        if os.path.exists(expected_musetalk_path):
            print("✅ MuseTalk目录存在")
        else:
            print("❌ MuseTalk目录不存在于预期位置")
            
            # 搜索可能的MuseTalk位置
            possible_paths = [
                os.path.join(self.script_dir, 'MuseTalk'),  # 同级目录
                os.path.join(self.script_dir, '..', '..', 'MuseTalk'),  # 上上级目录
                '/workspace/MuseTalk',  # 绝对路径
            ]
            
            for path in possible_paths:
                abs_path = os.path.abspath(path)
                if os.path.exists(abs_path):
                    print(f"✅ 找到MuseTalk目录: {abs_path}")
                    return abs_path
                else:
                    print(f"❌ 不存在: {abs_path}")
        
        return expected_musetalk_path if os.path.exists(expected_musetalk_path) else None
    
    def check_model_files(self, musetalk_path):
        """检查模型文件"""
        print(f"\n=== 模型文件检查 (路径: {musetalk_path}) ===")
        
        if not musetalk_path or not os.path.exists(musetalk_path):
            print("❌ MuseTalk路径无效")
            return False
            
        models_path = os.path.join(musetalk_path, 'models')
        if not os.path.exists(models_path):
            print(f"❌ models目录不存在: {models_path}")
            return False
        
        print(f"✅ models目录存在: {models_path}")
        
        # 检查关键模型文件
        required_files = {
            "UNet模型": "models/musetalkV15/unet.pth",
            "VAE配置": "models/sd-vae/config.json", 
            "VAE模型(.bin)": "models/sd-vae/diffusion_pytorch_model.bin",
            "VAE模型(.safetensors)": "models/sd-vae/diffusion_pytorch_model.safetensors",
            "DWPose模型": "models/dwpose/dw-ll_ucoco_384.pth"
        }
        
        all_good = True
        for name, rel_path in required_files.items():
            full_path = os.path.join(musetalk_path, rel_path)
            if os.path.exists(full_path):
                size_mb = os.path.getsize(full_path) / (1024*1024)
                print(f"✅ {name}: {size_mb:.1f}MB")
            else:
                print(f"❌ {name}: 不存在 ({full_path})")
                all_good = False
        
        return all_good
    
    def test_model_import(self, musetalk_path):
        """测试模型导入"""
        print(f"\n=== 模型导入测试 ===")
        
        if not musetalk_path:
            print("❌ MuseTalk路径无效，跳过导入测试")
            return False
        
        # 添加MuseTalk路径到Python路径
        if musetalk_path not in sys.path:
            sys.path.insert(0, musetalk_path)
            print(f"✅ 添加路径到sys.path: {musetalk_path}")
        
        # 尝试导入MuseTalk模块
        try:
            print("测试导入 musetalk.utils.utils...")
            from musetalk.utils.utils import load_all_model
            print("✅ 成功导入 load_all_model")
            
            # 切换到MuseTalk目录（这很重要！）
            original_cwd = os.getcwd()
            os.chdir(musetalk_path)
            print(f"✅ 切换工作目录到: {musetalk_path}")
            
            try:
                print("测试加载模型...")
                # 测试模型加载（仅在CPU上，避免GPU冲突）
                vae, unet, pe = load_all_model(vae_type="sd-vae")
                print("✅ 模型加载成功！")
                
                # 测试meta tensor问题
                if hasattr(unet.model, 'state_dict'):
                    state_dict = unet.model.state_dict()
                    meta_tensors = []
                    for name, param in state_dict.items():
                        if hasattr(param, 'is_meta') and param.is_meta:
                            meta_tensors.append(name)
                    
                    if meta_tensors:
                        print(f"❌ 发现meta tensor: {len(meta_tensors)}个")
                        print(f"示例: {meta_tensors[:3]}")
                        return "meta_tensor_issue"
                    else:
                        print("✅ 没有发现meta tensor问题")
                        return True
                
            except Exception as e:
                print(f"❌ 模型加载失败: {e}")
                if "Cannot copy out of meta tensor" in str(e):
                    return "meta_tensor_issue"
                elif "No such file or directory" in str(e):
                    return "file_missing"
                else:
                    return f"other_error: {e}"
            finally:
                # 恢复原工作目录
                os.chdir(original_cwd)
                
        except ImportError as e:
            print(f"❌ 导入失败: {e}")
            return "import_error"
        
        return False
    
    def fix_meta_tensor_issue(self, musetalk_path):
        """修复meta tensor问题"""
        print(f"\n=== 修复Meta Tensor问题 ===")
        
        unet_path = os.path.join(musetalk_path, "models", "musetalkV15", "unet.pth")
        if not os.path.exists(unet_path):
            print(f"❌ UNet模型文件不存在: {unet_path}")
            return False
        
        try:
            print("正在检查UNet模型...")
            
            # 切换到MuseTalk目录
            original_cwd = os.getcwd()
            os.chdir(musetalk_path)
            
            # 加载模型数据
            model_data = torch.load(unet_path, map_location='cpu')
            print(f"✅ UNet模型文件读取成功")
            
            # 检查是否有meta tensor
            meta_tensor_count = 0
            if isinstance(model_data, dict):
                for key, value in model_data.items():
                    if torch.is_tensor(value) and hasattr(value, 'is_meta') and value.is_meta:
                        meta_tensor_count += 1
            
            if meta_tensor_count > 0:
                print(f"❌ 发现 {meta_tensor_count} 个meta tensor")
                print("正在修复...")
                
                # 备份原文件
                backup_path = unet_path + ".backup"
                if not os.path.exists(backup_path):
                    import shutil
                    shutil.copy2(unet_path, backup_path)
                    print(f"✅ 原文件已备份到: {backup_path}")
                
                # 修复meta tensor（通过重新保存实现）
                try:
                    # 导入UNet类
                    sys.path.insert(0, musetalk_path)
                    from musetalk.models.unet import UNet
                    
                    # 重新加载模型
                    config_path = os.path.join(musetalk_path, "models", "musetalkV15", "musetalk.json")
                    unet = UNet(unet_config=config_path, model_path=unet_path, device='cpu')
                    
                    # 保存修复后的模型
                    torch.save(unet.model.state_dict(), unet_path)
                    print("✅ Meta tensor问题已修复")
                    
                    # 验证修复结果
                    model_data_fixed = torch.load(unet_path, map_location='cpu')
                    meta_count_after = 0
                    for key, value in model_data_fixed.items():
                        if torch.is_tensor(value) and hasattr(value, 'is_meta') and value.is_meta:
                            meta_count_after += 1
                    
                    if meta_count_after == 0:
                        print("✅ 修复验证成功，没有meta tensor")
                        return True
                    else:
                        print(f"❌ 修复后仍有 {meta_count_after} 个meta tensor")
                        return False
                        
                except Exception as fix_error:
                    print(f"❌ 修复失败: {fix_error}")
                    # 恢复备份
                    if os.path.exists(backup_path):
                        import shutil
                        shutil.copy2(backup_path, unet_path)
                        print("已恢复原文件")
                    return False
            else:
                print("✅ 没有发现meta tensor问题")
                return True
                
        except Exception as e:
            print(f"❌ 检查失败: {e}")
            return False
        finally:
            os.chdir(original_cwd)
    
    def generate_path_fix_suggestions(self):
        """生成路径修复建议"""
        print(f"\n=== 路径修复建议 ===")
        
        print("基于分析，建议检查以下几点：")
        print()
        print("1. **工作目录设置**")
        print("   确保Python脚本在正确的工作目录中运行")
        print("   应该在包含MuseTalk文件夹的目录中运行")
        print()
        print("2. **MuseTalk目录位置**")
        print("   确认MuseTalk目录与MuseTalkEngine目录在同一级别")
        print("   正确的目录结构应该是：")
        print("   ```")
        print("   digitalhuman/lmy-Digitalhuman/")
        print("   ├── MuseTalk/")
        print("   │   └── models/")
        print("   └── MuseTalkEngine/")
        print("   ```")
        print()
        print("3. **Python路径**")
        print("   检查sys.path是否正确包含了MuseTalk目录")
        print()
        print("4. **模型文件权限**")
        print("   确保Python进程有读取模型文件的权限")
        print()
        print("5. **GPU内存**")
        print("   如果是GPU内存不足，考虑减少并行GPU数量")

def main():
    print("MuseTalk 路径和模型加载问题修复工具")
    print("="*50)
    
    fixer = MuseTalkPathFixer()
    
    # 诊断路径问题
    musetalk_path = fixer.diagnose_path_issue()
    
    if musetalk_path:
        # 检查模型文件
        models_ok = fixer.check_model_files(musetalk_path)
        
        if models_ok:
            # 测试模型导入
            import_result = fixer.test_model_import(musetalk_path)
            
            if import_result == "meta_tensor_issue":
                print("\n检测到meta tensor问题，尝试修复...")
                if fixer.fix_meta_tensor_issue(musetalk_path):
                    print("✅ Meta tensor问题修复成功！")
                    print("现在可以重新启动MuseTalk服务")
                else:
                    print("❌ Meta tensor问题修复失败")
            elif import_result == True:
                print("\n🎉 所有检查都通过！MuseTalk应该可以正常工作")
            else:
                print(f"\n❌ 发现问题: {import_result}")
        else:
            print("\n❌ 模型文件检查失败")
    else:
        print("\n❌ 无法找到MuseTalk目录")
    
    # 生成修复建议
    fixer.generate_path_fix_suggestions()

if __name__ == "__main__":
    main()