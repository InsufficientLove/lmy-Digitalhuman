# CUDA 安装指南

## 版本选择建议

### 1. Whisper 兼容性
- Whisper 推荐 CUDA 11.7 或 11.8
- PyTorch 2.0+ 支持 CUDA 11.7/11.8/12.1

### 2. SadTalker 兼容性
- SadTalker 通常使用 CUDA 11.3-11.8
- 推荐使用 CUDA 11.7 或 11.8（最佳兼容性）

## 本地开发环境

### Windows 安装步骤
1. 下载 CUDA Toolkit 11.8：https://developer.nvidia.com/cuda-11-8-0-download-archive
2. 下载对应的 cuDNN：https://developer.nvidia.com/cudnn
3. 安装 CUDA Toolkit（默认路径即可）
4. 解压 cuDNN 到 CUDA 安装目录

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
# Ubuntu 20.04/22.04
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/cuda-keyring_1.0-1_all.deb
sudo dpkg -i cuda-keyring_1.0-1_all.deb
sudo apt-get update
sudo apt-get -y install cuda-11-8
```

## 环境变量配置
```bash
# 添加到 ~/.bashrc 或 /etc/environment
export PATH=/usr/local/cuda-11.8/bin:$PATH
export LD_LIBRARY_PATH=/usr/local/cuda-11.8/lib64:$LD_LIBRARY_PATH
```