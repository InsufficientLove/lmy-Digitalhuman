import sys

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

print("Checking Python dependencies for MuseTalk...")
print(f"Python version: {sys.version}")
print()

packages = [
    ('OpenCV', 'cv2'),
    ('NumPy', 'numpy'),
    ('PyTorch', 'torch'),
    ('Pillow', 'PIL'),
    ('TorchAudio', 'torchaudio'),
    ('Librosa', 'librosa'),
    ('SciPy', 'scipy'),
    ('Matplotlib', 'matplotlib')
]

missing = []
for package_name, import_name in packages:
    if not check_package(package_name, import_name):
        missing.append(package_name.lower())

print()
if missing:
    print("Missing packages. Install with:")
    if 'torch' in missing or 'torchaudio' in missing:
        print("pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118")
    
    other_packages = [p for p in missing if p not in ['torch', 'torchaudio']]
    if other_packages:
        package_map = {
            'opencv': 'opencv-python',
            'pillow': 'pillow',
            'numpy': 'numpy',
            'librosa': 'librosa',
            'scipy': 'scipy',
            'matplotlib': 'matplotlib'
        }
        install_packages = [package_map.get(p, p) for p in other_packages]
        print(f"pip install {' '.join(install_packages)}")
else:
    print("✅ All required packages are installed!")
