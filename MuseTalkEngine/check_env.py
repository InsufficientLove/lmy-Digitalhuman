#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MuseTalk 环境自检脚本
目的：在启动服务前验证所有依赖和模型文件
服务器：Ubuntu 22.04, CUDA 12.9
"""

import os
import sys
from pathlib import Path
import importlib


# ==================== 颜色输出 ====================
class Colors:
    """终端颜色"""
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'


def print_header(text):
    """打印标题"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'=' * 60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'=' * 60}{Colors.END}\n")


def print_success(text):
    """打印成功信息"""
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")


def print_error(text):
    """打印错误信息"""
    print(f"{Colors.RED}❌ {text}{Colors.END}")


def print_warning(text):
    """打印警告信息"""
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.END}")


def print_info(text):
    """打印信息"""
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.END}")


# ==================== 检查函数 ====================

def check_python_version():
    """检查 Python 版本"""
    print_header("🐍 Python 版本检查")
    
    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.micro}"
    
    print(f"当前版本: Python {version_str}")
    
    if version.major == 3 and version.minor >= 9:
        print_success(f"Python 版本符合要求 (>= 3.9)")
        return True
    else:
        print_error(f"Python 版本过低，需要 >= 3.9，当前: {version_str}")
        return False


def check_dependencies():
    """检查依赖库"""
    print_header("📦 依赖库检查")
    
    # 关键依赖列表
    dependencies = {
        # 核心框架
        'torch': 'PyTorch 深度学习框架',
        'torchvision': 'PyTorch 视觉库',
        'torchaudio': 'PyTorch 音频库',
        
        # FastAPI
        'fastapi': 'FastAPI Web 框架',
        'uvicorn': 'ASGI 服务器',
        
        # 图像处理
        'cv2': 'OpenCV 图像处理 (opencv-python)',
        'PIL': 'Pillow 图像库',
        'imageio': '图像IO库',
        
        # 音频处理
        'librosa': '音频分析库',
        'soundfile': '音频文件IO',
        
        # 深度学习工具
        'transformers': 'Hugging Face Transformers',
        'diffusers': 'Diffusers 扩散模型库',
        'accelerate': '加速训练库',
        
        # 人脸处理
        'face_alignment': '人脸对齐库',
        
        # 工具库
        'numpy': 'NumPy 数值计算',
        'scipy': 'SciPy 科学计算',
        'tqdm': '进度条库',
        'yaml': 'YAML 解析 (pyyaml)',
    }
    
    missing = []
    installed = []
    
    for module, description in dependencies.items():
        try:
            # 特殊处理 cv2
            if module == 'cv2':
                import cv2
            # 特殊处理 PIL
            elif module == 'PIL':
                from PIL import Image
            # 特殊处理 yaml
            elif module == 'yaml':
                import yaml
            else:
                importlib.import_module(module)
            
            installed.append(module)
            print_success(f"{module:20s} - {description}")
        except ImportError:
            missing.append(module)
            print_error(f"{module:20s} - {description} [缺失]")
    
    print()
    if missing:
        print_error(f"缺失 {len(missing)} 个依赖库:")
        for m in missing:
            print(f"   - {m}")
        print()
        print_info("安装命令:")
        print(f"   pip install {' '.join(missing)}")
        return False
    else:
        print_success(f"所有 {len(installed)} 个依赖库已安装")
        return True


def check_cuda():
    """检查 CUDA 环境"""
    print_header("🎮 CUDA 环境检查")
    
    try:
        import torch
        
        # 检查 CUDA 是否可用
        cuda_available = torch.cuda.is_available()
        
        if not cuda_available:
            print_error("CUDA 不可用")
            print_warning("可能原因:")
            print("   1. NVIDIA 驱动未安装")
            print("   2. CUDA Toolkit 未安装")
            print("   3. PyTorch 安装的是 CPU 版本")
            return False
        
        print_success("CUDA 可用")
        
        # CUDA 版本
        cuda_version = torch.version.cuda
        print(f"   CUDA 版本: {cuda_version}")
        
        # GPU 数量
        gpu_count = torch.cuda.device_count()
        print(f"   GPU 数量: {gpu_count}")
        
        # 检查每个 GPU
        for i in range(gpu_count):
            gpu_name = torch.cuda.get_device_name(i)
            
            # 显存信息
            total_memory = torch.cuda.get_device_properties(i).total_memory / 1e9
            
            print(f"\n   GPU {i}: {gpu_name}")
            print(f"   └─ 显存: {total_memory:.1f} GB")
            
            # 尝试在该 GPU 上创建张量
            try:
                test_tensor = torch.randn(100, 100).to(f'cuda:{i}')
                allocated = torch.cuda.memory_allocated(i) / 1e9
                reserved = torch.cuda.memory_reserved(i) / 1e9
                print(f"   └─ 状态: 可用")
                print(f"   └─ 已分配: {allocated:.3f} GB")
                print(f"   └─ 已预留: {reserved:.3f} GB")
                del test_tensor
                torch.cuda.empty_cache()
                print_success(f"GPU {i} 测试通过")
            except Exception as e:
                print_error(f"GPU {i} 测试失败: {e}")
                return False
        
        # 检查是否有足够的显存（至少 8GB）
        if total_memory < 8:
            print_warning(f"显存较小 ({total_memory:.1f}GB < 8GB)，可能需要降低 batch_size")
        
        return True
    
    except ImportError:
        print_error("无法导入 PyTorch")
        return False
    except Exception as e:
        print_error(f"CUDA 检查失败: {e}")
        return False


def check_model_files():
    """检查模型文件完整性"""
    print_header("📁 模型文件检查")
    
    # 导入路径配置
    try:
        # 尝试从当前目录导入
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from config_paths import ModelPaths
        print_success("成功导入 config_paths.py")
    except ImportError as e:
        print_error(f"无法导入 config_paths.py: {e}")
        print_warning("请确保 config_paths.py 在当前目录")
        return False
    
    # 定义要检查的路径
    paths_to_check = {
        "模型根目录": ModelPaths.MODEL_ROOT,
        "UNet 模型": ModelPaths.UNET_PATH,
        "UNet 配置": ModelPaths.UNET_CONFIG,
        "VAE 目录": ModelPaths.VAE_PATH,
        "Whisper 目录": ModelPaths.WHISPER_DIR,
        "DWPose 目录": ModelPaths.DWPOSE_PATH,
    }
    
    missing = []
    found = []
    
    for name, path in paths_to_check.items():
        if path.exists():
            # 检查是文件还是目录
            if path.is_file():
                size = path.stat().st_size / (1024 * 1024)  # MB
                print_success(f"{name:20s} - {path} ({size:.1f} MB)")
            else:
                # 列出目录内容
                try:
                    contents = list(path.iterdir())
                    print_success(f"{name:20s} - {path} ({len(contents)} 个文件)")
                except Exception as e:
                    print_success(f"{name:20s} - {path}")
            found.append(name)
        else:
            print_error(f"{name:20s} - {path} [不存在]")
            missing.append((name, path))
    
    print()
    if missing:
        print_error(f"缺失 {len(missing)} 个模型文件/目录:")
        for name, path in missing:
            print(f"   {name}: {path}")
        print()
        print_warning("请检查 /opt/musetalk/models/ 目录结构")
        print_info("如果文件名不同，请修改 config_paths.py")
        return False
    else:
        print_success(f"所有 {len(found)} 个模型路径验证通过")
        return True


def check_musetalk_source():
    """检查 MuseTalk 源码"""
    print_header("📚 MuseTalk 源码检查")
    
    musetalk_paths = [
        Path("/opt/musetalk/repo/MuseTalk"),
        Path("/opt/musetalk/repo/backend_python/musetalk"),
        Path("./musetalk"),
    ]
    
    musetalk_found = None
    for path in musetalk_paths:
        if path.exists() and path.is_dir():
            musetalk_found = path
            break
    
    if musetalk_found is None:
        print_error("未找到 MuseTalk 源码目录")
        print_info("尝试的路径:")
        for p in musetalk_paths:
            print(f"   - {p}")
        return False
    
    print_success(f"MuseTalk 源码: {musetalk_found}")
    
    # 检查关键模块
    key_modules = [
        "utils/utils.py",
        "utils/preprocessing.py",
        "utils/blending.py",
        "utils/audio_processor.py",
    ]
    
    missing_modules = []
    for module in key_modules:
        module_path = musetalk_found / module
        if module_path.exists():
            print_success(f"  └─ {module}")
        else:
            print_error(f"  └─ {module} [缺失]")
            missing_modules.append(module)
    
    if missing_modules:
        print_error(f"缺失 {len(missing_modules)} 个关键模块")
        return False
    
    return True


def check_workspace():
    """检查工作空间"""
    print_header("🗂️  工作空间检查")
    
    # 检查关键文件
    key_files = [
        "main_realtime.py",
        "preprocess_assets.py",
        "config_paths.py",
        "requirements_realtime.txt",
    ]
    
    missing = []
    for file in key_files:
        path = Path(file)
        if path.exists():
            print_success(f"{file}")
        else:
            print_error(f"{file} [缺失]")
            missing.append(file)
    
    if missing:
        print_warning(f"缺失 {len(missing)} 个文件，可能不在正确的目录")
        print_info("请确保在 backend_python/ 目录下运行此脚本")
        return False
    
    return True


def generate_report(results):
    """生成检查报告"""
    print_header("📊 检查报告")
    
    total = len(results)
    passed = sum(results.values())
    failed = total - passed
    
    print(f"总检查项: {total}")
    print(f"通过: {Colors.GREEN}{passed}{Colors.END}")
    print(f"失败: {Colors.RED}{failed}{Colors.END}")
    print()
    
    if failed == 0:
        print_success("🎉 所有检查通过！环境配置完美！")
        print()
        print_info("下一步:")
        print("   1. python main_realtime.py")
        print("   2. 或使用: ./scripts/start_realtime_service.sh")
        return True
    else:
        print_error("❌ 部分检查未通过，请解决上述问题后再启动服务")
        print()
        print_info("常见问题解决:")
        print("   1. 依赖缺失: pip install -r requirements_realtime.txt")
        print("   2. CUDA 不可用: 检查 NVIDIA 驱动和 CUDA Toolkit")
        print("   3. 模型缺失: 检查 /opt/musetalk/models/ 目录")
        print("   4. 路径错误: 修改 config_paths.py")
        return False


# ==================== 主函数 ====================
def main():
    """主函数"""
    print(f"\n{Colors.BOLD}{Colors.MAGENTA}")
    print("╔═══════════════════════════════════════════════════════════╗")
    print("║                                                           ║")
    print("║        MuseTalk 环境自检脚本                              ║")
    print("║        Environment Pre-flight Check                       ║")
    print("║                                                           ║")
    print("╚═══════════════════════════════════════════════════════════╝")
    print(f"{Colors.END}")
    
    print_info("服务器环境: Ubuntu 22.04, CUDA 12.9")
    print_info("模型路径: /opt/musetalk/models/")
    
    # 执行检查
    results = {}
    
    results['Python 版本'] = check_python_version()
    results['依赖库'] = check_dependencies()
    results['CUDA 环境'] = check_cuda()
    results['模型文件'] = check_model_files()
    results['MuseTalk 源码'] = check_musetalk_source()
    results['工作空间'] = check_workspace()
    
    # 生成报告
    success = generate_report(results)
    
    # 返回状态码
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
