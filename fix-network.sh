#!/bin/bash

echo "========================================="
echo "修复网络访问问题"
echo "========================================="

echo ""
echo "当前运行的容器："
docker ps --format "table {{.Names}}\t{{.Ports}}" | grep -E "NAMES|lmy-digitalhuman"

echo ""
echo "检查使用的docker-compose命令..."

# 检查容器是如何启动的
CONTAINER_LABELS=$(docker inspect lmy-digitalhuman 2>/dev/null | grep "com.docker.compose.project.config_files" | cut -d'"' -f4)

if [ -z "$CONTAINER_LABELS" ]; then
    echo "容器未运行或未使用docker-compose启动"
else
    echo "容器使用的配置文件: $CONTAINER_LABELS"
fi

echo ""
echo "========================================="
echo "解决方案："
echo "========================================="

echo ""
echo "方案1: 使用docker-compose.local.yml（推荐）"
echo "----------------------------------------"
echo "cd /opt/musetalk/repo"
echo "docker-compose -f docker-compose.yml -f docker-compose.local.yml down lmy-digitalhuman"
echo "docker-compose -f docker-compose.yml -f docker-compose.local.yml up -d lmy-digitalhuman"
echo ""

echo "方案2: 直接添加端口映射"
echo "----------------------------------------"
echo "docker stop lmy-digitalhuman"
echo "docker rm lmy-digitalhuman"
echo "docker run -d --name lmy-digitalhuman \\"
echo "  -p 5000:5000 \\"
echo "  -v /opt/musetalk/models:/models \\"
echo "  -v /opt/musetalk/videos:/videos \\"
echo "  -v /opt/musetalk/temp:/temp \\"
echo "  --network repo_web \\"
echo "  -e ASPNETCORE_URLS=http://0.0.0.0:5000 \\"
echo "  -e ASPNETCORE_ENVIRONMENT=Linux \\"
echo "  lmy-digitalhuman:latest"
echo ""

echo "方案3: 修改docker-compose.yml添加端口"
echo "----------------------------------------"
echo "在 docker-compose.yml 的 lmy-digitalhuman 服务下添加:"
echo "    ports:"
echo '      - "5000:5000"'
echo "然后重启服务"
echo ""

echo "========================================="
echo "防火墙配置（如果需要）："
echo "========================================="

# 检测系统和防火墙
if command -v ufw &> /dev/null; then
    echo "# Ubuntu/Debian (ufw):"
    echo "sudo ufw allow 5000/tcp"
    echo "sudo ufw reload"
elif command -v firewall-cmd &> /dev/null; then
    echo "# CentOS/RHEL (firewalld):"
    echo "sudo firewall-cmd --permanent --add-port=5000/tcp"
    echo "sudo firewall-cmd --reload"
else
    echo "# 使用iptables:"
    echo "sudo iptables -A INPUT -p tcp --dport 5000 -j ACCEPT"
    echo "sudo iptables-save"
fi

echo ""
echo "# 云服务器安全组："
echo "请在云服务商控制台添加入站规则："
echo "- 协议: TCP"
echo "- 端口: 5000"
echo "- 来源: 0.0.0.0/0 (或指定IP)"