# 远程调试指南

## 使用 Docker 的优势

1. **环境一致性**：开发和生产环境完全一致
2. **无需手动安装 CUDA**：Docker 镜像自带 CUDA 环境
3. **快速部署**：一条命令即可在任何服务器上运行
4. **隔离性**：不影响宿主机环境

## 快速开始

### 1. 服务器准备
```bash
# 安装 Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 安装 NVIDIA Container Toolkit
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker

# 安装 docker-compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 2. 启动开发环境
```bash
# 克隆项目
git clone https://github.com/InsufficientLove/lmy-Digitalhuman.git
cd lmy-Digitalhuman/LmyDigitalHuman

# 启动开发容器
docker-compose up lmy-digital-human-dev
```

## VS Code 远程调试

### 1. 安装扩展
- Remote - SSH
- Remote - Containers
- C# Dev Kit

### 2. 连接到容器
```json
// .vscode/launch.json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": ".NET Core Attach",
            "type": "coreclr",
            "request": "attach",
            "processId": "${command:pickRemoteProcess}",
            "pipeTransport": {
                "pipeCwd": "${workspaceRoot}",
                "pipeProgram": "docker",
                "pipeArgs": ["exec", "-i", "lmy-digital-human-dev"],
                "debuggerPath": "/vsdbg/vsdbg"
            }
        }
    ]
}
```

### 3. 使用 SSH 隧道
```bash
# 本地端口转发
ssh -L 5000:localhost:5000 -L 4024:localhost:4024 user@server

# 或使用 VS Code Remote SSH
# 1. 按 F1，输入 "Remote-SSH: Connect to Host"
# 2. 输入 user@server
# 3. 打开项目文件夹
```

## Visual Studio 远程调试

### 1. 配置发布配置文件
```xml
<!-- Properties/PublishProfiles/RemoteDebug.pubxml -->
<Project>
  <PropertyGroup>
    <PublishProtocol>Container</PublishProtocol>
    <ContainerConnectionProtocol>Docker</ContainerConnectionProtocol>
    <DockerfilePath>Dockerfile.dev</DockerfilePath>
    <EnableRemoteDebugger>true</EnableRemoteDebugger>
    <RemoteDebugEnabled>true</RemoteDebugEnabled>
    <RemoteDebugMachine>server-ip:4024</RemoteDebugMachine>
  </PropertyGroup>
</Project>
```

### 2. 附加到进程
1. 调试 -> 附加到进程
2. 连接类型：Docker (Linux Container)
3. 连接目标：lmy-digital-human-dev
4. 选择 dotnet 进程

## 调试技巧

### 1. 实时日志查看
```bash
# 查看容器日志
docker logs -f lmy-digital-human-dev

# 进入容器内部
docker exec -it lmy-digital-human-dev bash

# 查看应用日志
tail -f /app/logs/realtime-digital-human-*.log
```

### 2. 热重载
开发容器已配置 `dotnet watch`，代码修改会自动重新编译运行。

### 3. 断点调试
- 在 VS Code 或 Visual Studio 中设置断点
- 通过远程调试附加到进程
- 正常使用调试功能（步进、查看变量等）

## 生产环境部署

```bash
# 构建并运行生产容器
docker-compose up -d lmy-digital-human

# 查看运行状态
docker-compose ps

# 更新部署
docker-compose pull
docker-compose up -d
```

## 常见问题

### 1. GPU 不可用
```bash
# 检查 NVIDIA 驱动
nvidia-smi

# 检查容器是否能访问 GPU
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

### 2. 远程调试连接失败
- 确保防火墙开放了端口 4024
- 检查容器是否正在运行
- 验证调试器路径是否正确

### 3. 性能问题
- 使用 `docker stats` 监控资源使用
- 调整 Docker 资源限制
- 考虑使用本地 SSD 存储临时文件

## 推荐工作流

1. **本地开发**：使用 `docker-compose up lmy-digital-human-dev`
2. **远程调试**：通过 VS Code Remote SSH 连接
3. **测试部署**：在测试服务器运行生产容器
4. **监控日志**：使用 `docker logs` 或集成日志系统
5. **快速迭代**：利用热重载和远程调试快速修复问题