import sys
import os

def check_virtual_env():
    """检查是否在虚拟环境中"""
    in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    
    print("="*60)
    print("Python Environment Information")
    print("="*60)
    print(f"Python executable: {sys.executable}")
    print(f"Python version: {sys.version}")
    print(f"Virtual environment: {'Yes' if in_venv else 'No'}")
    
    if in_venv:
        print(f"Virtual env path: {sys.prefix}")
    
    print("="*60)
    print()

def check_package(package_name, import_name=None):
    if import_name is None:
        import_name = package_name
    
    try:
        module = __import__(import_name)
        version = getattr(module, '__version__', 'unknown')
        print(f"✅ {package_name}: {version}")
        return True
    except ImportError:
        print(f"❌ {package_name}: Not installed")
        return False

def check_cuda():
    """检查CUDA支持"""
    try:
        import torch
        print("\nCUDA Information:")
        print("-" * 40)
        print(f"PyTorch version: {torch.__version__}")
        print(f"CUDA available: {torch.cuda.is_available()}")
        
        if torch.cuda.is_available():
            print(f"CUDA version: {torch.version.cuda}")
            print(f"GPU count: {torch.cuda.device_count()}")
            
            for i in range(torch.cuda.device_count()):
                props = torch.cuda.get_device_properties(i)
                print(f"GPU {i}: {props.name}")
                print(f"  Memory: {props.total_memory / 1024**3:.1f} GB")
                print(f"  Compute Capability: {props.major}.{props.minor}")
        else:
            print("❌ CUDA not available")
            
    except ImportError:
        print("❌ PyTorch not installed")

# 主检查流程
check_virtual_env()

print("Checking MuseTalk Dependencies...")
print("-" * 40)

# 核心依赖
core_packages = [
    ('OpenCV', 'cv2'),
    ('NumPy', 'numpy'),
    ('PyTorch', 'torch'),
    ('Pillow', 'PIL'),
    ('TorchAudio', 'torchaudio'),
    ('TorchVision', 'torchvision'),
]

# 音频处理
audio_packages = [
    ('Librosa', 'librosa'),
    ('SoundFile', 'soundfile'),
    ('Resampy', 'resampy'),
]

# 深度学习
ml_packages = [
    ('Transformers', 'transformers'),
    ('Diffusers', 'diffusers'),
    ('Accelerate', 'accelerate'),
]

# 其他依赖
other_packages = [
    ('Face Alignment', 'face_alignment'),
    ('ImageIO', 'imageio'),
    ('OmegaConf', 'omegaconf'),
    ('Einops', 'einops'),
    ('TQDM', 'tqdm'),
    ('Requests', 'requests'),
]

# 可选优化包
optional_packages = [
    ('XFormers', 'xformers'),
    ('Flash Attention', 'flash_attn'),
    ('DeepSpeed', 'deepspeed'),
]

all_packages = core_packages + audio_packages + ml_packages + other_packages

missing = []
print("\nCore Dependencies:")
for package_name, import_name in all_packages:
    if not check_package(package_name, import_name):
        missing.append(package_name.lower())

print("\nOptional Optimizations:")
for package_name, import_name in optional_packages:
    check_package(package_name, import_name)

# CUDA检查
check_cuda()

# 总结
print("\n" + "="*60)
print("Summary")
print("="*60)

if missing:
    print(f"❌ Missing {len(missing)} core packages:")
    for pkg in missing:
        print(f"   - {pkg}")
    print("\nInstallation needed!")
else:
    print("✅ All core packages installed successfully!")
    print("✅ Ready for MuseTalk!")

print("\nIf you see any missing packages, run:")
print("   setup-musetalk-basic.bat")
print("or setup-musetalk-fixed.bat")
