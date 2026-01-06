#!/usr/bin/env python3
"""
环境依赖检查和自动修复脚本
检测缺失的OpenMMLab依赖并自动安装
"""

import subprocess
import sys
import importlib


def check_module(module_name, display_name=None):
    """检查模块是否已安装"""
    if display_name is None:
        display_name = module_name
    
    try:
        mod = importlib.import_module(module_name)
        version = getattr(mod, '__version__', 'unknown')
        print(f"✅ {display_name}: {version}")
        return True
    except ImportError:
        print(f"❌ {display_name}: 未安装")
        return False


def install_openmim():
    """安装openmim"""
    print("\n📦 安装openmim...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-U", "openmim"], 
                      check=True, capture_output=True)
        print("✅ openmim安装成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ openmim安装失败: {e}")
        return False


def install_mmlab_package(package_name, version_spec=""):
    """使用mim安装OpenMMLab包"""
    print(f"\n📦 安装{package_name}...")
    try:
        cmd = ["mim", "install", f"{package_name}{version_spec}"]
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"✅ {package_name}安装成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {package_name}安装失败: {e}")
        return False


def main():
    print("=" * 60)
    print("MuseTalkEngine 依赖检查工具")
    print("=" * 60)
    
    # 检查关键依赖
    print("\n🔍 检查依赖状态...\n")
    
    deps_status = {
        'torch': check_module('torch', 'PyTorch'),
        'cv2': check_module('cv2', 'OpenCV'),
        'mmengine': check_module('mmengine', 'MMEngine'),
        'mmcv': check_module('mmcv', 'MMCV'),
        'mmdet': check_module('mmdet', 'MMDetection'),
        'mmpose': check_module('mmpose', 'MMPose'),
    }
    
    # 统计结果
    total = len(deps_status)
    installed = sum(deps_status.values())
    missing = total - installed
    
    print("\n" + "=" * 60)
    print(f"依赖状态: {installed}/{total} 已安装, {missing} 缺失")
    print("=" * 60)
    
    if missing == 0:
        print("\n✅ 所有依赖已安装，环境正常！")
        return 0
    
    # 询问是否自动修复
    print("\n⚠️ 检测到缺失依赖")
    response = input("是否自动安装缺失依赖？[Y/n]: ").strip().lower()
    
    if response in ['', 'y', 'yes']:
        print("\n🔧 开始自动修复...")
        
        # 确保openmim已安装
        if not check_module('openmim', 'OpenMIM'):
            if not install_openmim():
                print("\n❌ 无法安装openmim，请手动安装")
                return 1
        
        # 安装缺失的OpenMMLab包
        mmlab_packages = [
            ('mmengine', '>=0.8.4'),
            ('mmcv', '>=2.0.1'),
            ('mmdet', '>=3.1.0'),
            ('mmpose', '>=1.1.0'),
        ]
        
        for package, version_spec in mmlab_packages:
            if not deps_status.get(package, False):
                install_mmlab_package(package, version_spec)
        
        # 再次检查
        print("\n" + "=" * 60)
        print("验证修复结果")
        print("=" * 60)
        
        all_ok = True
        for package in ['mmengine', 'mmcv', 'mmdet', 'mmpose']:
            if not check_module(package):
                all_ok = False
        
        if all_ok:
            print("\n✅ 所有依赖已修复，环境正常！")
            return 0
        else:
            print("\n⚠️ 部分依赖安装失败，请手动检查")
            return 1
    else:
        print("\n跳过自动修复")
        print("\n手动安装命令:")
        print("  pip install -U openmim")
        print("  mim install mmengine")
        print("  mim install 'mmcv>=2.0.1'")
        print("  mim install 'mmdet>=3.1.0'")
        print("  mim install 'mmpose>=1.1.0'")
        return 1


if __name__ == "__main__":
    sys.exit(main())
