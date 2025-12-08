#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动检测模型路径脚本
用途：自动扫描 /opt/musetalk/models/ 并生成正确的 config_paths.py
"""

import os
from pathlib import Path


def scan_models_directory():
    """扫描模型目录"""
    model_root = Path("/opt/musetalk/models")
    
    print("=" * 60)
    print("🔍 自动检测模型路径")
    print("=" * 60)
    print(f"扫描目录: {model_root}\n")
    
    if not model_root.exists():
        print(f"❌ 错误: 模型目录不存在: {model_root}")
        print("请确认模型是否已下载到该路径")
        return None
    
    results = {
        'model_root': model_root,
        'unet_path': None,
        'unet_config': None,
        'vae_path': None,
        'whisper_dir': None,
        'whisper_model': None,
        'dwpose_path': None,
    }
    
    # 1. 查找 UNet 模型
    print("🔍 查找 UNet 模型...")
    musetalk_dir = model_root / "musetalk"
    if musetalk_dir.exists():
        print(f"  ✅ 找到 musetalk 目录: {musetalk_dir}")
        
        # 查找可能的 UNet 文件
        unet_candidates = [
            "pytorch_model.bin",
            "unet.pth",
            "model.safetensors",
            "diffusion_pytorch_model.bin",
            "model.bin",
        ]
        
        for candidate in unet_candidates:
            unet_path = musetalk_dir / candidate
            if unet_path.exists():
                size_mb = unet_path.stat().st_size / (1024 * 1024)
                print(f"  ✅ 找到 UNet 模型: {candidate} ({size_mb:.1f} MB)")
                results['unet_path'] = unet_path
                break
        
        # 查找配置文件
        config_candidates = ["musetalk.json", "config.json"]
        for candidate in config_candidates:
            config_path = musetalk_dir / candidate
            if config_path.exists():
                print(f"  ✅ 找到配置文件: {candidate}")
                results['unet_config'] = config_path
                break
        
        if not results['unet_path']:
            print(f"  ⚠️ 未找到 UNet 模型文件")
            print(f"  目录内容:")
            for item in musetalk_dir.iterdir():
                print(f"    - {item.name}")
    else:
        print(f"  ❌ 未找到 musetalk 目录")
    
    # 2. 查找 VAE 目录
    print("\n🔍 查找 VAE 目录...")
    vae_candidates = [
        "sd-vae-ft-mse",
        "sd-vae",
        "vae",
        "stable-diffusion-vae",
    ]
    
    for candidate in vae_candidates:
        vae_path = model_root / candidate
        if vae_path.exists() and vae_path.is_dir():
            file_count = len(list(vae_path.iterdir()))
            print(f"  ✅ 找到 VAE 目录: {candidate} ({file_count} 个文件)")
            results['vae_path'] = vae_path
            break
    
    if not results['vae_path']:
        print(f"  ⚠️ 未找到 VAE 目录")
        print(f"  尝试的目录名: {', '.join(vae_candidates)}")
    
    # 3. 查找 Whisper 模型
    print("\n🔍 查找 Whisper 模型...")
    whisper_dir = model_root / "whisper"
    if whisper_dir.exists():
        print(f"  ✅ 找到 whisper 目录: {whisper_dir}")
        results['whisper_dir'] = whisper_dir
        
        # 查找模型文件
        whisper_models = []
        for item in whisper_dir.iterdir():
            if item.suffix == '.pt':
                size_mb = item.stat().st_size / (1024 * 1024)
                whisper_models.append((item, size_mb))
        
        if whisper_models:
            print(f"  ✅ 找到 {len(whisper_models)} 个 Whisper 模型:")
            for model_path, size_mb in whisper_models:
                print(f"    - {model_path.name} ({size_mb:.1f} MB)")
            
            # 默认使用第一个（通常是 tiny 或 base）
            results['whisper_model'] = whisper_models[0][0]
            print(f"  → 推荐使用: {whisper_models[0][0].name}")
        else:
            print(f"  ⚠️ whisper 目录存在但未找到 .pt 文件")
    else:
        print(f"  ❌ 未找到 whisper 目录")
    
    # 4. 查找 DWPose（可选）
    print("\n🔍 查找 DWPose 目录...")
    dwpose_dir = model_root / "dwpose"
    if dwpose_dir.exists():
        print(f"  ✅ 找到 dwpose 目录: {dwpose_dir}")
        results['dwpose_path'] = dwpose_dir
    else:
        print(f"  ⚠️ 未找到 dwpose 目录 (可选)")
    
    return results


def generate_config(results):
    """生成配置文件内容"""
    if not results:
        return None
    
    config_template = f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MuseTalk 路径配置 - 自动生成
生成时间: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

import os
from pathlib import Path


class ModelPaths:
    """模型路径配置类 - 自动检测生成"""
    
    # ==================== 基础路径 ====================
    MODEL_ROOT = Path("{results['model_root']}")
    REPO_ROOT = Path("/opt/musetalk/repo")
    
    # ==================== 核心模型路径 ====================
    
    # 1. UNet 模型
'''
    
    if results['unet_path']:
        rel_path = results['unet_path'].relative_to(results['model_root'])
        config_template += f'''    UNET_PATH = MODEL_ROOT / "{rel_path.as_posix()}"
'''
    else:
        config_template += '''    UNET_PATH = MODEL_ROOT / "musetalk" / "pytorch_model.bin"  # ⚠️ 未检测到，请手动修改
'''
    
    if results['unet_config']:
        rel_path = results['unet_config'].relative_to(results['model_root'])
        config_template += f'''    UNET_CONFIG = MODEL_ROOT / "{rel_path.as_posix()}"
'''
    else:
        config_template += '''    UNET_CONFIG = MODEL_ROOT / "musetalk" / "musetalk.json"  # ⚠️ 未检测到，请手动修改
'''
    
    config_template += '''
    # 2. VAE 模型
'''
    
    if results['vae_path']:
        rel_path = results['vae_path'].relative_to(results['model_root'])
        config_template += f'''    VAE_PATH = MODEL_ROOT / "{rel_path.as_posix()}"
    VAE_TYPE = "{rel_path.name}"
'''
    else:
        config_template += '''    VAE_PATH = MODEL_ROOT / "sd-vae-ft-mse"  # ⚠️ 未检测到，请手动修改
    VAE_TYPE = "sd-vae-ft-mse"
'''
    
    config_template += '''
    # 3. Whisper 模型
'''
    
    if results['whisper_dir']:
        rel_path = results['whisper_dir'].relative_to(results['model_root'])
        config_template += f'''    WHISPER_DIR = MODEL_ROOT / "{rel_path.as_posix()}"
'''
    else:
        config_template += '''    WHISPER_DIR = MODEL_ROOT / "whisper"  # ⚠️ 未检测到，请手动修改
'''
    
    if results['whisper_model']:
        model_name = results['whisper_model'].name
        config_template += f'''    WHISPER_MODEL = WHISPER_DIR / "{model_name}"
'''
    else:
        config_template += '''    WHISPER_MODEL = WHISPER_DIR / "tiny.pt"  # ⚠️ 未检测到，请手动修改
'''
    
    config_template += '''
    # 4. DWPose 模型（可选）
'''
    
    if results['dwpose_path']:
        rel_path = results['dwpose_path'].relative_to(results['model_root'])
        config_template += f'''    DWPOSE_PATH = MODEL_ROOT / "{rel_path.as_posix()}"
'''
    else:
        config_template += '''    DWPOSE_PATH = MODEL_ROOT / "dwpose"
'''
    
    config_template += '''
    # ==================== 辅助方法 ====================
    
    @classmethod
    def validate_all(cls):
        """验证所有关键路径是否存在"""
        critical_paths = {
            "UNet": cls.UNET_PATH,
            "VAE": cls.VAE_PATH,
            "Whisper Directory": cls.WHISPER_DIR,
        }
        
        missing = []
        for name, path in critical_paths.items():
            if not path.exists():
                missing.append(f"{name}: {path}")
        
        return len(missing) == 0, missing
    
    @classmethod
    def setup_environment(cls):
        """设置环境变量"""
        os.environ['MODEL_PATH'] = str(cls.MODEL_ROOT)
        os.environ['MUSETALK_MODEL_PATH'] = str(cls.MODEL_ROOT)
        os.environ['VAE_PATH'] = str(cls.VAE_PATH)
        os.environ['UNET_PATH'] = str(cls.UNET_PATH)
        os.environ['WHISPER_PATH'] = str(cls.WHISPER_DIR)
        
        import sys
        musetalk_src = cls.REPO_ROOT / "MuseTalk"
        if musetalk_src.exists():
            if str(musetalk_src) not in sys.path:
                sys.path.insert(0, str(musetalk_src))
    
    @classmethod
    def print_config(cls):
        """打印当前配置"""
        print("=" * 60)
        print("📁 MuseTalk 路径配置 (自动生成)")
        print("=" * 60)
        print(f"模型根目录:  {cls.MODEL_ROOT}")
        print(f"代码根目录:  {cls.REPO_ROOT}")
        print()
        print("核心模型路径:")
        print(f"  UNet:      {cls.UNET_PATH}")
        print(f"  VAE:       {cls.VAE_PATH}")
        print(f"  Whisper:   {cls.WHISPER_DIR}")
        print(f"  DWPose:    {cls.DWPOSE_PATH}")
        print()
        
        is_valid, missing = cls.validate_all()
        if is_valid:
            print("✅ 所有关键路径验证通过")
        else:
            print("❌ 缺失以下路径:")
            for path in missing:
                print(f"   - {path}")
        print("=" * 60)


if __name__ == "__main__":
    ModelPaths.print_config()
    ModelPaths.setup_environment()
'''
    
    return config_template


def main():
    """主函数"""
    print("\n")
    print("╔═══════════════════════════════════════════════════════════╗")
    print("║                                                           ║")
    print("║        MuseTalk 模型路径自动检测工具                     ║")
    print("║                                                           ║")
    print("╚═══════════════════════════════════════════════════════════╝")
    print("\n")
    
    # 扫描模型目录
    results = scan_models_directory()
    
    if not results:
        print("\n❌ 扫描失败，无法生成配置")
        return
    
    # 生成配置
    print("\n" + "=" * 60)
    print("📝 生成配置文件")
    print("=" * 60)
    
    config_content = generate_config(results)
    
    # 保存配置
    output_path = Path("config_paths.py")
    
    # 如果已存在，备份
    if output_path.exists():
        backup_path = Path("config_paths.py.backup")
        print(f"⚠️ 配置文件已存在，备份到: {backup_path}")
        with open(output_path, 'r') as f:
            backup_content = f.read()
        with open(backup_path, 'w') as f:
            f.write(backup_content)
    
    # 写入新配置
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(config_content)
    
    print(f"✅ 配置文件已生成: {output_path.absolute()}")
    
    # 验证配置
    print("\n" + "=" * 60)
    print("🔍 验证生成的配置")
    print("=" * 60)
    
    try:
        # 动态导入生成的配置
        import importlib.util
        spec = importlib.util.spec_from_file_location("config_paths", output_path)
        config_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(config_module)
        
        # 打印配置
        config_module.ModelPaths.print_config()
        
        # 检查完整性
        is_valid, missing = config_module.ModelPaths.validate_all()
        
        if is_valid:
            print("\n✅ 🎉 配置完美！可以启动服务了！")
            print("\n下一步:")
            print("  python3 scripts/check_env.py  # 完整环境检查")
            print("  python3 main_realtime.py      # 启动服务")
        else:
            print("\n⚠️ 配置生成成功，但部分路径需要手动调整")
            print("\n请编辑 config_paths.py，修改标记为 ⚠️ 的路径")
    
    except Exception as e:
        print(f"\n⚠️ 验证失败: {e}")
        print("请手动检查生成的 config_paths.py 文件")


if __name__ == "__main__":
    main()
