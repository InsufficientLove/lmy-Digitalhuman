#!/bin/bash
# 修复缓存路径配置

echo "修复Python文件中的缓存路径..."

# 修复global_musetalk_service.py
if [ -f "/workspace/MuseTalkEngine/global_musetalk_service.py" ]; then
    echo "处理 global_musetalk_service.py"
    # 在初始化部分添加缓存目录配置
    sed -i '/self._initialized = True/i \        # 获取统一的模板缓存目录\n        self.template_cache_dir = os.environ.get("MUSE_TEMPLATE_CACHE_DIR", "/opt/musetalk/template_cache")\n        print(f"使用模板缓存目录: {self.template_cache_dir}")\n' /workspace/MuseTalkEngine/global_musetalk_service.py
fi

# 创建初始化脚本
cat > /workspace/init_cache_dir.sh << 'SCRIPT'
#!/bin/bash
CACHE_DIR="${MUSE_TEMPLATE_CACHE_DIR:-/opt/musetalk/template_cache}"
echo "初始化缓存目录: $CACHE_DIR"
mkdir -p "$CACHE_DIR"
chmod 755 "$CACHE_DIR"
echo "缓存目录初始化完成"
SCRIPT

chmod +x /workspace/init_cache_dir.sh

echo "修复完成！"
