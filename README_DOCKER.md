# Docker 一键部署（含 HTTPS）

## 前提
- Linux 服务器（推荐 Ubuntu 22.04+）
- 公网域名，并将 A 记录指向服务器 IP（用于自动签发 Let’s Encrypt 证书）
- NVIDIA 驱动 + nvidia-container-toolkit（GPU加速）

## 一次性安装
```bash
git clone https://github.com/InsufficientLove/lmy-Digitalhuman /opt/musetalk/repo
cd /opt/musetalk/repo
chmod +x scripts/*.sh

# 安装 Docker + NVIDIA 工具包（Ubuntu）
./scripts/install_docker_gpu.sh

# 创建目录并生成 .env 模板
./scripts/setup_linux.sh
```

编辑 `.env`：
```env
DOMAIN=your.domain.com
ACME_EMAIL=your-email@example.com
CUDA_VISIBLE_DEVICES=0,1
```

## 准备 MuseTalk 源码
- 该项目依赖上游 `MuseTalk` 源码作为子目录：`/opt/musetalk/repo/MuseTalk`
- 如果根目录下没有 `MuseTalk` 文件夹，请按以下任一方式准备：
  - 从你已有的环境拷贝 `MuseTalk` 目录到仓库根目录
  - 或者在仓库根目录克隆上游仓库（示例）：
    ```bash
    cd /opt/musetalk/repo
    git clone <YOUR_MUSETALK_REPO_URL> MuseTalk
    ```

## 准备模型
- 推荐直接把旧服务器的 `models` 整个目录拷贝到 `/opt/musetalk/models`
- 可参见 `scripts/download_models.sh`

## 启动
```bash
docker compose up -d --build
```
- 首次启动需要 1-2 分钟，Traefik 会通过 Let’s Encrypt 自动获取证书
- 访问 `https://your.domain.com/swagger`

## 更新代码（多机通用）
```bash
cd /opt/musetalk/repo
./scripts/deploy.sh
```

## 本地/内网测试选项
- 若没有域名，Chrome 仅在 `https` 或 `localhost` 下允许麦克风。可以：
  - 在服务器本机浏览器访问 `http://localhost:5000`（允许麦克风）
  - 或者自签证书（浏览器会有警告，需要手动信任）。如需我提供自签TLS的 Nginx/Caddy 示例，请告诉我你的场景（内网/多端访问）。

## GPU 与 BatchSize 建议（4090D 48G ×2）
- `LmyDigitalHuman/appsettings.Linux.json` 中默认 `BatchSize=8`
- 可在运行中根据日志观察内存与速度，适当调整（8~10 之间）

## 目录挂载
- `/opt/musetalk/models` → 模型目录
- `/opt/musetalk/videos` → 输出视频
- `/opt/musetalk/temp`   → 临时缓存

## 组件说明
- Traefik（:80/:443）：反向代理 + 自动 HTTPS
- lmy-digitalhuman（:5000）：.NET 8 Web 服务
- musetalk-python（:28888）：MuseTalk Python 推理服务

## 常见问题
- 证书未签发：确保域名解析到公网IP，端口 80/443 未被占用/未被防火墙拦截
- GPU不可见：确认主机已安装 `nvidia-container-toolkit`，`nvidia-smi` 可用，并重启 docker
- 路径问题：若容器日志提示 `MuseTalk目录不存在`，请确认仓库根目录下存在 `MuseTalk` 文件夹，或按“准备 MuseTalk 源码”一节补齐。