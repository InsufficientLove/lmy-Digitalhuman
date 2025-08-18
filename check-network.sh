#!/bin/bash

echo "========================================="
echo "网络和端口诊断"
echo "========================================="

echo ""
echo "1. 检查容器是否在运行："
docker ps | grep lmy-digitalhuman

echo ""
echo "2. 检查容器端口映射："
docker port lmy-digitalhuman

echo ""
echo "3. 检查Docker网络配置："
docker inspect lmy-digitalhuman | grep -A 10 "NetworkMode"

echo ""
echo "4. 检查容器内部服务状态："
docker exec lmy-digitalhuman curl -s http://localhost:5000/health || echo "健康检查失败"

echo ""
echo "5. 检查防火墙状态（需要root权限）："
if command -v ufw &> /dev/null; then
    sudo ufw status | grep 5000 || echo "端口5000未在ufw规则中"
elif command -v firewall-cmd &> /dev/null; then
    sudo firewall-cmd --list-ports | grep 5000 || echo "端口5000未在firewalld规则中"
elif command -v iptables &> /dev/null; then
    sudo iptables -L -n | grep 5000 || echo "端口5000未在iptables规则中找到"
else
    echo "未检测到防火墙工具"
fi

echo ""
echo "6. 检查端口监听状态："
sudo netstat -tlnp | grep 5000 || sudo ss -tlnp | grep 5000 || echo "端口5000未监听"

echo ""
echo "7. 测试本地访问："
curl -s -o /dev/null -w "HTTP状态码: %{http_code}\n" http://localhost:5000/health

echo ""
echo "8. 检查Docker Compose配置的端口："
grep -A 5 "lmy-digitalhuman" docker-compose*.yml | grep -E "ports:|5000"

echo ""
echo "9. 检查容器日志（最后10行）："
docker logs --tail 10 lmy-digitalhuman

echo ""
echo "========================================="
echo "诊断建议："
echo "========================================="

# 检查是否使用了正确的compose文件
if [ -f "docker-compose.local.yml" ]; then
    echo "✓ 找到 docker-compose.local.yml"
    echo "  确保使用: docker-compose -f docker-compose.yml -f docker-compose.local.yml up -d"
else
    echo "✗ 未找到 docker-compose.local.yml"
fi

echo ""
echo "如果端口未开放，请执行："
echo "1. Ubuntu/Debian: sudo ufw allow 5000"
echo "2. CentOS/RHEL: sudo firewall-cmd --permanent --add-port=5000/tcp && sudo firewall-cmd --reload"
echo "3. 云服务器: 检查安全组规则，确保5000端口已开放"
echo ""
echo "重启容器："
echo "docker-compose -f docker-compose.yml -f docker-compose.local.yml restart lmy-digitalhuman"