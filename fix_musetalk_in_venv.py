#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
from pathlib import Path

class MuseTalkVenvFixer:
    def __init__(self):
        self.script_dir = Path(__file__).parent
        self.musetalk_dir = self.script_dir / "MuseTalk"
        
        # 虚拟环境路径
        self.venv_path = self.script_dir / "venv_musetalk"
        self.python_exe = self.venv_path / "Scripts" / "python.exe"
        
        print(f"脚本目录: {self.script_dir}")
        print(f"MuseTalk目录: {self.musetalk_dir}")
        print(f"虚拟环境: {self.venv_path}")
        print(f"Python可执行文件: {self.python_exe}")
    
    def check_venv(self):
        """检查虚拟环境"""
        print("\n=== 虚拟环境检查 ===")
        
        if not self.venv_path.exists():
            print(f"❌ 虚拟环境不存在: {self.venv_path}")
            return False
        
        if not self.python_exe.exists():
            print(f"❌ Python可执行文件不存在: {self.python_exe}")
            return False
        
        print(f"✅ 虚拟环境存在: {self.venv_path}")
        print(f"✅ Python可执行文件存在: {self.python_exe}")
        
        # 测试虚拟环境中的Python
        try:
            result = subprocess.run([str(self.python_exe), "--version"], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print(f"✅ Python版本: {result.stdout.strip()}")
            else:
                print(f"❌ Python版本检查失败: {result.stderr}")
                return False
        except Exception as e:
            print(f"❌ Python版本检查异常: {e}")
            return False
        
        return True
    
    def check_torch_in_venv(self):
        """检查虚拟环境中的PyTorch"""
        print("\n=== PyTorch检查 ===")
        
        check_torch_script = '''
import sys
import os
try:
    import torch
    print(f"[SUCCESS] PyTorch版本: {torch.__version__}")
    print(f"CUDA可用: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"CUDA版本: {torch.version.cuda}")
        print(f"GPU数量: {torch.cuda.device_count()}")
        for i in range(torch.cuda.device_count()):
            print(f"  GPU {i}: {torch.cuda.get_device_name(i)}")
    print("TORCH_CHECK_SUCCESS")
except ImportError as e:
    print(f"[ERROR] PyTorch未安装: {e}")
    print("TORCH_CHECK_FAILED")
except Exception as e:
    print(f"[ERROR] PyTorch检查失败: {e}")
    print("TORCH_CHECK_FAILED")
'''
        
        try:
            # 设置环境变量以使用UTF-8编码
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            
            result = subprocess.run([str(self.python_exe), "-c", check_torch_script], 
                                  capture_output=True, text=True, timeout=30, env=env)
            
            print(result.stdout)
            if result.stderr:
                print(f"错误信息: {result.stderr}")
            
            return "TORCH_CHECK_SUCCESS" in result.stdout
            
        except Exception as e:
            print(f"❌ PyTorch检查异常: {e}")
            return False
    
    def check_musetalk_files(self):
        """检查MuseTalk文件"""
        print("\n=== MuseTalk文件检查 ===")
        
        if not self.musetalk_dir.exists():
            print(f"❌ MuseTalk目录不存在: {self.musetalk_dir}")
            return False
        
        print(f"✅ MuseTalk目录存在: {self.musetalk_dir}")
        
        # 检查关键文件
        required_files = {
            "UNet模型": "models/musetalkV15/unet.pth",
            "UNet配置": "models/musetalkV15/musetalk.json",
            "VAE配置": "models/sd-vae/config.json",
            "VAE模型(.bin)": "models/sd-vae/diffusion_pytorch_model.bin",
            "DWPose模型": "models/dwpose/dw-ll_ucoco_384.pth"
        }
        
        all_good = True
        for name, rel_path in required_files.items():
            full_path = self.musetalk_dir / rel_path
            if full_path.exists():
                size_mb = full_path.stat().st_size / (1024*1024)
                print(f"✅ {name}: {size_mb:.1f}MB")
            else:
                print(f"❌ {name}: 不存在")
                all_good = False
        
        return all_good
    
    def test_unet_loading_in_venv(self):
        """在虚拟环境中测试UNet模型加载"""
        print("\n=== UNet模型加载测试 ===")
        
        test_script = f'''
import os
import sys
import torch
from pathlib import Path

# 切换到MuseTalk目录
musetalk_dir = Path(r"{self.musetalk_dir}")
os.chdir(musetalk_dir)
sys.path.insert(0, str(musetalk_dir))

print(f"工作目录: {{os.getcwd()}}")

try:
    # 测试基本的torch操作
    print("测试PyTorch基本操作...")
    x = torch.randn(2, 3, 4, 4)
    y = torch.nn.functional.relu(x)
    print("[SUCCESS] PyTorch基本操作正常")
    
    # 测试UNet模型文件加载
    unet_path = "models/musetalkV15/unet.pth"
    if os.path.exists(unet_path):
        print(f"正在测试加载UNet模型: {{unet_path}}")
        
        # 直接加载模型数据
        model_data = torch.load(unet_path, map_location='cpu')
        print("[SUCCESS] UNet模型文件读取成功")
        print(f"模型数据类型: {{type(model_data)}}")
        
        # 检查meta tensor
        meta_tensor_count = 0
        total_tensors = 0
        
        if isinstance(model_data, dict):
            for key, value in model_data.items():
                if torch.is_tensor(value):
                    total_tensors += 1
                    if hasattr(value, 'is_meta') and value.is_meta:
                        meta_tensor_count += 1
                        print(f"[ERROR] 发现meta tensor: {{key}}")
        
        print(f"总张量数: {{total_tensors}}")
        print(f"Meta张量数: {{meta_tensor_count}}")
        
        if meta_tensor_count > 0:
            print("META_TENSOR_DETECTED")
        else:
            print("NO_META_TENSOR")
        
        # 尝试导入MuseTalk模块
        try:
            print("\\n尝试导入MuseTalk模块...")
            from musetalk.utils.utils import load_all_model
            print("[SUCCESS] 成功导入load_all_model")
            
            # 测试模型加载
            print("测试完整模型加载...")
            vae, unet, pe = load_all_model(vae_type="sd-vae")
            print("[SUCCESS] 模型加载成功！")
            print("FULL_LOADING_SUCCESS")
            
        except Exception as load_error:
            print(f"[ERROR] 模型加载失败: {{load_error}}")
            if "Cannot copy out of meta tensor" in str(load_error):
                print("CONFIRMED_META_TENSOR_ISSUE")
            else:
                print(f"OTHER_LOADING_ERROR: {{load_error}}")
    else:
        print(f"[ERROR] UNet模型文件不存在: {{unet_path}}")
        print("UNET_FILE_MISSING")
        
except Exception as e:
    print(f"[ERROR] 测试失败: {{e}}")
    print(f"ERROR: {{e}}")
'''
        
        try:
            print("在虚拟环境中运行测试...")
            
            # 设置环境变量以使用UTF-8编码
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            
            result = subprocess.run([str(self.python_exe), "-c", test_script], 
                                  capture_output=True, text=True, timeout=60, env=env)
            
            print(result.stdout)
            if result.stderr:
                print(f"错误信息: {result.stderr}")
            
            # 分析结果
            output = result.stdout
            if "META_TENSOR_DETECTED" in output:
                return "meta_tensor_issue"
            elif "NO_META_TENSOR" in output and "FULL_LOADING_SUCCESS" in output:
                return "success"
            elif "CONFIRMED_META_TENSOR_ISSUE" in output:
                return "meta_tensor_issue"
            elif "UNET_FILE_MISSING" in output:
                return "file_missing"
            else:
                return "unknown_error"
                
        except Exception as e:
            print(f"❌ 测试异常: {e}")
            return "test_failed"
    
    def fix_meta_tensor_in_venv(self):
        """在虚拟环境中修复meta tensor问题"""
        print("\n=== Meta Tensor修复 ===")
        
        fix_script = f'''
import os
import sys
import torch
import shutil
from pathlib import Path

# 切换到MuseTalk目录
musetalk_dir = Path(r"{self.musetalk_dir}")
os.chdir(musetalk_dir)
sys.path.insert(0, str(musetalk_dir))

print(f"工作目录: {{os.getcwd()}}")

try:
    unet_path = "models/musetalkV15/unet.pth"
    
    if not os.path.exists(unet_path):
        print(f"❌ UNet模型文件不存在: {{unet_path}}")
        print("FIX_FAILED")
        exit(1)
    
    print(f"正在修复UNet模型: {{unet_path}}")
    
    # 备份原文件
    backup_path = unet_path + ".backup"
    if not os.path.exists(backup_path):
        shutil.copy2(unet_path, backup_path)
        print(f"✅ 原文件已备份到: {{backup_path}}")
    
    # 加载模型数据
    print("加载原始模型数据...")
    model_data = torch.load(unet_path, map_location='cpu')
    
    # 检查meta tensor
    meta_count = 0
    if isinstance(model_data, dict):
        for key, value in model_data.items():
            if torch.is_tensor(value) and hasattr(value, 'is_meta') and value.is_meta:
                meta_count += 1
    
    print(f"发现 {{meta_count}} 个meta tensor")
    
    if meta_count > 0:
        print("开始修复...")
        
        # 方法1: 尝试使用MuseTalk的UNet类重新保存
        try:
            from musetalk.models.unet import UNet
            
            config_path = "models/musetalkV15/musetalk.json"
            if os.path.exists(config_path):
                print("使用UNet类重新加载...")
                unet = UNet(unet_config=config_path, model_path=unet_path, device='cpu')
                
                # 保存修复后的模型
                torch.save(unet.model.state_dict(), unet_path)
                print("✅ 使用UNet类修复成功")
                
                # 验证修复结果
                model_data_fixed = torch.load(unet_path, map_location='cpu')
                meta_count_after = 0
                for key, value in model_data_fixed.items():
                    if torch.is_tensor(value) and hasattr(value, 'is_meta') and value.is_meta:
                        meta_count_after += 1
                
                if meta_count_after == 0:
                    print("✅ 修复验证成功")
                    print("FIX_SUCCESS")
                else:
                    print(f"❌ 修复后仍有 {{meta_count_after}} 个meta tensor")
                    print("FIX_PARTIAL")
            else:
                print(f"❌ 配置文件不存在: {{config_path}}")
                print("FIX_FAILED")
                
        except Exception as fix_error:
            print(f"❌ UNet类修复失败: {{fix_error}}")
            
            # 方法2: 简单的重新保存（移除meta tensor）
            try:
                print("尝试简单重新保存...")
                clean_data = {{}}
                for key, value in model_data.items():
                    if torch.is_tensor(value):
                        if hasattr(value, 'is_meta') and value.is_meta:
                            print(f"跳过meta tensor: {{key}}")
                        else:
                            clean_data[key] = value
                    else:
                        clean_data[key] = value
                
                torch.save(clean_data, unet_path)
                print("✅ 简单重新保存完成")
                print("FIX_SUCCESS")
                
            except Exception as simple_fix_error:
                print(f"❌ 简单修复也失败: {{simple_fix_error}}")
                # 恢复备份
                if os.path.exists(backup_path):
                    shutil.copy2(backup_path, unet_path)
                    print("已恢复原文件")
                print("FIX_FAILED")
    else:
        print("✅ 没有发现meta tensor问题")
        print("NO_META_TENSOR")
        
except Exception as e:
    print(f"❌ 修复过程异常: {{e}}")
    print("FIX_ERROR")
'''
        
        try:
            print("在虚拟环境中执行修复...")
            
            # 设置环境变量以使用UTF-8编码
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            
            result = subprocess.run([str(self.python_exe), "-c", fix_script], 
                                  capture_output=True, text=True, timeout=120, env=env)
            
            print(result.stdout)
            if result.stderr:
                print(f"错误信息: {result.stderr}")
            
            # 分析修复结果
            output = result.stdout
            if "FIX_SUCCESS" in output:
                return True
            elif "NO_META_TENSOR" in output:
                print("没有meta tensor问题，无需修复")
                return True
            else:
                return False
                
        except Exception as e:
            print(f"❌ 修复异常: {e}")
            return False
    
    def generate_batch_script(self):
        """生成批处理脚本，用于在虚拟环境中运行"""
        batch_script = f'''@echo off
chcp 65001 >nul
echo MuseTalk Meta Tensor 修复工具 (虚拟环境版本)
echo ================================================

cd /d "{self.script_dir}"

if not exist "{self.venv_path}" (
    echo [错误] 虚拟环境不存在: {self.venv_path}
    echo 请确保虚拟环境路径正确
    pause
    exit /b 1
)

if not exist "{self.python_exe}" (
    echo [错误] Python可执行文件不存在: {self.python_exe}
    echo 请检查虚拟环境是否正确安装
    pause
    exit /b 1
)

echo [成功] 使用虚拟环境: {self.venv_path}
echo [成功] Python路径: {self.python_exe}
echo.

echo 正在运行修复工具...
"{self.python_exe}" fix_musetalk_in_venv.py

echo.
echo 修复完成，按任意键退出...
pause
'''
        
        batch_file = self.script_dir / "run_fix_in_venv.bat"
        try:
            with open(batch_file, 'w', encoding='utf-8') as f:
                f.write(batch_script)
            print(f"✅ 批处理脚本已创建: {batch_file}")
            print("您可以直接双击运行 run_fix_in_venv.bat")
        except Exception as e:
            print(f"❌ 批处理脚本创建失败: {e}")
            print("将跳过批处理脚本创建，直接进行修复")
    
    def run_full_diagnosis_and_fix(self):
        """运行完整的诊断和修复流程"""
        print("MuseTalk Meta Tensor 修复工具 (虚拟环境版本)")
        print("="*60)
        
        # 检查虚拟环境
        if not self.check_venv():
            print("\n❌ 虚拟环境检查失败")
            return False
        
        # 检查PyTorch
        if not self.check_torch_in_venv():
            print("\n❌ PyTorch检查失败")
            return False
        
        # 检查MuseTalk文件
        if not self.check_musetalk_files():
            print("\n❌ MuseTalk文件检查失败")
            return False
        
        # 测试模型加载
        test_result = self.test_unet_loading_in_venv()
        
        if test_result == "meta_tensor_issue":
            print("\n🔧 检测到meta tensor问题，开始修复...")
            if self.fix_meta_tensor_in_venv():
                print("\n✅ Meta tensor问题修复成功！")
                print("现在可以重新启动MuseTalk服务")
                return True
            else:
                print("\n❌ Meta tensor问题修复失败")
                return False
        elif test_result == "success":
            print("\n🎉 所有检查都通过！MuseTalk应该可以正常工作")
            return True
        elif test_result == "file_missing":
            print("\n❌ UNet模型文件缺失")
            return False
        else:
            print(f"\n❌ 发现未知问题: {test_result}")
            return False

def main():
    fixer = MuseTalkVenvFixer()
    
    # 尝试生成批处理脚本（失败也继续）
    try:
        fixer.generate_batch_script()
    except Exception as e:
        print(f"❌ 批处理脚本生成失败: {e}")
        print("将直接进行修复，跳过批处理脚本生成")
    
    # 运行诊断和修复
    success = fixer.run_full_diagnosis_and_fix()
    
    if success:
        print("\n🎉 修复完成！")
        print("现在可以重新启动您的MuseTalk服务")
    else:
        print("\n❌ 修复失败，请检查上述错误信息")

if __name__ == "__main__":
    main()