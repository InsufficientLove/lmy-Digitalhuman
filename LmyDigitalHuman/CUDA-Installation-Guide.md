# CUDA 安装指南

## 版本选择建议

### 1. SadTalker 兼容性（优先考虑）
- SadTalker 官方使用 PyTorch 1.12.1 + CUDA 11.3
- 依赖库（如 kornia 0.6.8）与此版本兼容最佳
- **推荐使用 CUDA 11.3**

### 2. Whisper 兼容性
- Whisper 支持 CUDA 11.3-11.8
- 在 CUDA 11.3 环境下可正常运行

### 3. 综合建议
- **开发和生产环境统一使用 CUDA 11.3**
- 确保所有组件（SadTalker、Whisper、Edge-TTS）在同一环境

## 本地开发环境

### Windows 安装步骤
1. 下载 CUDA Toolkit 11.3：https://developer.nvidia.com/cuda-11-3-0-download-archive
2. 下载对应的 cuDNN 8.2：https://developer.nvidia.com/cudnn
3. 安装 CUDA Toolkit（默认路径即可）
4. 解压 cuDNN 到 CUDA 安装目录
5. 配置环境变量：
   - CUDA_PATH = C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.3
   - 添加到 PATH：%CUDA_PATH%\bin 和 %CUDA_PATH%\libnvvp

### 验证安装
```bash
nvcc --version
nvidia-smi
```

## 服务器部署

### 使用 NVIDIA Docker（推荐）
无需手动安装 CUDA，Docker 会自动处理：
```bash
# 安装 NVIDIA Container Toolkit
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker
```

### 传统安装（Ubuntu）
```bash
# Ubuntu 20.04
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/cuda-ubuntu2004.pin
sudo mv cuda-ubuntu2004.pin /etc/apt/preferences.d/cuda-repository-pin-600
wget https://developer.download.nvidia.com/compute/cuda/11.3.0/local_installers/cuda-repo-ubuntu2004-11-3-local_11.3.0-465.19.01-1_amd64.deb
sudo dpkg -i cuda-repo-ubuntu2004-11-3-local_11.3.0-465.19.01-1_amd64.deb
sudo apt-key add /var/cuda-repo-ubuntu2004-11-3-local/7fa2af80.pub
sudo apt-get update
sudo apt-get -y install cuda-11-3
```

## 环境变量配置
```bash
# 添加到 ~/.bashrc 或 /etc/environment
export PATH=/usr/local/cuda-11.3/bin:$PATH
export LD_LIBRARY_PATH=/usr/local/cuda-11.3/lib64:$LD_LIBRARY_PATH
export CUDA_HOME=/usr/local/cuda-11.3
```

## Python 环境配置
```bash
# 创建 SadTalker 虚拟环境
python3.8 -m venv sadtalker_env
source sadtalker_env/bin/activate

# 安装 PyTorch 1.12.1 + CUDA 11.3
pip install torch==1.12.1+cu113 torchvision==0.13.1+cu113 torchaudio==0.12.1 --extra-index-url https://download.pytorch.org/whl/cu113
```