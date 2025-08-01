#!/bin/bash

# 数字人系统 Docker 部署脚本
# 支持开发和生产环境

set -e

echo "================================"
echo "数字人系统 - Docker 部署脚本"
echo "================================"

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装！请先安装Docker"
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose 未安装！请先安装Docker Compose"
    exit 1
fi

# 获取部署模式
DEPLOY_MODE=${1:-"development"}

echo "🚀 部署模式: $DEPLOY_MODE"

# 创建必要的目录
echo "📁 创建数据目录..."
mkdir -p data/{templates,videos,temp,logs}
mkdir -p models
mkdir -p nginx

# 设置权限
chmod -R 755 data/
chmod -R 755 models/

echo "✅ 目录创建完成"

# 构建镜像
echo "🔨 构建Docker镜像..."
docker-compose build --no-cache

if [ $? -ne 0 ]; then
    echo "❌ 镜像构建失败！"
    exit 1
fi

echo "✅ 镜像构建成功"

# 启动服务
echo "🚀 启动服务..."

if [ "$DEPLOY_MODE" = "production" ]; then
    echo "🌐 生产模式 - 启动完整服务栈（包含Nginx）"
    docker-compose --profile production up -d
else
    echo "🔧 开发模式 - 仅启动核心服务"
    docker-compose up -d digitalhuman ollama
fi

if [ $? -ne 0 ]; then
    echo "❌ 服务启动失败！"
    exit 1
fi

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 健康检查
echo "🔍 检查服务状态..."
docker-compose ps

# 检查数字人服务
echo "🩺 健康检查..."
for i in {1..10}; do
    if curl -f http://localhost:5000/api/diagnostics/system-info > /dev/null 2>&1; then
        echo "✅ 数字人服务正常运行"
        break
    fi
    echo "⏳ 等待服务响应... ($i/10)"
    sleep 3
done

# 检查Ollama服务
if curl -f http://localhost:11434/api/version > /dev/null 2>&1; then
    echo "✅ Ollama服务正常运行"
else
    echo "⚠️  Ollama服务可能未完全启动，请检查日志"
fi

echo ""
echo "================================"
echo "🎉 部署完成！"
echo "================================"
echo ""
echo "服务地址："
echo "  数字人API: http://localhost:5000"
echo "  Swagger文档: http://localhost:5000/swagger"
echo "  Ollama API: http://localhost:11434"
echo "  系统诊断: http://localhost:5000/api/diagnostics/python-environments"

if [ "$DEPLOY_MODE" = "production" ]; then
    echo "  Web界面: http://localhost (通过Nginx)"
fi

echo ""
echo "常用命令："
echo "  查看日志: docker-compose logs -f digitalhuman"
echo "  停止服务: docker-compose down"
echo "  重启服务: docker-compose restart"
echo "  查看状态: docker-compose ps"
echo ""

# 显示下一步操作
echo "下一步操作："
echo "1. 访问 http://localhost:5000/api/diagnostics/python-environments 检查Python环境"
echo "2. 确保Ollama已下载所需模型: docker exec ollama-service ollama pull qwen2.5vl:7b"
echo "3. 上传数字人模板到 ./data/templates/ 目录"
echo "4. 测试API接口功能"
echo ""

echo "如需帮助，请查看日志:"
echo "  docker-compose logs digitalhuman"
echo "  docker-compose logs ollama"