#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import torch
import json
from pathlib import Path
import subprocess
import platform

class MuseTalkDiagnostics:
    def __init__(self):
        self.script_dir = Path(__file__).parent
        self.musetalk_path = self.script_dir / "MuseTalk"
        self.models_path = self.musetalk_path / "models"
        
        # Expected model files and their properties
        self.expected_models = {
            "unet": {
                "path": self.models_path / "musetalkV15" / "unet.pth",
                "config_path": self.models_path / "musetalkV15" / "musetalk.json",
                "description": "MuseTalk UNet Model",
                "expected_size_mb": (350, 450),  # Min, Max range
                "critical": True
            },
            "vae_bin": {
                "path": self.models_path / "sd-vae" / "diffusion_pytorch_model.bin",
                "config_path": self.models_path / "sd-vae" / "config.json",
                "description": "VAE Model (.bin)",
                "expected_size_mb": (300, 350),
                "critical": True
            },
            "vae_safetensors": {
                "path": self.models_path / "sd-vae" / "diffusion_pytorch_model.safetensors",
                "description": "VAE Model (.safetensors)",
                "expected_size_mb": (300, 350),
                "critical": False  # Alternative to .bin
            },
            "dwpose": {
                "path": self.models_path / "dwpose" / "dw-ll_ucoco_384.pth",
                "description": "DWPose Model",
                "expected_size_mb": (180, 220),
                "critical": True
            }
        }
        
        self.issues = []
        self.solutions = []
    
    def add_issue(self, issue_type, description, solution=None):
        """Add an issue and its solution"""
        self.issues.append({
            "type": issue_type,
            "description": description,
            "solution": solution
        })
    
    def check_python_environment(self):
        """Check Python environment and dependencies"""
        print("=== Python环境检查 ===")
        
        # Check Python version
        python_version = sys.version
        print(f"Python版本: {python_version}")
        
        # Check PyTorch
        try:
            import torch
            print(f"✅ PyTorch版本: {torch.__version__}")
            print(f"CUDA可用: {torch.cuda.is_available()}")
            if torch.cuda.is_available():
                print(f"CUDA版本: {torch.version.cuda}")
                print(f"GPU数量: {torch.cuda.device_count()}")
                for i in range(torch.cuda.device_count()):
                    gpu_name = torch.cuda.get_device_name(i)
                    print(f"  GPU {i}: {gpu_name}")
        except ImportError:
            self.add_issue("dependency", "PyTorch未安装", 
                          "运行: pip install torch torchvision torchaudio")
        
        # Check other dependencies
        required_packages = ["requests", "numpy", "PIL", "cv2"]
        missing_packages = []
        
        for package in required_packages:
            try:
                if package == "PIL":
                    import PIL
                elif package == "cv2":
                    import cv2
                else:
                    __import__(package)
                print(f"✅ {package} 已安装")
            except ImportError:
                missing_packages.append(package)
                print(f"❌ {package} 未安装")
        
        if missing_packages:
            package_map = {"PIL": "Pillow", "cv2": "opencv-python"}
            install_packages = [package_map.get(pkg, pkg) for pkg in missing_packages]
            self.add_issue("dependency", f"缺少依赖包: {', '.join(missing_packages)}", 
                          f"运行: pip install {' '.join(install_packages)}")
    
    def check_directory_structure(self):
        """Check MuseTalk directory structure"""
        print("\n=== 目录结构检查 ===")
        
        if not self.musetalk_path.exists():
            print(f"❌ MuseTalk目录不存在: {self.musetalk_path}")
            self.add_issue("structure", "MuseTalk目录不存在", 
                          "运行: python setup_musetalk_models.py")
            return False
        
        print(f"✅ MuseTalk目录存在: {self.musetalk_path}")
        
        # Check models directory
        if not self.models_path.exists():
            print(f"❌ models目录不存在: {self.models_path}")
            self.add_issue("structure", "models目录不存在", 
                          "运行: python setup_musetalk_models.py")
            return False
        
        print(f"✅ models目录存在: {self.models_path}")
        
        # Check subdirectories
        required_dirs = ["musetalkV15", "sd-vae", "dwpose"]
        for dir_name in required_dirs:
            dir_path = self.models_path / dir_name
            if dir_path.exists():
                print(f"✅ {dir_name}目录存在")
            else:
                print(f"❌ {dir_name}目录不存在")
                self.add_issue("structure", f"{dir_name}目录不存在", 
                              "运行: python setup_musetalk_models.py")
        
        return True
    
    def check_model_files(self):
        """Check model files integrity"""
        print("\n=== 模型文件检查 ===")
        
        critical_missing = []
        
        for model_name, model_info in self.expected_models.items():
            model_path = model_info["path"]
            description = model_info["description"]
            expected_size = model_info["expected_size_mb"]
            is_critical = model_info["critical"]
            
            print(f"\n检查 {description}...")
            
            if not model_path.exists():
                status = "❌ 缺失"
                if is_critical:
                    critical_missing.append(model_name)
                self.add_issue("model_missing", f"{description}文件不存在: {model_path}", 
                              "运行: python setup_musetalk_models.py")
            else:
                # Check file size
                size_mb = model_path.stat().st_size / (1024 * 1024)
                min_size, max_size = expected_size
                
                if min_size <= size_mb <= max_size:
                    status = f"✅ 正常 ({size_mb:.1f}MB)"
                else:
                    status = f"⚠️ 大小异常 ({size_mb:.1f}MB, 期望: {min_size}-{max_size}MB)"
                    self.add_issue("model_corrupt", f"{description}文件大小异常", 
                                  "重新下载模型文件")
            
            print(f"  {description}: {status}")
            
            # Check config files if specified
            if "config_path" in model_info and model_path.exists():
                config_path = model_info["config_path"]
                if config_path.exists():
                    print(f"  配置文件: ✅ 存在")
                else:
                    print(f"  配置文件: ❌ 缺失")
                    self.add_issue("config_missing", f"{description}配置文件不存在", 
                                  "运行: python setup_musetalk_models.py")
        
        return len(critical_missing) == 0
    
    def test_model_loading(self):
        """Test model loading capabilities"""
        print("\n=== 模型加载测试 ===")
        
        # Test PyTorch tensor operations
        try:
            print("测试PyTorch基本操作...")
            x = torch.randn(2, 3, 4, 4)
            y = torch.nn.functional.relu(x)
            print("✅ PyTorch基本操作正常")
        except Exception as e:
            print(f"❌ PyTorch基本操作失败: {e}")
            self.add_issue("pytorch", "PyTorch基本操作失败", 
                          "重新安装PyTorch")
            return False
        
        # Test CUDA if available
        if torch.cuda.is_available():
            try:
                print("测试CUDA操作...")
                x_cuda = torch.randn(2, 3, 4, 4).cuda()
                y_cuda = torch.nn.functional.relu(x_cuda)
                print("✅ CUDA操作正常")
            except Exception as e:
                print(f"❌ CUDA操作失败: {e}")
                self.add_issue("cuda", "CUDA操作失败", 
                              "检查CUDA驱动和PyTorch CUDA版本兼容性")
        
        # Test model file loading
        unet_path = self.models_path / "musetalkV15" / "unet.pth"
        if unet_path.exists():
            try:
                print("测试UNet模型加载...")
                model_data = torch.load(unet_path, map_location='cpu')
                print("✅ UNet模型文件加载成功")
                
                # Check for meta tensor issue
                if isinstance(model_data, dict):
                    for key, value in model_data.items():
                        if hasattr(value, 'is_meta') and value.is_meta:
                            print(f"❌ 发现meta tensor: {key}")
                            self.add_issue("meta_tensor", "UNet模型包含meta tensor", 
                                          "运行: python fix_unet_model.py")
                            return False
                
            except Exception as e:
                print(f"❌ UNet模型加载失败: {e}")
                if "Cannot copy out of meta tensor" in str(e):
                    self.add_issue("meta_tensor", "UNet模型meta tensor错误", 
                                  "运行: python fix_unet_model.py 或重新下载模型")
                else:
                    self.add_issue("model_corrupt", "UNet模型文件损坏", 
                                  "重新下载UNet模型文件")
                return False
        
        return True
    
    def check_system_resources(self):
        """Check system resources"""
        print("\n=== 系统资源检查 ===")
        
        # Check disk space
        try:
            import shutil
            total, used, free = shutil.disk_usage(str(self.script_dir))
            free_gb = free / (1024**3)
            print(f"可用磁盘空间: {free_gb:.1f}GB")
            
            if free_gb < 2:
                self.add_issue("disk_space", "磁盘空间不足", 
                              "清理磁盘空间，至少需要2GB")
        except Exception as e:
            print(f"无法检查磁盘空间: {e}")
        
        # Check memory (approximate)
        try:
            if torch.cuda.is_available():
                for i in range(torch.cuda.device_count()):
                    memory_total = torch.cuda.get_device_properties(i).total_memory / (1024**3)
                    print(f"GPU {i} 显存: {memory_total:.1f}GB")
                    
                    if memory_total < 4:
                        self.add_issue("gpu_memory", f"GPU {i} 显存不足", 
                                      "MuseTalk建议至少4GB显存")
        except Exception as e:
            print(f"无法检查GPU显存: {e}")
    
    def generate_report(self):
        """Generate diagnostic report"""
        print("\n" + "="*50)
        print("=== 诊断报告 ===")
        print("="*50)
        
        if not self.issues:
            print("🎉 恭喜！没有发现问题，MuseTalk应该可以正常运行")
            return True
        
        print(f"发现 {len(self.issues)} 个问题:")
        
        # Group issues by type
        issue_groups = {}
        for issue in self.issues:
            issue_type = issue["type"]
            if issue_type not in issue_groups:
                issue_groups[issue_type] = []
            issue_groups[issue_type].append(issue)
        
        # Display issues by priority
        priority_order = ["structure", "model_missing", "meta_tensor", "model_corrupt", 
                         "config_missing", "dependency", "pytorch", "cuda", 
                         "disk_space", "gpu_memory"]
        
        for issue_type in priority_order:
            if issue_type in issue_groups:
                print(f"\n【{issue_type.upper()}】")
                for issue in issue_groups[issue_type]:
                    print(f"  ❌ {issue['description']}")
                    if issue['solution']:
                        print(f"     💡 解决方案: {issue['solution']}")
        
        # Generate action plan
        print("\n=== 推荐解决步骤 ===")
        
        if any(i["type"] in ["structure", "model_missing"] for i in self.issues):
            print("1. 首先运行模型设置脚本:")
            print("   python setup_musetalk_models.py")
        
        if any(i["type"] == "meta_tensor" for i in self.issues):
            print("2. 修复UNet模型meta tensor问题:")
            print("   python fix_unet_model.py")
        
        if any(i["type"] == "dependency" for i in self.issues):
            print("3. 安装缺失的依赖包:")
            missing_deps = [i["solution"] for i in self.issues if i["type"] == "dependency"]
            for dep in missing_deps:
                print(f"   {dep}")
        
        if any(i["type"] in ["model_corrupt", "config_missing"] for i in self.issues):
            print("4. 重新下载损坏的模型文件:")
            print("   python setup_musetalk_models.py")
        
        print("\n如果问题仍然存在，请查看详细的下载说明:")
        print("   cat MuseTalk/DOWNLOAD_INSTRUCTIONS.md")
        
        return False
    
    def run_full_diagnosis(self):
        """Run complete diagnosis"""
        print("MuseTalk 问题诊断工具")
        print("="*50)
        
        self.check_python_environment()
        self.check_directory_structure()
        self.check_model_files()
        self.test_model_loading()
        self.check_system_resources()
        
        return self.generate_report()

def main():
    diagnostics = MuseTalkDiagnostics()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--models-only":
            diagnostics.check_directory_structure()
            diagnostics.check_model_files()
            diagnostics.generate_report()
        elif sys.argv[1] == "--env-only":
            diagnostics.check_python_environment()
            diagnostics.generate_report()
        else:
            print("用法:")
            print("  python diagnose_musetalk_issue.py           # 完整诊断")
            print("  python diagnose_musetalk_issue.py --models-only  # 仅检查模型")
            print("  python diagnose_musetalk_issue.py --env-only     # 仅检查环境")
    else:
        success = diagnostics.run_full_diagnosis()
        
        if success:
            print("\n✅ 诊断完成，系统状态良好")
            sys.exit(0)
        else:
            print("\n❌ 发现问题，请按照上述建议进行修复")
            sys.exit(1)

if __name__ == "__main__":
    main()