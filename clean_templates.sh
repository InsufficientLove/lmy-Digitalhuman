#!/bin/bash
# 模板清理脚本 - 彻底删除所有模板信息

echo "========================================="
echo "模板清理工具"
echo "========================================="

# 1. 清理容器内的模板文件
echo "1. 清理容器内模板文件..."
docker exec lmy-digitalhuman bash -c "rm -f /app/wwwroot/templates/*.json" 2>/dev/null
docker exec lmy-digitalhuman bash -c "rm -f /app/wwwroot/templates/*.jpg" 2>/dev/null
docker exec lmy-digitalhuman bash -c "rm -f /app/wwwroot/templates/*.png" 2>/dev/null
echo "   ✓ 容器内模板文件已清理"

# 2. 清理宿主机的预处理缓存
echo "2. 清理宿主机缓存..."
if [ -d "/opt/musetalk/template_cache" ]; then
    sudo rm -rf /opt/musetalk/template_cache/*
    echo "   ✓ 预处理缓存已清理"
else
    echo "   ! 缓存目录不存在"
fi

# 3. 清理本地开发目录（如果存在）
echo "3. 清理本地开发目录..."
if [ -d "./LmyDigitalHuman/wwwroot/templates" ]; then
    rm -f ./LmyDigitalHuman/wwwroot/templates/*.json
    rm -f ./LmyDigitalHuman/wwwroot/templates/*.jpg
    rm -f ./LmyDigitalHuman/wwwroot/templates/*.png
    echo "   ✓ 本地开发目录已清理"
fi

# 4. 重启服务以清空内存缓存
echo "4. 重启服务清空内存缓存..."
docker-compose restart lmy-digitalhuman
echo "   ✓ 服务已重启"

echo ""
echo "========================================="
echo "清理完成！所有模板信息已删除"
echo "========================================="
echo ""
echo "提示："
echo "1. 如果前端仍显示模板，请清除浏览器缓存（Ctrl+F5）"
echo "2. 或在浏览器开发者工具中清除Application Storage"