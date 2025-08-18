# CI/CD（Mode B：镜像仓库 + Docker）

## 目标
- 每次推送到 `main`，自动构建两套镜像并推送到 GHCR：
  - `ghcr.io/<owner>/musetalk-python:<tag>`
  - `ghcr.io/<owner>/lmy-digitalhuman:<tag>`
- 服务器只需 `docker compose pull && up -d`，无需本地构建

## 配置步骤（仓库）
1. 打开 GitHub 仓库 Settings → Actions → General：
   - Workflow permissions: 选择 “Read and write permissions”
   - 勾选 “Allow GitHub Actions to create and approve pull requests”（可选）
2. 无需额外 Secrets（使用内置 `GITHUB_TOKEN` 推送 GHCR）。
   - 若要推送 Docker Hub，配置 `DOCKERHUB_USERNAME`、`DOCKERHUB_TOKEN` Secrets，并在工作流中启用相应步骤。

## 工作流
- 文件：`.github/workflows/docker-images.yml`
- 触发：Push 到 `main` / 手动 `workflow_dispatch`
- Tag 规则：`latest`、短 SHA、时间戳

## 服务器部署（生产）
1. 准备目录与 `.env`：参考 `README_DOCKER.md` → 一次性安装
2. 编辑 `.env`：
   ```env
   # 镜像位置（默认GHCR）
   REGISTRY=ghcr.io
   NAMESPACE=你的GitHub用户名或组织
   PY_IMAGE=musetalk-python
   WEB_IMAGE=lmy-digitalhuman
   TAG=latest

   # HTTPS/域名
   DOMAIN=your.domain.com
   ACME_EMAIL=your-email@example.com

   # GPU选择
   CUDA_VISIBLE_DEVICES=0,1
   ```
3. 启动生产栈：
   ```bash
   ./scripts/deploy_prod.sh
   ```
   - 首次会自动申请证书，等待 1-2 分钟
   - 访问 `https://your.domain.com/swagger`

## 更新代码 → 发布镜像 → 部署
- 开发者：推送代码到 `main`，GitHub Actions 自动构建并推送镜像
- 服务器：
  ```bash
  cd /opt/musetalk/repo
  ./scripts/deploy_prod.sh
  ```

## 与现有应用共存
- 若服务器已有 Nginx 占用 80/443：
  - 方案A：不运行 Traefik，改用 Nginx 反向代理到 `lmy-digitalhuman:5000`（保持HTTPS）
  - 方案B：保留 Traefik 改到 8080/8443，并由外层 Nginx 反代到 Traefik（复杂度更高）

## 故障排查
- 镜像拉取失败：检查 `REGISTRY/NAMESPACE/TAG` 是否与CI输出一致，或改用 `TAG` 为短 SHA
- 证书未签发：确认域名解析与 80/443 未被占用/未被防火墙拦截
- GPU 不可见：确认安装并配置 `nvidia-container-toolkit`，`nvidia-smi` 正常