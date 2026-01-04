# 🐳 Docker 部署使用说明

## 📦 容器信息

您的项目包含 **3 个 Docker 容器**：

### 1. traefik
- **容器名称**: `traefik`
- **作用**: 反向代理和 HTTPS 证书管理
- **端口**: 
  - `80` (HTTP)
  - `443` (HTTPS)
- **状态**: 自动重启 (unless-stopped)

### 2. musetalk-python
- **容器名称**: `musetalk-python`
- **作用**: MuseTalk Python 推理引擎
- **端口**: 
  - `28888` (HTTP API)
  - `8766` (WebSocket 流式处理)
- **GPU**: 使用 GPU 0 和 1
- **状态**: 自动重启 (unless-stopped)

### 3. lmy-digitalhuman
- **容器名称**: `lmy-digitalhuman`
- **作用**: C# 前端 Web 服务
- **端口**: `5000`
- **依赖**: musetalk-python
- **状态**: 自动重启 (unless-stopped)

---

## 🚀 基本操作

### 启动所有服务
```bash
cd /workspace
docker-compose up -d
```

### 查看容器状态
```bash
docker-compose ps
# 或
docker ps
```

### 查看日志
```bash
# 查看所有容器日志
docker-compose logs -f

# 查看特定容器日志
docker-compose logs -f musetalk-python
docker-compose logs -f lmy-digitalhuman
docker-compose logs -f traefik
```

### 重启服务
```bash
# 重启所有服务
docker-compose restart

# 重启特定服务
docker-compose restart musetalk-python
docker-compose restart lmy-digitalhuman
```

### 停止服务
```bash
# 停止所有服务
docker-compose stop

# 停止特定服务
docker-compose stop musetalk-python
```

### 停止并删除容器
```bash
docker-compose down
```

---

## 🧪 测试方法

### 1. 健康检查

#### 测试 Python 推理服务
```bash
# 方法 1: HTTP API
curl http://localhost:28888/health

# 预期返回
{"status": "healthy", "service": "MuseTalk API"}
```

#### 测试 C# Web 服务
```bash
# 方法 1: 直接访问
curl http://localhost:5000

# 方法 2: 通过域名访问（如果配置了 HTTPS）
curl https://your-domain.com
```

### 2. GPU 使用检查

```bash
# 检查容器内 GPU 可用性
docker exec musetalk-python nvidia-smi

# 预期输出：显示 GPU 0 和 GPU 1 的状态
```

### 3. 进入容器调试

```bash
# 进入 Python 容器
docker exec -it musetalk-python bash

# 进入 C# 容器
docker exec -it lmy-digitalhuman bash
```

### 4. 完整功能测试

#### 访问 Web 界面
- **本地访问**: http://localhost:5000
- **域名访问**: https://your-domain.com (如果配置了 DOMAIN 环境变量)

#### 测试推理 API
```bash
# 查看 API 文档
curl http://localhost:28888/docs
# 在浏览器中访问: http://localhost:28888/docs
```

---

## 📊 监控和诊断

### 查看容器资源占用
```bash
docker stats
```

### 查看 GPU 使用情况
```bash
# 实时监控
watch -n 1 nvidia-smi

# 或进入容器查看
docker exec musetalk-python nvidia-smi
```

### 查看磁盘占用
```bash
# 查看 Docker 镜像大小
docker images

# 查看容器大小
docker ps -s
```

---

## ⚙️ 配置说明

### 环境变量

在启动前，需要设置环境变量（如果使用 HTTPS）：

```bash
# 创建 .env 文件
cat > .env << 'EOF'
DOMAIN=your-domain.com
ACME_EMAIL=your-email@example.com
EOF
```

### 挂载卷

以下目录会持久化存储：

- `/opt/musetalk/models` - 模型文件
- `/opt/musetalk/template_cache` - 模板预处理缓存
- `/opt/musetalk/templates` - 模板文件
- `/opt/musetalk/cache` - 其他缓存
- `/opt/musetalk/videos` - 生成的视频
- `/opt/musetalk/temp` - 临时文件

---

## 🔧 故障排查

### 问题 1: 容器无法启动

```bash
# 查看详细错误
docker-compose logs musetalk-python

# 检查端口占用
netstat -tulpn | grep -E '28888|8766|5000|80|443'
```

### 问题 2: GPU 不可用

```bash
# 检查 nvidia-container-toolkit
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi

# 如果失败，重启 Docker
sudo systemctl restart docker
```

### 问题 3: C# 服务无法连接 Python 服务

```bash
# 检查网络连通性
docker exec lmy-digitalhuman ping musetalk-python

# 检查 Python 服务是否运行
docker exec musetalk-python curl http://localhost:28888/health
```

### 问题 4: HTTPS 证书问题

```bash
# 查看 Traefik 日志
docker-compose logs traefik

# 检查 Let's Encrypt 证书
ls -la ./letsencrypt/acme.json
```

---

## 📝 更新服务

### 更新代码后重新构建

```bash
# 停止服务
docker-compose down

# 拉取最新代码
git pull

# 重新构建并启动
docker-compose up -d --build
```

### 仅更新特定服务

```bash
# 重新构建 C# 服务
docker-compose up -d --build lmy-digitalhuman

# 重新构建 Python 服务（如果使用 build 而不是 image）
docker-compose up -d --build musetalk-python
```

---

## 🎯 快速命令参考

```bash
# 启动
docker-compose up -d

# 查看状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 重启
docker-compose restart

# 停止
docker-compose stop

# 删除
docker-compose down

# 测试 Python API
curl http://localhost:28888/health

# 测试 C# Web
curl http://localhost:5000

# 查看 GPU
docker exec musetalk-python nvidia-smi

# 进入容器
docker exec -it musetalk-python bash
```

---

## 📞 技术支持

如遇问题，请提供以下信息：

1. 容器状态: `docker-compose ps`
2. 错误日志: `docker-compose logs [service-name]`
3. GPU 状态: `nvidia-smi`
4. 系统资源: `docker stats`

---

**部署成功！祝使用愉快！** 🎉
