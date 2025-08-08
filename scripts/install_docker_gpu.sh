#!/usr/bin/env bash
set -euo pipefail

if ! command -v docker &>/dev/null; then
  echo "Installing Docker..."
  curl -fsSL https://get.docker.com | sh
  sudo usermod -aG docker $USER || true
fi

if ! command -v nvidia-smi &>/dev/null; then
  echo "[WARN] NVIDIA driver not detected. Please install the driver (e.g., 550+) and reboot."
fi

echo "Installing NVIDIA Container Toolkit..."
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker || true
sudo systemctl restart docker

echo "Done. Please re-login your shell to use docker without sudo (or run: newgrp docker)"